import asyncio
import json
import time
from typing import List
import forced_alignment as fa
import fetchQuestions as fq
import discord.ext.commands
from discord import *
from discord.ext.commands import Context

class Game:
    def __init__(self, guild: Guild=None, textChannel: TextChannel=None, cats:str='', diff:str=''):

        self.gameStart = False
        self.tossupStart = False
        self.questionEnd = False
        self.buzzedIn = False
        self.buzzedInBy = None
        self.guild = guild
        self.textChannel = textChannel
        self.players: List[Player] = []
        self.timer = PausableTimer()

        self.playback_position = AudioTracker()
        self.buzzWordIndex = None
        self.displayAnswer = ''
        self.tossup = ''

        catsDict = {
            'hist' : 'History',
            'lit' : 'Literature',
            'sci' : 'Science',
            'geo' : 'Geography',
            'myth' : 'Mythology',
            'fa' : 'Fine Arts',
            'phil' : 'Philosophy',
            'tr' : 'Trash',
            'rel' : 'Religion',
            'ss' : 'Social Science',
            '' : '',
            'all' : ''
        }

        cats = cats.split(',')

        self.categories = []
        self.diff = diff

        for category in cats:
            if category not in catsDict:
                return False
            self.categories.append(catsDict[category])

    async def addPlayer(self, author: Context.author):
        self.players.append(Player(author))
        for part in self.players:
            print(part.name)
        return True

    async def checkForPlayer(self, ctx: Context):
        return any(ctx.author.id == part.id for part in self.players)

    async def checkAnswer(self, ctx: Context, answer: str):

        self.buzzWordIndex = None
        self.playback_position.resumeAudio()
        buzzInTime = self.playback_position.getPlaybackPosition()

        def checkPowerMark(playback_position: float) -> bool:
            # Load JSON file
            with open(f'temp/{self.guild.id}-{self.textChannel.id}syncmap.json') as f:
                data = json.load(f)

            # Check if playback_position falls within any power mark ranges
            for i, fragment in enumerate(data['fragments']):
                begin = float(fragment['begin'])
                end = float(fragment['end'])
                if begin <= playback_position <= end:
                    print(i)
                    self.buzzWordIndex = i
                    return '*' in fragment['lines']  # Check if power mark is present

            return False

        correct, self.displayAnswer = await fq.checkAnswer(answer,f'temp/{self.guild.id}-{self.textChannel.id}answer.txt')
        msg = ""
        if correct == 'accept':
            for i in range(len(self.players)):
                if self.players[i].id == ctx.author.id:
                    if checkPowerMark(buzzInTime):
                        self.players[i].addPower()
                    self.players[i].addTen()
                    break
            msg = 'You are correct!'
        # elif correct == 'prompt':
        #     msg = 'Please enter in a more specific answer.'
        elif correct == 'reject' or correct == 'prompt':
            for i in range(len(self.players)):
                if self.players[i].id == ctx.author.id:
                    if self.tossupStart:
                        self.players[i].addNeg()
                    break
            msg = 'You are incorrect.'
        self.buzzedIn = False

        return msg, correct

    async def createTossup(self):
        print(self.categories)
        print(self.diff)

        completed = fa.generate_sync_map(audio_file_path=f'temp/{self.guild.id}-{self.textChannel.id}audio.mp3', 
                                         text_file_path=f'temp/{self.guild.id}-{self.textChannel.id}myFile.txt',
                                         sync_map_file_path=f'temp/{self.guild.id}-{self.textChannel.id}syncmap.json',
                                         guildId=self.guild.id, channelId=self.textChannel.id,
                                         subjects=str(self.categories), question_numbers=self.diff)

        return True if completed else False
    
    async def playTossup(self, ctx: Context):
        self.gameStart = True
        self.questionEnd = False
        self.timer.seconds_passed = 0
        self.timer.stopped = False

        async def trueTossupEnded(error):
            if error:
                print(f'Error: {error}')
            else:
                print('Question finished')
            
            self.tossupStart = False
            self.playback_position.pauseAudio()
            # Wait for timer to complete
            if not self.questionEnd:
                await self.timer.start_timer(5, ctx)
                if not self.questionEnd:
                    await self.stopTossup(ctx)

        def tossupEnded(error):
            asyncio.run_coroutine_threadsafe(trueTossupEnded(error), ctx.bot.loop)

        audio_source = discord.FFmpegPCMAudio(f'temp/{self.guild.id}-{self.textChannel.id}audio.mp3')
        await asyncio.sleep(0.2)
        self.tossupStart = True

        self.playback_position.reset()
        self.playback_position.playAudio()
        ctx.voice_client.play(audio_source, after=tossupEnded)

    async def pauseTossup(self, ctx: Context):

        self.buzzedIn = True
        self.buzzedInBy = ctx.author.id
        if not self.tossupStart and not self.questionEnd:
            self.timer.pause()
        if self.tossupStart:
            print(self.playback_position.getPlaybackPosition())
            self.playback_position.pauseAudio()
        ctx.voice_client.pause()

    async def resumeTossup(self, ctx: Context):
        if not self.tossupStart and not self.questionEnd:
            self.timer.resume()
        ctx.voice_client.resume()
    
    async def stopTossup(self, ctx: Context):
        self.tossupStart = False
        self.questionEnd = True
        self.timer.stop()
        print('tossup ended')
        ctx.voice_client.stop()

        if self.gameStart:
            with open(f'temp/{self.guild.id}-{self.textChannel.id}myFile.txt', 'r', encoding='utf-8') as tossup:
                print('worked')
                real_tossup = ''
                if self.buzzWordIndex != None:
                    splitTossup = tossup.readlines()
                    splitTossup.insert(self.buzzWordIndex, '(#)')
                    real_tossup = ' '.join(splitTossup).replace('\n', ' ')
                else:
                    real_tossup = tossup.read().replace('\n', ' ')
            print('worked')
            await ctx.send(embed=create_embed('Tossup', f'{real_tossup}'))
            await ctx.send(embed=create_embed('Answer', f'{self.displayAnswer}\n\nTo get the next tossup, type !next'))
        else:
            await ctx.send('Game Ended.')

    async def getScores(self, ctx:Context):
        allPlayerScores = {}
        for player in self.players:
            allPlayerScores[player.name] = player.calcTotal()
        return str(allPlayerScores).replace(', ', '\n').replace(':', ' | ').replace('{', '').replace('}', '')
    
    async def getCatsAndDiff(self, ctx:Context):
        return self.categories, self.diff

