#!/usr/bin/env python
#-*- coding: utf-8 -*-

from httplib import HTTPConnection
import json
import time

HOST = "127.0.0.1"
PORT = "8080"

##################
# request_info
##################

def request_info(url_path, method, request):
    session = HTTPConnection("%s:%s" % (HOST, PORT))

    header = {
        "Content-Type": "application/json"
        }
    if method == "GET":
        print url_path
        session.request("GET", url_path, "", header)
    elif method == "POST":
        request = request
        print url_path
        print request
        session.request("POST", url_path, request, header)

    session.set_debuglevel(4)
    print "-----------------------------------------------------------"
    return json.load(session.getresponse())


###############
# get_arp
###############

def start_get_arp(dpid):
    url_path = "/openflow/" + dpid + "/arp" 
    method = "GET"

    arp_list = request_info(url_path, method, "")

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
        print "%8x %s %s" % (routerPort[a], hostMacAddr[a], hostIpAddr[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_arp(dpid)


if __name__ == "__main__":
    main()
