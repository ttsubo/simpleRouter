#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from common_func import request_info

###############
# get_vrf
###############

def start_get_vrf(dpid):
    operation = "get_vrf"
    url_path = "/openflow/" + dpid + "/vrf" 
    method = "GET"

    vrf_result = request_info(operation, url_path, method, "")

    nowtime = vrf_result['time']
    result = vrf_result['vrfs']
    print "+++++++++++++++++++++++++++++++"
    print "%s : Show vrf " % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "%s" % result
    print ""
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_vrf(dpid)


if __name__ == "__main__":
    main()
