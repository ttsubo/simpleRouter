#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo.config import cfg
from common_func import request_info

bgp_opts = []

bgp_opts.append(cfg.StrOpt('as_number', default=[], help='as_number'))
bgp_opts.append(cfg.StrOpt('router_id', default=[], help='router_id'))
bgp_opts.append(cfg.StrOpt('label_range_start', default=[], help='label_range_start'))
bgp_opts.append(cfg.StrOpt('label_range_end', default=[], help='label_range_end'))

CONF = cfg.CONF
CONF.register_cli_opts(bgp_opts, 'Bgp')

##################
# start_bgp
##################

def start_bgp(dpid, as_number, router_id, label_range_start, label_range_end):
    operation = "start_bgp"
    url_path = "/openflow/" + dpid + "/bgp"
    method = "POST"
    request = '''
{
"bgp": {
"as_number": "%s",
"router_id": "%s",
"label_range_start": "%s",
"label_range_end": "%s"
}
}'''%(as_number, router_id, label_range_start, label_range_end)

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
        label_range_start = CONF.Bgp.label_range_start
        label_range_end = CONF.Bgp.label_range_end
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_bgp(dpid, as_number, router_id, label_range_start, label_range_end)

if __name__ == "__main__":
    main()
