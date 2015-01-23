#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_flowstats
###############

def start_get_flowstats(dpid):
    operation = "get_flowstats"
    url_path = "/openflow/" + dpid + "/stats/flow" 
    method = "GET"

    flowstats_list = request_info(operation, url_path, method, "")

    ipv4Dst = {}
    packets = {}
    bytes = {}
    nowtime = flowstats_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : FlowStats" % nowtime
    print "+++++++++++++++++++++++++++++++"


    print "destination(label) packets    bytes"
    print "------------------ ---------- ----------"
    for a in range(len(flowstats_list['stats'])):
        ipv4Dst[a] = flowstats_list['stats'][a]['ipv4Dst']
        packets[a] = flowstats_list['stats'][a]['packets']
        bytes[a] = flowstats_list['stats'][a]['bytes']
        print "%-18s %10d %10d" % (ipv4Dst[a], packets[a], bytes[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_flowstats(dpid)


if __name__ == "__main__":
    main()
