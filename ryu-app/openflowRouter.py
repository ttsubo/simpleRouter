# Copyright (c) 2014 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

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
LOG.setLevel(logging.DEBUG)

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
        self.bgp_thread = hub.spawn(self.update_remotePrefix)
        self.redistributeConnect = False


    def register_localPrefix(self, dpid, destIpAddr, netMask, nextHopIpAddr, routeDist='65010:101'):
        if routeDist:
            label = self.bgps.add_prefix(destIpAddr, netMask, nextHopIpAddr, routeDist)
            self.register_route_pop_mpls(dpid, routeDist, destIpAddr, netMask, label, nextHopIpAddr)
        else:
            self.bgps.add_prefix(destIpAddr, netMask, nextHopIpAddr)
            self.register_route(dpid, destIpAddr, netMask, nextHopIpAddr)


    def delete_localPrefix(self, dpid, destIpAddr, netMask):
        self.remove_route(dpid, destIpAddr, netMask)
        self.bgps.remove_prefix(destIpAddr, netMask)


    def get_bgp_rib(self):
        return self.bgps.show_rib()


    def redistribute_connect(self, dpid, redistribute, routeDist='65010:101'):
        netMask = "255.255.255.255"
        nextHopIpAddr = None
        if redistribute == "ON":
            if self.redistributeConnect:
                LOG.info("Skip redistributeConnect[ON]")
            else:
                self.redistributeConnect = True
                for portNo, port in self.portInfo.items():
                    (routerIpAddr, routerMacAddr, routerPort1) = port.get_all()
                    for arp in self.arpInfo.values():
                        (hostIpAddr, hostMacAddr, routerPort2) = arp.get_all()
                        if routerPort1 == routerPort2:
                            destIpAddr = hostIpAddr
                            if routeDist:
                                label = self.bgps.add_prefix(destIpAddr,netMask
                                                    , None, routeDist)
                                self.register_route_pop_mpls(dpid, routeDist,
                                                    destIpAddr, netMask, label,
                                                    nextHopIpAddr)
                            else:
                                self.register_route(dpid, destIpAddr, netMask,
                                                    nextHopIpAddr)
                                self.bgps.add_prefix(destIpAddr, netMask)

        elif redistribute == "OFF":
            if self.redistributeConnect:
                self.redistributeConnect = False
                for portNo, port in self.portInfo.items():
                    (routerIpAddr, routerMacAddr, routerPort1) = port.get_all()
                    for arp in self.arpInfo.values():
                        (hostIpAddr, hostMacAddr, routerPort2) = arp.get_all()
                        if routerPort1 == routerPort2:
                            destIpAddr = hostIpAddr
                            self.remove_route(dpid, destIpAddr, netMask)
                            self.bgps.remove_prefix(destIpAddr, netMask)
            else:
                LOG.info("Skip redistributeConnect[OFF]")


    def update_remotePrefix(self):
        while True:
            dpid = 1
            if not self.bgps.bgp_q.empty():
                remotePrefix = self.bgps.bgp_q.get()
                LOG.debug("remotePrefix=%s"%remotePrefix)
                routeDist = remotePrefix['route_dist']
                destIpAddr = remotePrefix['prefix']
                netMask = remotePrefix['netmask']
                nextHopIpAddr = remotePrefix['nexthop']
                labelList = remotePrefix['label']
                label = labelList[0]
                withdraw = remotePrefix['withdraw']
                if withdraw:
                    if label:
                        pass
                    else:
                        self.remove_route(dpid, destIpAddr, netMask)
                else:
                    if label:
                        if destIpAddr != "0.0.0.0":
                            self.register_route_push_mpls(dpid, routeDist,
                                                     destIpAddr, netMask, label,
                                                     nextHopIpAddr)
                        else:
                            pass
                    else:
                        if destIpAddr != "0.0.0.0":
                            self.register_route(dpid, destIpAddr, netMask,
                                                nextHopIpAddr)
                        else:
                            self.register_gateway(dpid, nextHopIpAddr)
            hub.sleep(1)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(OpenflowRouter, self).switch_features_handler(ev)
        datapath = ev.msg.datapath


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        super(OpenflowRouter, self).packet_in_handler(ev)


    def start_bgpspeaker(self, dpid, as_number, router_id):
        if as_number:
            asNum = int(as_number)
        LOG.debug("start BGPSpeaker [%s, %s]"%(as_number, router_id))
        self.bgps.start_bgpspeaker(asNum, router_id)


    def start_bmpclient(self, dpid, address, port):
        if port:
            portNum = int(port)
        LOG.debug("start BmpClient [%s, %s]"%(address, port))
        self.bgps.start_bmpclient(address, portNum)


    def stop_bmpclient(self, dpid, address, port):
        if port:
            portNum = int(port)
        LOG.debug("stop BmpClient [%s, %s]"%(address, port))
        self.bgps.stop_bmpclient(address, portNum)


    def register_inf(self, dpid, routerIp, netMask, routerMac, hostIp, asNumber, Port, bgpPort, med, localPref, filterAsNumber):
        LOG.debug("Register Interface(port%s)"% Port)
        datapath = self.monitor.datapaths[dpid]
        outPort = int(Port)
        self.send_arp(datapath, 1, routerMac, routerIp, "ff:ff:ff:ff:ff:ff",
                      hostIp, outPort)
        LOG.debug("send ARP request %s => %s (port%d)"
                 %(routerMac, "ff:ff:ff:ff:ff:ff", outPort))

        if bgpPort:
            offloadPort = int(bgpPort)
            if asNumber:
                asNum = int(asNumber)

            if med:
                medValue = int(med)
            else:
                medValue = None

            if localPref:
                localPrefValue = int(localPref)
            else:
                localPrefValue = None

            if filterAsNumber:
                filterAsNum = int(filterAsNumber)
            else:
                filterAsNum = None

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
            self.bgps.add_neighbor(hostIp, asNum, medValue, localPrefValue,
                                   filterAsNum)


    def send_ping(self, dpid, targetIp, seq, data, sendPort):
        datapath = self.monitor.datapaths[dpid]

        for portNo, arp in self.arpInfo.items():
            if portNo == sendPort:
                (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()

        for portNo, port in self.portInfo.items():
            if portNo == sendPort:
                (routerIpAddr, routerMacAddr, routerPort) = port.get_all()

        srcIp = routerIpAddr
        srcMac = routerMacAddr
        dstIp = targetIp
        dstMac = hostMacAddr

        self.send_icmp(datapath, srcMac, srcIp, dstMac, dstIp, sendPort, seq,
                       data)
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

        if mod_dstMac and mod_srcMac:
            self.add_flow_gateway(datapath, ether.ETH_TYPE_IP, mod_srcMac,
                                  mod_dstMac, outPort, defaultIpAddr)
            LOG.debug("Send Flow_mod packet for gateway(%s)"% defaultIpAddr)
        else:
            LOG.debug("Unknown defaultIpAddress!!")


    def register_route(self, dpid, destIpAddr, netMask, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort
            else:
                if destIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort

        for port in self.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            if routerPort == outPort:
                mod_srcMac = routerMacAddr

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s]"%(destIpAddr,
                      netMask, nextHopIpAddr))
            self.add_flow_route(datapath, ether.ETH_TYPE_IP, destIpAddr,
                                netMask, mod_srcMac, mod_dstMac, outPort,
                                nextHopIpAddr)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")
 

    def register_route_push_mpls(self, dpid, routeDist, destIpAddr, netMask, label, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort
            else:
                if destIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort

        for port in self.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            if routerPort == outPort:
                mod_srcMac = routerMacAddr

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s, %s, %s]"%(routeDist,
                      destIpAddr, netMask, nextHopIpAddr, label))
            self.add_flow_push_mpls(datapath, ether.ETH_TYPE_IP, routeDist,
                                    label, destIpAddr, netMask, mod_srcMac,
                                    mod_dstMac, outPort, nextHopIpAddr)
            self.add_flow_mpls(datapath, label, mod_srcMac, mod_dstMac, outPort)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")

 
    def register_route_pop_mpls(self, dpid, routeDist, destIpAddr, netMask, label, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (hostIpAddr, hostMacAddr, routerPort) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort
            else:
                if destIpAddr == hostIpAddr:
                    mod_dstMac = hostMacAddr
                    outPort = routerPort

        for port in self.portInfo.values():
            (routerIpAddr, routerMacAddr, routerPort) = port.get_all()
            if routerPort == outPort:
                mod_srcMac = routerMacAddr

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s, %s, %s]"%(routeDist,
                       destIpAddr, netMask, nextHopIpAddr, label))
            self.add_flow_pop_mpls(datapath, ether.ETH_TYPE_IP, routeDist,
                                   label, destIpAddr, netMask, mod_srcMac,
                                   mod_dstMac, outPort, nextHopIpAddr)
