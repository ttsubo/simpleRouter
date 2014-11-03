#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo.config import cfg
from common_func import request_info

gateway_opts = []

gateway_opts.append(cfg.StrOpt('ipaddress', default=[],
                     help='gateway ipaddress'))


CONF = cfg.CONF
CONF.register_cli_opts(gateway_opts, 'Gateway')

##################
# create_gateway
##################

def start_create_gateway(dpid, ipaddress):
    operation = "create_gateway"
    url_path = "/openflow/" + dpid + "/gateway"
    method = "POST"
    request = '''
{
"gateway": {
"ipaddress": "%s"
}
}'''%ipaddress

    gateway_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(gateway_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        gatewayIp = CONF.Gateway.ipaddress
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_gateway(dpid, gatewayIp)

if __name__ == "__main__":
    main()
