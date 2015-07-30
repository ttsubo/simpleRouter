#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo_config import cfg
from common_func import request_info

bmp_opts = []

bmp_opts.append(cfg.StrOpt('address', default=[], help='address'))
bmp_opts.append(cfg.StrOpt('port', default=[], help='port'))

CONF = cfg.CONF
CONF.register_cli_opts(bmp_opts, 'Bmp')

##################
# start_bmp
##################

def start_bmp(dpid, address, port):
    operation = "start_bmp"
    url_path = "/openflow/" + dpid + "/bmp"
    method = "POST"
    request = '''
{
"bmp": {
"address": "%s",
"port": "%s"
}
}'''%(address, port)

    bmp_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(bmp_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        address = CONF.Bmp.address
        port = CONF.Bmp.port
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_bmp(dpid, address, port)

if __name__ == "__main__":
    main()
