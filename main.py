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

# Load environment variables
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

concurrentGames: Dict[tuple, TossupGame] = {}

# Centralized text storage


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
#discord.opus.load_opus('bin/opus.dll') #/usr/lib/x86_64-linux-gnu/libopus.so

@bot.event
async def on_ready() -> None:
    logging.info(f'Logged in as {bot.user} with Shard ID: {bot.shard_id}')

async def getAnswer(message: discord.Message, userAnswer: str, game: TossupGame) -> None:
    try:
        correctOrNot, correct = await responses.processAnswer(message, userAnswer, game)
        await message.channel.send(embed=create_embed('Answer Submitted', f'You answered: {userAnswer}'))
        await message.channel.send(embed=create_embed('Result', correctOrNot))
        if correct == 'accept':
            await game.stopTossup(message.channel)
        elif correct == 'prompt':
            pass
        elif correct == 'reject':
            await game.resumeTossup()
    except Exception as e:
        logging.error(f'Error sending message: {e}')

# Helper function to check if a game is active
async def isGameActive(message: discord.Message) -> bool:
    game_key = (message.guild.id, message.channel.id)
    if game_key not in concurrentGames:
        await message.channel.send(embed=create_embed('Error', TEXT["error"]["game_not_started"]))
        logging.warning(f"{message.author} tried to start a game that hasn't been created.")
        return False
    return True

# Helper function to check if a player is part of the game
async def isPlayerInGame(message: discord.Message, game: TossupGame) -> bool:
    if not await game.checkForPlayer(message.author.id):
        await message.channel.send(embed=create_embed('Error', TEXT["error"]["not_joined"].format(user=message.author.display_name)))
        return False
    return True

# Helper function to initialize a game
async def initializeGame(ctx: commands.Context, cats: str, diff: str) -> bool:
    try:
        game_key = (ctx.guild.id, ctx.channel.id)
        print(game_key, game_key in concurrentGames)

        if game_key in concurrentGames:
            print(concurrentGames[game_key].initalized)

        if game_key in concurrentGames and concurrentGames[game_key].initalized:
            await ctx.send(embed=create_embed('Error', TEXT['error']['already_started'] + ' Please end the current game first before trying again.'))
            return False
        
        voice_channel = ctx.author.voice.channel
        logging.info(f'Successfully found voice channel of user')
        try:
            voice_client = await voice_channel.connect(timeout=10)
            logging.info(f'Successfully connected to {ctx.author.voice.channel.name} in {ctx.guild.name}')
        except Exception as e:
            logging.error(f'Error connecting to voice channel: {e}')

        concurrentGames[game_key] = TossupGame(cats=cats, diff=diff, guild=ctx.guild, textChannel=ctx.channel)
        await concurrentGames[game_key].addPlayer(ctx.author)
        logging.info(f"Game created in {ctx.guild.name} at channel {ctx.channel.name}")
        
        if not await concurrentGames[game_key].createTossup():
            await ctx.send(embed=create_embed('Error', TEXT["error"]["something_wrong"]))
            concurrentGames.pop(game_key, None)
            logging.error(f"Failed to create tossup in {ctx.channel.name}")
            return False
        else:
            await ctx.send(embed=create_embed('Game Initialized', TEXT["game"]["initialized"]))
            logging.info(f"Game started successfully in {ctx.guild.name}, channel {ctx.channel.name}")
            return True
    except Exception as e:
        logging.error(f"Error while starting the game: {e}")
        await ctx.send(embed=create_embed('Error', TEXT["error"]["failed_to_start"]))
        return False

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return
    
    logging.info(f"[{message.channel}][{message.author}]: {message.content}")

    game_key = (message.guild.id, message.channel.id)

    if '!' in message.content:
        await bot.process_commands(message)

    #process buzzes & answers
    elif game_key in concurrentGames and concurrentGames[game_key].initalized and not concurrentGames[game_key].questionEnd:
        game = concurrentGames[game_key]

        if message.content == 'buzz':
            if not await isPlayerInGame(message, game):
                return
            elif game.buzzedIn:
                await message.channel.send(embed=create_embed('Error', TEXT["error"]["cannot_buzz"]))
            else:
                await game.pauseTossup(message)
                await message.channel.send(embed=create_embed('Buzzed In', TEXT["game"]["buzzed_in"].format(user=message.author.display_name)))
        
        elif game.buzzedIn:
            if not await isPlayerInGame(message, game):
                return
            
            if game.buzzedInBy != message.author.id:
                await message.channel.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            else:
                await getAnswer(message, message.content, game)

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

@bot.command(help=TEXT["help"][0])
async def play(ctx: commands.Context, cats: str = '', diff: str = '') -> None:
    logging.info(f"{ctx.author} invoked play with categories: {cats}, difficulty: {diff}")
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        logging.warning(f"{ctx.author} tried to start a game without joining a voice channel.")
        await ctx.send(embed=create_embed('Error', TEXT["error"]["no_voice_channel"]))
        return
    
    await initializeGame(ctx, cats, diff)

