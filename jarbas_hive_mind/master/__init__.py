import base64
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from jarbas_hive_mind.database import ClientDatabase
from jarbas_hive_mind.exceptions import UnauthorizedKeyError
from jarbas_utils.log import LOG
from jarbas_utils.messagebus import Message, get_mycroft_bus
from jarbas_hive_mind.utils import decrypt_from_json, encrypt_as_json
from jarbas_hive_mind.interface import HiveMindMasterInterface
import json


platform = "HiveMindV0.7"


# protocol
class HiveMindProtocol(WebSocketServerProtocol):
    def onConnect(self, request):

        LOG.info("Client connecting: {0}".format(request.peer))
        # validate user
        userpass_encoded = bytes(request.headers.get("authorization"),
                                 encoding="utf-8")[2:-1]
        userpass_decoded = base64.b64decode(userpass_encoded).decode("utf-8")
        name, key = userpass_decoded.split(":")
        ip = request.peer.split(":")[1]
        context = {"source": self.peer}
        self.platform = request.headers.get("platform", "unknown")

        try:
            with ClientDatabase() as users:
                user = users.get_client_by_api_key(key)
                if not user:
                    raise UnauthorizedKeyError
                self.crypto_key = users.get_crypto_key(key)
        except UnauthorizedKeyError:
            LOG.error("Client provided an invalid api key")
            self.factory.mycroft_send("hive.client.connection.error",
                                      {"error": "invalid api key",
                                       "ip": ip,
                                       "api_key": key,
                                       "platform": self.platform},
                                      context)
            raise

        # send message to internal mycroft bus
        data = {"ip": ip, "headers": request.headers}
        with ClientDatabase() as users:
            self.blacklist = users.get_blacklist_by_api_key(key)
        self.factory.mycroft_send("hive.client.connect", data, context)
        # return a pair with WS protocol spoken (or None for any) and
        # custom headers to send in initial WS opening handshake HTTP response
        headers = {"server": platform}
        return (None, headers)

    def onOpen(self):
        """
       Connection from client is opened. Fires after opening
       websockets handshake has been completed and we can send
       and receive messages.

       Register client in factory, so that it is able to track it.
       """
        self.factory.register_client(self, self.platform)
        LOG.info("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            LOG.info(
                "Binary message received: {0} bytes".format(len(payload)))
        else:
            payload = self.decode(payload)
            #LOG.debug(
            #    "Text message received: {0}".format(payload))

        self.factory.on_message(self, payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.factory.unregister_client(self, reason="connection closed")
        LOG.info("WebSocket connection closed: {0}".format(reason))
        ip = self.peer.split(":")[1]
        data = {"ip": ip, "code": code, "reason": "connection closed",
                "wasClean": wasClean}
        context = {"source": self.peer}
        self.factory.mycroft_send("hive.client.disconnect", data, context)

    def connectionLost(self, reason):
        """
       Client lost connection, either disconnected or some error.
       Remove client from list of tracked connections.
       """
        self.factory.unregister_client(self, reason="connection lost")
        LOG.info("WebSocket connection lost: {0}".format(reason))
        ip = self.peer.split(":")[1]
        data = {"ip": ip, "reason": "connection lost"}
        context = {"source": self.peer}
        self.factory.mycroft_send("hive.client.disconnect", data, context)

    def decode(self, payload):
        payload = payload.decode("utf-8")
        if self.crypto_key:
            payload = decrypt_from_json(self.crypto_key, payload)
        return payload

    def sendMessage(self,
                    payload,
                    isBinary=False,
                    fragmentSize=None,
                    sync=False,
                    doNotCompress=False):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if self.crypto_key and not isBinary:
            payload = encrypt_as_json(self.crypto_key, payload)
        if isinstance(payload, str):
            payload = bytes(payload, encoding="utf-8")
        super().sendMessage(payload, isBinary,
                            fragmentSize=fragmentSize,
                            sync=sync,
                            doNotCompress=doNotCompress)


class HiveMind(WebSocketServerFactory):
    def __init__(self, bus=None, *args, **kwargs):
        super(HiveMind, self).__init__(*args, **kwargs)
        # list of clients
        self.listener = None
        self.clients = {}
        # ip block policy
        self.ip_list = []
        self.blacklist = True  # if False, ip_list is a whitelist
        # mycroft_ws
        self.bus = bus or get_mycroft_bus()
        self.register_mycroft_messages()

        self.interface = HiveMindMasterInterface(self)

    def bind(self, listener):
        self.listener = listener

    @property
    def peer(self):
        if self.listener:
            return self.listener.peer
        return None

    @property
    def node_id(self):
        return self.peer + ":MASTER"

    def mycroft_send(self, type, data=None, context=None):
        data = data or {}
        context = context or {}
        if "client_name" not in context:
            context["client_name"] = platform
        self.bus.emit(Message(type, data, context))

    def register_mycroft_messages(self):
        self.bus.on("message", self.handle_outgoing_mycroft)
        self.bus.on('hive.send', self.handle_send)

    def shutdown(self):
        self.bus.remove('message', self.handle_outgoing_mycroft)
        self.bus.remove('hive.send', self.handle_send)

    # websocket handlers
    def register_client(self, client, platform=None):
        """
       Add client to list of managed connections.
       """
        platform = platform or "unknown"
        LOG.info("registering client: " + str(client.peer))
        t, ip, sock = client.peer.split(":")
        # see if ip address is blacklisted
        if ip in self.ip_list and self.blacklist:
            LOG.warning("Blacklisted ip tried to connect: " + ip)
            self.unregister_client(client, reason="Blacklisted ip")
            return
        # see if ip address is whitelisted
        elif ip not in self.ip_list and not self.blacklist:
            LOG.warning("Unknown ip tried to connect: " + ip)
            #  if not whitelisted kick
            self.unregister_client(client, reason="Unknown ip")
            return
        self.clients[client.peer] = {"instance": client,
                                     "status": "connected",
                                     "platform": platform}

    def unregister_client(self, client, code=3078,
                          reason="unregister client request"):
        """
       Remove client from list of managed connections.
       """
        LOG.info("deregistering client: " + str(client.peer))
        if client.peer in self.clients.keys():
            client_data = self.clients[client.peer] or {}
            j, ip, sock_num = client.peer.split(":")
            context = {"user": client_data.get("names", ["unknown_user"])[0],
                       "source": client.peer}
            self.bus.emit(
                Message("hive.client.disconnect",
                        {"reason": reason, "ip": ip, "sock": sock_num},
                        context))
            client.sendClose(code, reason)
            self.clients.pop(client.peer)

    def on_message(self, client, payload, isBinary):
        """
       Process message from client, decide what to do internally here
       """
        client_protocol, ip, sock_num = client.peer.split(":")

        if isBinary:
            # TODO receive files
            pass
        else:
            # Check protocol
            data = json.loads(payload)
            payload = data["payload"]
            msg_type = data["msg_type"]

            if msg_type == "bus":
                self.handle_bus_message(payload, client)

    # HiveMind protocol messages -  from DOWNstream
    def handle_bus_message(self, payload, client):
        # Generate mycroft Message
        if isinstance(payload, str):
            payload = json.loads(payload)
        msg_type = payload.get("msg_type") or payload["type"]
        data = payload.get("data") or {}
        context = payload.get("context") or {}
        message = Message(msg_type, data, context)
        message.context["source"] = client.peer
        message.context["destination"] = "skills"
        self.handle_incoming_mycroft(message, client)

    # parsed protocol messages
    def handle_incoming_mycroft(self, message, client):
        # A Slave wants to inject a message in internal mycroft bus
        # You are a Master, authorize bus message

        client_protocol, ip, sock_num = client.peer.split(":")

        # messages/skills/intents per user
        if message.msg_type in client.blacklist.get("messages", []):
            LOG.warning(client.peer + " sent a blacklisted message "
                                      "type: " + message.msg_type)
            return
        # TODO check intent / skill that will trigger

        # send client message to internal mycroft bus
        LOG.info("Forwarding message to mycroft bus from client: " +
                 str(client.peer))
        self.mycroft_send(message.msg_type, message.data, message.context)

    def handle_client_bus(self, message, client):
        # this message is going inside the client bus
        # take any metrics you need
        LOG.info("Monitoring bus from client: " + client.peer)
        assert isinstance(message, Message)

    # mycroft handlers
    def handle_send(self, message):
        payload = message.data.get("payload")
        peer = message.data.get("peer")
        if peer and peer in self.clients:
            # send message to client
            client = self.clients[peer].get("instance")
            self.interface.send(payload, client)
        else:
            LOG.error("That client is not connected")
            self.mycroft_send("hive.client.send.error",
                              {"error": "That client is not connected",
                               "peer": peer}, message.context)

    def handle_outgoing_mycroft(self, message=None):
        # forward internal messages to clients if they are the target
        if isinstance(message, dict):
            message = json.dumps(message)
        if isinstance(message, str):
            message = Message.deserialize(message)
        if message.msg_type == "complete_intent_failure":
            message.msg_type = "hive.complete_intent_failure"
        message.context = message.context or {}
        peer = message.context.get("destination")
        if peer and peer in self.clients:
            client = self.clients[peer].get("instance")
            payload = {"msg_type": "bus",
                       "payload": message.serialize()
                       }
            self.interface.send(payload, client)

