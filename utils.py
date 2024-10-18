import asyncio
import json
import time
from typing import List
import forcedAlignment as fa
import fetchQuestions as fq
import discord.ext.commands
from discord.ext.commands import Context
import aiofiles
import logging

class TossupGame:
    '''Class representing a TossupGame instance for managing tossup reading functionalities.
        Attributes:
            guild (Guild): The Discord guild where the game is taking place.
            textChannel (TextChannel): The text channel for communication.
            cats (str): Categories for the game questions.
            diff (str): Difficulty level for the questions.
            players (List[Player]): List of players participating in the game.
            timer (PausableTimer): Timer for managing game time.
            playback_position (AudioTracker): Tracker for audio playback position.
            buzzWordIndex (int): Index of the buzz word in the question.
            displayAnswer (str): Displayed answer for the current question.
            tossup (str): Current tossup question text.

        Methods:
            addPlayer (author: Context.author) -> bool: Add a player to the game.
            checkForPlayer (ctx: Context) -> bool: Check if a player is part of the game.
            checkAnswer (ctx: Context, answer: str) -> Tuple[str, str]: Check the answer provided by a player.
            createTossup () -> bool: Create a new tossup question.
            playTossup (ctx: Context) -> None: Start playing the tossup question.
            pauseTossup (ctx: Context) -> None: Pause the current tossup question.
            resumeTossup (ctx: Context) -> None: Resume the paused tossup question.
            stopTossup (ctx: Context) -> None: Stop the current tossup question.
            getScores (ctx: Context) -> str: Get scores of all players in the game.
            getCatsAndDiff (ctx: Context) -> Tuple[List[str], str]: Get the categories and difficulty level of the game questions.
        '''
    def __init__(self, guild: discord.Guild=None, textChannel: discord.TextChannel=None, cats:str='', diff:str=''):

        self.gameStart = False
        self.tossupStart = False
        self.questionEnd = True
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

        self.tossupsHeard = 0

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
        '''
        Add a player to the game.
        
        Parameters:
            author (Context.author): The author of the player being added.
        
        Returns:
            bool: True if the player is successfully added.
        '''

        self.players.append(Player(author))
        return True

    async def checkForPlayer(self, playerID: int):
        '''
        Check if a player with a specific ID is part of the game.

        Parameters:
            playerID (int): The ID of the player to check.

        Returns:
            bool: True if the player is found in the game, False otherwise.
        '''

        return any(playerID == part.id for part in self.players)
    
    async def getScores(self, ctx:Context):
        '''
        Get scores of all players in the game.

        Parameters:
            ctx (Context): The context of the command.

        Returns:
            str: A formatted string representing the scores of all players. 
        '''

        allPlayerScores = {}
        for player in self.players:
            allPlayerScores[player.name] = player.calcTotal()
        return str(allPlayerScores).replace(', ', '\n').replace(':', ' | ').replace('{', '').replace('}', '')
    
    async def getCatsAndDiff(self, ctx:Context):
        '''
        Get the number of tossups heard, categories, and difficulty level.

        Parameters:
            ctx (Context): The context of the command.

        Returns:
            Tuple[int, List[str], str]: The number of tossups heard, categories, and difficulty level.
        '''

        return self.tossupsHeard, self.categories, self.diff
    
    async def createTossup(self) -> bool:

        completed = await fa.generateSyncMap(audio_file_path=f'temp/{self.guild.id}-{self.textChannel.id}audio.mp3', 
                                            text_file_path=f'temp/{self.guild.id}-{self.textChannel.id}myFile.txt',
                                            sync_map_file_path=f'temp/{self.guild.id}-{self.textChannel.id}syncmap.json',
                                            guildId=self.guild.id, channelId=self.textChannel.id,
                                            subjects=str(self.categories), question_numbers=self.diff)

        return True if completed else False

    async def checkAnswer(self, authorID: int, answer: str):
        '''
    Check the provided answer against the correct answer retrieved from the API and update player scores accordingly.

    Parameters:
        authorID (int): The ID of the player providing the answer.
        answer (str): The answer provided by the player.

    Returns:
        tuple: A message indicating correctness and the status of the answer ('accept', 'reject', or 'prompt').
    '''

        self.buzzWordIndex = None
        self.playback_position.resumeAudio()
        buzzInTime = self.playback_position.getPlaybackPosition()

        async def checkPowerMark(playback_position: float) -> bool:
            # Load JSON file asynchronously
            async with aiofiles.open(f'temp/{self.guild.id}-{self.textChannel.id}syncmap.json', mode='r') as f:
                data = json.loads(await f.read())

            # Check if playback_position falls within any power mark ranges
            for i, fragment in enumerate(data['fragments']):
                begin = float(fragment['begin'])
                end = float(fragment['end'])
                if begin <= playback_position <= end:
                    self.buzzWordIndex = i
                    return '*' in fragment['lines']  # Check if power mark is present

            return False

        correct, self.displayAnswer = await fq.checkAnswer(answer, f'temp/{self.guild.id}-{self.textChannel.id}answer.txt')
        msg = ""
        if correct == 'accept':
            for i in range(len(self.players)):
                if self.players[i].id == authorID:
                    if await checkPowerMark(buzzInTime):
                        self.players[i].addPower()
                    self.players[i].addTen()
                    break
            msg = 'You are correct!'
        elif correct == 'reject' or correct == 'prompt':
            for i in range(len(self.players)):
                if self.players[i].id == authorID:
                    if self.tossupStart:
                        self.players[i].addNeg()
                    break
            msg = 'You are incorrect.'
        self.buzzedIn = False

        return msg, correct
    
    async def playTossup(self, ctx: Context):
        '''
        Start playing a tossup.

        Parameters:
            ctx (Context): The context of the command.

        Returns:
            None
        '''

        self.gameStart = True
        self.questionEnd = False
        self.timer.seconds_passed = 0
        self.timer.stopped = False
        self.tossupsHeard += 1

        async def trueTossupEnded(error):
            if error:
                logging.error(f'Error: {error}')
            else:
                logging.info('Question finished')
            
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

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: self.guild.voice_client.play(audio_source, after=tossupEnded))
        except Exception as e:
            logging.error(f'Error during audio playback: {e}')
            await ctx.send(embed=create_embed('Error', 'Failed to play audio. Please try again.'))

    async def pauseTossup(self, ctx: discord.Message) -> None:
        '''
        Pause the current tossup.

        Parameters:
            ctx (discord.Message): The message context triggering the pause action.

        Returns:
            None
        '''

        self.buzzedIn = True
        self.buzzedInBy = ctx.author.id
        if not self.tossupStart and not self.questionEnd:
            self.timer.pause()
        if self.tossupStart:
            self.playback_position.pauseAudio()
        self.guild.voice_client.pause()

    async def resumeTossup(self) -> None:
        '''
        Resume the paused tossup question and resume the timer if the tossup has not started and the question has not ended. Then, resume the voice client for the guild.
        '''

        if not self.tossupStart and not self.questionEnd:
            self.timer.resume()
        self.guild.voice_client.resume()
    
    async def stopTossup(self, channel: discord.TextChannel) -> None:
        '''
        Ends the current tossup question.

        Parameters:
            channel (discord.TextChannel): The text channel where the tossup is being paused.

        Returns:
            None
        '''

        self.tossupStart = False
        self.questionEnd = True
        self.timer.stop()
        logging.info('Tossup ended')
        self.guild.voice_client.stop()

        if self.gameStart:
            async with aiofiles.open(f'temp/{self.guild.id}-{self.textChannel.id}myFile.txt', 'r', encoding='utf-8') as tossup:
                real_tossup = ''
                if self.buzzWordIndex is not None:
                    splitTossup = (await tossup.readlines())
                    splitTossup.insert(self.buzzWordIndex, '(#)')
                    real_tossup = ' '.join(splitTossup).replace('\n', ' ')
                else:
                    real_tossup = (await tossup.read()).replace('\n', ' ')
            await channel.send(embed=create_embed('Tossup', f'{real_tossup}'))
            await channel.send(embed=create_embed('Answer', f'{self.displayAnswer}\n\nTo get the next tossup, type !next'))
        else:
            await channel.send('Game Ended.')

