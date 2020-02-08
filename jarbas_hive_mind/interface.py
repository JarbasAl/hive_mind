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
        raise NotImplementedError

    def propagate(self, payload, msg_data=None):
        raise NotImplementedError

    def escalate(self, payload, msg_data=None):
        raise NotImplementedError

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
        raise NotImplementedError

    def propagate(self, payload, msg_data=None):
        raise NotImplementedError

    def escalate(self, payload, msg_data=None):
        raise NotImplementedError

    def query(self, payload, msg_data=None):
        raise NotImplementedError

    def cascade(self, payload, msg_data=None):
        raise NotImplementedError

