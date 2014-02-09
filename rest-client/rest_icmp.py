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

def request_info(operation, url_path, method, request):
    print "=" *70
    print "%s" % operation
    print "=" *70
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
    elif method == "PUT":
        request = request
        print url_path
        print request
        session.request("PUT", url_path, request, header)


    session.set_debuglevel(4)
    print "----------"
    return json.load(session.getresponse())


##################
# ping
##################

def start_ping(dpid, hostIp, data, hostMac, routerMac, routerIp, outPort):
    operation = "ping"
    url_path = "/openflow/" + dpid + "/ping"
    method = "PUT"
    request = '''
{
"ping": {
"hostIp": "%s",
"data": "%s",
"hostMac": "%s",
"routerMac": "%s",
"routerIp": "%s",
"outPort": "%s"
}
}'''% (hostIp, data, hostMac, routerMac, routerIp, outPort)

    ping_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(ping_result, sort_keys=False, indent=4)
    print ""




##############
# main
##############

def main():
    dpid = "0000000000000001"

    hostIp = "192.168.0.1"
#    hostIp = "172.16.101.1"
    data = "Created by Openflow Router"
    hostMac = ""
    routerMac = ""
    routerIp = ""
    outPort = ""
    start_ping(dpid, hostIp, data, hostMac, routerMac, routerIp, outPort)

if __name__ == "__main__":
    main()
