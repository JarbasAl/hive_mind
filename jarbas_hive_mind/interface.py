import json
from jarbas_utils.messagebus import Message


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
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if not isinstance(payload, bytes):
            payload = bytes(payload, encoding="utf-8")

        self.client.sendMessage(payload)

    def send_to_hivemind_bus(self, payload):
        if isinstance(payload, Message):
            payload = payload.serialize()
        payload = {"msg_type": "bus",
                   "payload": payload
                   }
        self.send(payload)

    def broadcast(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "broadcast",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }
        if self.bus:
            message = Message("hive.send",
                              payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def propagate(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "propagate",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }

        no_send = [n["source"] for n in msg_data.get("route", [])]
        if self.peer not in no_send:
            self.send(payload)

        if self.bus and msg_data.get("node", "") == \
                self.peer + ":MASTER":
            message = Message("hive.send",
                              payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    # WIP ZONE
    def escalate(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "escalate",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer,
                   "node": self.client.node_id
                   }

        route_data = {"source": self.peer,
                      # when master receives this it will update this field
                      "targets": [self.peer]}
        if route_data not in payload["route"]:
            payload["route"].append(route_data)
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
        if isinstance(client, str):
            client = self.listener.clients[client]
        if isinstance(payload, dict):
            payload = json.dumps(payload)
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

    def broadcast(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "broadcast",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer
                   }
        no_send = [n["source"] for n in msg_data.get("route", [])]
        self.send_to_many(payload, no_send)

    def propagate(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "propagate",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer,
                   "node": self.node_id
                   }

        no_send = [n["source"] for n in msg_data.get("route", [])]
        self.send_to_many(payload, no_send)

        # tell Slave to propagate upstream
        if self.bus and msg_data.get("source_peer") != self.peer:
            payload["msg_type"] = "propagate"
            message = Message("hive.send",
                              payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    # WIP ZONE
    def escalate(self, payload, msg_data=None):
        msg_data = msg_data or {}
        payload = {"msg_type": "escalate",
                   "payload": payload,
                   "route": msg_data.get("route", []),
                   "source_peer": self.peer,
                   "node": self.node_id
                   }
        # tell Slave to escalate upstream
        if self.bus and msg_data.get("source_peer") != self.peer:
            message = Message("hive.send",
                              payload,
                              {"destination": "hive",
                               "source": self.peer})
            self.bus.emit(message)

    def query(self, payload, msg_data=None):
        raise NotImplementedError

    def cascade(self, payload, msg_data=None):
        raise NotImplementedError

