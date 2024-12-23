# voice_packet_reader_discord_bot

## Overview
`voice_packet_reader_discord_bot` is a Discord bot designed to facilitate quiz games by reading voice packets and managing game sessions. The bot allows users to select categories and difficulties for quiz questions, join voice channels, and interact with the bot through various commands.

## Features
- **Category and Difficulty Selection**: Users can select categories and difficulties for quiz questions.
- **Voice Channel Integration**: The bot can join voice channels and interact with users through voice commands.
- **Game Management**: The bot manages game sessions, including starting and stopping games, handling user interactions, and providing feedback.

## Commands
- `!playGame <category> <difficulty>`: Starts a new game with the specified category and difficulty.
- `!start`: Starts the game.
- `!buzz`: Buzzes in to answer a question.
- `!answer <answer>`: Submits an answer to the current question.
- `!nextTossup`: Moves to the next tossup question.
- `!shutdown`: Shuts down the bot.

## Adding the Bot to Your Server
1. **Invite the Bot**: Use the following link to invite the bot to your Discord server. Make sure you have the necessary permissions to add bots to the server.
    ```markdown
    [Invite Link](https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=YOUR_PERMISSIONS)
    ```
    Replace `YOUR_CLIENT_ID` with the bot's client ID and `YOUR_PERMISSIONS` with the required permissions.

2. **Authorize the Bot**: Follow the prompts to authorize the bot and add it to your server.

3. **Configure the Bot**: Once the bot is added to your server, you can configure it using the available commands.

## Usage
1. **Start a Game**: Use the `!playGame <category> <difficulty>` command to start a new game with the specified category and difficulty.
2. **Interact with the Bot**: Use the available commands to interact with the bot and manage the game session.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements
- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper.
- All contributors and users for their support and feedback.
