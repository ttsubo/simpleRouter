What's simpleRouter for Vpnv4
==========
simpleRouter for Vpnv4 is a software router based Ryu SDN Framework.  
It works as a openflow controller supporting mp-bgp in the LinuxBox. 


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
Get [simpleRouter v0.8](https://github.com/ttsubo/simpleRouter/releases/tag/v0.8) and deploy the code in your LinuxBox. 


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
	$ sudo ovs-vsctl set-fail-mode br0 secure
	$ sudo ovs-vsctl set bridge br0 datapath_type=netdev (*)

	(*) In case of using vpnv4, needs to switch ovs-vswitchd in userspace mode.


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

	$ cd simpleRouter-0.8/ryu-app/
	$ sudo ryu-manager --log-config-file logging.conf openflowRouter.py


(2) Configure BGP Information through RESTful as follows  
    Caution: the dpid is fixed value as "0000000000000001"

	$ curl -s -X POST -d '{"bgp": {"as_number": "65011", "router_id": "10.0.1.3", "label_range_start": "100", "label_range_end": "199"}}' http://localhost:8080/openflow/0000000000000001/bgp | python -mjson.tool

you will catch http response as bellow

	{
	    "bgp": {
	        "as_number": "65011",
	        "label_range_end": "199",
	        "label_range_start": "100",
	        "router_id": "10.0.1.3"
	    },
	    "id": "0000000000000001"
	}


(3) Configure Vrf Information through RESTful as follows  

	$ curl -s -X POST -d '{"vrf": {"route_dist": "65010:101", "import": "65010:101", "export": "65010:101"}}' http://localhost:8080/openflow/0000000000000001/vrf | python -mjson.tool

you will catch http response as bellow

        {
            "id": "0000000000000001", 
            "vrf": {
                "import": "65010:101", 
                "export": "65010:101", 
                "route_dist": "65010:101"
            }
        }


(4) Configure Port Information through RESTful as follows  
    Caution: If you don't want to use as bgp port, you must configure port_offload_bgp as blank""

	$ curl -s -X POST -d '{"interface": {"port": "1", "macaddress": "ee:14:28:ab:49:77", "ipaddress": "192.168.105.102", "netmask": "255.255.255.252", "opposite_ipaddress": "192.168.105.101", "opposite_asnumber": "65011", "port_offload_bgp": "4", "bgp_med": "", "bgp_local_pref": "300", "bgp_filter_asnumber": "65011", "vrf_routeDist": "65010:101"}}' http://localhost:8080/openflow/0000000000000001/interface | python -mjson.tool

you will catch http response as bellow

	{
	    "id": "0000000000000001",
	    "interface": {
	        "bgp_filter_asnumber": "65011",
	        "bgp_local_pref": "300",
	        "bgp_med": "",
	        "ipaddress": "192.168.105.102",
	        "macaddress": "ee:14:28:ab:49:77",
	        "netmask": "255.255.255.252",
	        "opposite_asnumber": "65011",
	        "opposite_ipaddress": "192.168.105.101",
	        "port": "1",
	        "port_offload_bgp": "4",
	        "vrf_routeDist": "65010:101"
	    }
	}


(5) Configure Static Routing Information through RESTful as follows  
    Caution: When "nexthop" isn't available, you will fail to configure it  
    In case of failure, you should check Arp Information as bellow

	$ curl -s -X POST -d '{"route": {"destination": "192.168.200.0", "netmask": "255.255.255.0", "nexthop": "192.168.100.1", "vrf_routeDist": "65010:101"}}' http://localhost:8080/openflow/0000000000000001/route | python -mjson.tool

you will catch http response as bellow

	{
	    "id": "0000000000000001",
	    "route": {
	        "destination": "192.168.200.0",
	        "netmask": "255.255.255.0",
	        "nexthop": "192.168.100.1",
	        "vrf_routeDist": "65010:101"
	    }
	}


(6) Configure "Redistribute connect" Information through RESTful as follows, if you need  

	$ curl -s -X POST -d '{"bgp": {"vrf_routeDist": "65010:101", "redistribute": "ON"}}' http://localhost:8080/openflow/0000000000000001/redistribute | python -mjson.tool

you will catch http response as bellow

	{
	    "bgp": {
	        "redistribute": "ON",
	        "vrf_routeDist": "65010:101"
	    },
	    "id": "0000000000000001"
	}


### STEP4: Confirm Port/BGP Information
You can check various information through RESTful in simpleRouter.  
These scripts are useful for checking simpleRouter as bellow. 

(1) Check Port Information  

	$ cd simpleRouter-0.8/rest-client
	$ ./get_interface.sh 
	======================================================================
	get_interface
	======================================================================
	/openflow/0000000000000001/interface
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 399
	header: Date: Fri, 20 Feb 2015 05:15:19 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:15:19 : PortTable
	+++++++++++++++++++++++++++++++
	portNo   IpAddress       MacAddress        RouteDist
	-------- --------------- ----------------- ---------
	       1 192.168.101.102 4a:6e:0e:de:27:54 
	       2 192.168.104.101 ea:65:4c:20:a0:0f 
	       3 192.168.105.101 fa:f4:2b:84:89:c4 


(2) Check Arp Information  

	$ cd simpleRouter-0.8/rest-client
	$ ./get_arp.sh 
	======================================================================
	get_arp
	======================================================================
	/openflow/0000000000000001/arp
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 506
	header: Date: Fri, 20 Feb 2015 05:13:14 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:13:14 : ArpTable 
	+++++++++++++++++++++++++++++++
	portNo   MacAddress        IpAddress
	-------- ----------------- ------------
	       1 16:3f:1e:5b:32:c6 192.168.101.101
	       2 ce:03:25:69:93:b7 192.168.104.102
	       3 ee:14:28:ab:49:77 192.168.105.102
	       4 4a:6e:0e:de:27:54 192.168.101.102
	       6 fa:f4:2b:84:89:c4 192.168.105.101



(3) Check BGP_rib Table Information  

	$ cd simpleRouter-0.8/rest-client
        $ ./get_rib.sh 
	======================================================================
	get_rib
	======================================================================
	/openflow/0000000000000001/rib
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 459
	header: Date: Fri, 20 Feb 2015 05:00:05 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:00:05 : Show rib 
	+++++++++++++++++++++++++++++++
	Status codes: * valid, > best
	Origin codes: i - IGP, e - EGP, ? - incomplete
	     Network                          Labels   Next Hop             Reason          Metric LocPrf Path
	 *>  65010:101:192.168.201.101/32     [1000]   192.168.101.101      Only Path       100           65010 ?
	 *>  65010:101:192.168.100.1/32       [300]    192.168.105.102      Only Path              100    ?




(4) Check Routing Table Information  

	$ cd simpleRouter-0.8/rest-client
	$ ./get_mpls.sh 
	======================================================================
	get_mpls
	======================================================================
	/openflow/0000000000000001/mpls
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 410
	header: Date: Fri, 20 Feb 2015 05:04:03 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:04:03 : MplsTable 
	+++++++++++++++++++++++++++++++
	routeDist  prefix             nexthop          label
	---------- ------------------ ---------------- -----
	65010:101  192.168.100.1/32   192.168.105.102  300  
	65010:101  192.168.201.101/32 192.168.101.101  1000


(5) Check BGP_neighbor Table Information  

	$ cd simpleRouter-0.8/rest-client
	$ ./get_neighbor.sh 
	======================================================================
	get_neighbor
	======================================================================
	/openflow/0000000000000001/neighbor
	
	{
	"neighbor": {
	"routetype": "received-routes",
	"address": "192.168.101.101"
	}
	}
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 366
	header: Date: Fri, 20 Feb 2015 05:08:45 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:08:45 : Show neighbor 
	+++++++++++++++++++++++++++++++
	Status codes: x filtered
	Origin codes: i - IGP, e - EGP, ? - incomplete
	    Timestamp           Network                          Labels   Next Hop             Metric LocPrf Path
	    2015/02/20 04:58:52 192.168.201.101/32               None     192.168.101.101      100    None   [65010] ?
	


(6) Check BGP Peering UP/DOWN log Information  

	$ cd simpleRouter-0.8/rest-client
	$ ./get_peer_status.sh 
	======================================================================
	get_peer_status
	======================================================================
	/openflow/0000000000000001/status/peer
	----------
	reply: 'HTTP/1.1 200 OK\r\n'
	header: Content-Type: application/json; charset=UTF-8
	header: Content-Length: 1209
	header: Date: Fri, 20 Feb 2015 05:11:03 GMT
	+++++++++++++++++++++++++++++++
	2015/02/20 14:11:02 : Peer Status
	+++++++++++++++++++++++++++++++
	occurTime            status    myPeer             remotePeer         asNumber
	-------------------- --------- ------------------ ------------------ --------
	2015/02/20 13:58:21  Peer Up   10.0.1.1           10.0.0.1           65010
	2015/02/20 13:58:26  Peer Up   10.0.1.1           10.0.1.2           65011
	2015/02/20 13:58:31  Peer Up   10.0.1.1           10.0.1.3           65011
	2015/02/20 13:58:36  Peer Down 10.0.1.1           10.0.0.1           65010
	2015/02/20 13:58:36  Peer Down 10.0.1.1           10.0.1.2           65011
	2015/02/20 13:58:36  Peer Down 10.0.1.1           10.0.1.3           65011
	2015/02/20 13:58:50  Peer Up   10.0.1.1           10.0.1.3           65011
	2015/02/20 13:58:52  Peer Up   10.0.1.1           10.0.0.1           65010
	2015/02/20 13:58:57  Peer Up   10.0.1.1           10.0.1.2           65011



### STEP5: starting BMP(BGP Monitoring Protocol)
You can start BMP client/server.  

(1) Configure BMP Information through RESTful as follows  
    Caution: the dpid is fixed value as "0000000000000001"

	$ curl -s -X POST -d '{"bmp": {"port": "11019", "address": "192.168.183.219"}}' http://localhost:8080/openflow/0000000000000001/bmp | python -mjson.tool

you will catch http response as bellow

        {
            "bmp": {
                "port": "11019", 
                "address": "192.168.183.219"
            }, 
            "id": "0000000000000001"
        }

(2) Starting BMP Server 

	$ cd simpleRouter/other/
	$ python sample_bmpServer.py 
	Start BMP session!! [192.168.183.218]
	192.168.183.218 | 2015/02/20 14:37:38 65011 10.0.1.3 | BGP_PeerUp
	192.168.183.218 | 2015/02/20 14:37:38 65011 10.0.1.3 | BGP_Update(add_prefix:65010:101:192.168.200.0/24, nexthop:192.168.105.102)
	192.168.183.218 | 2015/02/20 14:37:38 65011 10.0.1.3 | BGP_Update(add_prefix:65010:101:192.168.100.1/32, nexthop:192.168.105.102)
	192.168.183.218 | 2015/02/20 14:37:25 65011 10.0.1.2 | BGP_PeerUp
	192.168.183.218 | 2015/02/20 14:37:20 65010 10.0.0.1 | BGP_PeerUp
	192.168.183.218 | 2015/02/20 14:37:33 65010 10.0.0.1 | BGP_Update(add_prefix:65010:101:192.168.201.101/32, nexthop:192.168.101.101)
	192.168.183.218 | 2015/02/20 14:38:24 65011 10.0.1.3 | BGP_Update(del_prefix:65010:101:192.168.100.1/32)
	192.168.183.218 | ------------------- 65011 10.0.1.3 | BGP_PeerDown
	192.168.183.218 | 2015/02/20 14:39:01 65011 10.0.1.3 | BGP_PeerUp
	192.168.183.218 | 2015/02/20 14:39:16 65011 10.0.1.3 | BGP_Update(add_prefix:65010:101:192.168.100.1/32, nexthop:192.168.105.102)



