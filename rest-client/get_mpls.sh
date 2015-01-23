#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_mpls
###############

def start_get_mpls(dpid):
    operation = "get_mpls"
    url_path = "/openflow/" + dpid + "/mpls" 
    method = "GET"

    mpls_list = request_info(operation, url_path, method, "")

    routeDist = {}
    prefix = {}
    nextHopIpAddr = {}
    label = {}
    nowtime = mpls_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : MplsTable " % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "routeDist  prefix             nexthop          label"
    print "---------- ------------------ ---------------- -----"
    for a in range(len(mpls_list['mpls'])):
        routeDist[a] = mpls_list['mpls'][a]['routeDist']
        prefix[a] = mpls_list['mpls'][a]['prefix']
        nextHopIpAddr[a] = mpls_list['mpls'][a]['nextHopIpAddr']
        label[a] = mpls_list['mpls'][a]['label']
        print "%s  %-18s %-15s  %-5s" % (routeDist[a], prefix[a],
                                         nextHopIpAddr[a], label[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_mpls(dpid)


if __name__ == "__main__":
    main()
