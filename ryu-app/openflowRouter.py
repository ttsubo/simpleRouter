import json
import logging
import datetime
import time

from simpleRouter import *
from simpleMonitor import SimpleMonitor
from simpleBGPSpeaker import SimpleBGPSpeaker
from ryu.lib import dpid
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

LOG = logging.getLogger('OpenflowRouter')
LOG.setLevel(logging.INFO)

class OpenflowRouter(SimpleRouter):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'monitor' : SimpleMonitor,
        'bgps' : SimpleBGPSpeaker,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(OpenflowRouter, self).__init__(*args, **kwargs)
        self.monitor = kwargs['monitor']
        self.bgps = kwargs['bgps']
        self.ports = {}
        wsgi = kwargs['wsgi']
        wsgi.register(RouterController, {'OpenFlowRouter' : self})
        self.bgp_thread = hub.spawn(self.register_remotePrefix)


    def register_localPrefix(self, dpid, destIpAddr, netMask, nextHopIpAddr):
        self.register_route(dpid, destIpAddr, netMask, nextHopIpAddr)
        self.bgps.add_prefix(destIpAddr, netMask, nextHopIpAddr)


    def delete_localPrefix(self, dpid, destIpAddr, netMask):
        self.remove_route(dpid, destIpAddr, netMask)
        self.bgps.remove_prefix(destIpAddr, netMask)


    def register_remotePrefix(self):
        while True:
            dpid = 1
            if not self.bgps.bgp_q.empty():
                remotePrefix = self.bgps.bgp_q.get()
                LOG.debug("remotePrefix=%s"%remotePrefix)
                destIpAddr = remotePrefix['prefix']
                netMask = remotePrefix['netmask']
                nextHopIpAddr = remotePrefix['nexthop']
                self.register_route(dpid, destIpAddr, netMask, nextHopIpAddr)
            hub.sleep(1)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(OpenflowRouter, self).switch_features_handler(ev)
        datapath = ev.msg.datapath

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        super(OpenflowRouter, self).packet_in_handler(ev)


    def register_inf(self, dpid, routerIp, netMask, routerMac, hostIp, Port, bgpPort):
        LOG.debug("Register Interface(port%s)"% Port)
        datapath = self.monitor.datapaths[dpid]
        outPort = int(Port)
        if outPort == ROUTER_PORT1 or outPort == ROUTER_PORT2:
            self.send_arp(datapath, 1, routerMac, routerIp, "ff:ff:ff:ff:ff:ff",
                          hostIp, outPort)
            LOG.debug("send ARP request %s => %s (port%d)"
                     %(routerMac, "ff:ff:ff:ff:ff:ff", outPort))
            LOG.debug("Send Flow_mod packet for interface(%s)"% routerIp)
            self.add_flow_my_port(datapath, ether.ETH_TYPE_IP, routerIp)
            if bgpPort=="":
                pass
            else:
                offloadPort = int(bgpPort)
                LOG.debug("Send Flow_mod packet for bgp offload(arp)")
                self.add_flow_for_bgp(datapath, offloadPort, ether.ETH_TYPE_ARP,
                                      "", outPort)
                self.add_flow_for_bgp(datapath, outPort, ether.ETH_TYPE_ARP,
                                      "", offloadPort)
                LOG.debug("Send Flow_mod packet for bgp offload(%s)"% routerIp)
                self.add_flow_for_bgp(datapath, outPort, ether.ETH_TYPE_IP,
                                      routerIp, offloadPort)
                LOG.debug("Send Flow_mod packet for bgp offload(%s)"% hostIp)
                self.add_flow_for_bgp(datapath, offloadPort, ether.ETH_TYPE_IP,
                                      hostIp, outPort)
                LOG.debug("start BGP peering with [%s]"% hostIp)
                self.bgps.add_neighbor(hostIp, 65001)
        else:
            LOG.debug("Unknown Interface!!")

        self.bgps.add_prefix(routerIp, netMask)


    def send_ping(self, dpid, targetIp, seq, data, sendPort):
        datapath = self.monitor.datapaths[dpid]

        for portNo, arp in self.arpInfo.items():
            if portNo == ROUTER_PORT1:
                (hostIpAddr1, hostMacAddr1, routerPort1) = arp.get_all()
            elif portNo == ROUTER_PORT2:
                (hostIpAddr2, hostMacAddr2, routerPort2) = arp.get_all()

        for portNo, port in self.portInfo.items():
            if portNo == ROUTER_PORT1:
                (routerIpAddr1, routerMacAddr1, routerPort1) = port.get_all()
            elif portNo == ROUTER_PORT2:
                (routerIpAddr2, routerMacAddr2, routerPort2) = port.get_all()

        if sendPort == ROUTER_PORT1:
            srcIp = routerIpAddr1
            srcMac = routerMacAddr1
            dstIp = targetIp
            dstMac = hostMacAddr1
        elif sendPort == ROUTER_PORT2:
            srcIp = routerIpAddr2
            srcMac = routerMacAddr2
            dstIp = targetIp
            dstMac = hostMacAddr2
        else:
            LOG.debug("Illegal port!!")
            return

        self.send_icmp(datapath, srcMac, srcIp, dstMac, dstIp, sendPort, seq, data)
        LOG.debug("send icmp echo request %s => %s (port%d)"
                   %(srcMac, dstMac, sendPort))


    def register_gateway(self, dpid, defaultIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            if defaultIpAddr == hostIpAddr:
                mod_dstMac = hostMacAddr
                outPort = routerPort

        for port in self.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            if routerPort == outPort:
                mod_srcMac = routerMacAddr

        if mod_dstMac != None and mod_srcMac !=None:
            self.add_flow_gateway(datapath, ether.ETH_TYPE_IP, mod_srcMac,
                                  mod_dstMac, outPort, defaultIpAddr)
            LOG.debug("Send Flow_mod packet for gateway(%s)"% defaultIpAddr)
        else:
            LOG.debug("Unknown defaultIpAddress!!")


    def register_route(self, dpid, destIpAddr, netMask, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            if nextHopIpAddr == hostIpAddr:
                mod_dstMac = hostMacAddr
                outPort = routerPort

        for port in self.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            if routerPort == outPort:
                mod_srcMac = routerMacAddr

        if mod_dstMac != None and mod_srcMac !=None:
            LOG.debug("Send Flow_mod packet for route(%s, %s, %s)"%(destIpAddr, netMask, nextHopIpAddr))
            self.add_flow_route(datapath, ether.ETH_TYPE_IP, destIpAddr, netMask, mod_srcMac, mod_dstMac, outPort, nextHopIpAddr)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")


    def remove_route(self, dpid, destIpAddr, netMask):
        datapath = self.monitor.datapaths[dpid]

        LOG.debug("Send Flow_mod packet for route(%s, %s)"%(destIpAddr, netMask))
        self.remove_flow_route(datapath, ether.ETH_TYPE_IP, destIpAddr, netMask)


class RouterController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RouterController, self).__init__(req, link, data, **config)
        self.router_spp = data['OpenFlowRouter']

    @route('router', '/openflow/{dpid}/interface', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_interface(self, req, dpid, **kwargs):

        result = self.getInterface(int(dpid, 16))
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/arp', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_arp(self, req, dpid, **kwargs):

        result = self.getArp(int(dpid, 16))
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/route', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_route(self, req, dpid, **kwargs):

        result = self.getRoute(int(dpid, 16))
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/stats/port', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_portstats(self, req, dpid, **kwargs):

        result = self.getPortStats(int(dpid, 16))
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/stats/flow', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_flowstats(self, req, dpid, **kwargs):

        result = self.getFlowStats(int(dpid, 16))
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/ping', methods=['PUT'], requirements={'dpid': dpid.DPID_PATTERN})
    def put_ping(self, req, dpid, **kwargs):
        ping_param = eval(req.body)
        result = self.putIcmp(int(dpid, 16), ping_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/interface', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def set_interface(self, req, dpid, **kwargs):

        interface_param = eval(req.body)
        result = self.setInterface(int(dpid, 16), interface_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/gateway', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def set_gateway(self, req, dpid, **kwargs):

        gateway_param = eval(req.body)
        result = self.setGateway(int(dpid, 16), gateway_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)

    @route('router', '/openflow/{dpid}/route', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def set_route(self, req, dpid, **kwargs):

        route_param = eval(req.body)
        result = self.setRoute(int(dpid, 16), route_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/route', methods=['DELETE'], requirements={'dpid': dpid.DPID_PATTERN})
    def delete_route(self, req, dpid, **kwargs):

        route_param = eval(req.body)
        result = self.delRoute(int(dpid, 16), route_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    def setInterface(self, dpid, interface_param):
        simpleRouter = self.router_spp
        routerMac = interface_param['interface']['macaddress']
        routerIp = interface_param['interface']['ipaddress']
        netMask = interface_param['interface']['netmask']
        port = interface_param['interface']['port']
        hostIp = interface_param['interface']['opposite_ipaddress']
        port_offload_bgp = interface_param['interface']['port_offload_bgp']

        simpleRouter.register_inf(dpid, routerIp, netMask, routerMac, hostIp, port, port_offload_bgp)

        return {
            'id': '%016d' % dpid,
            'interface': {
                'port': '%s' % port,
                'macaddress': '%s' % routerMac,
                'ipaddress': '%s' % routerIp,
                'netmask': '%s' % netMask,
                'opposite_ipaddress': '%s' % hostIp,
                'port_offload_bgp': '%s' % port_offload_bgp
            }
        }


    def setGateway(self, dpid, gateway_param):
        simpleRouter = self.router_spp
        defaultIp = gateway_param['gateway']['ipaddress']

        simpleRouter.register_gateway(dpid, defaultIp)

        return {
            'id': '%016d' % dpid,
            'gateway': {
                'ipaddress': '%s' % defaultIp,
            }
        }

    def setRoute(self, dpid, route_param):
        simpleRouter = self.router_spp
        destinationIp = route_param['route']['destination']
        netMask = route_param['route']['netmask']
        nexthopIp = route_param['route']['nexthop']

        simpleRouter.register_localPrefix(dpid, destinationIp, netMask, nexthopIp)

        return {
            'id': '%016d' % dpid,
            'route': {
                'destination': '%s' % destinationIp,
                'netmask': '%s' % netMask,
                'nexthop': '%s' % nexthopIp,
            }
        }


    def delRoute(self, dpid, route_param):
        simpleRouter = self.router_spp
        destinationIp = route_param['route']['destination']
        netMask = route_param['route']['netmask']

        simpleRouter.delete_localPrefix(dpid, destinationIp, netMask)

        return {
            'id': '%016d' % dpid,
            'route': {
                'destination': '%s' % destinationIp,
                'netmask': '%s' % netMask,
            }
        }


    def putIcmp(self, dpid, ping_param):
        result = {}
        simpleRouter = self.router_spp
        hostIp = ping_param['ping']['hostIp']
        outPort = ping_param['ping']['outPort']
        data = ping_param['ping']['data']

        result[0] = "PING %s : %d data bytes" % (hostIp, len(data))
        for seq in range(1,6):
            ret = simpleRouter.send_ping(dpid, hostIp, seq, data, int(outPort))
            for i in range(5):
                if not simpleRouter.ping_q.empty():
                    result[seq] = "ping ok (%s)"% simpleRouter.ping_q.get()
                    break
                else:
                    time.sleep(1)
            else:
                result[seq] = "ping ng ( Request Timeout for icmp_seq %d )" %seq

        if result != None:
            return {
               'id': '%016d' % dpid,
               'ping': result.values()
            }


    def getInterface(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : PortTable" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("portNo   IpAddress       MacAddress")
        LOG.info("-------- --------------- -----------------")

        for port in simpleRouter.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            LOG.info("%8x %-15s %s" % (routerPort, routerIpAddr, routerMacAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'interface': [
            port.__dict__ for port in simpleRouter.portInfo.values()
          ]
        }


    def getArp(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : ArpTable " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("portNo   MacAddress        IpAddress")
        LOG.info("-------- ----------------- ------------")

        for arp in simpleRouter.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            LOG.info("%8x %s %s" % (routerPort, hostMacAddr, hostIpAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'arp': [
            arp.__dict__ for arp in simpleRouter.arpInfo.values()
          ]
        }


    def getRoute(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : RoutingTable " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("prefix             nexthop")
        LOG.info("------------------ ---------------")

        for route in simpleRouter.routingInfo.values():
            (prefix, nextHopIpAddr) = route.get_route()
            LOG.info("%-18s %-15s" % (prefix, nextHopIpAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'route': [
            route.__dict__ for route in simpleRouter.routingInfo.values()
          ]
        }


    def getPortStats(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : PortStats" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("portNo   rxPackets rxBytes  rxErrors txPackets txBytes  txErrors")
        LOG.info("-------- --------- -------- -------- --------- -------- --------")

        for stat in simpleRouter.monitor.portStats.values():
            (portNo, rxPackets, rxBytes, rxErrors) = stat.getPort("rx")
            (portNo, txPackets, txBytes, txErrors) = stat.getPort("tx")
            LOG.info("%8x %9d %8d %8d %9d %8d %8d" % (portNo,
                                                  rxPackets, rxBytes, rxErrors,
                                                  txPackets, txBytes, txErrors))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'stats': [
            stat.__dict__ for stat in simpleRouter.monitor.portStats.values()
          ]
        }


    def getFlowStats(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : FlowStats" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("inPort   ethSrc             ethDst             ipv4Dst         packets  bytes")
        LOG.info("-------- ------------------ ------------------ --------------- -------- --------")

        for stat in simpleRouter.monitor.flowStats.values():
            (inPort, ethSrc, ethDst, ipv4Dst, packets, bytes) = stat.getFlow()
            LOG.info("%8s %18s %18s %15s %8d %8d" % (inPort, ethSrc, ethDst,
                                                  ipv4Dst, packets, bytes))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'stats': [
            stat.__dict__ for stat in simpleRouter.monitor.flowStats.values()
          ]
        }

