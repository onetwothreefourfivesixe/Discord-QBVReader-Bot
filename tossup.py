import asyncio
import json
import time
from typing import List
from util.baseGame import BaseGame
import util.forcedAlignment as fa
import util.fetchQuestions as fq
import discord.ext.commands
from discord.ext.commands import Context
import aiofiles
import logging
from pathlib import Path
from util.player import Player
from util.timers import PausableTimer, AudioTracker
from util.utils import create_embed

class TossupGame(BaseGame):
    '''
    Class representing a TossupGame instance for managing tossup reading functionalities.
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

        super().__init__(guild, textChannel, cats, diff)
        self.gameStart = False
        self.tossupStart = False
        self.questionEnd = True
        self.buzzedIn = False
        self.buzzedInBy = None

        self.playback_position = AudioTracker()
        self.buzzWordIndex = None
        self.tossup = ''

        self.DIRECTORY_PATH = f'temp/{self.guild.id}-{self.textChannel.id}'
        self.TOSSUP_PATH = '/tossup.txt'
        self.AUDIO_PATH = '/tossup.mp3'
        self.SYNCMAP_PATH = '/tossupSyncmap.json'
        self.ANSWER_PATH = '/tossupAnswer.txt'

        self.tossupsHeard = 0

        path = Path(self.DIRECTORY_PATH)

        path.mkdir(parents=True, exist_ok=True)
    
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

        completed = await fa.generateSyncMap(directory_path=self.DIRECTORY_PATH, audio_file_path=self.AUDIO_PATH, 
                                            text_file_path=self.TOSSUP_PATH,
                                            sync_map_file_path=self.SYNCMAP_PATH,
                                            answer_file_path=self.ANSWER_PATH, reading_speed=1.0,
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
            async with aiofiles.open(f'{self.DIRECTORY_PATH}{self.SYNCMAP_PATH}', mode='r') as f:
                data = json.loads(await f.read())

            # Check if playback_position falls within any power mark ranges
            for i, fragment in enumerate(data['fragments']):
                begin = float(fragment['begin'])
                end = float(fragment['end'])
                if begin <= playback_position <= end:
                    self.buzzWordIndex = i
                    return '*' in fragment['lines']  # Check if power mark is present

            return False

        correct = await fq.checkAnswer(answer, f'{self.DIRECTORY_PATH}{self.ANSWER_PATH}')
        msg = ""
        if correct == 'accept':
            for i in range(len(self.players)):
                if self.players[i].id == authorID:
                    if await checkPowerMark(buzzInTime):
                        self.players[i].addPower()
                    self.players[i].addTen()
                    break
            msg = 'You are correct!'
        elif correct == 'prompt':
            msg = 'Your answer is close. Prompt?'

        elif correct == 'reject':
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

        audio_source = discord.FFmpegPCMAudio(f'{self.DIRECTORY_PATH}{self.AUDIO_PATH}')
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

        self.buzzedIn = False
        self.tossupStart = False
        self.questionEnd = True
        self.timer.stop()
        logging.info('Tossup ended')
        self.guild.voice_client.stop()

        if self.gameStart:
            async with aiofiles.open(f'{self.DIRECTORY_PATH}{self.TOSSUP_PATH}', 'r', encoding='utf-8') as tossup:
                real_tossup = ''
                if self.buzzWordIndex is not None:
                    splitTossup = await tossup.readlines()
                    splitTossup.insert(self.buzzWordIndex, '(#)')
                    real_tossup = ' '.join(splitTossup).replace('\n', ' ')
                else:
                    real_tossup = (await tossup.read()).replace('\n', ' ')
            
            async with aiofiles.open(f'{self.DIRECTORY_PATH}{self.ANSWER_PATH}', 'r', encoding='utf-8') as answers:
                file = await answers.readlines()
                answerLine = file[1].replace('\n', '')
                displayAnswer = answerLine.strip().replace('<b>', '**').replace('</b>', '**').replace('<u>', '__').replace('</u>', '__')
                    
            await channel.send(embed=create_embed('Tossup', f'{real_tossup}'))
            await channel.send(embed=create_embed('Answer', f'{displayAnswer}\n\nTo get the next tossup, type !next'))
        else:
            self.initalized = False
            await channel.send('Game Ended.')