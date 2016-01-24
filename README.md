What's simpleRouter for Raspberry Pi2
==========
The simpleRouter is a software BGP router based Ryu SDN Framework.  
It works as a OpenFlow equipment supporting Vpnv4(mp-bgp) under Raspberry Pi2. 


Installation
===========
### Raspberry Pi2 environment
It recommends for using "the Raspberry Pi 2 Model B" which have Multi USB Ports.
I've already confirmed that "Raspberry Pi Model B" works properly as well.

(1) Checking Raspberry pi2 edition

	processor	: 0
	model name	: ARMv7 Processor rev 5 (v7l)
	BogoMIPS	: 38.40
	Features	: half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm 
	CPU implementer	: 0x41
	CPU architecture: 7
	CPU variant	: 0x0
	CPU part	: 0xc07
	CPU revision	: 5

	...(snip)

	Hardware	: BCM2709
	Revision	: a01041
	Serial		: 00000000cacd6b93


(2) Checking Raspbian version

	pi@raspberrypi:~ $ uname -a
	Linux raspberrypi-1 4.1.13-v7+ #826 SMP PREEMPT Fri Nov 13 20:19:03 GMT 2015 armv7l GNU/Linux


### Ryu Controller installation

(1) Updating packages

	pi@raspberrypi:~ $ sudo apt-get update


(2) Installing Ryu Controller  

	pi@raspberrypi:~ $ sudo apt-get install python-dev
	pi@raspberrypi:~ $ sudo apt-get install python-pip
	pi@raspberrypi:~ $ sudo apt-get -y install libxml2-dev
	pi@raspberrypi:~ $ sudo apt-get -y install python-lxml
	pi@raspberrypi:~ $ sudo pip install --upgrade six
	pi@raspberrypi:~ $ git clone https://github.com/osrg/ryu.git
	pi@raspberrypi:~ $ cd ryu/tools/
	pi@raspberrypi:~/ryu/tools $ vi pip-requires
	---------
	eventlet>=0.15
	msgpack-python>=0.3.0  # RPC library, BGP speaker(net_cntl)
	netaddr
	oslo.config>=1.6.0
	routes  # wsgi
	six>=1.4.0
	webob>=1.2  # wsgi


	pi@raspberrypi:~/ryu/tools $ sudo pip install -r pip-requires
	pi@raspberrypi:~/ryu/tools $ cd ..
	pi@raspberrypi:~/ryu $ sudo python ./setup.py install
	pi@raspberrypi:~/ryu $ cd


(3) Checking Ryu version

	pi@raspberrypi:~ $ ryu-manager --version
	ryu-manager 3.29


### Get the latest simpleRouter code from github

	pi@raspberrypi:~ $ git clone https://github.com/ttsubo/simpleRouter.git


### OpenvSwitch installation

(1) Installing OpenvSwitch 

	pi@raspberrypi:~ $ sudo apt-get install openvswitch-switch


(2) Checking OpenvSwitch version

	pi@raspberrypi:~ $ sudo ovs-vsctl --version
	ovs-vsctl (Open vSwitch) 2.3.0
	Compiled Dec 24 2014 05:32:22
	DB Schema 7.6.0


(3) Checking the status of running of OpenvSwitch

	pi@raspberrypi:~ $ service openvswitch-switch status
	● openvswitch-switch.service - LSB: Open vSwitch switch
	   Loaded: loaded (/etc/init.d/openvswitch-switch)
	   Active: active (running) since 日 2016-01-24 08:00:10 JST; 1h 6min ago
	  Process: 541 ExecStart=/etc/init.d/openvswitch-switch start (code=exited, status=0/SUCCESS)
	   CGroup: /system.slice/openvswitch-switch.service
	           ├─734 ovsdb-server: monitoring pid 735 (healthy)
	           ├─735 ovsdb-server /etc/openvswitch/conf.db -vconsole:emer -vsyslo...
	           ├─744 ovs-vswitchd: monitoring pid 745 (healthy)
	           └─745 ovs-vswitchd unix:/var/run/openvswitch/db.sock -vconsole:eme...

Quick Start
===========
### STEP1: Basic and Additional networking configuration
You need to assign physical ports as following.
- eth0 : Management Port (use of maintenance)
- eth1 : OpenFlow Port
- eth2 : OpenFlow Port
- eth3 : OpenFlow Port
- bgpPort1 : Internal Port
- bgpPort2 : Internal Port

