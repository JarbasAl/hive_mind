from setuptools import setup

setup(
    name='jarbas_hive_mind',
    version='0.10.7',
    packages=['jarbas_hive_mind',
              'jarbas_hive_mind.master',
              'jarbas_hive_mind.slave',
              'jarbas_hive_mind.configuration',
              'jarbas_hive_mind.database',
              'jarbas_hive_mind.utils',
              'jarbas_hive_mind.discovery'],
    include_package_data=True,
    install_requires=["pyopenssl",
                      "service_identity",
                      "autobahn",
                      "twisted",
                      "ovos_utils>=0.0.1",
                      "json_database>=0.2.6",
                      "pycryptodome",
                      "zeroconf>=0.1.6",
                      "upnpclient>=0.0.8"],
    url='https://github.com/JarbasAl/hive_mind',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Mesh Networking utilities for mycroft core'
)
