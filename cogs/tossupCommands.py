import logging
from typing import Dict
import discord
import discord.ext.commands as commands

from tossup import TossupGame
from util.catsAndDiffSetup import GameSetupView
from util.text import TEXT
from util.utils import create_embed

class TossupCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot = bot
        self.concurrentTossups: Dict[tuple, TossupGame] = {}
        self.setup: Dict[tuple, bool] = {}
        
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return
        
        logging.info(f"[{message.channel}][{message.author}]: {message.content}")

        game_key = (message.guild.id, message.channel.id)

        #process buzzes & answers
        if game_key in self.setup and self.setup[game_key]:
            pass
        elif game_key in self.concurrentTossups and not self.concurrentTossups[game_key].questionEnd:
            game = self.concurrentTossups[game_key]
            if message.content == 'buzz':
                if not await TossupCommands.isPlayerInGame(message, game):
                    return
                elif game.buzzedIn:
                    await message.channel.send(embed=create_embed('Error', TEXT["error"]["cannot_buzz"]))
                else:
                    await game.pauseTossup(message)
                    await message.channel.send(embed=create_embed('Buzzed In', TEXT["game"]["buzzed_in"].format(user=message.author.display_name)))
            
            elif game.buzzedIn:
                if not await TossupCommands.isPlayerInGame(message, game):
                    return
                
                if game.buzzedInBy != message.author.id:
                    await message.channel.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
                else:
                    await TossupCommands.getAnswer(message, message.content, game)

    #Game loop commands
    @commands.command(help=TEXT["help"][0])
    async def play(self, ctx: commands.Context) -> None:
        logging.info(f"{ctx.author} invoked play")
    
        if not ctx.author.voice or not ctx.author.voice.channel:
            logging.warning(f"{ctx.author} tried to start a game without joining a voice channel.")
            await ctx.send(embed=create_embed('Error', TEXT["error"]["no_voice_channel"]))
            return
        
        view = GameSetupView(ctx)

        await ctx.send(embed=create_embed('Game Setup', TEXT["game"]["instructions"]),view=view)
        await view.wait()

        #await ctx.send(embed=create_embed('Game Setup', view.categories +"\n" + view.difficulties))

        await TossupCommands.initializeGame(ctx, self.concurrentTossups, view.categories, view.difficulties)

    @commands.command(help=TEXT["help"][2])
    async def start(self, ctx: commands.Context) -> None:
        logging.info(f"{ctx.author} invoked start command in {ctx.channel.name}")
        
        game_key = (ctx.guild.id, ctx.channel.id)
        
        if not await TossupCommands.isGameActive(ctx.message, self.concurrentTossups):
            return
        
        game = self.concurrentTossups[game_key]

        if not await TossupCommands.isPlayerInGame(ctx.message, game):
            return
        
        if ctx.guild != game.guild or ctx.channel != game.textChannel:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["wrong_channel"].format(channel=self.concurrentTossups[(ctx.guild.id, ctx.channel.id)].textChannel.name)))
        elif game.gameStart:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["already_started"]))
        else:
            await ctx.send(embed=create_embed('Reading Tossup', TEXT["game"]["reading_tossup"]))
            await game.playTossup(ctx)

    @commands.command(help=TEXT["help"][5])
    async def next(self, ctx: commands.Context) -> None:
        logging.info(f"{ctx.author} invoked next command in {ctx.channel.name}")

        game_key = (ctx.guild.id, ctx.channel.id)
        
        if not await TossupCommands.isGameActive(ctx.message, self.concurrentTossups):
            return
        
        game = self.concurrentTossups[game_key]

        if not game.gameStart:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            return

        if not await TossupCommands.isPlayerInGame(ctx.message, game):
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

    @commands.command(help=TEXT["help"][8])
    async def end(self, ctx: commands.Context) -> None:

        game_key = (ctx.guild.id, ctx.channel.id)
        
        if not await TossupCommands.isGameActive(ctx.message, self.concurrentTossups):
            logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
            return
        
        game = self.concurrentTossups[game_key]

        if not game.gameStart:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
            return

        if not await TossupCommands.isPlayerInGame(ctx.message, game):
            logging.warning(f"{ctx.author.display_name} tried to end a game without joining in {ctx.channel.name}.")
            return
        
        # if game.buzzedIn:
        #     await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
        #     logging.warning(f"{ctx.author} attempted to end a game while a tossup was being answered in {ctx.channel.name}.")
        #     return
        
        await TossupCommands.getscores(self, ctx)
        await TossupCommands.getinfo(self, ctx)
        game.gameStart = False
        await game.stopTossup(ctx.channel)
        await ctx.voice_client.disconnect()
        logging.info(f"Game successfully ended in {ctx.channel.name} for guild {ctx.guild.name}.")


    #Non game loop commands
    @commands.command(help=TEXT["help"][1])
    async def add(self, ctx: commands.Context) -> None:
        if (ctx.guild.id, ctx.channel.id) not in self.concurrentTossups:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["game_not_started"]))
        else:
            if await self.concurrentTossups[(ctx.guild.id, ctx.channel.id)].addPlayer(ctx.author):
                await ctx.send(embed=create_embed('Player Added', TEXT["game"]["player_added"].format(user=ctx.author.display_name)))
            else:
                await ctx.send(embed=create_embed('Error', TEXT["error"]["failed_to_add"]))

    @commands.command(help=TEXT["help"][7])
    async def getinfo(self, ctx: commands.Context) -> None:

        game_key = (ctx.guild.id, ctx.channel.id)
        
        if not await TossupCommands.isGameActive(ctx.message, self.concurrentTossups):
            logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
            return
        
        game = self.concurrentTossups[game_key]

        if not game.gameStart:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            logging.warning(f"{ctx.author} attempted to end a game that hasn't been started in {ctx.channel.name}.")
            return

        if not await TossupCommands.isPlayerInGame(ctx.message, game):
            logging.warning(f"{ctx.author.display_name} tried to end a game without joining in {ctx.channel.name}.")
            return

        tossupsHeard, categories, difficulties = await game.getCatsAndDiff(ctx)
        await ctx.send(embed=create_embed('Game Info', TEXT["game"]["game_info"].format(tossups=tossupsHeard, categories=categories, difficulties=difficulties)))

    @commands.command(help=TEXT["help"][6])
    async def getscores(self, ctx: commands.Context) -> None:
        logging.info(f"{ctx.author} invoked getscores command in {ctx.channel.name}")

        game_key = (ctx.guild.id, ctx.channel.id)
        
        if not await TossupCommands.isGameActive(ctx.message, self.concurrentTossups):
            return
        
        game = self.concurrentTossups[game_key]

        if not game.gameStart:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            return

        if not await TossupCommands.isPlayerInGame(ctx.message, game):
            return
        
        if game.buzzedIn:
            await ctx.send(embed=create_embed('Error', TEXT["error"]["cannot_use_command"]))
            return
        
        playerScores = await game.getScores(ctx)
        await ctx.send(embed=create_embed('Scores', TEXT["game"]["scores"].format(scores=playerScores)))

    #Helper Functions
    async def initializeGame(ctx: commands.Context, concurrentGames: dict[tuple, TossupGame], cats: str, diff: str) -> bool:
        try:
            game_key = (ctx.guild.id, ctx.channel.id)
            #print(game_key, game_key in concurrentGames)

            # if game_key in concurrentGames:
            #     print(concurrentGames[game_key].initalized)

            if game_key in concurrentGames and concurrentGames[game_key].gameStart:
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

    async def isGameActive(message: discord.Message, concurrentGames) -> bool:
        game_key = (message.guild.id, message.channel.id)
        if game_key not in concurrentGames:
            await message.channel.send(embed=create_embed('Error', TEXT["error"]["game_not_started"]))
            logging.warning(f"{message.author} tried to start a game that hasn't been created.")
            return False
        return True

    async def isPlayerInGame(message: discord.Message, game) -> bool:
        if not await game.checkForPlayer(message.author.id):
            await message.channel.send(embed=create_embed('Error', TEXT["error"]["not_joined"].format(user=message.author.display_name)))
            return False
        return True
    
    async def getAnswer(message: discord.Message, userAnswer: str, game: TossupGame) -> None:
        try:

            correctOrNot, correct = await game.checkAnswer(message.author.id, userAnswer)
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

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TossupCommands(bot))