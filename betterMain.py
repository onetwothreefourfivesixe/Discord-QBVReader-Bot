import asyncio
import time
from typing import Dict, Final
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import Bot, Context
import responses
import logging
from util.baseGame import BaseGame
import util.forcedAlignment as fa
from tossup import TossupGame
from util.utils import create_embed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d][%(message)s]',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

concurrentGames: Dict[tuple, BaseGame] = {}

TEXT = {
    "help": [
        "Starts a new game in the voice channel. You must be connected to a voice channel.\nLimits: Only one game can be started at a time.",
        "Adds the user to the current game. The player must add themselves with this command.\nLimits: Cannot add users if the game has not started yet.",
        "Starts the tossup round of the game.\nLimits: Must be called in the correct channel and after players have joined the game.",
        "Buzz in to answer the current tossup question.\nLimits: Only the player who buzzed in can answer. Cannot buzz if a tossup is not active.",
        "Submit your answer to the current tossup question.\nLimits: Only the player who buzzed in can answer; the game must be active.",
        "Move to the next tossup question in the game.\nLimits: Must be called after a tossup has ended and only if the game is active.",
        "Displays the current scores of all players in the game.\nLimits: Cannot be called while a tossup is being answered or if the game hasn't started.",
        "Displays the current settings of the game (More to be added soon):\n\t- Categories: The current categories being read\n\t- Diffi: The current difficulties being read\nLimits: Cannot be called while a tossup is being answered or if the game hasn't started.",
        "Displays the current scores of all players in the game one last time before ending the game.\nLimits: Cannot be called if a game has not been started yet."
    ],
    "error": {
        "no_voice_channel": "You are not connected to a voice channel.",
        "not_joined": "{user} has not joined the game.",
        "wrong_channel": "Wrong channel! Use commands in {channel}.",
        "game_not_started": "No game has been started yet.",
        "already_started": "The game has already started.",
        "cannot_buzz": "You cannot buzz right now.",
        "buzzed_in": "A tossup is being answered right now.",
        "failed_to_start": "Failed to start the game.",
        "something_wrong": "Something went wrong! If this issue occurs again, please fill out this form: https://forms.gle/fLd6r4yZGRyaRDnw6",
        "cannot_use_command": "You are not allowed to use this command right now.",
        "failed_to_add": "Failed to add player to the game."
    },
    "game": {
        "initialized": "Game started successfully! You have successfully initialized a game! Note, to start the game, type !start. To buzz on a question, type 'buzz'. To answer a question after buzzing, type [your answer], with no commands. To add another player to the game, the user must type !add while a game is running to add themselves.",
        "reading_tossup": "Reading tossup.",
        "buzzed_in": "{user} has buzzed in. Answer?",
        "player_added": "{user} has been added to the game!",
        "scores": "Scores:\n{scores}",
        "final_scores": "Final Scores: {scores}",
        "game_info": "Number of Tossups read: {tossups}\nCategories: {categories}\nDifficulties: {difficulties}",
        "connected": "Connected? {status}",
        "shutdown": "Bot is shutting down..."
    }
}

# Initialize bot
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)

# Activate Opus
# discord.opus.load_opus('/usr/lib/aarch-linux-gnu/libopus.so') #/usr/lib/x86_64-linux-gnu/libopus.so
discord.opus.load_opus('bin/opus.dll') #/usr/lib/x86_64-linux-gnu/libopus.so

@bot.event
async def on_ready() -> None:
    retry_count = 0
    while bot.shard_id is None and retry_count < 5:
        await asyncio.sleep(1)
        retry_count += 1
    print(retry_count)
    logging.info(f'Logged in as {bot.user} with Shard ID: {bot.shard_id}')

