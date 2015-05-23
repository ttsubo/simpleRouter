#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import sys
from common_func import request_info

##################
# delete_route
##################

def start_delete_route(dpid, destination, netmask, routeDist):
    operation = "delete_route"
    url_path = "/openflow/" + dpid + "/route"
    method = "DELETE"
    request = '''
{
"route": {
"destination": "%s",
"netmask": "%s",
"vrf_routeDist": "%s"
}
}'''%(destination, netmask, routeDist)

    route_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(route_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main(argv):
    dpid = "0000000000000001"
    destination = argv[1]
    netmask = argv[2]
    routeDist = argv[3]
    start_delete_route(dpid, destination, netmask, routeDist)

if __name__ == "__main__":
    if (len(sys.argv) != 4):
        print "Usage: delete_route.sh [destination] [netmask] [routeDist]"
        sys.exit()
    else:
        main(sys.argv)
