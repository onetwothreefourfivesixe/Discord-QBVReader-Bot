from random import choice
from discord import Message
import fetchQuestions
import utils

async def processAnswer(message: Message, userInput: str, game: utils.Game) -> tuple[str, str]:
    return await game.checkAnswer(message.author.id, userInput)
        # return 'Buzzed In', f'{message.author.display_name} has buzzed in. Answer? Type !answer [your answer] to answer.'
    #return 'This was not a command. To use a command, type !help to see all commands. Also, you ' + choice(["smell.", "cringe."])