What's simpleRouter for Raspberry Pi
==========
The simpleRouter is a software BGP router based Ryu SDN Framework.  
It works as a OpenFlow equipment supporting Vpnv4(mp-bgp) under Raspberry Pi. 


Installation
===========
### Raspberry Pi environment
It recommends for using "the Raspberry Pi 2 Model B" which have Multi USB Ports.
I've already confirmed that "Raspberry Pi Model B" works properly as following.

(1) Checking Raspberry pi edition

	pi@raspberrypi:~ $ cat /proc/cpuinfo
	processor	: 0
	model name	: ARMv6-compatible processor rev 7 (v6l)
	BogoMIPS	: 2.00
	Features	: half thumb fastmult vfp edsp java tls 
	CPU implementer	: 0x41
	CPU architecture: 7
	CPU variant	: 0x0
	CPU part	: 0xb76
	CPU revision	: 7

	Hardware	: BCM2708
	Revision	: 000e
	Serial		: 000000004ef7fbdf


(2) Checking Raspbian version

	pi@raspberrypi:~ $ uname -a
	Linux raspberrypi 4.1.13+ #826 PREEMPT Fri Nov 13 20:13:22 GMT 2015 armv6l GNU/Linux


### Ryu Controller installation

(1) Installing langage-pack-ja

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

(1) Installing Ryu Controller  

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
	   Active: active (running) since Sun 2016-01-17 08:29:31 JST; 5min ago
	   CGroup: /system.slice/openvswitch-switch.service
	           ├─22071 ovsdb-server: monitoring pid 22072 (healthy)
	           ├─22072 ovsdb-server /etc/openvswitch/conf.db -vconsole:emer -vsyslog:err -vfile...
	           ├─22081 ovs-vswitchd: monitoring pid 22082 (healthy)
	           └─22082 ovs-vswitchd unix:/var/run/openvswitch/db.sock -vconsole:emer -vsyslog:e...


Quick Start
===========
### STEP1: Basic networking configuration
You need to assign physical ports as following.
- eth0 : Management Port (use of maintenance)
- eth1 : OpenFlow Port
- eth2 : OpenFlow Port

(1) Configure the basic networking in Raspbian environment

	pi@raspberrypi:~ $ sudo vi /etc/network/interfaces
	---------
	auto lo
	iface lo inet loopback

	#iface eth0 inet manual
	auto eth0
	iface eth0 inet static
	address 192.168.100.102
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
	

	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart
	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart


(2) Configure the basic OpenvSwitch networking

	pi@raspberrypi:~ $ sudo ovs-vsctl add-br br0
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 eth1
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 eth2
	pi@raspberrypi:~ $ sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6633
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000001
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 protocols=OpenFlow13
	pi@raspberrypi:~ $ sudo ovs-vsctl set-fail-mode br0 secure
	pi@raspberrypi:~ $ sudo ovs-vsctl set bridge br0 datapath_type=netdev (*)

	(*) In case of using vpnv4, needs to switch ovs-vswitchd in userspace mode.


(3) Checking OpenFlow ports

	pi@raspberrypi:~ $ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	OFPST_PORT_DESC reply (OF1.3) (xid=0x2):
	 1(eth1): addr:34:95:db:0f:66:c1
	     config:     0
	     state:      0
	     current:    100MB-FD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 100 Mbps now, 100 Mbps max
	 2(eth2): addr:34:95:db:2a:8b:66
	     config:     0
	     state:      0
	     current:    100MB-FD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 100 Mbps now, 100 Mbps max
	 LOCAL(br0): addr:34:95:db:0f:66:c1
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max


### STEP2: Additional networking configuration
You need to assign internal ports as following.
- bgpPort1 : Internal Port
- bgpPort2 : Internal Port

(1) Configure the logical port in OpenvSwitch environment

	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 bgpPort1 -- set Interface bgpPort1 type=internal
	pi@raspberrypi:~ $ sudo ovs-vsctl add-port br0 bgpPort2 -- set Interface bgpPort2 type=internal


