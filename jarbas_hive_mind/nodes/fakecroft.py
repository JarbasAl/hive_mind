from jarbas_hive_mind.nodes.master import HiveMind, HiveMindProtocol
from jarbas_hive_mind.message import HiveMessage, HiveMessageType
from jarbas_hive_mind.nodes import HiveMindNodeType
from ovos_utils.log import LOG


platform = "FakeCroftMindV0.1"


class FakeCroftMindProtocol(HiveMindProtocol):
    """"""


class FakeCroftMind(HiveMind):
    protocol = FakeCroftMindProtocol
    node_type = HiveMindNodeType.FAKECROFT

    def __init__(self, *args, **kwargs):
        super().__init__(bus=False, *args, **kwargs)

    def handle_incoming_mycroft(self, message, client):
        """
        message (Message): mycroft bus message object
        """
        LOG.debug(f"Mycroft bus message received: {message.msg_type}")
        LOG.debug(f"data: {message.data}")
        LOG.debug(f"context: {message.context}")

        answer = "mycroft is dead! long live mycroft!"

        payload = HiveMessage(HiveMessageType.BUS,
                              message.reply("speak", {"utterance": answer}))
        self.interface.send(payload, client)
