<p align="center">
  <img src="./resources/logo/hivemind-512.png">
</p>

HiveMind is a community-developed superset or extension of [Mycroft](https://www.github.com/MycroftAI/mycroft-core), the open-source voice assistant.

With HiveMind, you can extend one (or more, but usually just one!) instance of Mycroft to as many devices as you want, including devices that can't ordinarily run Mycroft!

HiveMind's developers have successfully connected to Mycroft from a PinePhone, a 2009 MacBook, and a Raspberry Pi 0, among other devices. Mycroft itself usually runs on our desktop computers or our home servers, but you can use any Mycroft-branded device, or [OpenVoiceOS](https://github.com/OpenVoiceOS/), as your central unit.

# Stats:

| [![GitHub stars](https://img.shields.io/github/stars/OpenJarbas/HiveMind-core.svg)](https://github.com/OpenJarbas/HiveMind-core/stargazers)  | [![GitHub last commit](https://img.shields.io/github/last-commit/OpenJarbas/HiveMind-core.svg)](https://github.com/OpenJarbas/HiveMind-core/commits/dev) |
|:---:|:---:|
| Please :star: this repo if you find it useful| This shows when this repo was updated for the last time |
|[![License: Apache License 2.0](https://img.shields.io/crates/l/rustc-serialize.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)| [![contributions welcome](https://img.shields.io/badge/contributions-welcome-blue.svg?style=flat)](https://github.com/OpenJarbas/HiveMind-core/pulls) |
| I'm using the Apache License 2.0 which means commercial use is allowed | If you have any ideas, they're always welcome.  Either submit an issue or a PR! |
| [![Buy me a](https://img.shields.io/badge/BuyMeABeer-Paypal-blue.svg)](https://www.paypal.me/AnaIsabelFerreira) | [![Sponsor](https://img.shields.io/badge/SponsorDevelopment-Liberapay-blue.svg)](https://liberapay.com/jarbasAI/) |
| If you feel the need, now it's as easy as clicking this button!  | You can help sponsoring HiveMind continued development with recurring donations|

# Getting started

**NOTE:** Hivemind-core is also available as a Mycroft skill. You can use it *either* as a standalone program *or* as a Mycroft skill, but you can't run them both at the same time. During early development, testers are encouraged to choose this repository over the skill, as development takes place here.

---

At this moment development is in early stages, but mostly stable. Functionality is limited to basic questions and answers, but only because we haven't implemented the bit that lets Mycroft re-activate the mic to continue a discussion. 

Full tutorials will follow later. For now, you wanna do this:

1. Clone this repo onto the computer or device that's running Mycroft.
2. Note the scripts in the `examples` folder. These are enough to spin up your Hive and connect to Mycroft from another device.
3. Edit `examples/add_keys.py` to create names and keys for your devices. You can use HiveMind without encryption, but it's discouraged for security reasons.
4. Ensure Mycroft is running.
5. Run `examples/mycroft_master.py`. Your Hive is now running, and you're ready to connect. See below to find a client (ideally the Voice Satellite). You will need to know the hostname or IP address of the computer or device running Mycroft, and you'll also need the device name and key you created earlier.


The main configuration can be found at

    '~/.cache/json_database/HivemindCore.json'

![](./resources/hivemind.png)
![](./resources/hive.png)

## Terminals

- [Remote Cli](https://github.com/OpenJarbas/HiveMind-cli) **\<-- USE THIS FIRST**
- [Voice Satellite](https://github.com/OpenJarbas/HiveMind-voice-sat)
- [Flask Chatroom](https://github.com/OpenJarbas/HiveMind-flask-chatroom)
- [Webchat](https://github.com/OpenJarbas/HiveMind---Webchat-Terminal)
- [REST (https) Terminal]() - Coming soon
- [MQTT Terminal]() - Coming soon

## Bridges

- [Mattermost Bridge](https://github.com/OpenJarbas/HiveMind_mattermost_bridge)
- [HackChat Bridge](https://github.com/OpenJarbas/HiveMind-HackChatBridge)
- [Twitch Bridge](https://github.com/OpenJarbas/HiveMind-twitch-bridge)
- [Facebook Bridge]() - Coming soon
- [Twitter Bridge]() - Coming soon
- [MQTT Bridge]() - Coming soon

## Nodes

- [NodeRed](https://github.com/OpenJarbas/HiveMind-NodeRed)
- [Rendevouz Node]() - Coming soon
- [Flask Microservices Node]() - Coming soon


# Data flow

The hivemind can be seen as a global mycroft bus shared across devices

Bellow are some planned data flows and message types

Documentation coming soon

Red - original message

Yellow - reply message

#### Broadcast

propagate message to all slaves

![](./resources/data_flow/broadcast.gif)

#### Propagate

Send message to all slaves and masters

![](./resources/data_flow/propagate.gif)

#### Escalate

Send message up the authority chain, never to a slave

![](./resources/data_flow/escalate.gif)


# Credits

[JarbasAl](https://liberapay.com/jarbasAI/)

[AIIX](https://github.com/AIIX/) - hivemind logo
