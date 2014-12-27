# Copyright (c) 2014 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

import json

from webob import Response
from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib.dpid import DPID_PATTERN
from ryu.lib.ovs import bridge

OVSDB_ADDR1 = 'tcp:192.168.0.1:6632'
OVSDB_ADDR2 = 'tcp:192.168.0.2:6632'

class SetOvsdb(app_manager.RyuApp):

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(SetOvsdb, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(OvsdbController, {'SetOvsdb' : self})


    def setTunnel(self, id, name, type, local_ip, remote_ip):
        if id == 1:
            ovs_bridge = bridge.OVSBridge(id, OVSDB_ADDR1)
        elif id == 2:
            ovs_bridge = bridge.OVSBridge(id, OVSDB_ADDR2)
        else:
            return 1

        ovs_bridge.init()
        ovs_bridge.add_tunnel_port(name, type, local_ip, remote_ip)
        return 0



class OvsdbController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(OvsdbController, self).__init__(req, link, data, **config)
        self.ovsdb_spp = data['SetOvsdb']

    @route('router', '/ovsdb/{dpid}/tunnel', methods=['POST'], requirements={'dpid': DPID_PATTERN})
    def set_tunnel_port(self, req, dpid, **kwargs):

        tunnel_param = eval(req.body)
        result = self.setTunnel(int(dpid, 16), tunnel_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    def setTunnel(self, id, tunnel_param):
        simpleOvsdb = self.ovsdb_spp
        name = tunnel_param['tunnel']['name']
        type = tunnel_param['tunnel']['type']
        local_ip = tunnel_param['tunnel']['local_ip']
        remote_ip = tunnel_param['tunnel']['remote_ip']

        simpleOvsdb.setTunnel(id, name, type, local_ip, remote_ip)

        return {
            'id': '%016d' % id,
            'tunnel': {
                'name': '%s' % name,
                'type': '%s' % type,
                'local_ip': '%s' % local_ip,
                'remote_ip': '%s' % remote_ip
            }
        }


