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

FakeCroft = FakeMycroft(30001)
FakeCroft.connect(20000)


def test_broadcast():
    def broadcast_test():
        while True:
            sleep(5)
            print("\nTESTING BROADCAST FROM end2\n")
            FakeCroft.interface.broadcast({"ping": "pong"})

    create_daemon(broadcast_test)


# send broadcast message every 5 seconds
test_broadcast()

FakeCroft.run()


# Expected output - Nothing
