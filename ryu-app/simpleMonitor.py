# Copyright (c) 2014 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

import logging
import datetime

from netaddr.ip import IPNetwork
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

LOG = logging.getLogger('SimpleMonitor')
LOG.setLevel(logging.INFO)
logging.basicConfig()


class SimpleMonitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor, self).__init__(*args, **kwargs)
        self.name = 'monitor'
        self.monitor_thread = hub.spawn(self._monitor)
        self.datapaths = {}
        self.portStats = {}
        self.flowStats = {}


    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                LOG.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                LOG.debug('deregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]


    def _monitor(self):
        while True:
            for datapath in self.datapaths.values():
                self.request_stats(datapath)
            hub.sleep(10)


    def request_stats(self, datapath):
        LOG.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        for stat in sorted(body, key=attrgetter('port_no')):
            self.portStats[stat.port_no] = PortStats(stat.port_no,
                                                     stat.rx_packets,
                                                     stat.rx_bytes,
                                                     stat.rx_errors,
                                                     stat.tx_packets,
                                                     stat.tx_bytes,
                                                     stat.tx_errors)


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        for stat in [flow for flow in body if flow.priority == 2]: 
            self.flowStats[stat.match["in_port"]] = FlowStats(
                                                   stat.match["ipv4_dst"],
                                                   stat.packet_count,
                                                   stat.byte_count)

        for stat in [flow for flow in body if flow.priority == 15]: 
            if isinstance(stat.match["ipv4_dst"], str):
                ipv4dst = stat.match["ipv4_dst"]
                self.flowStats[ipv4dst] = FlowStats(
                                                   ipv4dst,
                                                   stat.packet_count,
                                                   stat.byte_count)
            else:
                ipaddress = stat.match["ipv4_dst"][0]
                netmask = stat.match["ipv4_dst"][1]
                prefix = IPNetwork(ipaddress + '/' + netmask)
                ipv4dst = str(prefix.cidr)
                self.flowStats[ipv4dst] = FlowStats(
                                                   ipv4dst,
                                                   stat.packet_count,
                                                   stat.byte_count)

        for stat in [flow for flow in body if flow.priority == 1]: 
            self.flowStats["*"] = FlowStats(
                                                   "0.0.0.0/0",
                                                   stat.packet_count,
                                                   stat.byte_count)


class PortStats(object):
    def __init__(self, portNo, rxPackets, rxBytes, rxErrors, txPackets,
                 txBytes, txErrors):
        super(PortStats, self).__init__()

        self.portNo = portNo
        self.rxPackets = rxPackets
        self.rxBytes = rxBytes
        self.rxErrors = rxErrors
        self.txPackets = txPackets
        self.txBytes = txBytes
        self.txErrors = txErrors

    def getPort(self, direction):
        if direction == "rx":
            return self.portNo, self.rxPackets, self.rxBytes, self.rxErrors
        elif direction == "tx":
            return self.portNo, self.txPackets, self.txBytes, self.txErrors


class FlowStats(object):
    def __init__(self, ipv4Dst, packetCount, byteCount):
        super(FlowStats, self).__init__()

        self.ipv4Dst = ipv4Dst
        self.packets = packetCount
        self.bytes = byteCount

    def getFlow(self):
        return self.ipv4Dst, self.packets, self.bytes
