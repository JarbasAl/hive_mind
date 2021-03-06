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


FakeCroft = FakeMycroft(10000)
FakeCroft.start_listener()


def test_escalate():
    msg = HiveMessage(msg_type=HiveMessageType.THIRDPRTY,
                      payload={"ping": "pong"})

    def escalate_test():
        while True:
            sleep(5)
            print("\nTESTING escalate FROM MASTER\n")
            FakeCroft.interface.escalate(msg)

    create_daemon(escalate_test)


# send escalate message every 5 seconds
test_escalate()

FakeCroft.run()


# Expected output - Nothing
