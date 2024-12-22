from typing import List
import discord

import discord.ext
from discord.ext.commands import Context
from util.player import Player
from util.timers import PausableTimer

class BaseGame:

    def __init__(self, guild: discord.Guild=None, textChannel: discord.TextChannel=None, cats:str='', diff:str=''):

        self.guild = guild
        self.textChannel = textChannel
        self.players: List[Player] = []
        self.timer = PausableTimer()

        catsDict = {
            'hist': 'History',
            'lit': 'Literature',
            'sci': 'Science',
            'geo': 'Geography',
            'myth': 'Mythology',
            'fa': 'Fine Arts',
            'phil': 'Philosophy',
            'tr': 'Trash',
            'rel': 'Religion',
            'ss': 'Social Science',
            '': '',
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

    async def getScores(self, ctx: Context):
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