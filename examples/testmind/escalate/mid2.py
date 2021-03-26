from jarbas_hive_mind.utils.emulation import FakeMycroft
from jarbas_hive_mind.message import HiveMessage, HiveMessageType
from ovos_utils import create_daemon
from time import sleep


# Here is a minimal test hive mind
#
#           Master
#         /       \
#       Mid      Mid2
#     /   \          \
#  end    end2       end3
#


FakeCroft = FakeMycroft(20001)
FakeCroft.start_listener()
FakeCroft.connect(10000)


def test_escalate():
    msg = HiveMessage(msg_type=HiveMessageType.THIRDPRTY,
                      payload={"ping": "MID2"})

    def escalate_test():
        while True:
            sleep(5)
            print("\nTESTING escalate FROM Mid2\n")
            FakeCroft.interface.escalate(msg)

    create_daemon(escalate_test)


# send escalate message every 5 seconds
test_escalate()

FakeCroft.run()


# Expected output


# Master
"""
INFO - Received escalate message at: tcp4:0.0.0.0:10000:MASTER
DEBUG - ROUTE: [{'source': 'tcp4:127.0.0.1:58496', 'targets': ['tcp4:0.0.0.0:10000']}]
DEBUG - PAYLOAD: {'mid2': 'pong'}
"""