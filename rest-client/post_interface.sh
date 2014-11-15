#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import sys
import time
from oslo.config import cfg
from common_func import request_info

port1_opts = []
port2_opts = []

port1_opts.append(cfg.StrOpt('port', default=[], help='OpenFlow Port'))
port1_opts.append(cfg.StrOpt('macaddress', default=[], help='MacAddress'))
port1_opts.append(cfg.StrOpt('ipaddress', default=[], help='IpAddress'))
port1_opts.append(cfg.StrOpt('opposite_ipaddress', default=[],
                   help='opposite_IpAddress'))
port1_opts.append(cfg.StrOpt('port_offload_bgp', default=[], help='port_offload_bgp'))
port2_opts.append(cfg.StrOpt('port', default=[], help='OpenFlow Port'))
port2_opts.append(cfg.StrOpt('macaddress', default=[], help='MacAddress'))
port2_opts.append(cfg.StrOpt('ipaddress', default=[], help='IpAddress'))
port2_opts.append(cfg.StrOpt('opposite_ipaddress', default=[],
                   help='opposite_IpAddress'))
port2_opts.append(cfg.StrOpt('port_offload_bgp', default=[], help='port_offload_bgp'))


CONF = cfg.CONF
CONF.register_cli_opts(port1_opts, 'Port1')
CONF.register_cli_opts(port2_opts, 'Port2')


##################
# create_interface
##################

def start_create_interface(dpid, port, macaddress, ipaddress, opposite_ipaddress, port_offload_bgp):
    operation = "create_interface"
    url_path = "/openflow/" + dpid + "/interface"
    method = "POST"
    request = '''
{
"interface": {
"port": "%s",
"macaddress": "%s",
"ipaddress": "%s",
"opposite_ipaddress": "%s",
"port_offload_bgp": "%s"
}
}'''% (port, macaddress, ipaddress, opposite_ipaddress, port_offload_bgp)

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
        opposite_ipaddress1 = CONF.Port1.opposite_ipaddress
        port_offload_bgp1 = CONF.Port1.port_offload_bgp
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_interface(dpid, port1, macaddress1, ipaddress1,
                           opposite_ipaddress1, port_offload_bgp1)

    time.sleep(5)
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        port2 = CONF.Port2.port
        macaddress2 = CONF.Port2.macaddress
        ipaddress2 = CONF.Port2.ipaddress
        opposite_ipaddress2 = CONF.Port2.opposite_ipaddress
        port_offload_bgp2 = CONF.Port2.port_offload_bgp
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_interface(dpid, port2, macaddress2, ipaddress2,
                           opposite_ipaddress2, port_offload_bgp2)

if __name__ == "__main__":
    main()
