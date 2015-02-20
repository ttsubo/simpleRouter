#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import time
from oslo.config import cfg
from common_func import request_info

port1_opts = []
port2_opts = []
port3_opts = []

port1_opts.append(cfg.StrOpt('port', default=[], help='OpenFlow Port'))
port1_opts.append(cfg.StrOpt('macaddress', default=[], help='MacAddress'))
port1_opts.append(cfg.StrOpt('ipaddress', default=[], help='IpAddress'))
port1_opts.append(cfg.StrOpt('netmask', default=[], help='netmask'))
port1_opts.append(cfg.StrOpt('opposite_ipaddress', default=[],
                   help='opposite_IpAddress'))
port1_opts.append(cfg.StrOpt('opposite_asnumber', default=[],
                   help='opposite_asnumber'))
port1_opts.append(cfg.StrOpt('port_offload_bgp', default=[], help='port_offload_bgp'))
port1_opts.append(cfg.StrOpt('bgp_med', default=[], help='bgp_med'))
port1_opts.append(cfg.StrOpt('bgp_local_pref', default=[], help='bgp_local_pref'))
port1_opts.append(cfg.StrOpt('bgp_filter_asnumber', default=[], help='bgp_filter_asnumber'))
port1_opts.append(cfg.StrOpt('vrf_routeDist', default=[], help='vrf_routeDist'))

port2_opts.append(cfg.StrOpt('port', default=[], help='OpenFlow Port'))
port2_opts.append(cfg.StrOpt('macaddress', default=[], help='MacAddress'))
port2_opts.append(cfg.StrOpt('ipaddress', default=[], help='IpAddress'))
port2_opts.append(cfg.StrOpt('netmask', default=[], help='netmask'))
port2_opts.append(cfg.StrOpt('opposite_ipaddress', default=[],
                   help='opposite_IpAddress'))
port2_opts.append(cfg.StrOpt('opposite_asnumber', default=[],
                   help='opposite_asnumber'))
port2_opts.append(cfg.StrOpt('port_offload_bgp', default=[], help='port_offload_bgp'))
port2_opts.append(cfg.StrOpt('bgp_med', default=[], help='bgp_med'))
port2_opts.append(cfg.StrOpt('bgp_local_pref', default=[], help='bgp_local_pref'))
port2_opts.append(cfg.StrOpt('bgp_filter_asnumber', default=[], help='bgp_filter_asnumber'))
port2_opts.append(cfg.StrOpt('vrf_routeDist', default=[], help='vrf_routeDist'))

port3_opts.append(cfg.StrOpt('port', default=[], help='OpenFlow Port'))
port3_opts.append(cfg.StrOpt('macaddress', default=[], help='MacAddress'))
port3_opts.append(cfg.StrOpt('ipaddress', default=[], help='IpAddress'))
port3_opts.append(cfg.StrOpt('netmask', default=[], help='netmask'))
port3_opts.append(cfg.StrOpt('opposite_ipaddress', default=[],
                   help='opposite_IpAddress'))
port3_opts.append(cfg.StrOpt('opposite_asnumber', default=[],
                   help='opposite_asnumber'))
port3_opts.append(cfg.StrOpt('port_offload_bgp', default=[], help='port_offload_bgp'))
port3_opts.append(cfg.StrOpt('bgp_med', default=[], help='bgp_med'))
port3_opts.append(cfg.StrOpt('bgp_local_pref', default=[], help='bgp_local_pref'))
port3_opts.append(cfg.StrOpt('bgp_filter_asnumber', default=[], help='bgp_filter_asnumber'))
port3_opts.append(cfg.StrOpt('vrf_routeDist', default=[], help='vrf_routeDist'))

CONF = cfg.CONF
CONF.register_cli_opts(port1_opts, 'Port1')
CONF.register_cli_opts(port2_opts, 'Port2')
CONF.register_cli_opts(port2_opts, 'Port3')


##################
# create_interface
##################

