#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_arp
###############

def start_get_arp(dpid):
    operation = "get_arp"
    url_path = "/openflow/" + dpid + "/arp" 
    method = "GET"

    arp_list = request_info(operation, url_path, method, "")

    hostIpAddr = {}
    hostMacAddr = {}
    routerPort = {}
    nowtime = arp_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : ArpTable " % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "portNo   MacAddress        IpAddress"
    print "-------- ----------------- ------------"
    for a in range(len(arp_list['arp'])):
        hostIpAddr[a] = arp_list['arp'][a]['hostIpAddr']
        hostMacAddr[a] = arp_list['arp'][a]['hostMacAddr']
        routerPort[a] = arp_list['arp'][a]['routerPort']
        print "%8x %17s %s" % (routerPort[a], hostMacAddr[a], hostIpAddr[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_arp(dpid)


if __name__ == "__main__":
    main()