@bot.command(help=TEXT["help"][1])
async def add(ctx: commands.Context) -> None:
    if (ctx.guild.id, ctx.channel.id) not in concurrentGames:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["game_not_started"]))
    else:
        if await concurrentGames[(ctx.guild.id, ctx.channel.id)].addPlayer(ctx.author):
            await ctx.send(embed=create_embed('Player Added', TEXT["game"]["player_added"].format(user=ctx.author.display_name)))
        else:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["failed_to_add"]))

@bot.command(help=TEXT["help"][2])
async def start(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked start command in {ctx.channel.name}")
    
    game_key = (ctx.guild.id, ctx.channel.id)
    
    if not await isGameActive(ctx.message):
        return
    
    game = concurrentGames[game_key]

    if not await isPlayerInGame(ctx.message, game):
        return
    
    if ctx.guild != game.guild or ctx.channel != game.textChannel:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["wrong_channel"].format(channel=concurrentGames[(ctx.guild.id, ctx.channel.id)].textChannel.name)))
    elif concurrentGames[(ctx.guild.id, ctx.channel.id)].gameStart:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["already_started"]))
    else:
        await ctx.send(embed=create_embed('Reading Tossup', TEXT["game"]["reading_tossup"]))
        await game.playTossup(ctx)

@bot.command(help=TEXT["help"][5])
async def next(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked next command in {ctx.channel.name}")

    game_key = (ctx.guild.id, ctx.channel.id)
    
    if not await isGameActive(ctx.message):
        return
    
    game = concurrentGames[game_key]

    if not game.initalized:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        return

    if not await isPlayerInGame(ctx.message, game):
        return
    
    if game.buzzedIn:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        return
    
    if game.tossupStart:
        await game.stopTossup(ctx.channel)

    if not await game.createTossup():
        await ctx.send(embed=create_embed('Error', TEXT["error"]["something_wrong"]))
    else:
        await game.playTossup(ctx)

    await ctx.send(embed=create_embed('Reading Tossup', TEXT["game"]["reading_tossup"]))

@bot.command(help=TEXT["help"][6])
async def getscores(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked getscores command in {ctx.channel.name}")

    game_key = (ctx.guild.id, ctx.channel.id)
    
    if not await isGameActive(ctx.message):
        return
    
    game = concurrentGames[game_key]

    if not game.initalized:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        return

    if not await isPlayerInGame(ctx.message, game):
        return
    
    if game.buzzedIn:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        return
    
    playerScores = await concurrentGames[game_key].getScores(ctx)
    await ctx.send(embed=create_embed('Scores', TEXT["game"]["scores"].format(scores=playerScores)))

@bot.command(help=TEXT["help"][8])
async def end(ctx: commands.Context) -> None:

    game_key = (ctx.guild.id, ctx.channel.id)
    
    if not await isGameActive(ctx.message):
        logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
        return
    
    game = concurrentGames[game_key]

    if not game.gameStart:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
        return

    if not await isPlayerInGame(ctx.message, game):
        logging.warning(f"{ctx.author.display_name} tried to end a game without joining in {ctx.channel.name}.")
        return
    
    # if game.buzzedIn:
    #     await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
    #     logging.warning(f"{ctx.author} attempted to end a game while a tossup was being answered in {ctx.channel.name}.")
    #     return
    
    playerScores = await game.getScores(ctx)
    await ctx.send(embed=create_embed('Final Scores', TEXT["game"]["final_scores"].format(scores=playerScores)))
    logging.info(f"Game ended by {ctx.author} in {ctx.guild.name}, channel {ctx.channel.name}. Final Scores: {playerScores}")
    
    await getinfo(ctx)
    game.gameStart = False
    await game.stopTossup(ctx.channel)
    await ctx.voice_client.disconnect()
    logging.info(f"Game successfully ended in {ctx.channel.name} for guild {ctx.guild.name}.")

@bot.command(help=TEXT["help"][7])
async def getinfo(ctx: commands.Context) -> None:

    game_key = (ctx.guild.id, ctx.channel.id)
    
    if not await isGameActive(ctx.message):
        logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
        return
    
    game = concurrentGames[game_key]

    if not game.initalized:
        await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
        return

    if not await isPlayerInGame(ctx.message, game):
        logging.warning(f"{ctx.author.display_name} tried to end a game without joining in {ctx.channel.name}.")
        return

    tossupsHeard, categories, difficulties = await concurrentGames[(ctx.guild.id, ctx.channel.id)].getCatsAndDiff(ctx)
    await ctx.send(embed=create_embed('Game Info', TEXT["game"]["game_info"].format(tossups=tossupsHeard, categories=categories, difficulties=difficulties)))

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
def main() -> None:
    bot.run(TOKEN)

if __name__ == '__main__':
    main()