#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import sys
from common_func import request_info

##################
# ping
##################

def start_ping(dpid, hostIp, data, outPort):
    operation = "ping"
    url_path = "/openflow/" + dpid + "/ping"
    method = "PUT"
    request = '''
{
"ping": {
"hostIp": "%s",
"data": "%s",
"outPort": "%s"
}
}'''% (hostIp, data, outPort)

    ping_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(ping_result, sort_keys=False, indent=4)
    print ""




##############
# main
##############

def main(argv):
    dpid = "0000000000000001"
    hostIp = argv[1]
    outPort = argv[2]
    data = argv[3]
    start_ping(dpid, hostIp, data, outPort)

if __name__ == "__main__":
    if (len(sys.argv) != 4):
        print "Usage: put_ping.sh [hostIp] [outPort] [data]"
        sys.exit()
    else:
        main(sys.argv)
