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

LOG = logging.getLogger('SimpleBGPSpeaker')
LOG.setLevel(logging.INFO)
logging.basicConfig()


class SimpleBGPSpeaker(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(SimpleBGPSpeaker, self).__init__(*args, **kwargs)
        self.bgp_q = hub.Queue()
        self.name = 'bgps'


    def dump_remote_best_path_change(self, event):
        remote_prefix = {}
        prefixInfo = IPNetwork(event.prefix)

        remote_prefix['remote_as'] = event.remote_as
        remote_prefix['prefix'] = str(prefixInfo.ip)
        remote_prefix['netmask'] = str(prefixInfo.netmask)
        remote_prefix['nexthop'] = event.nexthop
        remote_prefix['withdraw'] = event.is_withdraw
        LOG.info("remote_prefix=%s"%remote_prefix)
        self.bgp_q.put(remote_prefix)


    def add_neighbor(self, peerIp, asNumber):
        self.speaker = BGPSpeaker(as_number=65002, router_id='10.0.0.2',
                     best_path_change_handler=self.dump_remote_best_path_change,
                     ssh_console=True)
        self.speaker.neighbor_add(peerIp, asNumber)


    def add_prefix(self, ipaddress, netmask, nexthop=""):
        prefix = IPNetwork(ipaddress + '/' + netmask)
        local_prefix = str(prefix.cidr)
        if nexthop:
            print"add new prefix[prefix=%s, nexthop=%s]"%(local_prefix, nexthop)
            self.speaker.prefix_add(local_prefix, nexthop)
        else:
            print"add new prefix[prefix=%s]"%(local_prefix)
            self.speaker.prefix_add(local_prefix)