class Player:
    '''
    Class representing a player in the game.

    Attributes:
        name (str): The display name of the player.
        id (int): The unique identifier of the player.
        tens (int): Number of tens scored by the player.
        powers (int): Number of powers scored by the player.
        negs (int): Number of negs received by the player.

    Methods:
        addTen(): Increment the number of tens scored by the player.
        addPower(): Increment the number of powers scored by the player.
        addNeg(): Increment the number of negs received by the player.
        calcTotal() -> int: Calculate the total score of the player based on tens, powers, and negs.
    '''

    def __init__(self, player: Context.author):
        
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
    '''
    Class representing a pausable timer for managing time durations.

    Attributes:
        paused (bool): Indicates if the timer is paused.
        seconds_passed (int): Number of seconds passed during the timer.
        stopped (bool): Indicates if the timer is stopped.

    Methods:
        start_timer(duration, ctx: Context, msg: str='Question Done') -> bool: Start the timer for a specified duration.
        pause(): Pause the timer.
        resume(): Resume the timer.
        stop(): Stop the timer.
    '''
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
    '''
    Class representing an audio tracker for managing playback positions and pausing/resuming audio.

    Methods:
        playAudio(): Start tracking audio playback.
        pauseAudio(): Pause the audio playback.
        resumeAudio(): Resume the paused audio playback.
        getPlaybackPosition() -> float: Get the current playback position in seconds.
        reset(): Reset the audio tracker to its initial state.
    '''
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
    '''Helper function to create a Discord embed.'''
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    return embed