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


def test_broadcast():
    msg = HiveMessage(msg_type=HiveMessageType.THIRDPRTY,
                      payload={"ping": "MID2"})
    print(msg)

    def broadcast_test():
        while True:
            sleep(5)
            print("\nTESTING BROADCAST FROM Mid2\n")
            FakeCroft.interface.broadcast(msg)

    create_daemon(broadcast_test)


# send broadcast message every 5 seconds
test_broadcast()

FakeCroft.run()


# Expected output


# End 3
# 16:15:36.151 - jarbas_hive_mind.slave.terminal:handle_broadcast_message:137 - INFO - Received broadcast message at: tcp4:0.0.0.0:20001:SLAVE
# 16:15:36.152 - jarbas_hive_mind.slave.terminal:handle_broadcast_message:138 - DEBUG - ROUTE: [{'source': 'tcp4:0.0.0.0:20001', 'targets': ['tcp4:127.0.0.1:36078', 'tcp4:127.0.0.1:36080']}, {'source': 'tcp4:0.0.0.0:20001', 'targets': ['tcp4:127.0.0.1:48152']}]
# 16:15:36.153 - jarbas_hive_mind.slave.terminal:handle_broadcast_message:139 - DEBUG - PAYLOAD: {'mid2': 'pong'}