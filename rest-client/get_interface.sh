#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_interface
###############

def start_get_interface(dpid):
    operation = "get_interface"
    url_path = "/openflow/" + dpid + "/interface" 
    method = "GET"

    interface_list = request_info(operation, url_path, method, "")

    routerIpAddr = {}
    routerMacAddr = {}
    routerPort = {}
    routeDist = {}
    nowtime = interface_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : PortTable" % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "portNo   IpAddress       MacAddress        RouteDist"
    print "-------- --------------- ----------------- ---------"
    for a in range(len(interface_list['interface'])):
        routerIpAddr[a] = interface_list['interface'][a]['routerIpAddr']
        routerMacAddr[a] = interface_list['interface'][a]['routerMacAddr']
        routerPort[a] = interface_list['interface'][a]['routerPort']
        routeDist[a] = interface_list['interface'][a]['routeDist']
        print "%8x %-15s %-15s %s" % (routerPort[a], routerIpAddr[a], routerMacAddr[a], routeDist[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_interface(dpid)


if __name__ == "__main__":
    main()