(2) Checking OpenFlow ports for new logical port

	pi@raspberrypi:~ $ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	 ....
	 3(bgpPort1): addr:42:2f:a2:7d:50:64
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 4(bgpPort2): addr:9a:3a:b3:47:02:73
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 LOCAL(br0): addr:34:95:db:0f:66:c1
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max


(3) Configure the additional networking in Raspbian environment

	pi@raspberrypi:~ $ sudo vi /etc/network/interfaces
	————
	 ....
	auto bgpPort1
	iface bgpPort1 inet static
	address 172.16.1.101
	netmask 255.255.255.252
	hwaddress ether 00:00:00:11:11:11

	auto bgpPort2
	iface bgpPort2 inet static
	address 172.16.2.101
	netmask 255.255.255.252
	hwaddress ether 00:00:00:22:22:22

	
	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart
	pi@raspberrypi:~ $ sudo /etc/init.d/networking restart


(4) Checking OpenFlow ports again

	pi@raspberrypi:~ $ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	OFPST_PORT_DESC reply (OF1.3) (xid=0x2):
	 1(eth1): addr:34:95:db:0f:66:c1
	     config:     0
	     state:      0
	     current:    100MB-FD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 100 Mbps now, 100 Mbps max
	 2(eth2): addr:34:95:db:2a:8b:66
	     config:     0
	     state:      0
	     current:    100MB-FD AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG AUTO_PAUSE
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD COPPER AUTO_NEG
	     speed: 100 Mbps now, 100 Mbps max
	 3(bgpPort1): addr:00:00:00:11:11:11
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 4(bgpPort2): addr:00:00:00:22:22:22
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max
	 LOCAL(br0): addr:34:95:db:0f:66:c1
	     config:     0
	     state:      0
	     current:    10MB-FD COPPER
	     speed: 10 Mbps now, 0 Mbps max


### STEP3: Starting simpleRouter

	             +---------+  mp-BGP          +--------+
	... -------+ | simple  | +--------------+ |  BGP   | +---- ...
	      (eth2) | Router  | (eth1)           | Router |
	             +---------+                  +--------+
	< AS65011 >  172.16.1.101                172.16.1.102  < AS65011 >

	<-- Target in simpleRouter ---->   <---- out of scope ---->


### STEP4: Applying various information for simpleRouter
You can check various information through RESTful in simpleRouter.  
These scripts are useful for applying some parameters to simpleRouter. 

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
	port_offload_bgp = "3"
	bgp_med = ""
	bgp_local_pref = "300"
	bgp_filter_asnumber = "65011"
	vrf_routeDist = ""

	[Port2]
	port = "2"
	macaddress = "00:00:00:00:00:01"
	ipaddress = "192.168.1.101"
	netmask = "255.255.255.0"
	opposite_ipaddress = "192.168.1.102"
	opposite_asnumber = ""
	port_offload_bgp = ""
	bgp_med = ""
	bgp_local_pref = ""
	bgp_filter_asnumber = ""
	vrf_routeDist = "65011:101"

	[Neighbor]
	routetype = "received-routes"
	address = "172.16.1.102"


(2) You can Start simpleRouter.

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


(3) You need to apply some parameters of [Bgp] section in OpenFLow.ini. 

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
	header: Date: Sun, 17 Jan 2016 06:16:18 GMT
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


