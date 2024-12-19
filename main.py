import asyncio
import time
from typing import Dict, Final
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import Bot, Context
from cogs import tossupCommands
import responses
import logging
import util.forcedAlignment as fa
from tossup import TossupGame
from util.text import TEXT
from util.utils import create_embed
from util.HelpCommands import HelpCommand

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

# Load environment variables
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

concurrentGames: Dict[tuple, TossupGame] = {}

# Initialize bot
bot = commands.AutoShardedBot(command_prefix="!", intents=intents, help_command=HelpCommand())

# discord.opus.load_opus('/usr/lib/aarch-linux-gnu/libopus.so') #/usr/lib/x86_64-linux-gnu/libopus.so
#discord.opus.load_opus('bin/opus.dll') #/usr/lib/x86_64-linux-gnu/libopus.so

@bot.event
async def on_ready() -> None:
    logging.info(f'Logged in as {bot.user} with Shard ID: {bot.shard_id}')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))
@bot.event
async def on_error(event, *args, **kwargs):
    if event == 'on_command_error':
        logging.error(f'Command error: {args[0]}')
    elif event == 'on_voice_state_update':
        logging.error('Rate limit hit!')

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.error(f"Error in command '{ctx.command}': {error}")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see a list of available commands.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


@bot.command()
@commands.is_owner()
async def isconnected(ctx: commands.Context) -> None:
    await ctx.send(embed=create_embed('Connected?', TEXT["game"]["connected"].format(status=str(ctx.voice_client.is_connected()))))

@bot.command()
@commands.is_owner()
async def shutdown(ctx: commands.Context) -> None:
    logging.info('Shutting down bot')
    await ctx.send(embed=create_embed('Shutdown', TEXT["game"]["shutdown"]))
    await bot.close()

# Run the bot
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            if filename == "tossupCommands.py":
                await bot.load_extension(f"cogs.{filename[:-3]}")  # Example value
            else:
                await bot.load_extension(f"cogs.{filename[:-3]}")

async def main() -> None:
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())