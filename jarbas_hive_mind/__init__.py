import base64
from twisted.internet import reactor, ssl
from twisted.internet.error import ReactorNotRunning
from jarbas_hive_mind.master import HiveMind, HiveMindProtocol
from jarbas_hive_mind.configuration import CONFIGURATION
from jarbas_hive_mind.settings import DEFAULT_PORT
from jarbas_hive_mind.utils import create_self_signed_cert
from jarbas_hive_mind.exceptions import SecureConnectionFailed, ConnectionError
from ovos_utils.messagebus import get_mycroft_bus
from ovos_utils.log import LOG
from os.path import join, exists, isfile
from twisted.python.log import err
import logging

logging.getLogger("urllib3.connectionpool").setLevel("INFO")
logging.getLogger("Service").setLevel("INFO")
logging.getLogger("Device").setLevel("INFO")
logging.getLogger("JsonDatabase").setLevel("INFO")


class HiveMindConnection:
    _autorun = True

    def __init__(self, host="127.0.0.1", port=DEFAULT_PORT):
        host = host.replace("https://", "wss://").replace("http://", "ws://")
        if "wss://" in host:
            secure = True
        else:
            secure = False
        self._secure = secure

        host = host.replace("wss://", "").replace("ws://", "")
        self.host = host
        self.port = port

    @property
    def is_secure(self):
        return self._secure

    @property
    def address(self):
        if self.is_secure:
            if "wss://" in self.host:
                return self.host + u":" + str(self.port)
            return "wss://" + self.host + u":" + str(self.port)
        else:
            if "ws://" in self.host:
                return self.host + u":" + str(self.port)
            return "ws://" + self.host + u":" + str(self.port)

    @property
    def peer(self):
        return "tcp4:" + self.host + ":" + str(self.port)

    @staticmethod
    def get_headers(name, key):
        # Note that keys can be shared across users
        # name is not used for auth
        name = name.replace(":", "__")
        authorization = bytes(name + ":" + key, encoding="utf-8")
        key = base64.b64encode(authorization)
        headers = {'authorization': key}
        return headers

    def secure_connect(self, component):
        self._secure = True
        component.bind(self)
        LOG.info("Connecting securely to " + self.address)
        contextFactory = ssl.ClientContextFactory()
        self._run(reactor.connectSSL(self.host, self.port, component, contextFactory))
        return component

    def unsafe_connect(self, component):
        self._secure = False
        component.bind(self)
        LOG.info("Connecting to " + self.address)
        LOG.warning("This listener is unsecured")
        self._run(reactor.connectTCP(self.host, self.port, component))
        return component

    def _run(self, component):

        def fatalError(reason):
            LOG.error(reason)
            err(reason, "Absolutely needed the foo, could not get it")
            reactor.stop()

       # component.addErrback(fatalError)

        if not reactor.running and self._autorun:
            try:
                reactor.run()
            except Exception as e:
                LOG.exception(e)

    def connect(self, component):
        try:
            if self.is_secure:
                try:
                    return self.secure_connect(component)
                except ConnectionError:
                    raise SecureConnectionFailed
            else:
                return self.unsafe_connect(component)
        except Exception as e:
            LOG.exception(e)
            raise e


