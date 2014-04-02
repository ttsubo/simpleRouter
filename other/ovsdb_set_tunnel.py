#-*- coding: utf-8 -*-

import socket
import json

OVSDB_IP = '192.168.0.1'
OVSDB_PORT = 6632

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((OVSDB_IP, OVSDB_PORT))

monitor_query = \
{"method":"transact",
'params':["Open_vSwitch",{"rows":[{"ports":["set",[["uuid","0418fef3-1d61-4693-89cc-a002bca3c5bd"],["uuid","8f45538d-64b8-41df-bc51-6b0ea815065e"]]]}],"columns":["ports"],"table":"Bridge","until":"==","where":[["_uuid","==",["uuid","55d71da8-cd33-4117-b7a3-de8a5b4222a3"]]],"timeout":0,"op":"wait"},{"rows":[{"interfaces":["uuid","62353edf-7514-4a87-af11-be9d19330913"]}],"columns":["interfaces"],"table":"Port","until":"==","where":[["_uuid","==",["uuid","8f45538d-64b8-41df-bc51-6b0ea815065e"]]],"timeout":0,"op":"wait"},{"rows":[{"bridges":["uuid","55d71da8-cd33-4117-b7a3-de8a5b4222a3"]}],"columns":["bridges"],"table":"Open_vSwitch","until":"==","where":[["_uuid","==",["uuid","82524775-43a3-4838-90ae-61e2cbd10820"]]],"timeout":0,"op":"wait"},{"rows":[{"interfaces":["uuid","fc8c8235-8381-495a-b53e-0f2736d69ac5"]}],"columns":["interfaces"],"table":"Port","until":"==","where":[["_uuid","==",["uuid","0418fef3-1d61-4693-89cc-a002bca3c5bd"]]],"timeout":0,"op":"wait"},{"row":{"name":"vxlan1","options":["map",[["remote_ip","172.16.0.2"]]],"type":"vxlan"},"table":"Interface","uuid-name":"row968fcbc0_4881_4342_96b6_1a8673df5ac1","op":"insert"},{"row":{"ports":["set",[["uuid","0418fef3-1d61-4693-89cc-a002bca3c5bd"],["named-uuid","row7b1d3575_6de5_4329_8a5d_6a6dcedcec09"],["uuid","8f45538d-64b8-41df-bc51-6b0ea815065e"]]]},"table":"Bridge","where":[["_uuid","==",["uuid","55d71da8-cd33-4117-b7a3-de8a5b4222a3"]]],"op":"update"},{"row":{"name":"vxlan1","interfaces":["named-uuid","row968fcbc0_4881_4342_96b6_1a8673df5ac1"]},"table":"Port","uuid-name":"row7b1d3575_6de5_4329_8a5d_6a6dcedcec09","op":"insert"},{"mutations":[["next_cfg","+=",1]],"table":"Open_vSwitch","where":[["_uuid","==",["uuid","82524775-43a3-4838-90ae-61e2cbd10820"]]],"op":"mutate"},{"columns":["next_cfg"],"table":"Open_vSwitch","where":[["_uuid","==",["uuid","82524775-43a3-4838-90ae-61e2cbd10820"]]],"op":"select"},{"comment":"ovs-vsctl: ovs-vsctl -v add-port br0 vxlan1 -- set interface vxlan1 type=vxlan options:remote_ip=172.16.0.2","op":"comment"}],
"id":1}


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

