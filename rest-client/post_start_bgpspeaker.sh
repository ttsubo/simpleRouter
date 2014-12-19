#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo.config import cfg
from common_func import request_info

bgp_opts = []

bgp_opts.append(cfg.StrOpt('as_number', default=[], help='as_number'))
bgp_opts.append(cfg.StrOpt('router_id', default=[], help='router_id'))

CONF = cfg.CONF
CONF.register_cli_opts(bgp_opts, 'Bgp')

##################
# start_bgp
##################

def start_bgp(dpid, as_number, router_id):
    operation = "start_bgp"
    url_path = "/openflow/" + dpid + "/bgp"
    method = "POST"
    request = '''
{
"bgp": {
"as_number": "%s",
"router_id": "%s"
}
}'''%(as_number, router_id)

    bgp_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(bgp_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        as_number = CONF.Bgp.as_number
        router_id = CONF.Bgp.router_id
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_bgp(dpid, as_number, router_id)

if __name__ == "__main__":
    main()
