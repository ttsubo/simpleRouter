# Copyright (c) 2014-2015 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

import json
import logging
import socket
import time
import sys
import eventlet
import subprocess
eventlet.monkey_patch()

from ryu.lib.packet import bmp
from ryu.lib.packet import bgp
from ryu.lib import hub
from ryu.lib.hub import StreamServer
from oslo.config import cfg
log = logging.getLogger()
log.addHandler(logging.StreamHandler(sys.stderr))

HOST = '0.0.0.0'
PORT = 11019
ADDR = (HOST, PORT)
targetInfo = {}

target1_opts = []
target1_opts.append(cfg.StrOpt('prefix', default=[], help='prefix'))
target1_opts.append(cfg.StrOpt('target', default=[], help='target'))
target2_opts = []
target2_opts.append(cfg.StrOpt('prefix', default=[], help='prefix'))
target2_opts.append(cfg.StrOpt('target', default=[], help='target'))
CONF = cfg.CONF
CONF.register_cli_opts(target1_opts, 'Target1')
CONF.register_cli_opts(target2_opts, 'Target2')


class TargetTable(object):
    def __init__(self, target):
        self.target = target

    def get_target(self):
        return self.target

class Ping(object):
    def __init__(self, host):
        ping = subprocess.Popen(
            ["ping", "-c", "1", host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )
        ping_t = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        out, error = ping.communicate()
        if error:
            print(ping_t+'                | [ping NG]: '+'target->'+host+',Msg->\'' + error.rstrip() + '\'')
        else:
            print(ping_t+'                | [ping OK]: '+'target->'+host)

def print_BMPPeerUpNotification(msg, addr):
    peer_as = msg.peer_as
    peer_bgp_id = msg.peer_bgp_id
    bgp_t = time.strftime("%Y/%m/%d %H:%M:%S",
                           time.localtime(int(msg.timestamp)))
    print "%s %s %s | BGP_PeerUp" % (
           bgp_t, peer_as, peer_bgp_id)

def print_BMPRouteMonitoring(msg, addr):
    if msg.peer_type == bmp.BMP_PEER_TYPE_GLOBAL:
        print_global(msg, addr)
    elif msg.peer_type == bmp.BMP_PEER_TYPE_L3VPN:
        print_l3vpn(msg, addr)


def print_global(msg, addr):
    peer_as = msg.peer_as
    peer_bgp_id = msg.peer_bgp_id
    bgp_t = time.strftime("%Y/%m/%d %H:%M:%S",
                           time.localtime(int(msg.timestamp)))

    if msg.bgp_update.withdrawn_routes:
        del_nlri = msg.bgp_update.withdrawn_routes[0]
        del_prefix = del_nlri.addr +'/' + str(del_nlri.length)
        print "%s %s %s | BGP_Update(del_prefix:%-18s)" % (
               bgp_t, peer_as, peer_bgp_id, del_prefix)
    else:
        nlri = msg.bgp_update.nlri[0]
        prefix = nlri.addr +'/' + str(nlri.length)
        for data in msg.bgp_update.path_attributes:
            if isinstance(data, bgp.BGPPathAttributeNextHop):
                nexthop = data.value
                print "%s | %s %s %s | BGP_Update(add_prefix:%-18s, nexthop:%-15s)" % (
                       addr[0], bgp_t, peer_as, peer_bgp_id, prefix, nexthop)


def print_l3vpn(msg, addr):
    peer_as = msg.peer_as
    peer_bgp_id = msg.peer_bgp_id
    bgp_t = time.strftime("%Y/%m/%d %H:%M:%S",
                           time.localtime(int(msg.timestamp)))
    for data in msg.bgp_update.path_attributes:
        if isinstance(data, bgp.BGPPathAttributeMpUnreachNLRI):
            del_nlri = data.withdrawn_routes[0]
            routeDist = str(del_nlri.addr[1].admin)+':'+str(del_nlri.addr[1].assigned)
            del_vpnv4_prefix = routeDist + ':' + del_nlri.addr[2]
            print "%s %s %s | BGP_Update(del_prefix:%s)" % (
                   bgp_t, peer_as, peer_bgp_id, del_vpnv4_prefix)
            action_ping(del_vpnv4_prefix)
        elif isinstance(data, bgp.BGPPathAttributeMpReachNLRI):
            nlri = data.nlri[0]
            routeDist = str(nlri.addr[1].admin)+':'+str(nlri.addr[1].assigned)
            vpnv4_prefix = routeDist + ':' + nlri.addr[2]
            nexthop = data.next_hop
            print "%s %s %s | BGP_Update(add_prefix:%s, nexthop:%s)" % (
                   bgp_t, peer_as, peer_bgp_id, vpnv4_prefix, nexthop)
            action_ping(vpnv4_prefix)


def action_ping(vpnv4_prefix):
    for prefix, targetList in targetInfo.items():
        if prefix == vpnv4_prefix:
            hostIp = targetList.get_target()
            Ping(hostIp)


def start_ping(dpid, hostIp, data, outPort):
    operation = "ping"
    url_path = "/openflow/" + dpid + "/ping"
    method = "PUT"
    request = '''
{
"ping": {
"hostIp": "%s",
"data": "%s",
"outPort": "%s"
}
}'''% (hostIp, data, outPort)

    ping_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(ping_result, sort_keys=False, indent=4)
    print ""



def handler(sock, addr):
    buf = bytearray()
    required_len = bmp.BMPMessage._HDR_LEN
    is_active = True

    while is_active:
        ret = sock.recv(required_len)
        if len(ret) == 0:
            is_active = False
            break
        buf += ret
        while len(buf) >= required_len:
            version, len_, _ = bmp.BMPMessage.parse_header(buf)

            if len(buf) < len_:
                break

            try:
                msg, rest = bmp.BMPMessage.parser(buf)
            except Exception, e:
                pkt = buf[:len_]
                buf = buf[len_:]
            else:
                buf = rest
                if isinstance(msg, bmp.BMPInitiation):
                    print "Start BMP session!! [%s]"%addr[0]
                elif isinstance(msg, bmp.BMPPeerUpNotification):
                    print_BMPPeerUpNotification(msg, addr)
                elif isinstance(msg, bmp.BMPRouteMonitoring):
                    print_BMPRouteMonitoring(msg, addr)
                elif isinstance(msg, bmp.BMPPeerDownNotification):
                    print "%s | %s %s | BGP_PeerDown" % (
                           addr[0], msg.peer_as, msg.peer_bgp_id)

    print "End BMP session!! [%s]"%addr[0]
    sock.close()

def start_bmp_server():
    hub.spawn(StreamServer(ADDR,handler).serve_forever)

if __name__ == '__main__':
    CONF(default_config_files=['Target.ini'])
    prefix1 = CONF.Target1.prefix
    target1 = CONF.Target1.target
    targetInfo[prefix1] = TargetTable(target1)
    prefix2 = CONF.Target2.prefix
    target2 = CONF.Target2.target
    targetInfo[prefix2] = TargetTable(target2)


    start_bmp_server()
    eventlet.sleep(9999)
