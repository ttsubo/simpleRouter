import eventlet
import logging
import datetime

# BGPSpeaker needs sockets patched
eventlet.monkey_patch()

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
        self.name = 'bgps'
        self.bgps_thread = hub.spawn(self._bgps)

    def dump_remote_best_path_change(self, event):
        print('the best path changed:', event.remote_as, event.prefix,\
              event.nexthop, event.is_withdraw)

    def _bgps(self):
        hub.sleep(30)
        speaker = BGPSpeaker(as_number=65002, router_id='10.0.0.2',
                         best_path_change_handler=self.dump_remote_best_path_change)

        speaker.neighbor_add('192.168.200.1', 65001)

        # uncomment the below line if the speaker needs to talk with a bmp server.
        # speaker.bmp_server_add('192.168.177.2', 11019)
        count = 1
        while True:
            hub.sleep(10)
            prefix = '10.20.' + str(count) + '.0/24'
            print("add a new prefix", prefix)
            speaker.prefix_add(prefix)
            count += 1
            if count == 4:
                hub.sleep(60)

