import eventlet
import logging
import datetime

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

AS_NUMBER = 65002
ROUTER_ID = '10.0.1.1'

class SimpleBGPSpeaker(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(SimpleBGPSpeaker, self).__init__(*args, **kwargs)
        self.bgp_q = hub.Queue()
        self.name = 'bgps'
        self.bgps_thread = hub.spawn(self._bgpspeaker)


    def dump_remote_best_path_change(self, event):
        remote_prefix = {}
        prefixInfo = IPNetwork(event.prefix)

        remote_prefix['remote_as'] = event.remote_as
        remote_prefix['prefix'] = str(prefixInfo.ip)
        remote_prefix['netmask'] = str(prefixInfo.netmask)
        remote_prefix['nexthop'] = event.nexthop
        remote_prefix['withdraw'] = event.is_withdraw
        LOG.debug("remote_prefix=%s"%remote_prefix)
        self.bgp_q.put(remote_prefix)

    def _bgpspeaker(self):
        self.speaker = BGPSpeaker(as_number=AS_NUMBER, router_id=ROUTER_ID,
                     best_path_change_handler=self.dump_remote_best_path_change,
                     ssh_console=True)


    def add_neighbor(self, peerIp, asNumber, med, localPref, filterAsNum):
        self.speaker.neighbor_add(peerIp, asNumber, is_next_hop_self=True, multi_exit_disc=med)
        if filterAsNum:
            as_path_filter = ASPathFilter(filterAsNum, policy=ASPathFilter.POLICY_TOP)
            if localPref:
                attribute_map = AttributeMap([as_path_filter], AttributeMap.ATTR_LOCAL_PREF, localPref)
                self.speaker.attribute_map_set(peerIp, [attribute_map], route_family='ipv4')


    def add_prefix(self, ipaddress, netmask, nexthop=""):
        prefix = IPNetwork(ipaddress + '/' + netmask)
        local_prefix = str(prefix.cidr)
        if nexthop:
            LOG.info("Send BGP UPDATE Message for route(%s, %s)"%(local_prefix, nexthop))
            self.speaker.prefix_add(local_prefix, nexthop)
        else:
            LOG.info("Send BGP UPDATE Message for route(%s)"%(local_prefix))
            self.speaker.prefix_add(local_prefix)

    def remove_prefix(self, ipaddress, netmask):
        prefix = IPNetwork(ipaddress + '/' + netmask)
        local_prefix = str(prefix.cidr)

        LOG.info("Send BGP UPDATE(withdraw) Message for route(%s)"%(local_prefix))
        self.speaker.prefix_del(local_prefix)
