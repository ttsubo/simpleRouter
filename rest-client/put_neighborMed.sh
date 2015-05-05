#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import sys
from common_func import request_info

##################
# change med
##################

def start_change_med(dpid, peerIp, med):
    operation = "change med"
    url_path = "/openflow/" + dpid + "/neighbor"
    method = "PUT"
    request = '''
{
"neighbor": {
"peerIp": "%s",
"med": "%s"
}
}'''% (peerIp, med)

    change_med_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(change_med_result, sort_keys=False, indent=4)
    print ""




##############
# main
##############

def main(argv):
    dpid = "0000000000000001"
    peerIp = argv[1]
    med = argv[2]
    start_change_med(dpid, peerIp, med)

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print "Usage: put_neighborMed.sh [peerIp] [med]"
        sys.exit()
    else:
        main(sys.argv)
