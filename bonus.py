import asyncio
import json
import time
from typing import Dict, List
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

class BonusGame(BaseGame):

    def __init__(self, guild: discord.Guild=None, textChannel: discord.TextChannel=None, cats:str='', diff:str=''):

        super().__init__(self, guild, textChannel, cats, diff)
        self.gameStart = False
        self.tossupStart = False

        self.playback_position = AudioTracker()
        self.buzzWordIndex = None
        self.leadIn = ''
        self.bonusParts: Dict[str, str] = []

        self.DIRECTORY_PATH = f'temp/{self.guild.id}-{self.textChannel.id}'
        self.TOSSUP_PATH = '/bonus.txt'
        self.AUDIO_PATH = '/bonus.mp3'
        self.ANSWER_PATH = '/bonusAnswer.txt'

        self.bonusesHeard = 0

        path = Path(self.DIRECTORY_PATH)

        path.mkdir(parents=True, exist_ok=True)

    def createBonuses(self):
        self.leadIn, bonuses, answers = fq.fetchTossup(str(self.categories), self.diff)
        self.bonusParts = {bonuses[i] : answers[i] for i in range(len((bonuses)))}
        
    
    