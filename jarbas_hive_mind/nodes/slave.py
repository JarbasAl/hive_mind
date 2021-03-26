from jarbas_hive_mind.slave.terminal import HiveMindTerminal, \
    HiveMindTerminalProtocol
from jarbas_hive_mind.message import HiveMessageType, HiveMessage
from jarbas_hive_mind.nodes import HiveMindNodeType
from ovos_utils.log import LOG
from ovos_utils.messagebus import Message, get_mycroft_bus
import json


class HiveMindSlaveProtocol(HiveMindTerminalProtocol):
    platform = "HiveMindSlaveV0.2"

    @property
    def bus(self):
        return self.factory.bus

    def onConnect(self, response):
        self.bus.emit(Message("hive.mind.connected",
                              {"server_id": response.headers["server"]}))
        super().onConnect(response)

    def onOpen(self):
        self.bus.emit(Message("hive.mind.websocket.open"))
        super().onOpen()

    def onClose(self, wasClean, code, reason):
        self.bus.emit(Message("hive.mind.client.closed",
                              {"wasClean": wasClean,
                               "reason": reason,
                               "code": code}))
        super().onClose(wasClean, code, reason)


class HiveMindSlave(HiveMindTerminal):
    protocol = HiveMindSlaveProtocol
    node_type = HiveMindNodeType.SLAVE

    def __init__(self, bus=None, *args, **kwargs):
        super(HiveMindSlave, self).__init__(*args, **kwargs)
        # mycroft_ws
        self.bus = bus or get_mycroft_bus()
        self.register_mycroft_messages()

    # mycroft methods
    def register_mycroft_messages(self):
        self.bus.on("message", self.handle_outgoing_mycroft)
        self.bus.on("hive.send", self.handle_send)

    def shutdown(self):
        self.bus.remove("message", self.handle_outgoing_mycroft)
        self.bus.remove("hive.send", self.handle_send)

    def handle_send(self, message):
        msg_type = message.data["msg_type"]
        pload = message.data["payload"]

        if msg_type == HiveMessageType.BUS:
            self.send_to_hivemind_bus(pload)
        elif msg_type == HiveMessageType.PROPAGATE:
            self.interface.propagate(pload)
        elif msg_type == HiveMessageType.BROADCAST:
            # Ignore silently, if a Master is connected to bus it will
            # handle it
            pass
        elif msg_type == HiveMessageType.ESCALATE:
            self.interface.escalate(pload)
        else:
            LOG.error("Unknown HiveMind protocol msg_type")

    def handle_outgoing_mycroft(self, message=None):
        if not self.client:
            return  # not connected to hivemind yet

        # forward internal messages to connections if they are the target
        if isinstance(message, dict):
            message = json.dumps(message)
        if isinstance(message, str):
            message = Message.deserialize(message)
        if message.msg_type == "complete_intent_failure":
            message.msg_type = "hive.complete_intent_failure"

        message.context = message.context or {}
        message.context["source"] = self.client.peer
        peer = message.context.get("destination")
        if peer and peer == self.client.peer:
            msg = HiveMessage(HiveMessageType.BUS,
                              source_peer=self.client.peer,
                              payload=message.serialize())
            self.interface.send(msg)

    # parsed protocol messages
    def handle_incoming_mycroft(self, payload):
        """ HiveMind is sending a mycroft bus message"""
        # you are a slave_connection, just signal it in the bus
        self.bus.emit(Message("hive.message.received", payload))
        # and then actually inject it no questions asked
        # TODO make behaviour configurable
        super().handle_incoming_message(payload)

    # websocket handlers
    def on_binary(self, payload):
        # TODO receive binary file
        LOG.info("[BINARY MESSAGE]")

    def send_to_hivemind_bus(self, payload):
        super().send_to_hivemind_bus(payload)
        self.bus.emit(Message("hive.message.sent",
                              {"payload": payload}))

