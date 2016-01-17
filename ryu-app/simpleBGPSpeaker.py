# Copyright (c) 2014-2016 ttsubo
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

import eventlet
import logging
import datetime
import time

# BGPSpeaker needs sockets patched
eventlet.monkey_patch()

from netaddr.ip import IPNetwork
from operator import attrgetter
from ryu.base import app_manager
from ryu.lib import hub
from ryu.services.protocols.bgp.bgpspeaker import BGPSpeaker
from ryu.services.protocols.bgp.info_base.base import ASPathFilter
from ryu.services.protocols.bgp.info_base.base import AttributeMap

LOG = logging.getLogger('SimpleBGPSpeaker')
LOG.setLevel(logging.INFO)
logging.basicConfig()


class BgpPeerStatus(object):
    def __init__(self, nowtime, status, myRouterId, remote_ip, remote_as):
        super(BgpPeerStatus, self).__init__()

        self.occurTime = nowtime.strftime("%Y/%m/%d %H:%M:%S")
        self.status = status
        self.myPeer = myRouterId
        self.remotePeer = remote_ip
        self.asNumber = remote_as
    def getStatus(self):
        return self.occurTime, self.status, self.myPeer, self.remotePeer, self.asNumber


class SimpleBGPSpeaker(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(SimpleBGPSpeaker, self).__init__(*args, **kwargs)
        self.bgp_q = hub.Queue()
        self.name = 'bgps'
        self.bgpPeerStatus = {}
        self.target_route_dist = None
        self.bgp_thread = hub.spawn(self.monitor_target_remotePrefix)

    def monitor_target_remotePrefix(self):
        previous_route_dist = None
        while True:
            if self.target_route_dist == None:
                pass
            elif self.target_route_dist == previous_route_dist:
                self.target_route_dist = None
            else:
                previous_route_dist = self.target_route_dist
            time.sleep(60)


    def dump_remote_best_path_change(self, event):
        remote_prefix = {}
        prefixInfo = IPNetwork(event.prefix)

        remote_prefix['remote_as'] = event.remote_as
        remote_prefix['route_dist'] = event.route_dist
        remote_prefix['prefix'] = str(prefixInfo.ip)
        remote_prefix['netmask'] = str(prefixInfo.netmask)
        remote_prefix['nexthop'] = event.nexthop
        remote_prefix['label'] = event.label
        remote_prefix['withdraw'] = event.is_withdraw
        LOG.debug("remote_prefix=%s"%remote_prefix)

        if self.filter_regist_remotePrefix(event.route_dist):
            self.bgp_q.put(remote_prefix)

    def filter_regist_remotePrefix(self, route_dist):
        if self.target_route_dist == None:
            result = True
        elif self.target_route_dist == route_dist:
            result = True
        else:
            result = False

        return result


    def detect_peer_down(self, remote_ip, remote_as):
        nowtime = datetime.datetime.now()
        LOG.info("%s: Peer down!![remote_ip: %s, remote_as: %s]"%(nowtime, remote_ip, remote_as))
        self.bgpPeerStatus[nowtime] = BgpPeerStatus(nowtime,
                                                    "Peer Down",
                                                    self.myRouterId,
                                                    remote_ip,
                                                    remote_as)


    def detect_peer_up(self, remote_ip, remote_as):
        nowtime = datetime.datetime.now()
        LOG.info("%s: Peer up!![remote_ip: %s, remote_as: %s]"%(nowtime, remote_ip, remote_as))
        self.bgpPeerStatus[nowtime] = BgpPeerStatus(nowtime,
                                                    "Peer Up",
                                                    self.myRouterId,
                                                    remote_ip,
                                                    remote_as)


    def start_bgpspeaker(self, asNum, routerId, label_start, label_end):
        self.myRouterId = routerId
        self.labelRange = tuple([label_start, label_end])
        self.speaker = BGPSpeaker(as_number=asNum, router_id=routerId,
                     best_path_change_handler=self.dump_remote_best_path_change,
                     peer_down_handler=self.detect_peer_down,
                     peer_up_handler=self.detect_peer_up,
                     label_range=self.labelRange)


    def start_bmpclient(self, address, port):
        return self.speaker.bmp_server_add(address, port)


    def stop_bmpclient(self, address, port):
        return self.speaker.bmp_server_del(address, port)


    def add_neighbor(self, peerIp, asNumber, med, localPref, filterAsNum):
        self.speaker.neighbor_add(peerIp, asNumber, is_next_hop_self=True,
                               enable_vpnv4=True, enable_enhanced_refresh=True,
                               multi_exit_disc=med)
        if filterAsNum:
            as_path_filter = ASPathFilter(filterAsNum,
                                          policy=ASPathFilter.POLICY_TOP)
            if localPref:
                attribute_map = AttributeMap([as_path_filter],
                                             AttributeMap.ATTR_LOCAL_PREF,
                                             localPref)
                self.speaker.attribute_map_set(peerIp, [attribute_map],
                                               route_family='ipv4')


    def add_vrf(self, routeDist, importList, exportList):
        self.speaker.vrf_add(routeDist, importList, exportList)
        self.target_route_dist = routeDist


    def del_vrf(self, routeDist):
        self.speaker.vrf_del(routeDist)


    def add_prefix(self, ipaddress, netmask, nexthop=None, routeDist=None):
        prefix = IPNetwork(ipaddress + '/' + netmask)
        local_prefix = str(prefix.cidr)

        if routeDist:
            if nexthop:
                LOG.info("Send BGP UPDATE Message [%s, %s]"%(local_prefix,
                          nexthop))
            else:
                LOG.info("Send BGP UPDATE Message [%s]"%local_prefix)
                nexthop = "0.0.0.0"
            result_list = self.speaker.prefix_add(local_prefix, nexthop,
                                                  routeDist)
            result = result_list[0]
            label = result['label']
            return label
        else:
            if nexthop:
                LOG.info("Send BGP UPDATE Message [%s, %s]"%(local_prefix,
                          nexthop))
                self.speaker.prefix_add(local_prefix, nexthop)
            else:
                LOG.info("Send BGP UPDATE Message [%s]"%local_prefix)
                self.speaker.prefix_add(local_prefix)


    def remove_prefix(self, ipaddress, netmask, routeDist=None):
        prefix = IPNetwork(ipaddress + '/' + netmask)
        local_prefix = str(prefix.cidr)

        LOG.info("Send BGP UPDATE(withdraw) Message [%s]"%local_prefix)
        self.speaker.prefix_del(local_prefix, routeDist)


    def show_rib(self):
        family ="vpnv4"
        format = "cli"
        return self.speaker.rib_get(family, format)


    def show_vrfs(self):
        format = "cli"
        return self.speaker.vrfs_get(format)


    def show_neighbor(self, routetype, address):
        format = "cli"
        return self.speaker.neighbor_get(routetype, address, format)


    def update_neighbor_med(self, peerIp, med_value):
        conf_type = 'multi_exit_disc'
        conf_value = med_value
        LOG.info("Send BGP UPDATE Message for changing MED[%s]"%med_value)
        return self.speaker.neighbor_update(peerIp, conf_type, conf_value)
