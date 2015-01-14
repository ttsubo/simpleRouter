#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo.config import cfg
from common_func import request_info

redistribute_opts = []

redistribute_opts.append(cfg.StrOpt('redistribute', default=[],
                         help='redistribute'))
redistribute_opts.append(cfg.StrOpt('vrf_routeDist', default=[],
                         help='vrf_routeDist'))


CONF = cfg.CONF
CONF.register_cli_opts(redistribute_opts, 'Bgp')

##################
# set_redistribute
##################

def start_set_redistribute(dpid, redistribute, vrf_routeDist):
    operation = "set_redistribute"
    url_path = "/openflow/" + dpid + "/redistribute"
    method = "POST"
    request = '''
{
"bgp": {
"redistribute": "%s",
"vrf_routeDist": "%s"
}
}'''%(redistribute, vrf_routeDist)

    redistribute_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(redistribute_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        redistribute = CONF.Bgp.redistribute
        vrf_routeDist = CONF.Bgp.vrf_routeDist
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_set_redistribute(dpid, redistribute, vrf_routeDist)

if __name__ == "__main__":
    main()
