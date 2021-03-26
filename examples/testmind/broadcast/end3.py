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

FakeCroft = FakeMycroft(30002)
FakeCroft.connect(20001)


def test_broadcast():
    msg = HiveMessage(msg_type=HiveMessageType.THIRDPRTY,
                      payload={"ping": "END3"})
    print(msg)

    def broadcast_test():
        while True:
            sleep(5)
            print("\nTESTING BROADCAST FROM end3\n")
            FakeCroft.interface.broadcast(msg)

    create_daemon(broadcast_test)


# send broadcast message every 5 seconds
test_broadcast()

FakeCroft.run()


# Expected output - Nothing
