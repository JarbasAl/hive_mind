from enum import Enum


class HiveMindNodeType(str, Enum):
    CANDIDATE_NODE = "candidate"  # potential node, if it manages to connect...
    NODE = "node"  # anything connected to the hivemind is a "node"
    MIND = "mind"  # listening for connections and providing mycroft-core
                   # (mycroft itself may be running in a different "mind")
    SLAVE = "slave"  # node that can be partially controlled by a "mind"
    TERMINAL = "terminal"  # user facing endpoint that connects to some Mind
                           # and does not itself accept connections
    BRIDGE = "bridge"  # connects some external service to the hive

    # RESERVED
    HIVE = "hive"  # a collection of nodes
    MASTER_MIND = "master"  # the top level node, not connected to anything
                            # but receiving connections

