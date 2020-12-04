from ovos_utils.log import LOG
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet.protocol import ReconnectingClientFactory
from jarbas_hive_mind.exceptions import UnauthorizedKeyError, \
    SecureConnectionFailed, ConnectionError, HiveMindEntryPointNotFound
from jarbas_hive_mind.utils import encrypt_as_json, decrypt_from_json
from jarbas_hive_mind.interface import HiveMindSlaveInterface
from ovos_utils.messagebus import Message
import json
from twisted.internet import reactor

platform = "HiveMindTerminalv0.2"


class HiveMindTerminalProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        LOG.info("HiveMind connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        LOG.info("HiveMind websocket connection open. ")

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = self.decode(payload)
            data = {"payload": payload, "isBinary": isBinary}
        else:
            data = {"payload": None, "isBinary": isBinary}
        self.factory.handle_incoming_message(data)

    def onClose(self, wasClean, code, reason):
        LOG.warning("HiveMind websocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"
        if "WebSocket connection upgrade failed" in reason:
            # key rejected
            LOG.error("Key rejected")
            #raise UnauthorizedKeyError

        elif self.factory.connection.is_secure:
            if "WebSocket opening handshake timeout" in reason:
                LOG.error("SecureConnectionFailed: " + reason)
                # raise SecureConnectionFailed

        else:
            LOG.error("ConnectionError")
        reactor.stop()

    def decode(self, payload):
        payload = payload.decode("utf-8")
        if self.factory.crypto_key:
            payload = decrypt_from_json(self.factory.crypto_key, payload)
        return payload

    def sendMessage(self,
                    payload,
                    isBinary=False,
                    fragmentSize=None,
                    sync=False,
                    doNotCompress=False):
        if self.factory.crypto_key and not isBinary:
            payload = encrypt_as_json(self.factory.crypto_key, payload)
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if isinstance(payload, str):
            payload = bytes(payload, encoding="utf-8")
        super().sendMessage(payload, isBinary, fragmentSize=fragmentSize,
                            sync=sync, doNotCompress=doNotCompress)


class HiveMindTerminal(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = HiveMindTerminalProtocol
    announce = False

    def __init__(self, crypto_key=None, connection=None,
                 auto_reconnect=False, *args, **kwargs):
        super(HiveMindTerminal, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None
        self.crypto_key = crypto_key
        self.connection = None
        self.interface = HiveMindSlaveInterface(self)
        self.auto_reconnect = auto_reconnect
        self.upnp_server = None
        self.ssdp = None
        if connection:
            self.bind(connection)

    def bind(self, connection):
        self.connection = connection

    @property
    def node_id(self):
        if not self.peer:
            return None
        return self.peer + ":SLAVE"

    @property
    def peer(self):
        if self.client:
            return self.client.peer
        return None

    @property
    def master(self):
        return self.connection.peer

    # parsed protocol messages
    def handle_incoming_mycroft(self, message):
        assert isinstance(message, Message)
        LOG.debug("[Mycroft Message] " + message.serialize())

    # HiveMind protocol messages - from UPstream
    def handle_bus_message(self, payload):
        # Generate mycroft Message
        if isinstance(payload, str):
            payload = json.loads(payload)
        msg_type = payload.get("msg_type") or payload["type"]
        data = payload.get("data") or {}
        context = payload.get("context") or {}
        message = Message(msg_type, data, context)
        message.context["source"] = self.client.peer
        message.context["destination"] = "skills"
        if "platform" not in message.context:
            message.context["platform"] = platform
        self.handle_incoming_mycroft(message)

    def handle_propagate_message(self, payload, msg_data):
        LOG.info("Received propagate message at: " + self.node_id)
        LOG.debug("ROUTE: " + str(msg_data["route"]))
        LOG.debug("PAYLOAD: " + str(payload))
        self.interface.propagate(payload, msg_data)

    def handle_broadcast_message(self, payload, msg_data):
        LOG.info("Received broadcast message at: " + self.node_id)
        LOG.debug("ROUTE: " + str(msg_data["route"]))
        LOG.debug("PAYLOAD: " + str(payload))
        self.interface.broadcast(payload, msg_data)

    def handle_escalate_message(self, payload, msg_data):
        # only Slaves are allowed to escalate, by definition escalate
        # goes upstream only
        LOG.debug("Ignoring escalate message from upstream, illegal action")

    def handle_incoming_message(self, data):
        payload = data.get("payload")
        if data.get("isBinary"):
            self.on_binary(payload)
        else:
            self.on_message(payload)

    # websocket handlers
    def send_to_hivemind_bus(self, payload):
        if isinstance(payload, Message):
            payload = payload.serialize()
        self.interface.send_to_hivemind_bus(payload)
        return payload

    def sendBinary(self, payload):
        if self.client is None:
            LOG.error("Client is none")
            return
        self.client.sendMessage(payload, isBinary=True)

    def sendMessage(self, payload):
        if self.client is None:
            LOG.error("Client is none")
            return
        self.client.sendMessage(payload, isBinary=False)

    def on_binary(self, payload):
        LOG.info("[BINARY MESSAGE]")

    def on_message(self, payload):
        msg = json.loads(payload)
        msg_type = msg["msg_type"]
        payload = msg["payload"]

        # Parse hive protocol
        if msg_type == "bus":
            self.handle_bus_message(payload)
        elif msg_type == "propagate":
            self.handle_propagate_message(payload, msg)
        elif msg_type == "broadcast":
            self.handle_broadcast_message(payload, msg)
        elif msg_type == "escalate":
            self.handle_escalate_message(payload, msg)
        else:
            LOG.error("Unknown HiveMind protocol msg_type")

    def clientConnectionFailed(self, connector, reason):
        self.status = "disconnected"
        if "DNS lookup failed:" in str(reason):
            LOG.error("Could not find the specified HiveMind entry point")
            LOG.debug("Does this look like a valid address? " +
                      self.connection.address)
            raise HiveMindEntryPointNotFound
        else:

            if self.auto_reconnect:
                LOG.error("HiveMind client failed: " + str(reason) +
                          " .. retrying ..")
                self.retry(connector)
            else:
                LOG.error("HiveMind client failed: " + str(reason))

    def clientConnectionLost(self, connector, reason):
        LOG.error("HiveMind connection lost: " + str(reason) +
                  " .. retrying ..")
        self.status = "disconnected"
        if self.auto_reconnect:
            LOG.error("HiveMind connection lost: " + str(reason) +
                      " .. retrying ..")
            self.retry(connector)
        else:
            LOG.error("HiveMind connection lost: " + str(reason))

