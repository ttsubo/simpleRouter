#!/usr/bin/env python
#-*- coding: utf-8 -*-

from common_func import request_info

###############
# get_peerstatus
###############

def start_get_peer_status(dpid):
    operation = "get_peer_status"
    url_path = "/openflow/" + dpid + "/status/peer" 
    method = "GET"

    peerstatus_list = request_info(operation, url_path, method, "")

    occurTime = {}
    status = {}
    myPeer = {}
    remotePeer = {}
    asNumber = {}
    nowtime = peerstatus_list['time']
    print "+++++++++++++++++++++++++++++++"
    print "%s : Peer Status" % nowtime
    print "+++++++++++++++++++++++++++++++"


    print "occurTime            status    myPeer             remotePeer         asNumber"
    print "-------------------- --------- ------------------ ------------------ --------"
    for a in range(len(peerstatus_list['status'])):
        occurTime[a] = peerstatus_list['status'][a]['occurTime']
        status[a] = peerstatus_list['status'][a]['status']
        myPeer[a] = peerstatus_list['status'][a]['myPeer']
        remotePeer[a] = peerstatus_list['status'][a]['remotePeer']
        asNumber[a] = peerstatus_list['status'][a]['asNumber']
        print "%s  %-9s %-18s %-18s %s" % (occurTime[a], status[a],
                                        myPeer[a], remotePeer[a],
                                        asNumber[a])
        

##############
# main
##############

def main():
    dpid = "0000000000000001"
    start_get_peer_status(dpid)


if __name__ == "__main__":
    main()
