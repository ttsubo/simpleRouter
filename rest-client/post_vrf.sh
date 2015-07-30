#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from oslo_config import cfg
from common_func import request_info

vrf_opts = []

vrf_opts.append(cfg.StrOpt('route_dist', default=[],  help='route_dist'))
vrf_opts.append(cfg.StrOpt('import_routeTarget', default=[],  help='import'))
vrf_opts.append(cfg.StrOpt('export_routeTarget', default=[],  help='export'))


CONF = cfg.CONF
CONF.register_cli_opts(vrf_opts, 'Vrf')

##################
# create_vrf
##################

def start_create_vrf(dpid, route_dist, importRt, exportRt):
    operation = "create_vrf"
    url_path = "/openflow/" + dpid + "/vrf"
    method = "POST"
    request = '''
{
"vrf": {
"route_dist": "%s",
"import": "%s",
"export": "%s"
}
}'''%(route_dist, importRt, exportRt)

    vrf_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(vrf_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
    try:
        CONF(default_config_files=['OpenFlow.ini'])
        route_dist = CONF.Vrf.route_dist
        importRt = CONF.Vrf.import_routeTarget
        exportRt = CONF.Vrf.export_routeTarget
    except cfg.ConfigFilesNotFoundError:
        print "Error: Not Found <OpenFlow.ini> "

    start_create_vrf(dpid, route_dist, importRt, exportRt)

if __name__ == "__main__":
    main()
