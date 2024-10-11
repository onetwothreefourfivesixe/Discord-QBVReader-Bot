import asyncio
import time
from typing import Dict, Final
import os
import discord
from dotenv import load_dotenv
from discord import *
from discord.ext import commands
from discord.ext.commands import Bot, Context
import responses
import logging
import forced_alignment as fa
from utils import TossupGame, create_embed

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

# Help text
helpText = [
    "Starts a new game in the voice channel. You must be connected to a voice channel.\n"
    "Limits: Only one game can be started at a time.",
    
    "Adds the user to the current game. The player must add themselves with this command.\n"
    "Limits: Cannot add users if the game has not started yet.",
    
    "Starts the tossup round of the game.\n"
    "Limits: Must be called in the correct channel and after players have joined the game.",
    
    "Buzz in to answer the current tossup question.\n"
    "Limits: Only the player who buzzed in can answer. Cannot buzz if a tossup is not active.",
    
    "Submit your answer to the current tossup question.\n"
    "Limits: Only the player who buzzed in can answer; the game must be active.",
    
    "Move to the next tossup question in the game.\n"
    "Limits: Must be called after a tossup has ended and only if the game is active.",
    
    "Displays the current scores of all players in the game.\n"
    "Limits: Cannot be called while a tossup is being answered or if the game hasn't started.",

    "Displays the current settings of the game (More to be added soon):\n"
    "\t- Categories: The current categories being read\n"
    "\t- Diffi: The current difficulties being read\n"
    "Limits: Cannot be called while a tossup is being answered or if the game hasn't started.",    

    "Displays the current scores of all players in the game one last time before ending the game.\n"
    "Limits: Cannot be called if a game has not been started yet."
]

# Initialize bot
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)
#bot = commands.Bot(command_prefix="!", intents=intents, shard_co)

# Activate Opus
# discord.opus.load_opus('bin/opus.dll') #/usr/lib/x86_64-linux-gnu/libopus.so

@bot.event
async def on_ready() -> None:
    retry_count = 0
    while bot.shard_id is None and retry_count < 5:
        await asyncio.sleep(1)
        retry_count += 1
    logging.info(f'Logged in as {bot.user} with Shard ID: {bot.shard_id}')

async def getAnswer(message: discord.Message, userAnswer: str, game: TossupGame) -> None:
    try:
        correctOrNot, correct = await responses.processAnswer(message, userAnswer, game)
        await message.channel.send(embed=create_embed('Answer Submitted', f'You answered: {userAnswer}'))
        await message.channel.send(embed=create_embed('Result', correctOrNot))
        if correct == 'accept':
            await game.stopTossup(message.channel)
        else:
            await game.resumeTossup()
        # await message.channel.send(response)
        #logging.info(f"Sent message: {response}")
    except Exception as e:
        logging.error(f'Error sending message: {e}')

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return
    
    logging.info(f"[{message.channel}][{message.author}]: {message.content}")

    if '!' in message.content:
        await bot.process_commands(message)

    elif (message.guild.id, message.channel.id) in concurrentGames and concurrentGames[(message.guild.id, message.channel.id)].buzzedIn:
        if not await concurrentGames[(message.guild.id, message.channel.id)].checkForPlayer(message.author.id):
            await message.channel.send(embed=create_embed('Error', f'{message.author.display_name} has not joined the game.'))

        else:
            if concurrentGames[(message.guild.id, message.channel.id)].buzzedInBy != message.author.id:
                await message.channel.send(embed=create_embed('Error', 'You are not allowed to answer right now.'))
            else:
                await getAnswer(message, message.content, concurrentGames[(message.guild.id, message.channel.id)])

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

