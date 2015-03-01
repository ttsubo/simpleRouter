#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
from httplib import HTTPConnection

HOST = "127.0.0.1"
PORT = "8080"

##################
# request_info
##################

def request_info(operator, url_path, method, request=None):
    print "=" *70
    print "%s" % operator
    print "=" *70
    session = HTTPConnection("%s:%s" % (HOST, PORT))

    header = {
        "Content-Type": "application/json"
        }
    if method == "GET":
        if request:
            print url_path
            print request
            session.request("GET", url_path, request, header)
        else:
            print url_path
            session.request("GET", url_path, "", header)
    elif method == "POST":
        print url_path
        print request
        session.request("POST", url_path, request, header)
    elif method == "PUT":
        print url_path
        print request
        session.request("PUT", url_path, request, header)
    elif method == "DELETE":
        print url_path
        print request
        session.request("DELETE", url_path, request, header)



    session.set_debuglevel(4)
    print "----------"
    return json.load(session.getresponse())