def start_create_interface(dpid, port, macaddress, ipaddress, netmask, opposite_ipaddress, opposite_asnumber, port_offload_bgp, bgp_med, bgp_local_pref, bgp_filter_asnumber, vrf_routeDist):
    operation = "create_interface"
    url_path = "/openflow/" + dpid + "/interface"
    method = "POST"
    request = '''
{
"interface": {
"port": "%s",
"macaddress": "%s",
"ipaddress": "%s",
"netmask": "%s",
"opposite_ipaddress": "%s",
"opposite_asnumber": "%s",
"port_offload_bgp": "%s",
"bgp_med": "%s",
"bgp_local_pref": "%s",
"bgp_filter_asnumber": "%s",
"vrf_routeDist": "%s"
}
}'''% (port, macaddress, ipaddress, netmask, opposite_ipaddress, opposite_asnumber, port_offload_bgp, bgp_med, bgp_local_pref, bgp_filter_asnumber, vrf_routeDist)

    interface_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(interface_result, sort_keys=False, indent=4)
    print ""


##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        port1 = CONF.Port1.port
        macaddress1 = CONF.Port1.macaddress
        ipaddress1 = CONF.Port1.ipaddress
        netmask1 = CONF.Port1.netmask
        opposite_ipaddress1 = CONF.Port1.opposite_ipaddress
        opposite_asnumber1 = CONF.Port1.opposite_asnumber
        port_offload_bgp1 = CONF.Port1.port_offload_bgp
        bgp_med1 = CONF.Port1.bgp_med
        bgp_local_pref1 = CONF.Port1.bgp_local_pref
        bgp_filter_asnumber1 = CONF.Port1.bgp_filter_asnumber
        vrf_routeDist1 = CONF.Port1.vrf_routeDist
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_interface(dpid, port1, macaddress1, ipaddress1, netmask1,
                           opposite_ipaddress1, opposite_asnumber1,
                           port_offload_bgp1, bgp_med1, bgp_local_pref1,
                           bgp_filter_asnumber1, vrf_routeDist1)

    time.sleep(5)
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        port2 = CONF.Port2.port
        macaddress2 = CONF.Port2.macaddress
        ipaddress2 = CONF.Port2.ipaddress
        netmask2 = CONF.Port2.netmask
        opposite_ipaddress2 = CONF.Port2.opposite_ipaddress
        opposite_asnumber2 = CONF.Port2.opposite_asnumber
        port_offload_bgp2 = CONF.Port2.port_offload_bgp
        bgp_med2 = CONF.Port2.bgp_med
        bgp_local_pref2 = CONF.Port2.bgp_local_pref
        bgp_filter_asnumber2 = CONF.Port2.bgp_filter_asnumber
        vrf_routeDist2 = CONF.Port2.vrf_routeDist
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_interface(dpid, port2, macaddress2, ipaddress2, netmask2,
                           opposite_ipaddress2, opposite_asnumber2,
                           port_offload_bgp2, bgp_med2, bgp_local_pref2,
                           bgp_filter_asnumber2, vrf_routeDist2)

    time.sleep(5)
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        port3 = CONF.Port3.port
        macaddress3 = CONF.Port3.macaddress
        ipaddress3 = CONF.Port3.ipaddress
        netmask3 = CONF.Port3.netmask
        opposite_ipaddress3 = CONF.Port3.opposite_ipaddress
        opposite_asnumber3 = CONF.Port3.opposite_asnumber
        port_offload_bgp3 = CONF.Port3.port_offload_bgp
        bgp_med3 = CONF.Port3.bgp_med
        bgp_local_pref3 = CONF.Port3.bgp_local_pref
        bgp_filter_asnumber3 = CONF.Port3.bgp_filter_asnumber
        vrf_routeDist3 = CONF.Port3.vrf_routeDist
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_interface(dpid, port3, macaddress3, ipaddress3, netmask3,
                           opposite_ipaddress3, opposite_asnumber3,
                           port_offload_bgp3, bgp_med3, bgp_local_pref3,
                           bgp_filter_asnumber3, vrf_routeDist3)
if __name__ == "__main__":
    main()
