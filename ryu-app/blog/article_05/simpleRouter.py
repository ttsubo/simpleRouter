import logging

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.arp import arp
from ryu.lib.packet.ipv4 import ipv4
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet

LOG = logging.getLogger('SimpleRouter')
#LOG.setLevel(logging.DEBUG)
logging.basicConfig()




class SimpleRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    ROUTER_IPADDR1 = None
    ROUTER_IPADDR2 = None
    ROUTER_MACADDR1 = None
    ROUTER_MACADDR2 = None
    HOST_IPADDR1 = None
    HOST_IPADDR2 = None
    HOST_MACADDR1 = None
    HOST_MACADDR2 = None
    ROUTER_PORT1 = 1
    ROUTER_PORT2 = 2

    def __init__(self, *args, **kwargs):
        super(SimpleRouter, self).__init__(*args, **kwargs)


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
            datapath.ofproto.OFPCML_MAX
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
        return 0


    def receive_ip(self, datapath, packet, etherFrame, inPort):
        ipPacket = packet.get_protocol(ipv4)
        LOG.debug("receive IP packet %s => %s (port%d)"
                       %(etherFrame.src, etherFrame.dst, inPort))
        self.print_etherFrame(etherFrame)
        self.print_ipPacket(ipPacket)
        LOG.debug("Drop packet")

        if inPort == self.ROUTER_PORT1 and ipPacket.src == self.HOST_IPADDR1:
            self.HOST_MACADDR1 = etherFrame.src
        elif inPort == self.ROUTER_PORT2 and ipPacket.src == self.HOST_IPADDR2:
            self.HOST_MACADDR2 = etherFrame.src

        if self.HOST_MACADDR1 != None and self.HOST_MACADDR2 != None:
            if ipPacket.dst == self.HOST_IPADDR1:
                self.send_flow(datapath)
            if ipPacket.dst == self.HOST_IPADDR2:
                self.send_flow(datapath)
            else:
                LOG.debug("unknown ip received !")
                return 1
        elif (self.HOST_MACADDR1 == None) or (self.HOST_MACADDR2 == None):
            if ipPacket.dst == self.HOST_IPADDR2:
                self.send_arp(datapath, 1, self.ROUTER_MACADDR2,
                              self.ROUTER_IPADDR2, "ff:ff:ff:ff:ff:ff",
                              self.HOST_IPADDR2, self.ROUTER_PORT2)
                LOG.debug("send ARP request %s => %s (port%d)"
                         %(self.ROUTER_MACADDR2, "ff:ff:ff:ff:ff:ff",
                         self.ROUTER_PORT2))
            elif ipPacket.dst == self.HOST_IPADDR1:
                self.send_arp(datapath, 1, self.ROUTER_MACADDR1,
                              self.ROUTER_IPADDR1, "ff:ff:ff:ff:ff:ff",
                              self.HOST_IPADDR1, self.ROUTER_PORT1)
                LOG.debug("send ARP request %s => %s (port%d)"
                         %(self.ROUTER_MACADDR1, "ff:ff:ff:ff:ff:ff",
                         self.ROUTER_PORT1))
            else:
                LOG.debug("unknown ip received !")
                return 1
        return 0


    def receive_arp(self, datapath, packet, etherFrame, inPort):
        arpPacket = packet.get_protocol(arp)
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
            if inPort == self.ROUTER_PORT1:
                self.HOST_IPADDR1 = arpPacket.src_ip
                self.HOST_MACADDR1 = arpPacket.src_mac
                self.ROUTER_IPADDR1 = arpPacket.dst_ip
                self.ROUTER_MACADDR1 = arpPacket.dst_mac
            elif inPort == self.ROUTER_PORT2:
                self.HOST_IPADDR2 = arpPacket.src_ip
                self.HOST_MACADDR2 = arpPacket.src_mac
                self.ROUTER_IPADDR2 = arpPacket.dst_ip
                self.ROUTER_MACADDR2 = arpPacket.dst_mac
            if self.HOST_MACADDR1 != None and self.HOST_MACADDR2 != None:
                self.send_flow(datapath)
        return 0


    def reply_arp(self, datapath, etherFrame, arpPacket, arp_dstIp, inPort):
        dstIp = arpPacket.src_ip
        srcIp = arpPacket.dst_ip
        dstMac = etherFrame.src
        if arp_dstIp == self.ROUTER_IPADDR1:
            srcMac = self.ROUTER_MACADDR1
            outPort = self.ROUTER_PORT1
        elif arp_dstIp == self.ROUTER_IPADDR2:
            srcMac = self.ROUTER_MACADDR2
            outPort = self.ROUTER_PORT2
        else:
            LOG.debug("unknown arp requst received !")
            return 1

        self.send_arp(datapath, 2, srcMac, srcIp, dstMac, dstIp, outPort)
        LOG.debug("send ARP reply %s => %s (port%d)" %(srcMac, dstMac, outPort))
        return 0


    def send_arp(self, datapath, opcode, srcMac, srcIp, dstMac, dstIp, outPort):
        if opcode == 1:
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


    def send_flow(self, datapath):
        LOG.debug("Send Flow_mod packet for %s"% self.HOST_IPADDR2)
        self.add_flow(datapath, self.ROUTER_PORT1, self.HOST_MACADDR1,
                      self.ROUTER_MACADDR1, ether.ETH_TYPE_IP,
                      self.HOST_IPADDR2, self.ROUTER_MACADDR2,
                      self.HOST_MACADDR2, self.ROUTER_PORT2)
        LOG.debug("Send Flow_mod packet for %s"% self.HOST_IPADDR1)
        self.add_flow(datapath, self.ROUTER_PORT2, self.HOST_MACADDR2,
                      self.ROUTER_MACADDR2, ether.ETH_TYPE_IP,
                      self.HOST_IPADDR1, self.ROUTER_MACADDR1,
                      self.HOST_MACADDR1, self.ROUTER_PORT1)
        return 0


    def add_flow(self, datapath, inPort, org_srcMac, org_dstMac, ethertype,
                 targetIp, mod_srcMac, mod_dstMac, outPort):

        match = datapath.ofproto_parser.OFPMatch(
                in_port=inPort,
                eth_src=org_srcMac,
                eth_dst=org_dstMac,
                eth_type=ethertype,
                ipv4_dst=targetIp )
        actions =[datapath.ofproto_parser.OFPActionSetField(eth_src=mod_srcMac),
                datapath.ofproto_parser.OFPActionSetField(eth_dst=mod_dstMac),
                datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                flags=datapath.ofproto.OFPFF_CHECK_OVERLAP,
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


