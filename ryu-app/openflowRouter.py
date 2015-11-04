# Copyright (c) 2014-2015 ttsubo
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
        self.bgp_thread = hub.spawn(self.update_remotePrefix)
        self.arp_thread = hub.spawn(self.send_arpRequest)


    def register_localPrefix(self, dpid, destIpAddr, netMask, nextHopIpAddr,
                             vrf_routeDist):
        if vrf_routeDist:
            label = self.bgps.add_prefix(destIpAddr, netMask, nextHopIpAddr,
                                         vrf_routeDist)
            self.register_route_pop_mpls(dpid, vrf_routeDist, destIpAddr,
                                         netMask, label, nextHopIpAddr)
        else:
            self.bgps.add_prefix(destIpAddr, netMask, nextHopIpAddr)
            self.register_route(dpid, destIpAddr, netMask, nextHopIpAddr)


    def delete_localPrefix(self, dpid, destIpAddr, netMask, vrf_routeDist):
        if vrf_routeDist:
            self.remove_route_pop_mpls(dpid, vrf_routeDist, destIpAddr, netMask)
            self.bgps.remove_prefix(destIpAddr, netMask, vrf_routeDist)
        else:
            self.remove_route(dpid, destIpAddr, netMask)
            self.bgps.remove_prefix(destIpAddr, netMask)


    def get_bgp_rib(self):
        return self.bgps.show_rib()


    def get_bgp_vrfs(self):
        return self.bgps.show_vrfs()


    def get_bgp_neighbor(self, routetype, address):
        return self.bgps.show_neighbor(routetype, address)


    def redistribute_connect(self, dpid, redistribute, vrf_routeDist):
        netMask = "255.255.255.255"
        nextHopIpAddr = None
        if redistribute == "ON":
            for portNo, port in self.portInfo.items():
                (ipAddr1, macAddr1, port1, routeDist) = port.get_all()
                if vrf_routeDist == routeDist:
                    for arp in self.arpInfo.values():
                        (ipAddr2, macAddr2, port2) = arp.get_all()
                        if port1 == port2:
                            destIpAddr = ipAddr2

            label = self.bgps.add_prefix(destIpAddr, netMask, None, routeDist)
            self.register_route_pop_mpls(dpid, routeDist, destIpAddr, netMask,
                                         label, nextHopIpAddr)
        elif redistribute == "OFF":
            for portNo, port in self.portInfo.items():
                (ipAddr1, macAddr1, port1, routeDist) = port.get_all()
                if vrf_routeDist == routeDist:
                    for arp in self.arpInfo.values():
                        (ipAddr2, macAddr2, port2) = arp.get_all()
                        if port1 == port2:
                            destIpAddr = ipAddr2
            self.bgps.remove_prefix(destIpAddr, netMask, routeDist)
            self.remove_route_pop_mpls(dpid, routeDist, destIpAddr, netMask)


    def update_remotePrefix(self):
        while True:
            dpid = 1
            if not self.bgps.bgp_q.empty():
                remotePrefix = self.bgps.bgp_q.get()
                LOG.debug("remotePrefix=%s"%remotePrefix)
                vrf_routeDist = remotePrefix['route_dist']
                destIpAddr = remotePrefix['prefix']
                netMask = remotePrefix['netmask']
                nextHopIpAddr = remotePrefix['nexthop']
                labelList = remotePrefix['label']
                label = labelList[0]
                withdraw = remotePrefix['withdraw']
                if withdraw:
                    if label:
                        self.remove_route_push_mpls(dpid, vrf_routeDist, label,
                                                    destIpAddr, netMask)
                    else:
                        self.remove_route(dpid, destIpAddr, netMask)
                else:
                    if label:
                        if destIpAddr != "0.0.0.0":
                            self.register_route_push_mpls(dpid, vrf_routeDist,
                                                     destIpAddr, netMask, label,
                                                     nextHopIpAddr)
                        else:
                            self.register_gateway_push_mpls(dpid, vrf_routeDist,
                                                            label, nextHopIpAddr)
                    else:
                        if destIpAddr != "0.0.0.0":
                            self.register_route(dpid, destIpAddr, netMask,
                                                nextHopIpAddr)
                        else:
                            self.register_gateway(dpid, nextHopIpAddr)
            hub.sleep(1)


    def send_arpRequest(self):
        dpid = 1
        while True:
            try:
                datapath = self.monitor.datapaths[dpid]
                for arp in self.arpInfo.values():
                    (hostIp, hostMac, inPort) = arp.get_all()

                    for port in self.portInfo.values():
                        (routerIp, routerMac, port, routeDist) = port.get_all()

                        if inPort == port:
                            self.send_arp(datapath, 1, routerMac, routerIp,
                               "ff:ff:ff:ff:ff:ff", hostIp, inPort, routeDist)
                            LOG.info("send ARP request %s => %s (port%d)"
                                   %(routerMac, "ff:ff:ff:ff:ff:ff", inPort))
            except KeyError:
                datapath = None

            hub.sleep(60)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(OpenflowRouter, self).switch_features_handler(ev)
        datapath = ev.msg.datapath


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        super(OpenflowRouter, self).packet_in_handler(ev)


    def start_bgpspeaker(self, dpid, as_number, router_id, label_range_start, label_range_end):
        if as_number:
            asNum = int(as_number)
            label_start = int(label_range_start)
            label_end = int(label_range_end)
        LOG.debug("start BGPSpeaker [%s, %s]"%(as_number, router_id))
        self.bgps.start_bgpspeaker(asNum, router_id, label_start, label_end)


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


    def register_vrf(self, dpid, vrf_routeDist, importRt, exportRt):
        importList = []
        exportList = []
        importList.append(importRt)
        exportList.append(exportRt)
        LOG.debug("Register vrf(RD:%s)"%vrf_routeDist)
        self.bgps.add_vrf(vrf_routeDist, importList, exportList)


    def delete_vrf(self, dpid, vrf_routeDist):
        LOG.debug("Delete vrf(RD:%s)"%vrf_routeDist)
        self.bgps.del_vrf(vrf_routeDist)


    def register_inf(self, dpid, routerIp, netMask, routerMac, hostIp, asNumber, Port, bgpPort, med, localPref, filterAsNumber, vrf_routeDist):
        LOG.debug("Register Interface(port%s)"% Port)
        datapath = self.monitor.datapaths[dpid]
        outPort = int(Port)
        self.send_arp(datapath, 1, routerMac, routerIp, "ff:ff:ff:ff:ff:ff",
                      hostIp, outPort, vrf_routeDist)
        self.arpInfo[outPort] = ArpTable(hostIp, "", outPort)
        LOG.info("send ARP request %s => %s (port%d)"
                 %(routerMac, "ff:ff:ff:ff:ff:ff", outPort))


    def send_ping(self, dpid, targetIp, seq, data, sendPort):
        datapath = self.monitor.datapaths[dpid]

        for portNo, arp in self.arpInfo.items():
            if portNo == sendPort:
                (ipAddr1, macAddr1, port1) = arp.get_all()

        for portNo, port in self.portInfo.items():
            if portNo == sendPort:
                (ipAddr2, macAddr2, port2, routeDist) = port.get_all()

        srcIp = ipAddr2
        srcMac = macAddr2
        dstIp = targetIp
        dstMac = macAddr1

        self.send_icmp(datapath, srcMac, srcIp, dstMac, dstIp, sendPort, seq,
                       data)
        LOG.debug("send icmp echo request %s => %s (port%d)"
                   %(srcMac, dstMac, sendPort))


    def register_gateway(self, dpid, defaultIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (ipAddr1, macAddr1, port1) = arp.get_all()
            if defaultIpAddr == ipAddr1:
                mod_dstMac = macAddr1
                outPort = port1

        for port in self.portInfo.values():
            (ipAddr2, macAddr2, port2, routeDist) = port.get_all()
            if port2 == outPort:
                mod_srcMac = macAddr2

        if mod_dstMac and mod_srcMac:
            self.add_flow_gateway(datapath, ether.ETH_TYPE_IP, mod_srcMac,
                                  mod_dstMac, outPort, defaultIpAddr)
            LOG.debug("Send Flow_mod packet for gateway(%s)"% defaultIpAddr)
        else:
            LOG.debug("Unknown defaultIpAddress!!")


    def register_gateway_push_mpls(self, dpid, vrf_routeDist, label, defaultIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (ipAddr1, macAddr1, port1) = arp.get_all()
            if defaultIpAddr == ipAddr1:
                mod_dstMac = macAddr1
                outPort = port1

        for port in self.portInfo.values():
            (ipAddr2, macAddr2, port2, routeDist) = port.get_all()
            if port2 == outPort:
                mod_srcMac = macAddr2

        if mod_dstMac and mod_srcMac:
            self.add_flow_gateway_push_mpls(datapath, ether.ETH_TYPE_IP,
                                            vrf_routeDist, label, mod_srcMac,
                                            mod_dstMac, outPort, defaultIpAddr)
            LOG.debug("Send Flow_mod packet for gateway(%s)"% defaultIpAddr)
            self.add_flow_mpls(datapath, label, mod_srcMac, mod_dstMac, outPort)
        else:
            LOG.debug("Unknown defaultIpAddress!!")


    def register_route(self, dpid, destIpAddr, netMask, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (ipAddr1, macAddr1, port1) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1
            else:
                if destIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1

        for port in self.portInfo.values():
            (ipAddr2, macAddr2, port2, routeDist) = port.get_all()
            if port2 == outPort:
                mod_srcMac = macAddr2

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s]"%(destIpAddr,
                      netMask, nextHopIpAddr))
            self.add_flow_route(datapath, ether.ETH_TYPE_IP, destIpAddr,
                                netMask, mod_srcMac, mod_dstMac, outPort,
                                nextHopIpAddr)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")
 

    def register_route_push_mpls(self, dpid, vrf_routeDist, destIpAddr, netMask, label, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (ipAddr1, macAddr1, port1) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1
            else:
                if destIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1

        for port in self.portInfo.values():
            (ipAddr2, macAddr2, port2, routeDist) = port.get_all()
            if port2 == outPort:
                mod_srcMac = macAddr2

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s, %s, %s]"%(
                      vrf_routeDist, destIpAddr, netMask, nextHopIpAddr, label))
            self.add_flow_push_mpls(datapath, ether.ETH_TYPE_IP, vrf_routeDist,
                                    label, destIpAddr, netMask, mod_srcMac,
                                    mod_dstMac, outPort, nextHopIpAddr)
            self.add_flow_mpls(datapath, label, mod_srcMac, mod_dstMac, outPort)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")

 
    def register_route_pop_mpls(self, dpid, vrf_routeDist, destIpAddr, netMask, label, nextHopIpAddr):
        datapath = self.monitor.datapaths[dpid]

        for arp in self.arpInfo.values():
            (ipAddr1, macAddr1, port1) = arp.get_all()
            if nextHopIpAddr:
                if nextHopIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1
            else:
                if destIpAddr == ipAddr1:
                    mod_dstMac = macAddr1
                    outPort = port1

        for port in self.portInfo.values():
            (ipAddr2, macAddr2, port2, routeDist) = port.get_all()
            if port2 == outPort:
                mod_srcMac = macAddr2

        if mod_dstMac and mod_srcMac:
            LOG.debug("Send Flow_mod(create) [%s, %s, %s, %s, %s]"%(
                      vrf_routeDist, destIpAddr, netMask, nextHopIpAddr, label))
            self.add_flow_pop_mpls(datapath, ether.ETH_TYPE_IP, vrf_routeDist,
                                   label, destIpAddr, netMask, mod_srcMac,
                                   mod_dstMac, outPort, nextHopIpAddr)
        else:
            LOG.debug("Unknown nextHopIpAddress!!")


    def remove_route(self, dpid, destIpAddr, netMask):
        datapath = self.monitor.datapaths[dpid]
        LOG.debug("Send Flow_mod(delete) [%s, %s]"%(destIpAddr, netMask))
        self.remove_flow_route(datapath, ether.ETH_TYPE_IP, destIpAddr, netMask)


    def remove_route_pop_mpls(self, dpid, vrf_routeDist, destIpAddr, netMask):
        datapath = self.monitor.datapaths[dpid]
        LOG.debug("Send Flow_mod(delete) [%s, %s, %s]"%(vrf_routeDist,
                  destIpAddr, netMask))
        ipaddress = IPNetwork(destIpAddr + '/' + netMask)
        prefix = str(ipaddress.cidr)
        vpnv4Prefix = vrf_routeDist + ':' + prefix

        for vpnv4_prefix, mpls in self.mplsInfo.items():
            if vpnv4_prefix == vpnv4Prefix:
                (routeDist, prefix, label, nexthop) = mpls.get_mpls()
                self.remove_flow_pop_mpls(datapath, vpnv4_prefix, label)


    def remove_route_push_mpls(self, dpid, vrf_routeDist, label, destIpAddr, netMask):
        datapath = self.monitor.datapaths[dpid]
        LOG.debug("Send Flow_mod(delete) [%s, %s, %s]"%(vrf_routeDist,
                  destIpAddr, netMask))
        ipaddress = IPNetwork(destIpAddr + '/' + netMask)
        prefix = str(ipaddress.cidr)
        vpnv4Prefix = vrf_routeDist + ':' + prefix

        self.remove_flow_push_mpls(datapath, label, destIpAddr, netMask,
                                   vpnv4Prefix)
        self.remove_flow_mpls(datapath, label)


    def update_neighborMed(self, dpid, peerIp, med): 
        LOG.debug("change MED [%s]"% med)
        med_value = int(med)
        self.bgps.update_neighbor_med(peerIp, med_value)


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


    @route('router', '/openflow/{dpid}/mpls', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_MPLS(self, req, dpid, **kwargs):
        result = self.getMpls(int(dpid, 16))
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


    @route('router', '/openflow/{dpid}/neighbor', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_bgpneighbor(self, req, dpid, **kwargs):
        show_param = eval(req.body)
        result = self.getBgpNeighbor(int(dpid, 16), show_param)
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/vrf', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_bgpvrfs(self, req, dpid, **kwargs):
        result = self.getBgpVrfs(int(dpid, 16))
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


    @route('router', '/openflow/{dpid}/vrf', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def create_vrf(self, req, dpid, **kwargs):
        vrf_param = eval(req.body)
        result = self.createVrf(int(dpid, 16), vrf_param)
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/vrf', methods=['DELETE'], requirements={'dpid': dpid.DPID_PATTERN})
    def delete_vrf(self, req, dpid, **kwargs):
        vrf_param = eval(req.body)
        result = self.deleteVrf(int(dpid, 16), vrf_param)
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
    def create_route(self, req, dpid, **kwargs):
        route_param = eval(req.body)
        result = self.createRoute(int(dpid, 16), route_param)
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/route', methods=['DELETE'], requirements={'dpid': dpid.DPID_PATTERN})
    def delete_route(self, req, dpid, **kwargs):
        route_param = eval(req.body)
        result = self.deleteRoute(int(dpid, 16), route_param)
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


    @route('router', '/openflow/{dpid}/neighbor', methods=['PUT'], requirements={'dpid': dpid.DPID_PATTERN})
    def update_med(self, req, dpid, **kwargs):
        neighbor_param = eval(req.body)
        result = self.updateNeighborMed(int(dpid, 16), neighbor_param)
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    def startBgp(self, dpid, bgp_param):
        simpleRouter = self.router_spp
        as_number = bgp_param['bgp']['as_number']
        router_id = bgp_param['bgp']['router_id']
        label_range_start = bgp_param['bgp']['label_range_start']
        label_range_end = bgp_param['bgp']['label_range_end']
        simpleRouter.start_bgpspeaker(dpid, as_number, router_id, label_range_start, label_range_end)
        return {
            'id': '%016d' % dpid,
            'bgp': {
                'as_number': '%s' % as_number,
                'router_id': '%s' % router_id,
                'label_range_start': '%s' % label_range_start,
                'label_range_end': '%s' % label_range_end,
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


    def createVrf(self, dpid, vrf_param):
        simpleRouter = self.router_spp
        routeDist = vrf_param['vrf']['route_dist']
        importRt = vrf_param['vrf']['import']
        exportRt = vrf_param['vrf']['export']
        simpleRouter.register_vrf(dpid, routeDist, importRt, exportRt)
        return {
            'id': '%016d' % dpid,
            'vrf': {
                'route_dist': '%s' % routeDist,
                'import': '%s' % importRt,
                'export': '%s' % exportRt,
            }
        }


    def deleteVrf(self, dpid, vrf_param):
        simpleRouter = self.router_spp
        routeDist = vrf_param['vrf']['route_dist']
        simpleRouter.delete_vrf(dpid, routeDist)
        return {
            'id': '%016d' % dpid,
            'vrf': {
                'route_dist': '%s' % routeDist
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
        vrf_routeDist = interface_param['interface']['vrf_routeDist']
        simpleRouter.register_inf(dpid, routerIp, netMask, routerMac, hostIp, asNumber, port, port_offload_bgp, bgp_med, bgp_local_pref, filterAsNumber, vrf_routeDist)
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
                'bgp_filter_asnumber': '%s' % filterAsNumber,
                'vrf_routeDist': '%s' % vrf_routeDist
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


    def createRoute(self, dpid, route_param):
        simpleRouter = self.router_spp
        destinationIp = route_param['route']['destination']
        netMask = route_param['route']['netmask']
        nexthopIp = route_param['route']['nexthop']
        vrf_routeDist = route_param['route']['vrf_routeDist']
        simpleRouter.register_localPrefix(dpid, destinationIp, netMask,
                                          nexthopIp, vrf_routeDist)
        return {
            'id': '%016d' % dpid,
            'route': {
                'destination': '%s' % destinationIp,
                'netmask': '%s' % netMask,
                'nexthop': '%s' % nexthopIp,
                'vrf_routeDist': '%s' % vrf_routeDist
            }
        }



    def deleteRoute(self, dpid, route_param):
        simpleRouter = self.router_spp
        destinationIp = route_param['route']['destination']
        netMask = route_param['route']['netmask']
        vrf_routeDist = route_param['route']['vrf_routeDist']
        simpleRouter.delete_localPrefix(dpid, destinationIp, netMask,
                                        vrf_routeDist)
        return {
            'id': '%016d' % dpid,
            'route': {
                'destination': '%s' % destinationIp,
                'netmask': '%s' % netMask,
                'vrf_routeDist': '%s' % vrf_routeDist
            }
        }


    def redistributeConnect(self, dpid, connect_param):
        simpleRouter = self.router_spp
        redistribute = connect_param['bgp']['redistribute']
        vrf_routeDist = connect_param['bgp']['vrf_routeDist']
        simpleRouter.redistribute_connect(dpid, redistribute, vrf_routeDist)
        return {
            'id': '%016d' % dpid,
            'bgp': {
                'redistribute': '%s' % redistribute,
                'vrf_routeDist': '%s' % vrf_routeDist,
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


    def updateNeighborMed(self, dpid, neighbor_param):
        simpleRouter = self.router_spp
        peerIp = neighbor_param['neighbor']['peerIp']
        med = neighbor_param['neighbor']['med']
        simpleRouter.update_neighborMed(dpid, peerIp, med)
        return {
            'id': '%016d' % dpid,
            'neighbor': {
                'peerIp': '%s' % peerIp,
                'med': '%s' % med,
            }
        }


    def getInterface(self, dpid):
        simpleRouter = self.router_spp
        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : PortTable" % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("portNo   IpAddress       MacAddress        RouteDist")
        LOG.info("-------- --------------- ----------------- ---------")
        for k, v in sorted(simpleRouter.portInfo.items()):
            (routerIpAddr, routerMacAddr, routerPort, routeDist) = v.get_all()
            LOG.info("%8x %-15s %-15s %s" % (routerPort, routerIpAddr, routerMacAddr, routeDist))
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
            LOG.info("%8x %17s %s" % (routerPort, hostMacAddr, hostIpAddr))
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


    def getMpls(self, dpid):
        simpleRouter = self.router_spp
        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : MplsTable " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("routeDist  prefix             nexthop          label")
        LOG.info("---------- ------------------ ---------------- -----")
        for k, v in sorted(simpleRouter.mplsInfo.items()):
            (routeDist, prefix, label, nextHopIpAddr) = v.get_mpls()
            LOG.info("%s  %-18s %-15s  %-5s" % (routeDist, prefix,
                                               nextHopIpAddr, label))
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'mpls': [
            v.__dict__ for k, v in sorted(simpleRouter.mplsInfo.items())
          ]
        }


    def getBgpNeighbor(self, dpid, show_param):
        simpleRouter = self.router_spp
        routetype = show_param['neighbor']['routetype']
        address = show_param['neighbor']['address']
        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : Show neighbor " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        result = simpleRouter.get_bgp_neighbor(routetype, address)
        LOG.info("%s" % result)
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'neighbor': '%s' % result,
        }


    def getBgpVrfs(self, dpid):
        simpleRouter = self.router_spp
        nowtime = datetime.datetime.now()
        LOG.info("+++++++++++++++++++++++++++++++")
        LOG.info("%s : Show vrf " % nowtime.strftime("%Y/%m/%d %H:%M:%S"))
        LOG.info("+++++++++++++++++++++++++++++++")
        result = simpleRouter.get_bgp_vrfs()
        LOG.info("%s" % result)
        return {
          'id': '%016d' % dpid,
          'time': '%s' % nowtime.strftime("%Y/%m/%d %H:%M:%S"),
          'vrfs': '%s' % result,
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
        LOG.info("destination(label) packets    bytes")
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

