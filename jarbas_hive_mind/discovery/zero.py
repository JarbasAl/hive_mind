from ovos_utils import get_ip
from ovos_utils.log import LOG
import time
from zeroconf import Zeroconf, ServiceInfo
import ipaddress
import threading
from uuid import uuid4
from time import sleep

from zeroconf import ServiceBrowser, ServiceStateChange


class ZeroConfAnnounce(threading.Thread):
    def __init__(self,
                 uuid=None,
                 host=None,
                 port=5678,
                 service_type="HiveMind-websocket",
                 name="HiveMind-Node", *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.port = port
        self.service_type = service_type
        self.host = host or get_ip()
        self.uuid = uuid or str(uuid4())

    @property
    def ssl(self):
        return self.host.startswith("wss://") or \
               self.host.startswith("https://")

    def run(self):
        """Start advertising to other devices about the ip address"""
        # Get the local ip address
        ip = get_ip()

        info = ServiceInfo(
            "_http._tcp.local.",
            " - {}._http._tcp.local.".format(self.name),
            addresses=[ipaddress.ip_address(ip).packed],
            port=self.port,
            properties={"type": self.service_type,
                        "ssl": self.ssl,
                        "host": self.host,
                        "port": self.port},
        )

        zeroconf = Zeroconf()
        # Registering service
        zeroconf.register_service(info)
        try:
            while True:
                time.sleep(0.1)
        finally:
            # Unregister service for whatever reason
            zeroconf.unregister_service(info)
            zeroconf.close()


class ZeroScanner(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zero = Zeroconf()
        self.browser = ServiceBrowser(self.zero, "_http._tcp.local.",
                                      handlers=[self.on_service_state_change])
        self.nodes = {}
        self.running = False

    def get_nodes(self):
        return self.nodes

    def on_new_node(self, node_data):
        self.nodes[node_data["address"]] = node_data

    def on_node_update(self, node_data):
        pass

    def on_service_state_change(self, zeroconf, service_type, name,
                                state_change):

        if state_change is ServiceStateChange.Added or state_change is \
                ServiceStateChange.Updated:
            info = zeroconf.get_service_info(service_type, name)
            node_data = {}
            if info:
                if info.properties:
                    for key, value in info.properties.items():
                        if key == b"type" and value == b"HiveMind-websocket":
                            node_data["address"] = info._properties[b"host"].decode("utf-8")
                            node_data["weight"] = info.weight
                            node_data["priority"] = info.priority
                            node_data["server"] = info.server
                            node_data["type"] = value.decode("utf-8")
                            if state_change is ServiceStateChange.Added:

                                self.on_new_node(node_data)
                            else:
                                #LOG.info("Node Updated: " + str(node_data))
                                self.on_node_update(node_data)
                            LOG.debug(str(zeroconf.cache.__dict__))
                else:
                    LOG.debug("  No properties")

            else:
                LOG.debug("  No info")

    def run(self) -> None:
        self.running = True
        while self.running:
            sleep(0.1)
        self.stop()

    def stop(self):
        self.running = False
        self.zero.close()


if __name__ == '__main__':
    z = ZeroScanner()
    z.start()


