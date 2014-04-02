from ryu.lib.of_config.capable_switch import OFCapableSwitch
import ryu.lib.of_config.classes as ofc
import time

sess = OFCapableSwitch(
    host='192.168.100.1',
    port=1830,
    username='linc',
    password='linc',
    unknown_host_cb=lambda host, fingeprint: True)

csw = sess.get()
for p in csw.resources.port:
    print p.resource_id, p.current_rate

csw = sess.get_config('running')
for p in csw.resources.port:
    print p.resource_id, p.configuration.admin_state

time.sleep(2)
csw = sess.get_config('running')
for p in csw.resources.port:
    p.configuration.admin_state = 'down'
sess.edit_config('running', csw)

csw = sess.get_config('running')
for p in csw.resources.port:
    print p.resource_id, p.configuration.admin_state

