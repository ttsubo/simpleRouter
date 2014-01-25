import json
import logging

from simpleRouter import *
from ryu.controller import dpset
from ryu.lib import dpid
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

LOG = logging.getLogger('OpenflowRouter')
#LOG.setLevel(logging.DEBUG)

class OpenflowRouter(SimpleRouter):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(OpenflowRouter, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        self.ports = {}
        wsgi = kwargs['wsgi']
        wsgi.register(RouterController, {'OpenFlowRouter' : self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(OpenflowRouter, self).switch_features_handler(ev)
        datapath = ev.msg.datapath

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        super(OpenflowRouter, self).packet_in_handler(ev)

    def register_inf(self, dpid, routerIp, routerMac, hostIp, outPort):
        LOG.debug("Register Interface(port%s)"% outPort)
        datapath = self.dpset.get(dpid)
        if outPort == self.ROUTER_PORT1:
            self.send_arp(datapath, 1, routerMac, routerIp, "ff:ff:ff:ff:ff:ff",
                          hostIp, self.ROUTER_PORT1)
            LOG.debug("send ARP request %s => %s (port%d)"
                     %(routerMac, "ff:ff:ff:ff:ff:ff", self.ROUTER_PORT1))
        elif outPort == self.ROUTER_PORT2:
            self.send_arp(datapath, 1, routerMac, routerIp, "ff:ff:ff:ff:ff:ff",
                          hostIp, self.ROUTER_PORT2)
            LOG.debug("send ARP request %s => %s (port%d)"
                     %(routerMac, "ff:ff:ff:ff:ff:ff", self.ROUTER_PORT2))
        else:
            LOG.debug("Unknown Interface!!")



class RouterController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RouterController, self).__init__(req, link, data, **config)
        self.router_spp = data['OpenFlowRouter']

    @route('router', '/openflow/{dpid}/interface/{port}', methods=['GET'], requirements={'dpid': dpid.DPID_PATTERN})
    def get_interface(self, req, dpid, port, **kwargs):

        result = self.getInterface(int(dpid, 16), port)
        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    @route('router', '/openflow/{dpid}/interface', methods=['POST'], requirements={'dpid': dpid.DPID_PATTERN})
    def set_interface(self, req, dpid, **kwargs):

        interface_param = eval(req.body)
        result = self.setInterface(int(dpid, 16), interface_param)

        message = json.dumps(result)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)


    def setInterface(self, dpid, interface_param):
        simpleRouter = self.router_spp
        routerMac = interface_param['interface']['macaddress']
        routerIp = interface_param['interface']['ipaddress']
        port = int(interface_param['interface']['port'])
        hostIp = interface_param['interface']['opposite_ipaddress']

        simpleRouter.register_inf(dpid, routerIp, routerMac, hostIp, port)

        return {
            'id': '%016d' % dpid,
            'interface': {
                'port': '%s' % port,
                'macaddress': '%s' % routerMac,
                'ipaddress': '%s' % routerIp,
                'opposite_ipaddress': '%s' % hostIp
            }
        }


    def getInterface(self, dpid, port):
        simpleRouter = self.router_spp

        if port == "1":
            return {
                'id': '%016d' % dpid,
                'interface': {
                    'port': '%s' % simpleRouter.ROUTER_PORT1,
                    'macaddress': '%s' % simpleRouter.ROUTER_MACADDR1,
                    'ipaddress': '%s' % simpleRouter.ROUTER_IPADDR1,
                    'opposite_ipaddress': '%s' % simpleRouter.HOST_IPADDR1
                }
            }
        elif port == "2":
            return {
                'id': '%016d' % dpid,
                'interface': {
                    'port': '%s' % simpleRouter.ROUTER_PORT2,
                    'macaddress': '%s' % simpleRouter.ROUTER_MACADDR2,
                    'ipaddress': '%s' % simpleRouter.ROUTER_IPADDR2,
                    'opposite_ipaddress': '%s' % simpleRouter.HOST_IPADDR2
                }
            }


