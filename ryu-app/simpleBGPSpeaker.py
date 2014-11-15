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
        self.bgps_thread = hub.spawn(self._bgps)


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


    def _bgps(self):
        hub.sleep(30)
        speaker = BGPSpeaker(as_number=65002, router_id='10.0.0.2',
                     best_path_change_handler=self.dump_remote_best_path_change)

        speaker.neighbor_add('192.168.200.1', 65001)

        count = 1
        while True:
            hub.sleep(10)
            prefix = '10.20.' + str(count) + '.0/24'
            print("add a new prefix", prefix)
            speaker.prefix_add(prefix)
            count += 1
            if count == 4:
                hub.sleep(60)

