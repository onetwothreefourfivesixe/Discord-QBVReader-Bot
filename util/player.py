from discord.ext.commands import Context

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