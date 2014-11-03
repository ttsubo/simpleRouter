#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_portstats
###############

def start_get_portstats(dpid):
    operation = "get_portstats"
    url_path = "/openflow/" + dpid + "/stats/port" 
    method = "GET"

    portstats_list = request_info(operation, url_path, method, "")

    portNo = {}
    rxBytes = {}
    rxErrors = {}
    rxPackets = {}
    txBytes = {}
    txErrors = {}
    txPackets = {}
    nowtime = portstats_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : PortStats" % nowtime
    print "+++++++++++++++++++++++++++++++"

    print "portNo   rxPackets rxBytes  rxErrors txPackets txBytes  txErrors"
    print "-------- --------- -------- -------- --------- -------- --------"
    for a in range(len(portstats_list['stats'])):
        portNo[a] = portstats_list['stats'][a]['portNo']
        rxBytes[a] = portstats_list['stats'][a]['rxBytes']
        rxErrors[a] = portstats_list['stats'][a]['rxErrors']
        rxPackets[a] = portstats_list['stats'][a]['rxPackets']
        txBytes[a] = portstats_list['stats'][a]['txBytes']
        txErrors[a] = portstats_list['stats'][a]['txErrors']
        txPackets[a] = portstats_list['stats'][a]['txPackets']
        print "%8x %9d %8d %8d %9d %8d %8d" % (portNo[a],
                                          rxPackets[a], rxBytes[a], rxErrors[a],
                                          txPackets[a], txBytes[a], txErrors[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_portstats(dpid)


if __name__ == "__main__":
    main()
