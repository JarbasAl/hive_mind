import json
from jarbas_hive_mind.utils import serialize_message
from jarbas_hive_mind.message import HiveMessage, HiveMessageType
from ovos_utils.messagebus import Message


def _get_payload(msg):
    if isinstance(msg, HiveMessage):
        msg = msg.payload
    if isinstance(msg, Message):
        msg = msg.serialize()
    if isinstance(msg, str):
        msg = json.loads(msg)
    return msg


def _get_hivemsg(msg):
    if isinstance(msg, str):
        msg = json.loads(msg)
    if isinstance(msg, dict):
        msg = HiveMessage(**msg)
    if isinstance(msg, Message):
        msg = HiveMessage(msg_type=HiveMessageType.BUS, payload=msg)
    assert isinstance(msg, HiveMessage)
    return msg


class HiveMindSlaveInterface:
    def __init__(self, connection):
        self.client = connection

    @property
    def bus(self):
        # if bus is None -> Terminal
        # else -> Slave
        return self.client.bus

    @property
    def node_id(self):
        return self.client.node_id

    @property
    def peer(self):
        return self.client.peer

    def send(self, payload):
        payload = serialize_message(payload)
        if not isinstance(payload, bytes):
            payload = bytes(payload, encoding="utf-8")
        self.client.sendMessage(payload)

    def send_to_hivemind_bus(self, payload):
        payload = {"msg_type": HiveMessageType.BUS,
                   "payload": _get_payload(payload),
                   "node": self.node_id,
                   "source_peer": self.peer
                   }
        self.send(payload)

    def broadcast(self, message):
        message = _get_hivemsg(message)
        payload = {"msg_type": HiveMessageType.BROADCAST,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }
        if self.bus:
            message = Message("hive.send", payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def propagate(self, message):
        message = _get_hivemsg(message)
        payload = {"msg_type": HiveMessageType.PROPAGATE,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }

        no_send = [n["source"] for n in message.route]
        if self.peer not in no_send:
            self.send(payload)

        if self.bus and payload.get("node", "") == self.peer + ":MASTER":
            message = Message("hive.send", payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def escalate(self, message):
        message = _get_hivemsg(message)
        # when master receives this it will
        # update "targets" field with it's own id
        route_data = {"source": self.peer,
                      "targets": []}
        message.update_hop_data(route_data)
        payload = {"msg_type": HiveMessageType.ESCALATE,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }
        self.send(payload)

    def query(self, payload, msg_data=None):
        raise NotImplementedError

    def cascade(self, payload, msg_data=None):
        raise NotImplementedError


class HiveMindMasterInterface:
    def __init__(self, listener):
        self.listener = listener

    @property
    def peer(self):
        return self.listener.peer

    @property
    def clients(self):
        return [c["instance"] for c in
                self.listener.clients.values()]

    @property
    def node_id(self):
        return self.listener.node_id

    @property
    def bus(self):
        return self.listener.bus

    def send(self, payload, client):
        payload = serialize_message(payload)
        if isinstance(client, str):
            client = self.listener.clients[client]
        if not isinstance(payload, bytes):
            payload = bytes(payload, encoding="utf-8")

        client.sendMessage(payload)

    def send_to_many(self, payload, no_send=None):
        no_send = no_send or []
        payload["route"] = payload["route"] or []
        route_data = {"source": self.peer,
                      "targets": [c.peer for c in self.clients]}
        # No resend
        if route_data in payload["route"]:
            return

        payload["route"].append(route_data)

        for client in self.clients:
            if client.peer not in no_send:
                self.send(payload, client)

    def broadcast(self, message):
        message = _get_hivemsg(message)
        payload = {"msg_type": HiveMessageType.BROADCAST,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.node_id
                   }
        no_send = [n["source"] for n in message.route]
        self.send_to_many(payload, no_send)

    def propagate(self, message):
        message = _get_hivemsg(message)
        payload = {"msg_type": HiveMessageType.PROPAGATE,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.node_id
                   }
        no_send = [n["source"] for n in message.route]
        self.send_to_many(payload, no_send)

        # tell Slave to propagate upstream
        if self.bus and message.source_peer != self.peer:
            message = Message("hive.send", payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def escalate(self, message):
        message = _get_hivemsg(message)
        payload = {"msg_type": HiveMessageType.ESCALATE,
                   "payload": message,
                   "route": message.route,
                   "source_peer": self.peer,
                   "node": self.node_id
                   }
        # tell Slave to escalate upstream
        if self.bus and message.source_peer != self.peer:
            message = Message("hive.send", payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def query(self, payload, msg_data=None):
        raise NotImplementedError

    def cascade(self, payload, msg_data=None):
        raise NotImplementedError

