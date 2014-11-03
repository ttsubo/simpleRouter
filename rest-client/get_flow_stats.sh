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

    inPort = {}
    ethSrc = {}
    ethDst = {}
    ipv4Dst = {}
    packets = {}
    bytes = {}
    nowtime = flowstats_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : FlowStats" % nowtime
    print "+++++++++++++++++++++++++++++++"


    print "inPort   ethSrc             ethDst             ipv4Dst         packets  bytes"
    print "-------- ------------------ ------------------ --------------- -------- --------"
    for a in range(len(flowstats_list['stats'])):
        inPort[a] = flowstats_list['stats'][a]['inPort']
        ethSrc[a] = flowstats_list['stats'][a]['ethSrc']
        ethDst[a] = flowstats_list['stats'][a]['ethDst']
        ipv4Dst[a] = flowstats_list['stats'][a]['ipv4Dst']
        packets[a] = flowstats_list['stats'][a]['packets']
        bytes[a] = flowstats_list['stats'][a]['bytes']
        print "%8s %18s %18s %15s %8d %8d" % (inPort[a], ethSrc[a], ethDst[a],
                                              ipv4Dst[a], packets[a], bytes[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_flowstats(dpid)


if __name__ == "__main__":
    main()
