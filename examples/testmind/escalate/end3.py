from jarbas_hive_mind.utils.emulation import FakeMycroft
from jarbas_utils import create_daemon
from time import sleep


# Here is a minimal test hive mind
#
#           Master
#         /       \
#       Mid      Mid2
#     /   \          \
#  end    end2       end3
#

FakeCroft = FakeMycroft(30002)
FakeCroft.connect(20001)


def test_escalate():
    def escalate_test():
        while True:
            sleep(5)
            print("\nTESTING escalate FROM end3\n")
            FakeCroft.interface.escalate({"ping": "pong"})

    create_daemon(escalate_test)


# send escalate message every 5 seconds
test_escalate()

FakeCroft.run()


# Expected output

# Mid2
"""
INFO - Received escalate message at: tcp4:0.0.0.0:20001:MASTER
DEBUG - ROUTE: [{'source': 'tcp4:127.0.0.1:39742', 'targets': ['tcp4:0.0.0.0:20001']}]
DEBUG - PAYLOAD: {'ping': 'pong'}
"""

# Master
"""
INFO - Received escalate message at: tcp4:0.0.0.0:10000:MASTER
DEBUG - ROUTE: [{'source': 'tcp4:127.0.0.1:39742', 'targets': ['tcp4:0.0.0.0:20001']}, {'source': 'tcp4:127.0.0.1:58498', 'targets': ['tcp4:0.0.0.0:10000']}]
DEBUG - PAYLOAD: {'ping': 'pong'}
"""
