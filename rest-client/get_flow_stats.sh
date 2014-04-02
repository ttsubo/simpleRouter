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
# get_flowstats
###############

def start_get_flowstats(dpid):
    url_path = "/openflow/" + dpid + "/stats/flow" 
    method = "GET"

    flowstats_list = request_info(url_path, method, "")

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