(1) Configure the basic networking in Raspbian environment

	pi@raspberrypi:~ $ sudo vi /etc/network/interfaces
	---------
	auto lo
	iface lo inet loopback

	auto eth0
	iface eth0 inet static
	address 192.168.100.101
	netmask 255.255.255.0
	gateway 192.168.100.1

	auto eth1
	iface eth1 inet manual
	up ifconfig $IFACE 0.0.0.0 up
	up ip link set $IFACE promisc on
	down ip link set $IFACE promisc off
	down ifconfig $IFACE down

	auto eth2
	iface eth2 inet manual
	up ifconfig $IFACE 0.0.0.0 up
	up ip link set $IFACE promisc on
	down ip link set $IFACE promisc off
	down ifconfig $IFACE down
	
	auto eth3
	iface eth3 inet manual
	up ifconfig $IFACE 0.0.0.0 up
	up ip link set $IFACE promisc on
	down ip link set $IFACE promisc off
	down ifconfig $IFACE down

	auto bgpPort1
	iface bgpPort1 inet static
	address 172.16.1.101
	netmask 255.255.255.252
	hwaddress ether 00:00:00:11:11:11

	auto bgpPort2
	iface bgpPort2 inet static
	address 172.16.2.102
	netmask 255.255.255.252
	hwaddress ether 00:00:00:22:22:22


	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart


(2) Configure the basic OpenvSwitch networking

	pi@raspberrypi:~ $ sudo ovs-vsctl add-br br0
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 eth1
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 eth2
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 eth3
	pi@raspberrypi:~ $ sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6633
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000001
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 protocols=OpenFlow13
	pi@raspberrypi:~ $ sudo ovs-vsctl set-fail-mode br0 secure
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 datapath_type=netdev (*)

	(*) In case of using vpnv4, needs to switch ovs-vswitchd in userspace mode.


(3) Configure the logical port in OpenvSwitch environment

	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 bgpPort1 -- set Interface bgpPort1 type=internal
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 bgpPort2 -- set Interface bgpPort2 type=internal
	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart


(4) Checking OpenFlow ports

	pi@raspberrypi:~ $ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	OFPST_PORT_DESC reply (OF1.3) (xid=0x2):
	 1(eth1): addr:34:95:db:2a:89:ba
	     config:     0
	     state:      LINK_DOWN
	     current:    10MB-HD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 10 Mbps now, 100 Mbps max
	 2(eth2): addr:34:95:db:2a:8d:c2
	     config:     0
	     state:      LINK_DOWN
	     current:    10MB-HD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 10 Mbps now, 100 Mbps max
	 3(eth3): addr:34:95:db:0b:3d:87
	     config:     0
	     state:      LINK_DOWN
	     current:    10MB-HD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 10 Mbps now, 100 Mbps max
	 4(bgpPort1): addr:00:00:00:11:11:11
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 5(bgpPort2): addr:00:00:00:22:22:22
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 LOCAL(br0): addr:34:95:db:0b:3d:87
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max


### STEP2: Starting simpleRouter
You can Start simpleRouter.

        pi@raspberrypi:~ $ cd simpleRouter/ryu-app/
        pi@raspberrypi:~/simpleRouter/ryu-app $ sudo ryu-manager openflowRouter.py
        loading app openflowRouter.py
        loading app ryu.controller.ofp_handler
        creating context wsgi
        instantiating app None of SimpleMonitor
        creating context monitor
        instantiating app None of SimpleBGPSpeaker
        creating context bgps
        instantiating app openflowRouter.py of OpenflowRouter
        instantiating app ryu.controller.ofp_handler of OFPHandler
        (1594) wsgi starting up on http://0.0.0.0:8080/


### STEP3: Applying various information for simpleRouter
You can apply various information through RESTful in simpleRouter.  
These scripts are useful for applying some parameters to simpleRouter. 

	static   (eth3) +---------+ (eth1)   mp-BGP     +--------+
	... ----------+ | simple  | +-----------------+ |  BGP   | +---- ...
	    192.168.0.1 | Router  | 172.16.1.101/30     | Router |
	                |         |                     +--------+
	                |         |                     < AS65011 >
	                |         |
	                |         | (eth2)   mp-BGP     +--------+
	                |         | +-----------------+ |  BGP   | +---- ...
	                |         | 172.16.2.101/30     | Router |
	                +---------+                     +--------+
	                < AS65011 >                     < AS65011 >

	<-- Target in simpleRouter -------------->     <-- out of scope -->


