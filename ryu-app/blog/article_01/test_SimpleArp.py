import unittest
import logging
from simpleArp import SimpleArp
from ryu.controller import ofp_event
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet.arp import arp
from ryu.lib.packet.packet import Packet
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether, ofproto_v1_3_parser
from ryu.ofproto import ofproto_v1_3_parser
from ryu.ofproto.ofproto_v1_3_parser import OFPPacketIn, OFPMatch

dstMac = "ff:ff:ff:ff:ff:ff"
srcMac = "52:54:00:75:4e:57"
targetMac = "00:00:00:00:00:00"
srcIp = "192.168.0.1"
dstIp = "192.168.0.10"

class _Datapath(object):
    ofproto = ofproto_v1_3
    ofproto_parser = ofproto_v1_3_parser

    def send_msg(self, msg):
        pass

class TestSimpleArp(unittest.TestCase):
    def setUp(self):
        pass

    def testDown(self):
        pass

    def test_Packet_in(self):
        sa = SimpleArp()

        datapath = _Datapath()
        e = ethernet.ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
        a = arp(1, 0x0800, 6, 4, 1, srcMac, srcIp, targetMac, dstIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        packetIn = OFPPacketIn(datapath, match=OFPMatch(in_port=1), data=buffer(p.data))

        ev = ofp_event.EventOFPPacketIn(packetIn)

        result = sa.packet_in_handler(ev)
        self.assertEqual(result, 0)

if __name__ == "__main__":
    unittest.main()
