# Copyright (c) 2014-2015 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

import logging
import socket

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.arp import arp
from ryu.lib.packet.ipv4 import ipv4
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.lib import hub
from netaddr.ip import IPNetwork

LOG = logging.getLogger('SimpleRouter')
LOG.setLevel(logging.INFO)
logging.basicConfig()


class PortTable(object):
    def __init__(self, routerPort, routerIpAddr, routerMacAddr, routeDist):
        self.routerPort = routerPort
        self.routerIpAddr = routerIpAddr
        self.routerMacAddr = routerMacAddr
        self.routeDist = routeDist

    def get_ip(self):
        return self.routerIpAddr

    def get_all(self):
        return self.routerIpAddr, self.routerMacAddr, self.routerPort, self.routeDist

class ArpTable(object):
    def __init__(self, hostIpAddr, hostMacAddr, routerPort):
        self.hostIpAddr = hostIpAddr
        self.hostMacAddr = hostMacAddr
        self.routerPort = routerPort

    def get_mac(self):
        return self.hostMacAddr

    def get_all(self):
        return self.hostIpAddr, self.hostMacAddr, self.routerPort


class RoutingTable(object):
    def __init__(self, prefix, destIpAddr, netMask, nextHopIpAddr):
        self.prefix = prefix
        self.destIpAddr = destIpAddr
        self.netMask = netMask
        self.nextHopIpAddr = nextHopIpAddr

    def get_route(self):
        return self.prefix, self.nextHopIpAddr


class MplsTable(object):
    def __init__(self, routeDist, prefix, label, destIpAddr, netMask, nextHopIpAddr):
        self.routeDist = routeDist
        self.prefix = prefix
        self.label = label
        self.destIpAddr = destIpAddr
        self.netMask = netMask
        self.nextHopIpAddr = nextHopIpAddr

    def get_mpls(self):
        return self.routeDist, self.prefix, self.label, self.nextHopIpAddr


class SimpleRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleRouter, self).__init__(*args, **kwargs)
        self.ping_q = hub.Queue()
        self.portInfo = {}
        self.arpInfo = {}
        self.routingInfo = {}
        self.mplsInfo = {}


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        datapath.id = msg.datapath_id
        ofproto_parser = datapath.ofproto_parser

        set_config = ofproto_parser.OFPSetConfig(
            datapath,
            datapath.ofproto.OFPC_FRAG_NORMAL,
            datapath.ofproto.OFPCML_MAX,
        )
        datapath.send_msg(set_config)
        self.install_table_miss(datapath, datapath.id)
        return 0


    def install_table_miss(self, datapath, dpid):
        datapath.id = dpid

        match = datapath.ofproto_parser.OFPMatch()

        actions = [datapath.ofproto_parser.OFPActionOutput(
                datapath.ofproto.OFPP_CONTROLLER,
                datapath.ofproto.OFPCML_NO_BUFFER)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath,
                priority=0,
                buffer_id=0xffffffff,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        inPort = msg.match['in_port']

        packet = Packet(msg.data)
        etherFrame = packet.get_protocol(ethernet)
        if etherFrame.ethertype == ether.ETH_TYPE_ARP:
            self.receive_arp(datapath, packet, etherFrame, inPort)
        elif etherFrame.ethertype == ether.ETH_TYPE_IP:
            self.receive_ip(datapath, packet, etherFrame, inPort)
        else:
            LOG.debug("receive Unknown packet %s => %s (port%d)"
                       %(etherFrame.src, etherFrame.dst, inPort))
            self.print_etherFrame(etherFrame)
            LOG.debug("Drop packet")
            return 1
        return 0


    def receive_ip(self, datapath, packet, etherFrame, inPort):
        ipPacket = packet.get_protocol(ipv4)
        LOG.debug("receive IP packet %s => %s (port%d)"
                       %(etherFrame.src, etherFrame.dst, inPort))
        self.print_etherFrame(etherFrame)
        self.print_ipPacket(ipPacket)
        if ipPacket.proto == inet.IPPROTO_ICMP:
            icmpPacket = packet.get_protocol(icmp.icmp)
            self.check_icmp(datapath, etherFrame, ipPacket, icmpPacket, inPort)
            return 0
        else:
            LOG.debug("Drop packet")
            return 1

        for portNo in self.arpInfo.keys():
            if portNo == inPort:
                break
        else:
            hostIpAddr = ipPacket.src
            hostMacAddr = etherFrame.src
            self.arpInfo[inPort] = ArpTable(hostIpAddr, hostMacAddr, inPort)
        return 0


    def check_icmp(self, datapath, etherFrame, ipPacket, icmpPacket, inPort):
        srcMac = etherFrame.src
        dstMac = etherFrame.dst
        srcIp = ipPacket.src
        dstIp = ipPacket.dst
        ttl = ipPacket.ttl
        type = icmpPacket.type
        try:
            id = icmpPacket.data.id
        except:
            id = 1
        try:
            seq = icmpPacket.data.seq
        except:
            seq = 1
        try:
            data = icmpPacket.data.data
        except:
            data = ''

        if icmpPacket.type == 0: 
            self.print_icmp( icmpPacket )
            icmp_length = ipPacket.total_length - 20
            buf = (" %d bytes from %s: icmp_req=%d ttl=%d data=[%s] "
                   % (icmp_length, srcIp, seq, ttl, data))
            self.ping_q.put(buf)
        elif icmpPacket.type == 3: 
            buf = "ping ng ( Detination Unreachable )"
            self.ping_q.put(buf)
        elif icmpPacket.type == 8: 
            self.reply_icmp(datapath, srcMac, dstMac, srcIp, dstIp, ttl, type,
                            id, seq, data, inPort)
        elif icmpPacket.type == 11: 
            buf = "ping ng ( Time Exceeded )"
            self.ping_q.put(buf)
        else: 
            buf = "ping ng ( Unknown reason )"
            self.ping_q.put(buf)
        return 0


    def reply_icmp(self, datapath, srcMac, dstMac, srcIp, dstIp, ttl, type, id,
                   seq, data, inPort):

        sendSrcMac = None

        for portNo, port in self.portInfo.items():
            routerIpAddr = port.get_ip()
            if routerIpAddr == dstIp:
                sendSrcMac = dstMac
                sendDstMac = srcMac
                sendSrcIp = dstIp
                sendDstIp = srcIp
                sendPort = inPort

        if sendSrcMac:
            self.send_icmp(datapath, sendSrcMac, sendSrcIp, sendDstMac,
                           sendDstIp, sendPort, seq, data, id, 0, ttl)
            LOG.debug("send icmp echo reply %s => %s (port%d)"
                       %(sendSrcMac, sendDstMac, sendPort))
        else:
            LOG.debug("Drop packet")
        return 0


    def receive_arp(self, datapath, packet, etherFrame, inPort):
        arpPacket = packet.get_protocol(arp)
        hostIpAddr = arpPacket.src_ip
        hostMacAddr = arpPacket.src_mac
        if arpPacket.opcode == 1:
            operation = "ARP Request"
            arp_dstIp = arpPacket.dst_ip
        elif arpPacket.opcode == 2:
            operation = "ARP Reply"

        LOG.debug("receive %s %s => %s (port%d)"
                       %(operation, etherFrame.src, etherFrame.dst, inPort))
        self.print_etherFrame(etherFrame)
        self.print_arpPacket(arpPacket)

        if arpPacket.opcode == 1:
            self.reply_arp(datapath, etherFrame, arpPacket, arp_dstIp, inPort)
        elif arpPacket.opcode == 2:
            self.arpInfo[inPort] = ArpTable(hostIpAddr, hostMacAddr, inPort)
        return 0


    def reply_arp(self, datapath, etherFrame, arpPacket, arp_dstIp, inPort):

        srcMac = None
        dstIp = arpPacket.src_ip
        srcIp = arpPacket.dst_ip
        dstMac = etherFrame.src

        for portNo, port in self.portInfo.items():
            (routerIpAddr, routerMacAddr, routerPort, routeDist) = port.get_all()
            if arp_dstIp == routerIpAddr:
                srcMac = routerMacAddr
                outPort = portNo

        if srcMac:
            self.send_arp(datapath, 2, srcMac, srcIp, dstMac, dstIp, outPort)
            LOG.debug("send ARP reply %s => %s (port%d)" %(srcMac, dstMac, outPort))
            return 0
        else:
            LOG.debug("unknown arp requst received !")
            return 1


    def send_icmp(self, datapath, srcMac, srcIp, dstMac, dstIp, outPort, seq, data, id=1, type=8, ttl=64):

        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_IP)
        iph = ipv4(4, 5, 0, 0, 0, 2, 0, ttl, 1, 0, srcIp, dstIp)
        echo = icmp.echo(id, seq, data)
        icmph = icmp.icmp(type, 0, 0, echo)

        p = Packet()
        p.add_protocol(e)
        p.add_protocol(iph)
        p.add_protocol(icmph)
        p.serialize()

        actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=0xffffffff,
            in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=p.data)
        datapath.send_msg(out)
        return 0


    def send_arp(self, datapath, opcode, srcMac, srcIp, dstMac, dstIp, outPort, RouteDist=None):
        if opcode == 1:
            self.portInfo[outPort] = PortTable(outPort, srcIp, srcMac, RouteDist)

            targetMac = "00:00:00:00:00:00"
            targetIp = dstIp
        elif opcode == 2:
            targetMac = dstMac
            targetIp = dstIp

        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
        a = arp(1, 0x0800, 6, 4, opcode, srcMac, srcIp, targetMac, targetIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=0xffffffff,
            in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=p.data)
        datapath.send_msg(out)
        return 0


    def add_flow_gateway(self, datapath, ethertype, mod_srcMac, mod_dstMac, outPort, defaultGateway):
        ipaddress = IPNetwork("0.0.0.0" + '/' + "0.0.0.0")
        prefix = str(ipaddress.cidr)
        LOG.debug("add RoutingInfo(gateway) for %s"% prefix)
        self.routingInfo[prefix] = RoutingTable(prefix, "0.0.0.0", "0.0.0.0", defaultGateway)
        match = datapath.ofproto_parser.OFPMatch(eth_type=ethertype)
        actions =[datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionDecNwTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0x1,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def add_flow_gateway_push_mpls(self, datapath, ethertype, routeDist, label, mod_srcMac, mod_dstMac, outPort, defaultIpAddr):
        ipaddress = IPNetwork("0.0.0.0" + '/' + "0.0.0.0")
        prefix = str(ipaddress.cidr)
        vpnv4_prefix = routeDist + ':' + prefix
        LOG.debug("add MplsInfo(%s, [%s])"%(vpnv4_prefix, label))
        self.mplsInfo[vpnv4_prefix] = MplsTable(routeDist, prefix, label,
                                                "0.0.0.0", "0.0.0.0",
                                                defaultIpAddr)

        match = datapath.ofproto_parser.OFPMatch(eth_type=ethertype)
        actions =[datapath.ofproto_parser.OFPActionPushMpls(0x8847),
                datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionSetField(mpls_label=label),
                datapath.ofproto_parser.OFPActionSetField(mpls_tc=1),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionSetMplsTtl(255),
                datapath.ofproto_parser.OFPActionDecMplsTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0x1,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)


    def add_flow_route(self, datapath, ethertype, mod_dstIp, mod_dstMask, mod_srcMac, mod_dstMac, outPort, nexthop):
        ipaddress = IPNetwork(mod_dstIp + '/' + mod_dstMask)
        prefix = str(ipaddress.cidr)
        if nexthop is None:
            nexthop = "0.0.0.0"
        LOG.debug("add RoutingInfo(prefix) for %s"% prefix)
        self.routingInfo[prefix] = RoutingTable(prefix, mod_dstIp, mod_dstMask, nexthop)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=ethertype,
                ipv4_dst=(mod_dstIp, mod_dstMask))
        actions =[datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionDecNwTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xf,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def add_flow_mpls(self, datapath, label, mod_srcMac, mod_dstMac, outPort):
        match = datapath.ofproto_parser.OFPMatch(
                eth_type=0x8847,
                mpls_label=label)
        actions =[datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionDecMplsTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xff,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)


    def add_flow_push_mpls(self, datapath, ethertype, routeDist, label, mod_dstIp, mod_dstMask, mod_srcMac, mod_dstMac, outPort, nexthop):

        ipaddress = IPNetwork(mod_dstIp + '/' + mod_dstMask)
        prefix = str(ipaddress.cidr)
        vpnv4_prefix = routeDist + ':' + prefix
        if nexthop is None:
            nexthop = "0.0.0.0"
        LOG.debug("add MplsInfo(%s, [%s])"%(vpnv4_prefix, label))
        self.mplsInfo[vpnv4_prefix] = MplsTable(routeDist, prefix, label,
                                                mod_dstIp, mod_dstMask, nexthop)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=ethertype,
                ipv4_dst=(mod_dstIp, mod_dstMask))
        actions =[datapath.ofproto_parser.OFPActionPushMpls(0x8847),
                datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionSetField(mpls_label=label),
                datapath.ofproto_parser.OFPActionSetField(mpls_tc=1),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionSetMplsTtl(255),
                datapath.ofproto_parser.OFPActionDecMplsTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xf,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)


    def add_flow_pop_mpls(self, datapath, ethertype, routeDist, label, mod_dstIp, mod_dstMask, mod_srcMac, mod_dstMac, outPort, nexthop):

        ipaddress = IPNetwork(mod_dstIp + '/' + mod_dstMask)
        prefix = str(ipaddress.cidr)
        vpnv4_prefix = routeDist + ':' + prefix
        if nexthop is None:
            nexthop = "0.0.0.0"
        LOG.debug("add MplsInfo(%s, [%s])"%(vpnv4_prefix, label))
        self.mplsInfo[vpnv4_prefix] = MplsTable(routeDist, prefix, label,
                                                mod_dstIp, mod_dstMask, nexthop)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=0x8847,
                mpls_label=label)
        actions =[datapath.ofproto_parser.OFPActionPopMpls(ethertype),
                datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                datapath.ofproto_parser.OFPActionDecNwTtl()]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xe,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)


    def remove_flow_route(self, datapath, ethertype, dstIp, dstMask):
        ipaddress = IPNetwork(dstIp + '/' + dstMask)
        prefix = str(ipaddress.cidr)
        LOG.debug("delete RoutingInfo for %s"% prefix)
        self.routingInfo.pop(prefix)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=ethertype,
                ipv4_dst=(dstIp, dstMask))
        inst = []
        mod = datapath.ofproto_parser.OFPFlowMod(
                command=datapath.ofproto.OFPFC_DELETE_STRICT,
                datapath=datapath,
                priority=0xf,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def remove_flow_push_mpls(self, datapath, label, mod_dstIp, mod_dstMask, vpnv4_prefix):
        LOG.debug("delete MplsInfo(%s, [%s])"%(vpnv4_prefix, label))
        self.mplsInfo.pop(vpnv4_prefix)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=0x0800,
                ipv4_dst=(mod_dstIp, mod_dstMask))
        inst = []
        mod = datapath.ofproto_parser.OFPFlowMod(
                command=datapath.ofproto.OFPFC_DELETE_STRICT,
                datapath=datapath,
                priority=0xf,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def remove_flow_pop_mpls(self, datapath, vpnv4_prefix, label):
        LOG.debug("delete MplsInfo(%s, [%s])"%(vpnv4_prefix, label))
        self.mplsInfo.pop(vpnv4_prefix)

        match = datapath.ofproto_parser.OFPMatch(
                eth_type=0x8847,
                mpls_label=label)
        inst = []
        mod = datapath.ofproto_parser.OFPFlowMod(
                command=datapath.ofproto.OFPFC_DELETE_STRICT,
                datapath=datapath,
                priority=0xf,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def remove_flow_mpls(self, datapath, label):
        match = datapath.ofproto_parser.OFPMatch(
                eth_type=0x8847,
                mpls_label=label)
        inst = []
        mod = datapath.ofproto_parser.OFPFlowMod(
                command=datapath.ofproto.OFPFC_DELETE_STRICT,
                datapath=datapath,
                priority=0xf,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def add_flow_for_bgp(self, datapath, inPort, ethertype, destIp, outPort):
        if destIp:
            match = datapath.ofproto_parser.OFPMatch(
                in_port=inPort,
                eth_type=ethertype,
                ipv4_dst=destIp)
            actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                       datapath.ofproto_parser.OFPActionOutput(
                                             datapath.ofproto.OFPP_CONTROLLER,
                                             datapath.ofproto.OFPCML_NO_BUFFER)]
        else:
            match = datapath.ofproto_parser.OFPMatch(
                in_port=inPort,
                eth_type=ethertype)
            actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0),
                       datapath.ofproto_parser.OFPActionOutput(
                                             datapath.ofproto.OFPP_CONTROLLER,
                                             datapath.ofproto.OFPCML_NO_BUFFER)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xff,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
        return 0


    def print_etherFrame(self, etherFrame):
        LOG.debug("---------------------------------------")
        LOG.debug("eth_dst_address :%s"% etherFrame.dst)
        LOG.debug("eth_src_address :%s"% etherFrame.src)
        LOG.debug("eth_ethertype :0x%04x"% etherFrame.ethertype)
        LOG.debug("---------------------------------------")


    def print_arpPacket(self, arpPacket):
        LOG.debug("arp_hwtype :%d"% arpPacket.hwtype)
        LOG.debug("arp_proto :0x%04x"% arpPacket.proto)
        LOG.debug("arp_hlen :%d"% arpPacket.hlen)
        LOG.debug("arp_plen :%d"% arpPacket.plen)
        LOG.debug("arp_opcode :%d"% arpPacket.opcode)
        LOG.debug("arp_src_mac :%s"% arpPacket.src_mac)
        LOG.debug("arp_src_ip :%s"% arpPacket.src_ip)
        LOG.debug("arp_dst_mac :%s"% arpPacket.dst_mac)
        LOG.debug("arp_dst_ip :%s"% arpPacket.dst_ip)
        LOG.debug("---------------------------------------")


    def print_ipPacket(self, ipPacket):
        LOG.debug("ip_version :%d"% ipPacket.version)
        LOG.debug("ip_header_length :%d"% ipPacket.header_length)
        LOG.debug("ip_tos :%d"% ipPacket.tos)
        LOG.debug("ip_total_length :%d"% ipPacket.total_length)
        LOG.debug("ip_identification:%d"% ipPacket.identification)
        LOG.debug("ip_flags :%d"% ipPacket.flags)
        LOG.debug("ip_offset :%d"% ipPacket.offset)
        LOG.debug("ip_ttl :%d"% ipPacket.ttl)
        LOG.debug("ip_proto :%d"% ipPacket.proto)
        LOG.debug("ip_csum :%d"% ipPacket.csum)
        LOG.debug("ip_src :%s"% ipPacket.src)
        LOG.debug("ip_dst :%s"% ipPacket.dst)
        LOG.debug("---------------------------------------")


    def print_icmp(self, icmpPacket):
        LOG.debug("icmp_type :%d", icmpPacket.type)
        LOG.debug("icmp_code :%d", icmpPacket.code)
        LOG.debug("icmp_csum :%d", icmpPacket.csum)
        LOG.debug("icmp_id :%d", icmpPacket.data.id)
        LOG.debug("icmp_seq :%d", icmpPacket.data.seq)
        LOG.debug("icmp_data :%s", icmpPacket.data.data)


