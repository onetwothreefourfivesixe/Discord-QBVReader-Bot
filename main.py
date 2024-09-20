from typing import Final
import os
import discord
from dotenv import load_dotenv
from discord import *
from discord.ext import commands
from discord.ext.commands import Bot, Context
import responses
import logging
import forced_alignment as fa
from utils import Game, create_embed

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s][%(levelname)s][%(name)s][%(message)s]',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a'),
                              logging.StreamHandler()])

# Load environment variables
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

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
    
    "Displays the current scores of all players in the game one last time before ending the game.\n"
    "Limits: Cannot be called if a game has not been started yet."
]

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Activate Opus
opus.load_opus('bin\opus.dll')

# Game instance (Optional, because it can be None when no game is active)
game: Game = None

@bot.event
async def on_ready() -> None:
    logging.info(f'Logged in as {bot.user}')

async def send_message(message: discord.Message, userMessage: str) -> None:
    try:
        response = responses.get_response(message, userMessage)
        await message.channel.send(response)
        logging.info(f"Sent message: {response}")
    except Exception as e:
        logging.error(f'Error sending message: {e}')

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return
    logging.info(f"[{message.channel}][{message.author}]: {message.content}")
    if '!' in message.content:
        await bot.process_commands(message)
    else:
        await send_message(message, message.content)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see a list of available commands.")

@bot.command(help=helpText[0])
async def playGame(ctx: commands.Context, cats: str = '', diff: str = '') -> None:
    global game
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(embed=create_embed('Error', 'You are not connected to a voice channel.'))
        return
    voice_channel = ctx.author.voice.channel
    await voice_channel.connect()
    game = Game(cats=cats, diff=diff, guild=ctx.guild, textChannel=ctx.channel)
    await game.addPlayer(ctx.author)
    if not await game.createTossup():
        await ctx.send(embed=create_embed('Error', 'Something went wrong!'))
    else:
        await ctx.send(embed=create_embed('Game Initialized', 'Game started successfully! You have sucessfully initalized a game! Note, to start the game, type !start. To buzz on a question, type !buzz. To answer a question after buzzing, type !answer [your answer]. To add another player to the game, the user must type !addUser while a game is running to add themselves.'))
    logging.info(f'Game started in {ctx.guild}')

@bot.command(help=helpText[1])
async def addUser(ctx: commands.Context) -> None:
    global game
    if game is None:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    else:
        if await game.addPlayer(ctx.author):
            await ctx.send(embed=create_embed('Player Added', f'{ctx.author.display_name} has been added to the game!'))
        else:
            await ctx.send(embed=create_embed('Error', 'Failed to add player to the game.'))

@bot.command(help=helpText[2])
async def start(ctx: commands.Context) -> None:
    global game
    if game is None:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if ctx.guild != game.guild or ctx.channel != game.textChannel:
            await ctx.send(embed=create_embed('Error', f'Wrong channel! Use commands in {game.textChannel.name}.'))
        elif game.gameStart:
            await ctx.send(embed=create_embed('Error', 'The game has already started.'))
        else:
            await game.playTossup(ctx)

@bot.command(help=helpText[3])
async def buzz(ctx: commands.Context) -> None:
    global game
    if game is None or not game.gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if game.buzzedIn:
            await ctx.send(embed=create_embed('Error', 'You cannot buzz right now.'))
        else:
            await game.pauseTossup(ctx)
            await ctx.send(embed=create_embed('Buzzed In', f'{ctx.author.display_name} has buzzed in. Answer?'))

@bot.command(help=helpText[4])
async def answer(ctx: commands.Context, *, userAnswer: str = '') -> None:
    global game
    if game is None or not game.gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if not game.buzzedIn or game.buzzedInBy != ctx.author.id:
            await ctx.send(embed=create_embed('Error', 'You are not allowed to answer right now.'))
        else:
            correctOrNot, correct = await game.checkAnswer(ctx=ctx, answer=userAnswer)
            await ctx.send(embed=create_embed('Answer Submitted', f'You answered: {userAnswer}'))
            await ctx.send(embed=create_embed('Result', correctOrNot))
            if correct == 'accept':
                await game.stopTossup(ctx)
            else:
                await game.resumeTossup(ctx)

@bot.command(help=helpText[5])
async def nextTossup(ctx: commands.Context) -> None:
    global game
    if game is None or not game.gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    else:
        if game.tossupStart:
            await game.stopTossup(ctx)
        if not await game.createTossup():
            await ctx.send(embed=create_embed('Error', 'Something went wrong!'))
        else:
            await game.playTossup(ctx)

@bot.command(help=helpText[6])
async def getScores(ctx: commands.Context) -> None:
    global game
    if game is None or not game.gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    elif game.buzzedIn:
        await ctx.send(embed=create_embed('Error', 'A tossup is being answered right now.'))
    else:
        playerScores = await game.getScores(ctx)
        await ctx.send(embed=create_embed('Scores', f'Scores:\n{playerScores}'))

@bot.command(help=helpText[7])
async def endGame(ctx: commands.Context) -> None:
    global game
    if game is None or not game.gameStart:
        await ctx.send(embed=create_embed('Error', 'No game has been started yet.'))
    elif not await game.checkForPlayer(ctx):
        await ctx.send(embed=create_embed('Error', f'{ctx.author.display_name} has not joined the game.'))
    elif game.buzzedIn:
        await ctx.send(embed=create_embed('Error', 'A tossup is being answered right now.'))
    else:
        playerScores = await game.getScores(ctx)
        print(game.gameStart)
        await ctx.send(embed=create_embed('Final Scores', playerScores))
        print(game.gameStart)
        game.gameStart = False
        print(game.gameStart)
        await game.stopTossup(ctx)
        await ctx.voice_client.disconnect()

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
