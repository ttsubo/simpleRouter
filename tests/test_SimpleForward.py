# -*- coding: utf-8 -*-

import unittest
import logging
from simpleForward import SimpleForward
from ryu.controller import ofp_event
from ryu.lib.packet import ethernet
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
from ryu.ofproto import ofproto_v1_3_parser
from ryu.ofproto.ofproto_v1_3_parser import OFPPacketIn, OFPMatch

HOST_IPADDR1 = "192.168.0.1"
HOST_MACADDR1 = "52:54:00:75:4e:57"
HOST_IPADDR2 = "192.168.1.1"
HOST_MACADDR2 = "52:54:00:0b:d0:48"
ROUTER_IPADDR1 = "192.168.0.10"
ROUTER_IPADDR2 = "192.168.1.10"
ROUTER_MACADDR1 = "00:00:00:00:00:01"
ROUTER_MACADDR2 = "00:00:00:00:00:02"
ROUTER_PORT1 = 1
ROUTER_PORT2 = 2

class _Datapath(object):
    ofproto = ofproto_v1_3
    ofproto_parser = ofproto_v1_3_parser

    def send_msg(self, msg):
        pass

class TestSimpleForward(unittest.TestCase):
    def setUp(self):
        pass

    def testDown(self):
        pass

    def test_Packet_in_1_arpRequest(self):
        print "*** Case1: HOST1からARP Request受信 ***"

        sr = SimpleForward()
        dstMac = "ff:ff:ff:ff:ff:ff"
        srcMac = HOST_MACADDR1
        srcIp = HOST_IPADDR1
        dstIp = ROUTER_IPADDR1
        targetMac = dstMac
        targetIp = dstIp

        datapath = _Datapath()
        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
        a = arp(1, 0x0800, 6, 4, 1, srcMac, srcIp, targetMac, targetIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        packetIn = OFPPacketIn(datapath, match=OFPMatch(in_port=1), data=buffer(p.data))

        ev = ofp_event.EventOFPPacketIn(packetIn)

        result = sr.packet_in_handler(ev)
        self.assertEqual(result, 0)
        print ""


    def test_Packet_in_2_icmpEcho1(self):
        print "*** Case2: HOST2のMAC未学習の時、HOST1からICMP Echoを受信 ***"

        sr = SimpleForward()
        dstMac = ROUTER_MACADDR1
        srcMac = HOST_MACADDR1
        srcIp = HOST_IPADDR1
        dstIp = HOST_IPADDR2
        targetMac = dstMac
        targetIp = dstIp
        ttl = 64

        datapath = _Datapath()
        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_IP)

        iph = ipv4(4, 5, 0, 0, 0, 2, 0, ttl, 1, 0, srcIp, dstIp)
        echo = icmp.echo(1, 1, 'unit test')
        icmph = icmp.icmp(8, 0, 0, echo)

        p = Packet()
        p.add_protocol(e)
        p.add_protocol(iph)
        p.add_protocol(icmph)
        p.serialize()

        packetIn = OFPPacketIn(datapath, match=OFPMatch(in_port=1), data=buffer(p.data))

        ev = ofp_event.EventOFPPacketIn(packetIn)

        result = sr.packet_in_handler(ev)
        self.assertEqual(result, 1)
        print ""


    def test_Packet_in_3_arpReply2(self):
        print "*** Case3: HOST1のMAC学習済の時、HOST2からARP Replyを受信 ***"

        sr = SimpleForward()
        sr.HOST_MACADDR1 = HOST_MACADDR1
        sr.HOST_MACADDR2 = HOST_MACADDR2

        dstMac = ROUTER_MACADDR2
        srcMac = HOST_MACADDR2
        srcIp = HOST_IPADDR2
        dstIp = ROUTER_IPADDR2
        targetMac = dstMac
        targetIp = dstIp

        datapath = _Datapath()
        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
        a = arp(1, 0x0800, 6, 4, 2, srcMac, srcIp, targetMac, targetIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        packetIn = OFPPacketIn(datapath, match=OFPMatch(in_port=2), data=buffer(p.data))

        ev = ofp_event.EventOFPPacketIn(packetIn)

        result = sr.packet_in_handler(ev)
        self.assertEqual(result, 0)
        print ""


    def test_Packet_in_4_icmpEcho2(self):
        print "*** Case4: HOST2からHOST1以外の宛先IPへのIPパケットを受信 ***"

        sr = SimpleForward()
        sr.HOST_MACADDR1 = HOST_MACADDR1
        sr.HOST_MACADDR2 = HOST_MACADDR2

        dstMac = ROUTER_MACADDR2
        srcMac = HOST_MACADDR2
        srcIp = HOST_IPADDR2
        dstIp = "91.189.89.22"
        ttl = 64

        datapath = _Datapath()
        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_IP)

        iph = ipv4(4, 5, 0, 0, 0, 2, 0, ttl, 1, 0, srcIp, dstIp)

        p = Packet()
        p.add_protocol(e)
        p.add_protocol(iph)
        p.serialize()

        packetIn = OFPPacketIn(datapath, match=OFPMatch(in_port=2), data=buffer(p.data))

        ev = ofp_event.EventOFPPacketIn(packetIn)

        result = sr.packet_in_handler(ev)
        self.assertEqual(result, 1)
        print ""


if __name__ == "__main__":
    unittest.main()
