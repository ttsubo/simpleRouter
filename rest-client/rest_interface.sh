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

###############
# get_switches
###############

def start_get_switches():
    operation = "get_switches"
    url_path = "/openflow" 
    method = "GET"

    switches_result = request_info(operation, url_path, method, "")
    print "----------"
    print json.dumps(switches_result, sort_keys=False, indent=4)
    print ""


###############
# get_interface
###############

def start_get_interface(dpid, port):
    operation = "get_interface"
    url_path = "/openflow/" + dpid + "/interface/" + port 
    method = "GET"

    interface_result = request_info(operation, url_path, method, "")
    print "----------"
    print json.dumps(interface_result, sort_keys=False, indent=4)
    print ""


##################
# create_interface
##################

def start_create_interface(dpid, port, macaddress, ipaddress, opposite_ipaddress):
    operation = "create_interface"
    url_path = "/openflow/" + dpid + "/interface"
    method = "POST"
    request = '''
{
"interface": {
"port": "%s",
"macaddress": "%s",
"ipaddress": "%s",
"opposite_ipaddress": "%s"
}
}'''% (port, macaddress, ipaddress, opposite_ipaddress)

    interface_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(interface_result, sort_keys=False, indent=4)
    print ""


###############
# create_prefix
###############

def start_create_prefix(dpid, prefix, nexthop):
    operation = "create_prefix"
    url_path = "/openflow/" + dpid + "/route"
    method = "POST"
    request = '''
{
"route": {
"prefix": "%s",
"nexthop": "%s",
}
}'''% (prefix, nexthop)

    prefix_result = request_info(operation, url_path, method, request)
    print "----------"
    print json.dumps(prefix_result, sort_keys=False, indent=4)
    print ""



##############
# main
##############

def main():
    dpid = "0000000000000001"
#    prefix = "192.168.100.1"
#    nexthop = "192.168.0.1"
#    start_create_prefix(dpid, prefix, nexthop)

#    start_get_switches()

    port = "1"
    macaddress = "00:00:00:00:00:01"
    ipaddress = "192.168.0.10"
    opposite_ipaddress = "192.168.0.1"
    start_create_interface(dpid, port, macaddress, ipaddress, opposite_ipaddress)

    time.sleep(10)
    port = "2"
    macaddress = "00:00:00:00:00:02"
    ipaddress = "192.168.1.10"
    opposite_ipaddress = "192.168.1.1"
    start_create_interface(dpid, port, macaddress, ipaddress, opposite_ipaddress)

    time.sleep(2)
    port = "1"
    start_get_interface(dpid, port)

    time.sleep(2)
    port = "2"
    start_get_interface(dpid, port)

if __name__ == "__main__":
    main()
