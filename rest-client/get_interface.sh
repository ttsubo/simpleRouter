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
# get_interface
###############

def start_get_interface(dpid):
    url_path = "/openflow/" + dpid + "/interface" 
    method = "GET"

    interface_list = request_info(url_path, method, "")

    routerIpAddr = {}
    routerMacAddr = {}
    routerPort = {}
    nowtime = interface_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : PortTable" % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "portNo   IpAddress    MacAddress"
    print "-------- ------------ -----------------"
    for a in range(len(interface_list['interface'])):
        routerIpAddr[a] = interface_list['interface'][a]['routerIpAddr']
        routerMacAddr[a] = interface_list['interface'][a]['routerMacAddr']
        routerPort[a] = interface_list['interface'][a]['routerPort']
        print "%8x %s %s" % (routerPort[a], routerIpAddr[a], routerMacAddr[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_interface(dpid)


if __name__ == "__main__":
    main()