(1) You can edit some parammeters for simpleRouter.

	pi@raspberrypi:~ $ cat simpleRouter/rest-client/OpenFlow.ini 
	[Bgp]
	as_number = "65011"
	router_id = "10.0.0.1"
	redistribute_on = "ON"
	redistribute_off = "OFF"
	vrf_routeDist = "65011:101"
	label_range_start = "100"
	label_range_end = "199"

	[Vrf]
	route_dist = "65011:101"
	import_routeTarget = "65011:101"
	export_routeTarget = "65011:101"

	[Port1]
	port = "1"
	macaddress = "00:00:00:11:11:11"
	ipaddress = "172.16.1.101"
	netmask = "255.255.255.252"
	opposite_ipaddress = "172.16.1.102"
	opposite_asnumber = "65011"
	port_offload_bgp = "4"
	vrf_routeDist = ""

	[Port2]
	port = "2"
	macaddress = "00:00:00:22:22:22"
	ipaddress = "172.16.2.101"
	netmask = "255.255.255.252"
	opposite_ipaddress = "172.16.2.102"
	opposite_asnumber = "65011"
	port_offload_bgp = "5"
	vrf_routeDist = ""

	[Port3]
	port = "3"
	macaddress = "00:00:00:00:00:01"
	ipaddress = "192.168.0.1"
	netmask = "255.255.255.0"
	opposite_ipaddress = "192.168.0.2"
	opposite_asnumber = ""
	port_offload_bgp = ""
	vrf_routeDist = "65011:101"