class HiveMindListener:
    _autorun = True
    default_factory = HiveMind
    default_protocol = HiveMindProtocol

    def __init__(self, port=DEFAULT_PORT, max_cons=-1, bus=None):
        self.host = "0.0.0.0"
        self.port = port
        self.max_cons = max_cons
        self._use_ssl = CONFIGURATION["ssl"].get("use_ssl", False)
        self.certificate_path = CONFIGURATION["ssl"]["certificates"]
        self._key_file = CONFIGURATION["ssl"].get("ssl_keyfile",
                                                  "HiveMind.key")
        self._cert_file = CONFIGURATION["ssl"].get("ssl_certfile",
                                                   "HiveMind.crt")
        self.bus = bus

    def bind(self, bus=None):
        # TODO read config for bus options
        self.bus = bus or get_mycroft_bus()

    @property
    def ssl_key(self):
        if isfile(self._key_file):
            return self._key_file
        return join(self.certificate_path, self._key_file)

    @property
    def ssl_cert(self):
        if isfile(self._cert_file):
            return self._cert_file
        return join(self.certificate_path, self._cert_file)

    def load_config(self, config=CONFIGURATION, gen_keys=True):
        # read configuration
        self.port = config["port"]
        self.max_cons = config.get("max_connections", -1)

        ssl_config = config.get("ssl", {})
        self.certificate_path = ssl_config.get("certificates",
                                               self.certificate_path)
        self._key_file = ssl_config.get("ssl_keyfile", self._key_file)
        self._cert_file = ssl_config.get("ssl_certfile", self._cert_file)
        self._use_ssl = ssl_config.get("use_ssl", True)

        # generate self signed keys
        if not exists(self.ssl_key) and gen_keys and \
                self.is_secure:
            LOG.warning("ssl keys dont exist")
            self.generate_keys(self.certificate_path)

    @property
    def is_secure(self):
        return self._use_ssl

    @property
    def address(self):
        if self.is_secure:
            return "wss://" + self.host + ":" + str(self.port)
        return "ws://" + self.host + ":" + str(self.port)

    @property
    def peer(self):
        return "tcp4:" + self.host + ":" + str(self.port)

    @staticmethod
    def generate_keys(path=CONFIGURATION["ssl"]["certificates"],
                      key_name="HiveMind"):
        LOG.info("creating self signed SSL keys")
        name = key_name.split("/")[-1].replace(".key", "")
        create_self_signed_cert(path, name)
        cert = path + "/" + name + ".crt"
        key = path + "/" + name + ".key"
        LOG.info("key created at: " + key)
        LOG.info("crt created at: " + cert)

    def secure_listen(self, key=None, cert=None, factory=None, protocol=None):
        self._use_ssl = True
        key = key or self.ssl_key
        cert = cert or self.ssl_cert

        # SSL server context: load server key and certificate
        contextFactory = ssl.DefaultOpenSSLContextFactory(key, cert)

        factory = factory or self.default_factory(bus=self.bus)
        factory.protocol = protocol or self.default_protocol
        if self.max_cons >= 0:
            factory.setProtocolOptions(maxConnections=self.max_cons)
        factory.bind(self)
        self.factory = factory
        reactor.listenSSL(self.port, factory, contextFactory)
        LOG.info("HiveMind Listening: " + self.address)
        if self._autorun and not reactor.running:
            reactor.run()
        return factory

    def unsafe_listen(self, factory=None, protocol=None):
        self._use_ssl = False
        factory = factory or self.default_factory(bus=self.bus)
        factory.protocol = protocol or self.default_protocol
        if self.max_cons >= 0:
            factory.setProtocolOptions(maxConnections=self.max_cons)
        factory.bind(self)
        self.factory = factory
        reactor.listenTCP(self.port, factory)
        LOG.info("HiveMind Listening (UNSECURED): " + self.address)
        if self._autorun and not reactor.running:
            reactor.run()
        return factory

    def listen(self, factory=None, protocol=None):
        if self.is_secure:
            return self.secure_listen(factory=factory, protocol=protocol)
        else:
            return self.unsafe_listen(factory=factory, protocol=protocol)

    def stop(self):
        """Stop the reactor and join the reactor thread until it stops.
        """
        try:
            reactor.stop()
        except ReactorNotRunning:
            LOG.info("twisted reactor stopped")
        except Exception as e:
            LOG.error(e)

    def stop_from_thread(self):
        reactor.callFromThread(self.stop)
        for p in reactor.getDelayedCalls():
            if p.active():
                p.cancel()


def get_listener(port=DEFAULT_PORT, max_connections=-1, bus=None):
    return HiveMindListener(port, max_connections, bus)


def get_connection(host="127.0.0.1", port=DEFAULT_PORT):
    return HiveMindConnection(host, port)