(4) You need to apply some parameters of [Port..] section in OpenFLow.ini. 

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
	"port_offload_bgp": "3",
	"bgp_med": "",
	"bgp_local_pref": "300",
	"bgp_filter_asnumber": "65011",
	"vrf_routeDist": ""
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 334
	header: Date: Sun, 17 Jan 2016 06:16:28 GMT
	----------
	{
	    "interface": {
	        "port_offload_bgp": "3", 
	        "bgp_local_pref": "300", 
	        "opposite_asnumber": "65011", 
	        "macaddress": "00:00:00:11:11:11", 
	        "bgp_med": "", 
	        "netmask": "255.255.255.252", 
	        "opposite_ipaddress": "172.16.1.102", 
	        "vrf_routeDist": "", 
	        "bgp_filter_asnumber": "65011", 
	        "ipaddress": "172.16.1.101", 
	        "port": "1"
	    }, 
	    "id": "0000000000000001"
	}

	======================================================================
	create_interface
	======================================================================
	/openflow/0000000000000001/interface

	{
	"interface": {
	"port": "2",
	"macaddress": "00:00:00:00:00:01",
	"ipaddress": "192.168.1.101",
	"netmask": "255.255.255.0",
	"opposite_ipaddress": "192.168.1.102",
	"opposite_asnumber": "",
	"port_offload_bgp": "",
	"bgp_med": "",
	"bgp_local_pref": "",
	"bgp_filter_asnumber": "",
	"vrf_routeDist": "65011:101"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 329
	header: Date: Sun, 17 Jan 2016 06:16:33 GMT
	----------
	{
	    "interface": {
	        "port_offload_bgp": "", 
	        "bgp_local_pref": "", 
	        "opposite_asnumber": "", 
	        "macaddress": "00:00:00:00:00:01", 
	        "bgp_med": "", 
	        "netmask": "255.255.255.0", 
	        "opposite_ipaddress": "192.168.1.102", 
	        "vrf_routeDist": "65011:101", 
	        "bgp_filter_asnumber": "", 
	        "ipaddress": "192.168.1.101", 
	        "port": "2"
	    }, 
	    "id": "0000000000000001"
	}


(5) You need to apply some parameters of [Vrf] section in OpenFLow.ini. 

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
	header: Date: Sun, 17 Jan 2016 06:16:39 GMT
	----------
	{
	    "id": "0000000000000001", 
	    "vrf": {
	        "import": "65011:101", 
	        "export": "65011:101", 
	        "route_dist": "65011:101"
	    }
	}

(6) Some static routing informations need to be redistributed in BGP Peering. 

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
	header: Date: Sun, 17 Jan 2016 06:16:47 GMT
	----------
	{
	    "bgp": {
	        "vrf_routeDist": "65011:101", 
	        "redistribute": "ON"
	    }, 
	    "id": "0000000000000001"
	}


### STEP5: Confirm Port/BGP Information
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
	header: Content-Length: 294
	header: Date: Sun, 17 Jan 2016 06:48:35 GMT
	+++++++++++++++++++++++++++++++
	2016/01/17 15:48:35 : PortTable
	+++++++++++++++++++++++++++++++
	portNo   IpAddress       MacAddress        RouteDist
	-------- --------------- ----------------- ---------
	       1 172.16.1.101    00:00:00:11:11:11 
	       2 192.168.1.101   00:00:00:00:00:01 65011:101


(2) Checking Arp Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_arp.sh 
	======================================================================
	get_arp
	======================================================================
	/openflow/0000000000000001/arp
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 322
	header: Date: Sun, 17 Jan 2016 06:49:52 GMT
	+++++++++++++++++++++++++++++++
	2016/01/17 15:49:52 : ArpTable 
	+++++++++++++++++++++++++++++++
	portNo   MacAddress        IpAddress
	-------- ----------------- ------------
	       1 00:00:00:01:01:01 172.16.1.102
	       2 00:23:81:14:e8:17 192.168.1.102
	       3 00:00:00:11:11:11 172.16.1.101



(3) Checking adh_rib_in of receiving BGP_update messages from BGP Peering.

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_neighbor.sh 
	======================================================================
	get_neighbor
	======================================================================
	/openflow/0000000000000001/neighbor

	{
	"neighbor": {
	"routetype": "received-routes",
	"address": "172.16.1.102"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 1398
	header: Date: Sun, 17 Jan 2016 06:51:19 GMT
	+++++++++++++++++++++++++++++++
	2016/01/17 15:51:19 : Show neighbor 
	+++++++++++++++++++++++++++++++
	Status codes: x filtered
	Origin codes: i - IGP, e - EGP, ? - incomplete
	    Timestamp           Network                          Labels   Next Hop             Metric LocPrf Path
	    2016/01/17 06:16:39 110.1.0.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.5.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.6.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.3.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.4.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.9.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.7.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.1.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:39 110.1.2.0/24                     None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:40 10.1.0.2/32                      None     172.16.1.102         100    100    ?
	    2016/01/17 06:16:40 110.1.8.0/24                     None     172.16.1.102         100    100    ?



(4) Checking Routing Table Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_rib.sh 
	======================================================================
	get_rib
	======================================================================
	/openflow/0000000000000001/rib
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 1463
	header: Date: Sun, 17 Jan 2016 06:55:47 GMT
	+++++++++++++++++++++++++++++++
	2016/01/17 15:55:47 : Show rib 
	+++++++++++++++++++++++++++++++
	Status codes: * valid, > best
	Origin codes: i - IGP, e - EGP, ? - incomplete
	     Network                          Labels   Next Hop             Reason          Metric LocPrf Path
	 *>  65011:101:110.1.1.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.7.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.2.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:10.1.0.2/32            [1000]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.8.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:192.168.1.102/32       [100]    0.0.0.0              Only Path                     ?
	 *>  65011:101:110.1.0.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.6.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.5.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.9.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.4.0/24           [1001]   172.16.1.102         Only Path       100    100    ?
	 *>  65011:101:110.1.3.0/24           [1001]   172.16.1.102         Only Path       100    100    ?


(5) Check BGP Peering UP/DOWN log Information  

	pi@raspberrypi:~/simpleRouter/rest-client $ ./get_peer_status.sh 
	======================================================================
	get_peer_status
	======================================================================
	/openflow/0000000000000001/status/peer
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 197
	header: Date: Sun, 17 Jan 2016 06:58:14 GMT
	+++++++++++++++++++++++++++++++
	2016/01/17 15:58:14 : Peer Status
	+++++++++++++++++++++++++++++++
	occurTime            status    myPeer             remotePeer         asNumber
	-------------------- --------- ------------------ ------------------ --------
	2016/01/17 15:16:29  Peer Up   10.0.0.1           10.10.10.2         65011


### STEP6: Confirm Reachability of End-End communication via simpleRouter

	+--------+-+          +---------+           +--------+         +----------+
	| End      |+-------+ | simple  | +-------+ |  BGP   | +------+| End      |
	| station1 |          | Router  |           | Router |         | station2 |
	+----------+          +---------+           +--------+         +----------+
	192.168.1.102                                                  110.1.0.1


Checking End station1 environment.

	$ ip addr
	 ...
	2: p2p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 00:23:81:14:e8:17 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.102/24 brd 192.168.1.255 scope global p2p1
       valid_lft forever preferred_lft forever
    inet6 fe80::223:81ff:fe14:e817/64 scope link 
       valid_lft forever preferred_lft forever

	$ route -n
	Kernel IP routing table
	Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
	110.1.0.0       192.168.1.101   255.255.255.0   UG    0      0        0 p2p1
	192.168.1.0     0.0.0.0         255.255.255.0   U     0      0        0 p2p1
	192.168.100.0   0.0.0.0         255.255.255.0   U     9      0        0 wlan0
	192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0


Ping result from End Station1 to End Station2 is good as following.

	$ ping 110.1.0.1
	PING 110.1.0.1 (110.1.0.1) 56(84) bytes of data.
	64 bytes from 110.1.0.1: icmp_seq=1 ttl=64 time=5.04 ms
	64 bytes from 110.1.0.1: icmp_seq=2 ttl=64 time=4.27 ms
	64 bytes from 110.1.0.1: icmp_seq=3 ttl=64 time=4.27 ms
	64 bytes from 110.1.0.1: icmp_seq=4 ttl=64 time=3.93 ms
	64 bytes from 110.1.0.1: icmp_seq=5 ttl=64 time=4.06 ms
	^C
	--- 110.1.0.1 ping statistics ---
	5 packets transmitted, 5 received, 0% packet loss, time 4005ms
	rtt min/avg/max/mdev = 3.930/4.316/5.042/0.391 ms

