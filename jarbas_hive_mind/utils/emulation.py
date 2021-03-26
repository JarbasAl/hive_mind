from jarbas_hive_mind import get_listener, get_connection
from jarbas_hive_mind.slave import HiveMindSlave
from jarbas_hive_mind.configuration import CONFIGURATION
from twisted.internet import reactor


# TODO ovos_utils FakeBus
class FakeBus:
    def __init__(self, *args, **kwargs):
        self.events = {}

    def on(self, msg_type, handler):
        if msg_type not in self.events:
            self.events[msg_type] = []
        self.events[msg_type].append(handler)

    def emit(self, message):
        if message.msg_type in self.events:
            for handler in self.events[message.msg_type]:
                handler(message)

    def remove(self, msg_type, handler):
        pass


class FakeMycroft:

    def __init__(self, port, key="dummy_key", config=None):
        self.bus = FakeBus()
        self.config = config or CONFIGURATION
        self.port = port
        self.user_agent = "fakeCroft:{n}".format(n=self.port)
        self.key = key
        # hive mind objects
        self.hive = None
        self.slave_connection = None
        self.connection = None
        self.listener = None

    @property
    def interface(self):
        if self.hive_interface:
            return self.hive_interface
        elif self.slave_interface:
            return self.slave_interface
        else:
            return None

    @property
    def hive_interface(self):
        # the master can send requests downstream with this interface
        if self.hive:
            return self.hive.interface
        return None

    @property
    def slave_interface(self):
        # the slave_connection can send requests upstream with this interface
        if self.slave_connection:
            return self.slave_connection.interface
        return None

    def start_listener(self):
        # listen
        self.listener = get_listener(port=self.port,
                                     bus=self.bus)

        # this flag is not meant for the end user
        # used here so the twisted reactor can be started manually
        self.listener._autorun = False

        # returns a HiveMind object
        self.hive = self.listener.listen()

    def connect(self, port, host="0.0.0.0"):
        self.connection = get_connection(host, port)

        # this flag is not meant for the end user
        # used here so the twisted reactor can be started manually
        self.connection._autorun = False

        con = HiveMindSlave(bus=self.bus,
                            headers=self.connection.get_headers(self.user_agent,
                                                                self.key),
                            useragent=self.user_agent)

        # returns a HiveMindSlave object
        self.slave_connection = self.connection.connect(con)

    def run(self):
        reactor.run()

