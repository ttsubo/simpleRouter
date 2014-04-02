#-*- coding: utf-8 -*-

import socket
import json

OVSDB_IP = '192.168.0.1'
OVSDB_PORT = 6632

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((OVSDB_IP, OVSDB_PORT))

monitor_query = \
{"method":"monitor",
"params":["Open_vSwitch","null",{"Open_vSwitch":{"columns":["bridges","cur_cfg","db_version","external_ids","manager_options","next_cfg","other_config","ovs_version","ssl","statistics","system_type","system_version"]}}],
"id":0}

print "----------------------------------"
print "json rpc request"
print "----------------------------------"
print json.dumps(monitor_query, sort_keys=False, indent=1)
s.send(json.dumps(monitor_query))

print "----------------------------------"
print "json rpc reply"
print "----------------------------------"
response = s.recv(8192)
result = json.loads(response)
print json.dumps(result, sort_keys=False, indent=1)
