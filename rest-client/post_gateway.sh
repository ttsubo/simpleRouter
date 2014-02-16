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

    session.set_debuglevel(4)
    print "----------"
    return json.load(session.getresponse())


##################
# create_gateway
##################

def start_create_gateway(dpid, ipaddress):
    operation = "create_gateway"
    url_path = "/openflow/" + dpid + "/gateway"
    method = "POST"
    request = '''
{
"gateway": {
"ipaddress": "%s"
}
}'''%ipaddress

    gateway_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(gateway_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"

    ipaddress = "192.168.0.1"
    start_create_gateway(dpid, ipaddress)

if __name__ == "__main__":
    main()