@bot.command(help=helpText[0])
async def play(ctx: commands.Context, cats: str = '', diff: str = '') -> None:
    logging.info(f"{ctx.author} invoked play with categories: {cats}, difficulty: {diff}")
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        logging.warning(f"{ctx.author} tried to start a game without joining a voice channel.")
        await ctx.send(embed=create_embed('Error', 'You are not connected to a voice channel.'))
        return
    
    try:
        voice_channel = ctx.author.voice.channel
        logging.info(f'Sucessfully found voice channel of user')
        try:
            voice_client = await voice_channel.connect(timeout=10)
            logging.info(f'Successfully connected to {ctx.author.voice.channel.name} in {ctx.guild.name}')
        except Exception as e:
            logging.error(f'Error connecting to voice channel: {e}')

        if voice_client.channel:
            logging.info('The bot is connected to the voice channel.')
        else:
            logging.error('The bot failed to connect to the voice channel.')

        concurrentGames[(ctx.guild.id, ctx.channel.id)] = TossupGame(cats=cats, diff=diff, guild=ctx.guild, textChannel=ctx.channel)
        await concurrentGames[(ctx.guild.id, ctx.channel.id)].addPlayer(ctx.author)
        logging.info(f"Game created in {ctx.guild.name} at channel {ctx.channel.name}")
        
        if not await concurrentGames[(ctx.guild.id, ctx.channel.id)].createTossup():
            await ctx.send(embed=create_embed('Error', 'Something went wrong!'))
            logging.error(f"Failed to create tossup in {ctx.channel.name}")
        else:
            await ctx.send(embed=create_embed('Game Initialized', 'Game started successfully! You have sucessfully initalized a game! Note, to start the game, type !start. To buzz on a question, type !buzz. To answer a question after buzzing, type !answer [your answer]. To add another player to the game, the user must type !add while a game is running to add themselves.'))
            logging.info(f"Game started successfully in {ctx.guild.name}, channel {ctx.channel.name}")
    except Exception as e:
        logging.error(f"Error while starting the game: {e}")
        await ctx.send(embed=create_embed('Error', 'Failed to start the game.'))