(2) You need to apply some parameters of [Bgp] section in OpenFLow.ini. 

	pi@raspberrypi:~/simpleRouter/rest-client $ ./post_start_bgpspeaker.sh
	======================================================================
	start_bgp
	======================================================================
	/openflow/0000000000000001/bgp

	{
	"bgp": {
	"as_number": "65011",
	"router_id": "10.0.0.1",
	"label_range_start": "100",
	"label_range_end": "199"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 136
	header: Date: Sun, 24 Jan 2016 06:34:49 GMT
	----------
	{
	    "bgp": {
	        "router_id": "10.0.0.1", 
	        "as_number": "65011", 
	        "label_range_start": "100", 
	        "label_range_end": "199"
	    }, 
	    "id": "0000000000000001"
	}


(3) You need to apply some parameters of [Port..] section in OpenFLow.ini. 

	pi@raspberrypi:~/simpleRouter/rest-client $ ./post_interface.sh 
	======================================================================
	create_interface
	======================================================================
	/openflow/0000000000000001/interface

	{
	"interface": {
	"port": "1",
	"macaddress": "00:00:00:11:11:11",
	"ipaddress": "172.16.1.101",
	"netmask": "255.255.255.252",
	"opposite_ipaddress": "172.16.1.102",
	"opposite_asnumber": "65011",
	"port_offload_bgp": "4",
	"bgp_med": "",
	"bgp_local_pref": "",
	"bgp_filter_asnumber": "",
	"vrf_routeDist": ""
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 326
	header: Date: Sun, 24 Jan 2016 06:34:53 GMT
	----------
	{
	    "interface": {
	        "port_offload_bgp": "4", 
	        "bgp_local_pref": "", 
	        "opposite_asnumber": "65011", 
	        "macaddress": "00:00:00:11:11:11", 
	        "bgp_med": "", 
	        "netmask": "255.255.255.252", 
	        "opposite_ipaddress": "172.16.1.102", 
	        "vrf_routeDist": "", 
	        "bgp_filter_asnumber": "", 
	        "ipaddress": "172.16.1.101", 
	        "port": "1"
	    }, 
	    "id": "0000000000000001"
	}

	...(snip)


(4) You need to apply some parameters of [Vrf] section in OpenFLow.ini. 

	pi@raspberrypi:~/simpleRouter/rest-client $ ./post_vrf.sh 
	======================================================================
	create_vrf
	======================================================================
	/openflow/0000000000000001/vrf

	{
	"vrf": {
	"route_dist": "65011:101",
	"import": "65011:101",
	"export": "65011:101"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 108
	header: Date: Sun, 24 Jan 2016 06:35:23 GMT
	----------
	{
	    "id": "0000000000000001", 
	    "vrf": {
	        "import": "65011:101", 
	        "export": "65011:101", 
	        "route_dist": "65011:101"
	    }
	}


(5) Some static routing informations need to be redistributed in BGP Peering. 

	pi@raspberrypi:~/simpleRouter/rest-client $ ./post_redistributeConnect_on.sh 
	======================================================================
	set_redistribute
	======================================================================
	/openflow/0000000000000001/redistribute

	{
	"bgp": {
	"redistribute": "ON",
	"vrf_routeDist": "65011:101"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 87
	header: Date: Sun, 24 Jan 2016 06:35:45 GMT
	----------
	{
	    "bgp": {
	        "vrf_routeDist": "65011:101", 
	        "redistribute": "ON"
	    }, 
	    "id": "0000000000000001"
	}


### STEP4: Confirm Port/BGP Information
You can check various information through RESTful in simpleRouter.  
These scripts are useful for checking some parameters in simpleRouter. 

(1) Checking Port Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_interface.sh 
	======================================================================
	get_interface
	======================================================================
	/openflow/0000000000000001/interface
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 398
	header: Date: Sun, 24 Jan 2016 06:48:20 GMT
	+++++++++++++++++++++++++++++++
	2016/01/24 15:48:20 : PortTable
	+++++++++++++++++++++++++++++++
	portNo   IpAddress       MacAddress        RouteDist
	-------- --------------- ----------------- ---------
	       1 172.16.1.101    00:00:00:11:11:11 
	       2 172.16.2.101    00:00:00:22:22:22 
	       3 192.168.0.1     00:00:00:00:00:01 65011:101


(2) Checking Arp Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_arp.sh 
	======================================================================
	get_arp
	======================================================================
	/openflow/0000000000000001/arp
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 490
	header: Date: Sun, 24 Jan 2016 06:48:36 GMT
	+++++++++++++++++++++++++++++++
	2016/01/24 15:48:36 : ArpTable 
	+++++++++++++++++++++++++++++++
	portNo   MacAddress        IpAddress
	-------- ----------------- ------------
	       1 00:00:00:55:55:55 172.16.1.102
	       2 00:00:00:33:33:33 172.16.2.102
	       3 00:23:81:14:e8:17 192.168.0.2
	       4 00:00:00:11:11:11 172.16.1.101
	       5 00:00:00:22:22:22 172.16.2.101


(3) Checking Routing Table Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_rib.sh 
	======================================================================
	get_rib
	======================================================================
	/openflow/0000000000000001/rib
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 453
	header: Date: Sun, 24 Jan 2016 06:49:00 GMT
	+++++++++++++++++++++++++++++++
	2016/01/24 15:49:00 : Show rib 
	+++++++++++++++++++++++++++++++
	Status codes: * valid, > best
	Origin codes: i - IGP, e - EGP, ? - incomplete
	     Network                          Labels   Next Hop             Reason          Metric LocPrf Path
	 *>  65011:101:192.168.1.2/32         [300]    172.16.1.102         Only Path              100    ?
	 *>  65011:101:192.168.0.2/32         [100]    0.0.0.0              Only Path                     ?


(4) Check BGP Peering UP/DOWN log Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_peer_status.sh 
	======================================================================
	get_peer_status
	======================================================================
	/openflow/0000000000000001/status/peer
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 321
	header: Date: Sun, 24 Jan 2016 06:49:41 GMT
	+++++++++++++++++++++++++++++++
	2016/01/24 15:49:41 : Peer Status
	+++++++++++++++++++++++++++++++
	occurTime            status    myPeer             remotePeer         asNumber
	-------------------- --------- ------------------ ------------------ --------
	2016/01/24 15:34:54  Peer Up   10.0.0.1           10.0.0.3           65011
	2016/01/24 15:34:59  Peer Up   10.0.0.1           10.0.0.2           65011


### STEP5: Confirm Reachability of End-End communication via simpleRouter

	+--------+-+          +---------+           +--------+         +----------+
	| End      |+-------+ | simple  | +-------+ |  BGP   | +------+| End      |
	| station1 |          | Router  |           | Router |         | station2 |
	+----------+          +---------+           +--------+         +----------+
	192.168.0.2                                                    192.168.1.2


Checking End station1 environment.

	$ ip addr
	 ...
	2: p2p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
	    link/ether 00:23:81:14:e8:17 brd ff:ff:ff:ff:ff:ff
	    inet 192.168.0.2/24 brd 192.168.0.255 scope global p2p1
	       valid_lft forever preferred_lft forever
	    inet6 fe80::223:81ff:fe14:e817/64 scope link 
	       valid_lft forever preferred_lft forever

	$ route -n
	Kernel IP routing table
	Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
	0.0.0.0         192.168.0.1     0.0.0.0         UG    0      0        0 p2p1
	192.168.0.0     0.0.0.0         255.255.255.0   U     0      0        0 p2p1
	192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0


Checking Reachability from End Station1 to End Station2 is good as following.

	$ ping 192.168.1.2
	PING 192.168.1.2 (192.168.1.2) 56(84) bytes of data.
	64 bytes from 192.168.1.2: icmp_seq=1 ttl=64 time=4.14 ms
	64 bytes from 192.168.1.2: icmp_seq=2 ttl=64 time=4.00 ms
	64 bytes from 192.168.1.2: icmp_seq=3 ttl=64 time=4.34 ms
	64 bytes from 192.168.1.2: icmp_seq=4 ttl=64 time=5.38 ms
	64 bytes from 192.168.1.2: icmp_seq=5 ttl=64 time=4.45 ms
	^C
	--- 192.168.1.2 ping statistics ---
	5 packets transmitted, 5 received, 0% packet loss, time 4006ms
	rtt min/avg/max/mdev = 4.001/4.466/5.387/0.488 ms

It looks good !!