class Player:
    
    def __init__(self, player:Context.author):
        
        self.name = player.display_name
        self.id = player.id

        self.tens = 0
        self.powers = 0
        self.negs = 0

    def addTen(self):
        self.tens += 1
    
    def addPower(self):
        self.powers += 1

    def addNeg(self):
        self.negs += 1

    def calcTotal(self):
        return self.tens * 10 + self.powers * 15 - self.negs * 5

class PausableTimer:
    def __init__(self):
        self.paused = False
        self.seconds_passed = 0
        self.stopped = False

    async def start_timer(self, duration, ctx: Context, msg: str='Question Done'):
        print("Timer started!")
        self.seconds_passed = 0  # Reset seconds passed
        while self.seconds_passed < duration:
            if self.stopped:
                print("Timer stopped prematurely.")
                return False  # Indicate that the timer was stopped early
            if self.paused:
                await asyncio.sleep(1)  # Check every second if still paused
            else:
                print(f"Timer: {self.seconds_passed} second(s)")
                await asyncio.sleep(1)  # Wait for 1 second
                self.seconds_passed += 1

        if not self.stopped and not self.paused:
            print("Timer finished!")
            #await ctx.send(msg)
            return True  # Indicate the timer finished successfully
        return False  # If stopped or paused

    def pause(self):
        self.paused = True
        print("Pausing timer...")

    def resume(self):
        self.paused = False
        print("Resuming timer...")
 
    def stop(self):
        self.stopped = True
        print("Stopping the timer...")

class AudioTracker:
    def __init__(self):
        self.start_time = None
        self.orginal_start_time = None
        self.paused_time = 0  # To accumulate paused time
        self.is_paused = False

    def playAudio(self):
        self.start_time = time.time()
        self.orginal_start_time = time.time()

    def pauseAudio(self):
        if not self.is_paused:
            self.start_time = time.time()
            self.is_paused = True

    def resumeAudio(self):
        if self.is_paused:
            self.paused_time += time.time() - self.start_time
            self.is_paused = False

    def getPlaybackPosition(self):
        if self.orginal_start_time is None:
            return 0
        
        current_time = time.time()
        elapsed_time = current_time - self.orginal_start_time - self.paused_time
        return elapsed_time
    
    def reset(self):
        self.start_time = None
        self.paused_time = 0  # To accumulate paused time
        self.is_paused = False

def create_embed(title: str, description: str) -> discord.Embed:
    """Helper function to create a Discord embed."""
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    return embed