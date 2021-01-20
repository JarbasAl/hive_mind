from jarbas_hive_mind.slave.terminal import HiveMindTerminal, \
    HiveMindTerminalProtocol
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
        payload = message.data
        msg_type = payload["msg_type"]

        if msg_type == "bus":
            mycroft_message = payload["payload"]
            self.send_to_hivemind_bus(mycroft_message)
        elif msg_type == "propagate":
            self.interface.propagate(payload["payload"], payload)
        elif msg_type == "broadcast":
            # LOG.debug("Slaves can not broadcast messages")
            # Ignore silently, if a Master is connected to bus it will
            # handle it
            pass
        elif msg_type == "escalate":
            self.interface.escalate(payload["payload"], payload)
        else:
            LOG.error("Unknown HiveMind protocol msg_type")

    def handle_outgoing_mycroft(self, message=None):
        if not self.client:
            return  # not connected to hivemind yet
        # forward internal messages to clients if they are the target
        if isinstance(message, dict):
            message = json.dumps(message)
        if isinstance(message, str):
            message = Message.deserialize(message)
        if message.msg_type == "complete_intent_failure":
            message.msg_type = "hive.complete_intent_failure"
        message.context = message.context or {}
        message.context["source"] = self.client.peer
        peer = message.context.get("destination")
        message = message.serialize()
        if peer and peer == self.client.peer:
            payload = {"msg_type": "bus",
                       "payload": message
                       }
            self.interface.send(payload)

    # parsed protocol messages
    def handle_incoming_mycroft(self, payload):
        """ HiveMind is sending a mycroft bus message"""
        # you are a slave_connection, just forward to the bus
        self.bus.emit(Message("hive.message.received", payload))
        super().handle_incoming_message(payload)

    # websocket handlers
    def on_binary(self, payload):
        # TODO receive binary file
        LOG.info("[BINARY MESSAGE]")

    def send_to_hivemind_bus(self, payload):
        super().send_to_hivemind_bus(payload)
        self.bus.emit(Message("hive.message.sent",
                              {"payload": payload}))

