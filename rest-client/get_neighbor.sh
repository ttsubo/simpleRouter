#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import time
from oslo.config import cfg
from common_func import request_info

neighbor_opts = []

neighbor_opts.append(cfg.StrOpt('routetype', default=[],  help='routetype'))
neighbor_opts.append(cfg.StrOpt('address', default=[],  help='address'))


CONF = cfg.CONF
CONF.register_cli_opts(neighbor_opts, 'Neighbor')

##################
# get_neighbor
##################

def start_get_neighbor(dpid, routetype, address):
    operation = "get_neighbor"
    url_path = "/openflow/" + dpid + "/neighbor"
    method = "GET"
    request = '''
{
"neighbor": {
"routetype": "%s",
"address": "%s"
}
}'''%(routetype, address)

    neighbor_result = request_info(operation, url_path, method, request)

    nowtime = neighbor_result['time']
    result = neighbor_result['neighbor']
    print "+++++++++++++++++++++++++++++++"
    print "%s : Show neighbor " % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "%s" % result
    print ""




##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        routetype = CONF.Neighbor.routetype
        address = CONF.Neighbor.address
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_get_neighbor(dpid, routetype, address)

if __name__ == "__main__":
    main()
