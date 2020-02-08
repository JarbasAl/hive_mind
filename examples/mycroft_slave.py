from jarbas_hive_mind import get_connection
from jarbas_hive_mind.slave import HiveMindSlave


def connect_to_hivemind(host="wss://0.0.0.0", port=5678,
                        name="Jarbas Drone",
                        key="dummy_key", crypto_key=None,
                        useragent="JarbasDroneV0.2",
                        bus=None):
    con = get_connection(host, port)

    component = HiveMindSlave(bus=bus, headers=con.get_headers(name, key),
                              crypto_key=crypto_key, useragent=useragent)

    # will check url for ssl
    con.connect(component)


if __name__ == '__main__':
    # TODO arg parse
    connect_to_hivemind()

    # That's it, now the hive mind can send messages to the mycroft bus

    # you can react to hive mind events
    # NOTE the payload from hive mind is also sent directly to the messagebus
    # "hive.mind.connected"
    # "hive.mind.websocket.open"
    # "hive.mind.connection.closed"
    # "hive.mind.message.received"
    # "hive.mind.message.sent"

    # you can send messages to the mycroft bus to send to the HiveMind
    # for example to interact with a skill
    # 'Message("hive.mind.message.send",
    #           {"payload":
    #               {"msg_type": "sensor.data",
    #               "data": {"status": "off"}
    #           })
