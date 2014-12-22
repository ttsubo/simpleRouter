What's simpleRouter
==========
simpleRouter is a software router based Ryu SDN Framework.  
It works as a openflow controller supporting bgp in the LinuxBox. 


Installation
===========
### LinuxBox environment
It recommends for using the LinuxBox which have multiple NICs.
For example:
[DNA 940](http://nexcom.co.uk/Products/network-and-communication-solutions/desktop-appliance/desktop-appliance/communication-gateway-dna-940/Specifications) is a desktop communication gateway platform by NEXCOM.
- Intel® Celeron® M 600MHz Processor
- Supports one DDR2 400/533 Memory, up to 2GB
- 4 x GbE LAN ports

(1) Check LinuxOS version

	$ cat /etc/lsb-release
	DISTRIB_ID=Ubuntu
	DISTRIB_RELEASE=12.04
	DISTRIB_CODENAME=precise
	DISTRIB_DESCRIPTION="Ubuntu 12.04.4 LTS"


(2) Check Ubuntu version

	$ uname -a
	Linux OVS1 3.2.0-60-generic #91-Ubuntu SMP Wed Feb 19 03:55:18 UTC 2014 i686 i686 i386 GNU/Linux


### Ryu Controller installation

(1) Install langage-pack-ja

	$ sudo apt-get update
	$ sudo apt-get install language-pack-ja


(2) Install Ryu Controller  
    Caution: you should install the latest code from master branch

	$ sudo apt-get install python-dev
	$ sudo apt-get install python-pip
	$ sudo apt-get -y install libxml2-dev
	$ sudo apt-get -y install python-lxml
	$ sudo pip install --upgrade six
	$ git clone https://github.com/osrg/ryu.git
	$ cd ryu/tools/
	$ sudo pip install -r pip-requires
	$ cd ..
	$ sudo python ./setup.py install
	$ cd


(3) Check Ryu version

	$ ryu-manager --version
	3.16


### Get the simpleRouter code from github
Get [simpleRouter v0.3](https://github.com/ttsubo/simpleRouter/releases/tag/v0.3) and deploy the code in your LinuxBox. 


### OpenvSwitch installation
(1) Install packages

	$ sudo apt-get install -y linux-source kernel-package
	$ sudo apt-get install -y debhelper devscripts autoconf automake
	$ sudo apt-get install -y libtool libssl-dev dkms


(2) Get OpenvSwitch and deploy the code in your LinuxBox

	$ wget http://openvswitch.org/releases/openvswitch-2.3.1.tar.gz
	$ tar zxvf openvswitch-2.3.1.tar.gz
	$ cd openvswitch-2.3.1
	$ sudo apt-get install build-essential fakeroot
	$ sudo apt-get install graphviz
	$ dpkg-checkbuilddeps
	$ fakeroot debian/rules binary
	 ....


(3) Check binary files

	$ cd
	$ ls -l
	 ....
	 openvswitch-common_2.3.1-1_i386.deb
	 openvswitch-switch_2.3.1-1_i386.deb
	 openvswitch-datapath-dkms_2.3.1-1_all.deb


(4) Install OpenvSwitch packages

	$ sudo dpkg -i openvswitch-common_2.3.1-1_i386.deb
	$ sudo dpkg -i openvswitch-switch_2.3.1-1_i386.deb
	$ sudo dpkg -i openvswitch-datapath-dkms_2.3.1-1_all.deb


(5) Check the kernel modules

	$ lsmod | grep openvswitch
	openvswitch            75156  0 
	gre                    12853  1 openvswitch
	libcrc32c              12543  1 openvswitch


(6) Start OpenvSwitch

	$ sudo service openvswitch-switch start
	 * ovsdb-server is already running
	 * ovs-vswitchd is already running
	 * Enabling remote OVSDB managers


(7) Check OpenvSwitch version

	$ sudo ovs-vsctl --version
	ovs-vsctl (Open vSwitch) 2.3.1
	Compiled Dec 21 2014 10:20:49
	DB Schema 7.6.2


Quick Start
===========
### STEP1: Basic networking configuration
You should assign physical ports as following.
- eth0 : Management Port (use of maintenance)
- eth1 : OpenFlow Port
- eth2 : OpenFlow Port
- eth3 : OpenFlow Port

(1) Configure the basic networking in Linux environment

	$ sudo vi /etc/network/interfaces
	————
	auto lo
	iface lo inet loopback

	auto eth0
	iface eth0 inet static
	address 192.168.0.101
	netmask 255.255.255.0

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
	————
	
	$ sudo reboot
	 ....


(2) Configure the basic OpenvSwitch networking

	$ sudo ovs-vsctl add-br br0
	$ sudo ovs-vsctl add-port br0 eth1
	$ sudo ovs-vsctl add-port br0 eth2
	$ sudo ovs-vsctl add-port br0 eth3
	$ sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6633
	$ sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000001
	$ sudo ovs-vsctl set bridge br0 protocols=OpenFlow13


(3) Check OpenFlow ports

	$ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	OFPST_PORT_DESC reply (OF1.3) (xid=0x2):
	 1(eth1): addr:00:10:f3:1d:3d:1d
	     config:     0
	     state:      LINK_DOWN
	     current:    COPPER AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     speed: 0 Mbps now, 1000 Mbps max
	 2(eth2): addr:00:10:f3:1d:3d:1e
	     config:     0
	     state:      LINK_DOWN
	     current:    COPPER AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     speed: 0 Mbps now, 1000 Mbps max
	 3(eth3): addr:00:10:f3:1d:3d:1f
	     config:     0
	     state:      LINK_DOWN
	     current:    COPPER AUTO_NEG
	     advertised: 10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     supported:  10MB-HD 10MB-FD 100MB-HD 100MB-FD 1GB-FD COPPER AUTO_NEG
	     speed: 0 Mbps now, 1000 Mbps max
	 LOCAL(br0): addr:00:10:f3:1d:3d:1d
	     config:     PORT_DOWN
	     state:      LINK_DOWN
	     speed: 0 Mbps now, 0 Mbps max


### STEP2: Additional networking configuration
You should assign internal ports as following.
- bgpPort1 : Internal Port
- bgpPort2 : Internal Port
- bgpPort3 : Internal Port

(1) Configure the logical port in OpenvSwitch environment

	$ sudo ovs-vsctl add-port br0 bgpPort1 -- set Interface bgpPort1 type=internal
	$ sudo ovs-vsctl add-port br0 bgpPort2 -- set Interface bgpPort2 type=internal
	$ sudo ovs-vsctl add-port br0 bgpPort3 -- set Interface bgpPort3 type=internal


(2) Check OpenFlow ports

	$ sudo ovs-ofctl dump-ports-desc br0 --protocol=OpenFlow13
	 ....
	 4(bgpPort1): addr:e6:56:ea:af:3e:e8
	     config:     PORT_DOWN
	     state:      LINK_DOWN
	     speed: 0 Mbps now, 0 Mbps max
	 5(bgpPort2): addr:b6:7a:b7:0d:a8:c4
	     config:     PORT_DOWN
	     state:      LINK_DOWN
	     speed: 0 Mbps now, 0 Mbps max
	 6(bgpPort3): addr:ea:e8:50:7a:6b:47
	     config:     PORT_DOWN
	     state:      LINK_DOWN
	     speed: 0 Mbps now, 0 Mbps max
	 LOCAL(br0): addr:00:10:f3:1d:3d:1d
	     config:     PORT_DOWN
	     state:      LINK_DOWN
	     speed: 0 Mbps now, 0 Mbps max


(3) Configure the additional networking in Linux environment

	$ sudo vi /etc/network/interfaces
	————
	 ....
	auto bgpPort1
	iface bgpPort1 inet static
	address 192.168.201.101
	netmask 255.255.255.0
	hwaddress ether e6:56:ea:af:3e:e8

	auto bgpPort2
	iface bgpPort2 inet static
	address 172.16.201.101
	netmask 255.255.255.0
	hwaddress ether b6:7a:b7:0d:a8:c4

	auto bgpPort3
	iface bgpPort3 inet static
	address 172.16.203.1
	netmask 255.255.255.0
	hwaddress ether ea:e8:50:7a:6b:47
	————
	
	$ sudo reboot


### STEP3: Starting simpleRouter
(1) You can Start simpleRouter.

	$ cd simpleRouter-0.3/ryu-app/
	$ sudo ryu-manager openflowRouter.py


(2) Configure BGP Information through RESTful as follows  
    Caution: the dpid is fixed value as "0000000000000001"

	$ curl -s -X POST -d '{"bgp": {"as_number": "65002", "router_id": "10.0.1.1"}}' http://localhost:8080/openflow/0000000000000001/bgp | python -mjson.tool

you will catch http response as bellow

	{
	    "bgp": {
	        "as_number": "65002", 
	        "router_id": "10.0.1.1"
	    }, 
	    "id": "0000000000000001"
	}


(3) Configure Port Information through RESTful as follows  
    Caution: If you don't want to use as bgp port, you must configure port_offload_bgp as blank""

	$ curl -s -X POST -d '{"interface": {"port": "1", "macaddress": "e6:56:ea:af:3e:e8", "ipaddress": "192.168.201.101", "netmask": "255.255.255.0", "opposite_ipaddress": "192.168.201.1", "opposite_asnumber": "65001", "port_offload_bgp": "4", "bgp_med": "100", "bgp_local_pref": "", "bgp_filter_asnumber": ""}}' http://localhost:8080/openflow/0000000000000001/interface | python -mjson.tool

you will catch http response as bellow

	{
	    "id": "0000000000000001", 
	    "interface": {
	        "bgp_filter_asnumber": "", 
	        "bgp_local_pref": "", 
	        "bgp_med": "100", 
	        "ipaddress": "192.168.201.101", 
	        "macaddress": "e6:56:ea:af:3e:e8", 
	        "netmask": "255.255.255.0", 
	        "opposite_asnumber": "65001", 
	        "opposite_ipaddress": "192.168.201.1", 
	        "port": "1", 
	        "port_offload_bgp": "4"
	    }
	}

(4) Configure Static Routing Information through RESTful as follows  
    Caution: When "nexthop" isn't available, you will fail to configure it  
    In case of failure, you should check Arp Information as bellow

	$ curl -s -X POST -d '{"route": {"destination": "192.168.102.0", "netmask": "255.255.255.0", "nexthop": "172.16.201.1"}}' http://localhost:8080/openflow/0000000000000001/route | python -mjson.tool

you will catch http response as bellow

	{
	    "id": "0000000000000001", 
	    "route": {
	        "destination": "192.168.102.0", 
	        "netmask": "255.255.255.0", 
	        "nexthop": "172.16.201.1"
	    }
	}


(5) Configure "Redistribute connect" Information through RESTful as follows, if you need  

	$ curl -s -X POST -d '{"bgp": {"redistribute": "ON"}}' http://localhost:8080/openflow/0000000000000001/redistribute | python -mjson.tool

you will catch http response as bellow

	{
	    "bgp": {
	        "redistribute": "ON"
	    }, 
	    "id": "0000000000000001"
	}


### STEP4: Confirm Port/BGP Information
You can check various information through RESTful in simpleRouter.  
These scripts are useful for checking simpleRouter as bellow. 

(1) Check Port Information  

	$ cd simpleRouter-0.3/rest-client
	$ ./get_interface.sh 
	======================================================================
	get_interface
	======================================================================
	/openflow/0000000000000001/interface
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 344
	header: Date: Tue, 23 Dec 2014 07:13:59 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:13:59 : PortTable
	+++++++++++++++++++++++++++++++
	portNo   IpAddress       MacAddress
	-------- --------------- -----------------
	       1 192.168.201.101 e6:56:ea:af:3e:e8
	       2 172.16.201.101  b6:7a:b7:0d:a8:c4
	       3 172.16.203.1    ea:e8:50:7a:6b:47


(2) Check Arp Information  

	$ cd simpleRouter-0.3/rest-client
	$ $ ./get_arp.sh 
	======================================================================
	get_arp
	======================================================================
	/openflow/0000000000000001/arp
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 409
	header: Date: Tue, 23 Dec 2014 07:15:49 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:15:49 : ArpTable 
	+++++++++++++++++++++++++++++++
	portNo   MacAddress        IpAddress
	-------- ----------------- ------------
	       1 96:56:69:f9:6d:b5 192.168.201.1
	       2 ba:cb:1e:6f:04:70 172.16.201.1
	       3 2e:b3:e5:63:6d:c3 172.16.203.101
	       6 ea:e8:50:7a:6b:47 172.16.203.1


(3) Check BGP_Rib Table Information  

	$ cd simpleRouter-0.3/rest-client
	$ ./get_rib.sh 
	======================================================================
	get_rib
	======================================================================
	/openflow/0000000000000001/rib
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 1529
	header: Date: Tue, 23 Dec 2014 07:18:37 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:18:37 : Show rib 
	+++++++++++++++++++++++++++++++
	Status codes: * valid, > best
	Origin codes: i - IGP, e - EGP, ? - incomplete
	     Network                          Labels   Next Hop             Reason          Metric LocPrf Path
	 *>  0.0.0.0/0                        None     192.168.201.1        Only Path       100           65001 ?
	 *>  192.168.100.0/24                 None     192.168.201.1        Only Path       100           65001 ?
	 *>  192.168.0.0/24                   None     192.168.201.1        Only Path       100           65001 ?
	 *>  172.16.101.0/24                  None     192.168.201.1        Only Path       100           65001 ?
	 *>  192.168.201.0/24                 None     192.168.201.1        Only Path       100           65001 ?
	 *>  10.0.0.1/32                      None     192.168.201.1        Only Path       100           65001 ?
	 *>  172.16.102.0/24                  None     192.168.201.1        Only Path       100           65001 ?
	 *>  10.0.0.2/32                      None     192.168.201.1        Only Path       100           65001 ?
	 *>  172.16.104.0/24                  None     192.168.201.1        Only Path       100           65001 ?
	 *>  172.16.103.0/24                  None     192.168.201.1        Only Path       100           65001 ?
	 *>  192.168.202.0/24                 None     192.168.201.1        Only Path       100           65001 ?
	 *>  192.168.102.0/24                 None     172.16.201.1         Only Path                     i


(4) Check Routing Information  

	$ cd simpleRouter-0.3/rest-client
	$ ./get_route.sh 
	======================================================================
	get_route
	======================================================================
	/openflow/0000000000000001/route
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 1520
	header: Date: Tue, 23 Dec 2014 07:20:54 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:20:54 : RoutingTable 
	+++++++++++++++++++++++++++++++
	prefix             nexthop
	------------------ ----------------
	0.0.0.0/0          192.168.201.1  
	10.0.0.1/32        192.168.201.1  
	10.0.0.2/32        192.168.201.1  
	172.16.101.0/24    192.168.201.1  
	172.16.102.0/24    192.168.201.1  
	172.16.103.0/24    192.168.201.1  
	172.16.104.0/24    192.168.201.1  
	192.168.0.0/24     192.168.201.1  
	192.168.100.0/24   192.168.201.1  
	192.168.102.0/24   172.16.201.1   
	192.168.201.0/24   192.168.201.1  
	192.168.202.0/24   192.168.201.1 


(5) Check FlowStats Information  

	$ cd simpleRouter-0.3/rest-client
	$ ./get_flow_stats.sh 
	======================================================================
	get_flowstats
	======================================================================
	/openflow/0000000000000001/stats/flow
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 803
	header: Date: Tue, 23 Dec 2014 07:23:02 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:23:02 : FlowStats
	+++++++++++++++++++++++++++++++
	destination        packets    bytes
	------------------ ---------- ----------
	0.0.0.0/0                   0          0
	10.0.0.1                    0          0
	10.0.0.2                    0          0
	172.16.101.0/24             0          0
	172.16.102.0/24             0          0
	172.16.103.0/24             0          0
	172.16.104.0/24             0          0
	192.168.0.0/24              0          0
	192.168.100.0/24            0          0
	192.168.102.0/24            0          0
	192.168.201.0/24            0          0
	192.168.201.1               0          0
	192.168.202.0/24            0          0


(6) Check BGP Peering UP/DOWN log Information  

	$ cd simpleRouter-0.3/rest-client
	$ ./get_peer_status.sh 
	======================================================================
	get_peer_status
	======================================================================
	/openflow/0000000000000001/status/peer
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 701
	header: Date: Tue, 23 Dec 2014 07:30:02 GMT
	+++++++++++++++++++++++++++++++
	2014/12/23 16:30:02 : Peer Status
	+++++++++++++++++++++++++++++++
	occurTime            status    myPeer             remotePeer         asNumber
	-------------------- --------- ------------------ ------------------ --------
	2014/12/23 15:39:13  Peer Up   10.0.1.1           10.0.0.1           65001
	2014/12/23 15:39:18  Peer Up   10.0.1.1           10.0.1.3           65002
	2014/12/23 15:41:51  Peer Up   10.0.1.1           10.0.1.2           65002
	2014/12/23 16:29:17  Peer Down 10.0.1.1           10.0.0.1           65001
	2014/12/23 16:30:00  Peer Up   10.0.1.1           10.0.0.1           65001

