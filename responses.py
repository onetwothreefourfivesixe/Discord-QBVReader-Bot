from random import choice
from discord import Message
import fetchQuestions

def get_response(message: Message, userInput: str) -> str:
    lowered: str = userInput.lower()
    return 'This was not a command. To use a command, type !help to see all commands. Also, you ' + choice(["smell.", "cringe."])