@bot.command(help=helpText[2])
async def start(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked start command in {ctx.channel.name}")
    
    game_key = (ctx.guild.id, ctx.channel.id)
    if (ctx.guild.id, ctx.channel.id) not in concurrentGames:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
        logging.warning(f"{ctx.author} tried to start a game that hasn't been created.")
    elif not await concurrentGames[(ctx.guild.id, ctx.channel.id)].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if ctx.guild != concurrentGames[(ctx.guild.id, ctx.channel.id)].guild or ctx.channel != concurrentGames[(ctx.guild.id, ctx.channel.id)].textChannel:
            await ctx.send(embed=create_embed('Error', f'Wrong channel! Use commands in {concurrentGames[(ctx.guild.id, ctx.channel.id)].textChannel.name}.'))
        elif concurrentGames[(ctx.guild.id, ctx.channel.id)].gameStart:
            await ctx.send(embed=create_embed('Error', 'The game has already started.'))
        else:
            await ctx.send(embed=create_embed('Reading Tossup', 'Reading tossup.'))
            await concurrentGames[(ctx.guild.id, ctx.channel.id)].playTossup(ctx)

@bot.command(help=helpText[3])
async def buzz(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked buzz command in {ctx.channel.name}")

    game_key = (ctx.guild.id, ctx.channel.id)
    if concurrentGames[(ctx.guild.id, ctx.channel.id)] is None or not concurrentGames[(ctx.guild.id, ctx.channel.id)].gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await concurrentGames[(ctx.guild.id, ctx.channel.id)].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if concurrentGames[(ctx.guild.id, ctx.channel.id)].buzzedIn:
            await ctx.send(embed=create_embed('Error', 'You cannot buzz right now.'))
        else:
            await concurrentGames[(ctx.guild.id, ctx.channel.id)].pauseTossup(ctx)
            await ctx.send(embed=create_embed('Buzzed In', f'{ctx.author.display_name} has buzzed in. Answer?'))

@bot.command(help=helpText[5])
async def next(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked next command in {ctx.channel.name}")

    game_key = (ctx.guild.id, ctx.channel.id)
    if game_key not in concurrentGames or not concurrentGames[game_key].gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await concurrentGames[game_key].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    elif concurrentGames[game_key].buzzedIn:
        await ctx.send(embed=create_embed('Error', 'You are not allowed to use this command right now.'))
    else:
        if concurrentGames[game_key].tossupStart:
            await concurrentGames[game_key].stopTossup(ctx.channel)
        if not await concurrentGames[game_key].createTossup():
            await ctx.send(embed=create_embed('Error', 'Something went wrong!'))
        else:
            await concurrentGames[game_key].playTossup(ctx)
    await ctx.send(embed=create_embed('Reading Tossup', 'Reading the next tossup.'))

@bot.command(help=helpText[6])
async def getscores(ctx: commands.Context) -> None:
    logging.info(f"{ctx.author} invoked getscores command in {ctx.channel.name}")

    game_key = (ctx.guild.id, ctx.channel.id)
    if game_key not in concurrentGames or not concurrentGames[game_key].gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await concurrentGames[game_key].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    elif concurrentGames[game_key].buzzedIn:
        await ctx.send(embed=create_embed('Error', 'A tossup is being answered right now.'))
    else:
        playerScores = await concurrentGames[game_key].getScores(ctx)
        await ctx.send(embed=create_embed('Scores', f'Scores:\n{playerScores}'))

@bot.command(help=helpText[8])
async def end(ctx: commands.Context) -> None:
    game_key = (ctx.guild.id, ctx.channel.id)
    
    if game_key not in concurrentGames or not concurrentGames[game_key].gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
        logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
    elif not await concurrentGames[game_key].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
        logging.warning(f"{ctx.author.display_name} tried to end a game without joining in {ctx.channel.name}.")
    elif concurrentGames[game_key].buzzedIn:
        await ctx.send(embed=create_embed('Error', 'A tossup is being answered right now.'))
        logging.warning(f"{ctx.author} attempted to end a game while a tossup was being answered in {ctx.channel.name}.")
    else:
        playerScores = await concurrentGames[game_key].getScores(ctx)
        await ctx.send(embed=create_embed('Final Scores', playerScores))
        logging.info(f"Game ended by {ctx.author} in {ctx.guild.name}, channel {ctx.channel.name}. Final Scores: {playerScores}")
        
        await getinfo(ctx)
        concurrentGames[game_key].gameStart = False
        await concurrentGames[game_key].stopTossup(ctx.channel)
        await ctx.voice_client.disconnect()
        logging.info(f"Game successfully ended in {ctx.channel.name} for guild {ctx.guild.name}.")

# #Utility commands/methods
# async def checkGameStatus(ctx: commands.Context) -> bool:
#     game_key = (ctx.guild.id, ctx.channel.id)
    
#     if game_key not in concurrentGames or not concurrentGames[game_key].gameStart:
#         await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
#         return False
#     elif not await concurrentGames[game_key].checkForPlayer(ctx):
#         await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
#         return False
#     # elif concurrentGames[game_key].buzzedIn:
#     #     await ctx.send(embed=create_embed('Error', 'A tossup is being answered right now.'))
#     #     return False

#     return True

@bot.command(help=helpText[7])
async def getinfo(ctx: commands.Context) -> None:
    if (ctx.guild.id, ctx.channel.id) not in concurrentGames or not concurrentGames[(ctx.guild.id, ctx.channel.id)].gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await concurrentGames[(ctx.guild.id, ctx.channel.id)].checkForPlayer(ctx.author.id):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        tossupsHeard, categories, difficulties = await concurrentGames[(ctx.guild.id, ctx.channel.id)].getCatsAndDiff(ctx)
        await ctx.send(embed=create_embed('Game Info', f'Number of Tossups read: {tossupsHeard}\nCatagories: {categories}\nDifficulties: {difficulties}'))

@bot.command(help=helpText[1])
async def add(ctx: commands.Context) -> None:
    if (ctx.guild.id, ctx.channel.id) not in concurrentGames:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    else:
        if await concurrentGames[(ctx.guild.id, ctx.channel.id)].addPlayer(ctx.author):
            await ctx.send(embed=create_embed('Player Added', f'{ctx.author.display_name} has been added to the game!'))
        else:
            await ctx.send(embed=create_embed('Error', 'Failed to add player to the game.'))

@bot.command()
@commands.is_owner()
async def isconnected(ctx: commands.Context) -> None:
    #discord.VoiceClient
    await ctx.send(embed=create_embed('Connected?', str(ctx.voice_client.is_connected())))

@bot.command()
@commands.is_owner()
async def shutdown(ctx: commands.Context) -> None:
    logging.info('Shutting down bot')
    await ctx.send(embed=create_embed('Shutdown', 'Bot is shutting down...'))
    await bot.close()

# Run the bot
def main() -> None:
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
