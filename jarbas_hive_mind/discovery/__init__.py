import upnpclient
import threading
from time import sleep
from ovos_utils.log import LOG
from ovos_utils.xml_helper import xml2dict
from jarbas_hive_mind.slave import HiveMindSlave
from jarbas_hive_mind.slave.terminal import HiveMindTerminal
from jarbas_hive_mind.discovery.zero import ZeroScanner
import requests


class _Device:
    def __init__(self, host, device_type='HiveMind-websocket'):
        self.host = host
        self.device_type = device_type

    @property
    def services(self):
        return {}

    @property
    def location(self):
        return None

    @property
    def device_name(self):
        return self.host

    @property
    def friendly_name(self):
        return self.device_name

    @property
    def model_description(self):
        return self.device_name

    @property
    def model_name(self):
        return self.device_type

    @property
    def model_number(self):
        return "0.1"

    @property
    def udn(self):
        return self.model_name + ":" + self.model_number

    @property
    def address(self):
        return self.location

    @property
    def data(self):
        return {"host": self.host,
                "type": self.device_type}


class HiveMindNode:
    def __init__(self, d=None):
        self.device = d
        self._data = None

    @property
    def services(self):
        return self.device.service_map

    @property
    def xml(self):
        return self.device.location

    @property
    def device_name(self):
        return self.device.device_name

    @property
    def friendly_name(self):
        return self.device.friendly_name

    @property
    def description(self):
        return self.device.model_description

    @property
    def node_tyoe(self):
        return self.device.model_name

    @property
    def version(self):
        return self.device.model_number

    @property
    def device_id(self):
        return self.device.udn

    @property
    def data(self):
        if self.xml and self._data is None:
            LOG.info("Fetching Node data: {url}".format(url=self.xml))
            xml = requests.get(self.xml).text
            self._data = xml2dict(xml)
        return self._data

    @property
    def address(self):
        try:
            if self.device.location:
                services = self.data["root"]["device"]['serviceList']
                for s in services:
                    service = services[s]
                    if service["serviceType"] == \
                            'urn:jarbasAi:HiveMind:service:Master':
                        return service["URLBase"]
        except:
            pass
        return self.device.data.get("host")

    @property
    def host(self):
        return ":".join(self.address.split(":")[:-1])

    @property
    def port(self):
        return int(self.address.split(":")[-1])

    def connect(self, headers, crypto_key=None, bus=None,
                node_type=None):
        try:
            # TODO cyclic import
            from jarbas_hive_mind import HiveMindConnection
            con = HiveMindConnection(self.host, self.port)
            if node_type:
                clazz = node_type
            else:
                if bus:
                    clazz = HiveMindSlave
                else:
                    clazz = HiveMindTerminal
            if bus:
                component = clazz(bus=bus,
                                  headers=headers,
                                  crypto_key=crypto_key)
            else:
                component = clazz(headers=headers,
                                  crypto_key=crypto_key)
            # will check url for ssl
            LOG.debug("Connecting to HiveMind websocket @ {url}".format(
                url=self.address))
            con.connect(component)
        except Exception as e:
            LOG.error("Connection failed")
            LOG.exception(e)


class LocalDiscovery(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pause = 20  # scan every 20 seconds
        self._nodes = {}
        self.blacklist = []
        self.running = False
        self.connected = False
        self.zero = ZeroScanner()
        self.zero.on_new_node = self.on_new_zeroconf_node
        self.zero.daemon = True
        self.zero.start()

    def on_new_zeroconf_node(self, node):
        node = HiveMindNode(_Device(node["address"]))
        LOG.info("ZeroConf Node Found: " + str(node.address))
        self._nodes[node.address] = node
        self.on_new_node(node)

    def on_new_upnp_node(self, node):
        LOG.info("UpNp Node Found: " + node.xml)
        self._nodes[node.xml] = node
        self.on_new_node(node)

    def on_new_node(self, node):
        pass

    @property
    def nodes(self):
        return self._nodes

    def scan(self):
        for node_url in self._nodes:
            if node_url in self.blacklist:
                continue
            yield node_url
        for node_url in self.upnp_scan():
            if node_url in self.blacklist:
                continue
            self.blacklist.append(node_url)
            yield node_url

    def upnp_scan(self):
        devices = upnpclient.discover()
        for d in devices:
            if d.location in self.nodes:
                continue
            if d.model_name == "HiveMind-core":
                node = HiveMindNode(d)
                self.on_new_upnp_node(node)
                yield node.xml

    def run(self) -> None:
        self.running = True
        while self.running:
            self.scan()
            sleep(self.pause)
        self.stop()

    def stop(self):
        self.running = False
        self.zero.stop()

    def search_and_connect(self, *args, **kwargs):
        while True:
            # allow zeroconf to get result before upnp check
            sleep(0.5)
            if self.connected:
                continue
            for node_url in self.scan():
                if node_url in self.blacklist:
                    continue

                self.blacklist.append(node_url)
                node = self.nodes[node_url]
                node.connect(*args, **kwargs)
                self.connected = True

