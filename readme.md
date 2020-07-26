# HiveMind

Check [examples](./examples) for setup

- run add_keys to add authorized connection
- run mycroft_master in mycroft device

![](./hivemind.png)

## Terminals

- [Remote Cli](https://github.com/OpenJarbas/HiveMind-cli)
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


### Mesh Networking

The glocal mycroft bus

Red - original message

Yellow - reply message

#### Broadcast

Propagate message to all slaves

![](./data_flow/broadcast.gif)

#### Propagate

Send message to all slaves and masters

![](./data_flow/propagate.gif)

#### Escalate

Send message up the authority chain, never to a slave

![](./data_flow/escalate.gif)