#            self.add_flow_mpls(datapath, label, mod_srcMac, mod_dstMac, outPort)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")


    def remove_route(self, dpid, destIpAddr, netMask):
        datapath = self.monitor.datapaths[dpid]

        LOG.debug("Send Flow_mod(delete) [%s, %s]"%(destIpAddr, netMask))
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


    @route('router', '/openflow/{dpid}/rib', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_bgprib(self, req, dpid, **kwargs):

        result = self.getBgpRib(int(dpid, 16))
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


    @route('router', '/openflow/{dpid}/status/peer', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_peerstatus(self, req, dpid, **kwargs):

        result = self.getPeerStatus(int(dpid, 16))
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


    @route('router', '/openflow/{dpid}/bgp', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def start_bgp(self, req, dpid, **kwargs):

        bgp_param = eval(req.body)
        result = self.startBgp(int(dpid, 16), bgp_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/bmp', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def start_bmp(self, req, dpid, **kwargs):

        bmp_param = eval(req.body)
        result = self.startBmp(int(dpid, 16), bmp_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/bmp', methods=['DELETE'], requirements={'dpid': dpid.DPID_PATTERN})
    def stop_bmp(self, req, dpid, **kwargs):

        bmp_param = eval(req.body)
        result = self.stopBmp(int(dpid, 16), bmp_param)

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

    @route('router', '/openflow/{dpid}/redistribute', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def set_redistributeConnect(self, req, dpid, **kwargs):

        connect_param = eval(req.body)
        result = self.redistributeConnect(int(dpid, 16), connect_param)

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


    def startBgp(self, dpid, bgp_param):
        simpleRouter = self.router_spp
        as_number = bgp_param['bgp']['as_number']
        router_id = bgp_param['bgp']['router_id']

        simpleRouter.start_bgpspeaker(dpid, as_number, router_id)

        return {
            'id': '%016d' % dpid,
            'bgp': {
                'as_number': '%s' % as_number,
                'router_id': '%s' % router_id,
            }
        }


    def startBmp(self, dpid, bmp_param):
        simpleRouter = self.router_spp
        address = bmp_param['bmp']['address']
        port = bmp_param['bmp']['port']

        simpleRouter.start_bmpclient(dpid, address, port)

        return {
            'id': '%016d' % dpid,
            'bmp': {
                'address': '%s' % address,
                'port': '%s' % port,
            }
        }


    def stopBmp(self, dpid, bmp_param):
        simpleRouter = self.router_spp
        address = bmp_param['bmp']['address']
        port = bmp_param['bmp']['port']

        simpleRouter.stop_bmpclient(dpid, address, port)

        return {
            'id': '%016d' % dpid,
            'bmp': {
                'address': '%s' % address,
                'port': '%s' % port,
            }
        }


    def setInterface(self, dpid, interface_param):
        simpleRouter = self.router_spp
        routerMac = interface_param['interface']['macaddress']
        routerIp = interface_param['interface']['ipaddress']
        netMask = interface_param['interface']['netmask']
        port = interface_param['interface']['port']
        hostIp = interface_param['interface']['opposite_ipaddress']
        asNumber = interface_param['interface']['opposite_asnumber']
        port_offload_bgp = interface_param['interface']['port_offload_bgp']
        bgp_med = interface_param['interface']['bgp_med']
        bgp_local_pref = interface_param['interface']['bgp_local_pref']
        filterAsNumber = interface_param['interface']['bgp_filter_asnumber']


        simpleRouter.register_inf(dpid, routerIp, netMask, routerMac, hostIp, asNumber, port, port_offload_bgp, bgp_med, bgp_local_pref, filterAsNumber)

        return {
            'id': '%016d' % dpid,
            'interface': {
                'port': '%s' % port,
                'macaddress': '%s' % routerMac,
                'ipaddress': '%s' % routerIp,
                'netmask': '%s' % netMask,
                'opposite_ipaddress': '%s' % hostIp,
                'opposite_asnumber': '%s' % asNumber,
                'port_offload_bgp': '%s' % port_offload_bgp,
                'bgp_med': '%s' % bgp_med,
                'bgp_local_pref': '%s' % bgp_local_pref,
                'bgp_filter_asnumber': '%s' % filterAsNumber
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


    def redistributeConnect(self, dpid, connect_param):
        simpleRouter = self.router_spp
        redistribute = connect_param['bgp']['redistribute']

        simpleRouter.redistribute_connect(dpid, redistribute)

        return {
            'id': '%016d' % dpid,
            'bgp': {
                'redistribute': '%s' % redistribute,
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

        if result:
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

        for k, v in sorted(simpleRouter.portInfo.items()):
            (routerIpAddr, routerMacAddr, routerPort) = v.get_all()
            LOG.info("%8x %-15s %s" % (routerPort, routerIpAddr, routerMacAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'interface': [
            v.__dict__ for k, v in sorted(simpleRouter.portInfo.items())
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

        for k, v in sorted(simpleRouter.arpInfo.items()):
            (hostIpAddr, hostMacAddr, routerPort) = v.get_all()
            LOG.info("%8x %s %s" % (routerPort, hostMacAddr, hostIpAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'arp': [
            v.__dict__ for k, v in sorted(simpleRouter.arpInfo.items())
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

        for k, v in sorted(simpleRouter.routingInfo.items()):
            (prefix, nextHopIpAddr) = v.get_route()
            LOG.info("%-18s %-15s" % (prefix, nextHopIpAddr))

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'route': [
            v.__dict__ for k, v in sorted(simpleRouter.routingInfo.items())
          ]
        }


    def getBgpRib(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : Show rib " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")

        result = simpleRouter.get_bgp_rib()
        LOG.info("%s" % result)

        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'rib': '%s' % result,
        }



    def getPortStats(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : PortStats" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("portNo   rxPackets rxBytes  rxErrors txPackets txBytes  txErrors")
        LOG.info("-------- --------- -------- -------- --------- -------- --------")

        for k, v in sorted(simpleRouter.monitor.portStats.items()):
            (portNo, rxPackets, rxBytes, rxErrors) = v.getPort("rx")
            (portNo, txPackets, txBytes, txErrors) = v.getPort("tx")
            LOG.info("%8x %9d %8d %8d %9d %8d %8d" % (portNo,
                                                  rxPackets, rxBytes, rxErrors,
                                                  txPackets, txBytes, txErrors))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'stats': [
            v.__dict__ for k, v in sorted(simpleRouter.monitor.portStats.items())
          ]
        }


    def getFlowStats(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : FlowStats" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("destination        packets    bytes")
        LOG.info("------------------ ---------- ----------")

        for k, v in sorted(simpleRouter.monitor.flowStats.items()):
            (ipv4Dst, packets, bytes) = v.getFlow()
            LOG.info("%-18s %10d %10d" % (ipv4Dst, packets, bytes))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'stats': [
            v.__dict__ for k, v in sorted(simpleRouter.monitor.flowStats.items())
          ]
        }


    def getPeerStatus(self, dpid):
        simpleRouter = self.router_spp

        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : Peer Status " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("occurTime            status    myPeer             remotePeer         asNumber")
        LOG.info("-------------------- --------- ------------------ ------------------ --------")

        for k, v in sorted(simpleRouter.bgps.bgpPeerStatus.items()):
            (occurTime, status, myPeer, remotePeer, asNumber) = v.getStatus()
            LOG.info("%s  %-9s %-18s %-18s %s" % (occurTime, status, myPeer,
                                               remotePeer, asNumber))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'status': [
            v.__dict__ for k, v in sorted(simpleRouter.bgps.bgpPeerStatus.items())
          ]
        }

