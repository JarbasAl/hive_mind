from pyee import ExecutorEventEmitter
from threading import Event


class FakeBus:
    def __init__(self, *args, **kwargs):
        self.events = {}
        self.once_events = {}
        self.skill_id = None
        self.ee = ExecutorEventEmitter()
        self.ee.on("error", self.on_error)

    def bind(self, skill):
        if isinstance(skill, str):
            self.skill_id = skill
        else:
            self.skill_id = skill.skill_id

    def on(self, msg_type, handler):
        if msg_type not in self.events:
            self.events[msg_type] = []
        self.events[msg_type].append(handler)
        self.ee.on(msg_type, handler)

    def once(self, msg_type, handler):
        if msg_type not in self.once_events:
            self.once_events[msg_type] = []
        self.once_events[msg_type].append(handler)
        self.ee.once(msg_type, handler)

    def emit(self, message):
        if self.skill_id is not None:
            message.context["skill_id"] = self.skill_id
            message.context["source"] = message.context.get("source") or \
                                        self.skill_id
        self.ee.emit("message", message.serialize())
        self.ee.emit(message.msg_type, message)

    def wait_for_message(self, message_type, timeout=3.0):
        """Wait for a message of a specific type.

        Arguments:
            message_type (str): the message type of the expected message
            timeout: seconds to wait before timeout, defaults to 3

        Returns:
            The received message or None if the response timed out
        """
        received_event = Event()
        received_event.clear()

        msg = None

        def rcv(m):
            nonlocal msg
            msg = m

        self.ee.on(message_type, rcv)
        received_event.wait(timeout)
        return msg

    def wait_for_response(self, message, reply_type=None, timeout=3.0):
        """Send a message and wait for a response.

        Arguments:
            message (Message): message to send
            reply_type (str): the message type of the expected reply.
                              Defaults to "<message.msg_type>.response".
            timeout: seconds to wait before timeout, defaults to 3

        Returns:
            The received message or None if the response timed out
        """
        reply_type = reply_type or message.msg_type + ".response"
        received_event = Event()
        received_event.clear()

        msg = None

        def rcv(m):
            nonlocal msg
            msg = m

        self.ee.once(reply_type, rcv)
        self.emit(message)
        received_event.wait(timeout)
        return msg

    def remove(self, msg_type, handler):
        if msg_type in self.events:
            if handler in self.events[msg_type]:
                self.events[msg_type].remove(handler)
                self.ee.remove_listener(msg_type, handler)
        if msg_type in self.once_events:
            if handler in self.once_events[msg_type]:
                self.once_events[msg_type].remove(handler)
                self.ee.remove_listener(msg_type, handler)

    def remove_all_listeners(self, event_name):
        self.ee.remove_all_listeners(event_name)
        if event_name in self.events:
            self.events.pop(event_name)
        if event_name in self.once_events:
            self.once_events.pop(event_name)

    def create_client(self):
        return self

    def on_error(self, error):
        print(error)

    def on_open(self):
        pass

    def on_close(self):
        pass

    def run_forever(self):
        pass

    def close(self):
        pass

