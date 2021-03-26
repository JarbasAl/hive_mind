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

FakeCroft = FakeMycroft(30000)
FakeCroft.connect(20000)


def test_escalate():
    msg = HiveMessage(msg_type=HiveMessageType.THIRDPRTY,
                      payload={"ping": "END"})

    def escalate_test():
        while True:
            sleep(5)
            print("\nTESTING escalate FROM end\n")
            FakeCroft.interface.escalate(msg)

    create_daemon(escalate_test)


# send escalate message every 5 seconds
test_escalate()

FakeCroft.run()


# Expected output


# Mid
"""
INFO - Received escalate message at: tcp4:0.0.0.0:20000:MASTER
DEBUG - ROUTE: [{'source': 'tcp4:127.0.0.1:39742', 'targets': ['tcp4:0.0.0.0:20000']}]
DEBUG - PAYLOAD: {'ping': 'pong'}
"""

# Master
"""
INFO - Received escalate message at: tcp4:0.0.0.0:10000:MASTER
DEBUG - ROUTE: [{'source': 'tcp4:127.0.0.1:39742', 'targets': ['tcp4:0.0.0.0:20000']}, {'source': 'tcp4:127.0.0.1:58498', 'targets': ['tcp4:0.0.0.0:10000']}]
DEBUG - PAYLOAD: {'ping': 'pong'}
"""
