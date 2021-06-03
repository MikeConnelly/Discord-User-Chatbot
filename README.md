A chatbot that trains itself on a user's discord messages

TODO: Turn the chatbot into a discord bot

## Setup
Create a config.ini file with the following options:
```ini
[DEFAULT]
User = 123456789  # REQUIRED - Your target user ID
Data = ./data
Randomness = 1
Elasticsearch = localhost:9200
```

Create a data directory to store you exported discord messages.
To export discord channels use this [exporter](https://github.com/Tyrrrz/DiscordChatExporter) and select JSON.

## Running

This code basically follows this guide on chatbots:

https://towardsdatascience.com/how-to-build-an-easy-quick-and-essentially-useless-chatbot-using-your-own-text-messages-f2cb8b84c11d

Using option 1 actually relates messages with responses, but is kinda boring for a chatbot
For this option you need to download and run [elasticsearch](https://www.elastic.co/)

option 2 seems to give responses at random, which is bad for chatting but kinda fun

