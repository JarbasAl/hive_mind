from jarbas_hive_mind.discovery import LocalDiscovery
from jarbas_hive_mind import HiveMindConnection
from ovos_utils.log import LOG


def discover_hivemind(key="dummy_key",
                      name="HiveDummyNode"):
    headers = HiveMindConnection.get_headers(name, key)
    discovery = LocalDiscovery()
    discovery.search_and_connect(headers=headers)


if __name__ == '__main__':
    # TODO arg parse
    discover_hivemind()
