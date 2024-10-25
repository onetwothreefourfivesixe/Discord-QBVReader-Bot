import asyncio
from typing import Final
from dotenv import load_dotenv
import os
import re
import requests 
from google.cloud import texttospeech
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Set the environment variable for Google credentials
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not credentials_path:
    raise Exception("Google Application Credentials not set in .env file.")
client = texttospeech.TextToSpeechClient()

def fetchQuestion(difficulties=None, categories=None):
    '''
    Fetches a random question from the QBReader API based on specified difficulties and categories.

    Args:
        difficulties (list): List of difficulty levels to filter the questions.
        categories (str): String of categories to filter the questions.

    Returns:
        tuple: A tuple containing the sanitized question and answer retrieved from the API.
    '''
    
    url = 'https://www.qbreader.org/api/random-tossup'
    categories = ''.join(char for char in categories if char not in [';', ':', '!', '*', '[', ']', '"', "'"])
    categories = categories.replace(', ', ',')
    print(categories, difficulties)
    # Prepare parameters
    params = {
        'difficulties': str(difficulties),
        'categories': str(categories),
        'number': 1,
        'minYear': 2014,
        'maxYear': 2024,
        'powermarkOnly': True,
        'standardOnly': True
    }

    # Make the GET request with params dictionary
    encoded_params = urllib.parse.urlencode(params, safe=",")
    response = requests.get(url, params=encoded_params)
    
    try:
        pattern = r'(\[.*?\]|\(".*?"\))'
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        tossup = data['tossups'][0]
        return re.sub(pattern, '', tossup['question_sanitized']), tossup['answer_sanitized'], tossup['answer']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def saveSpeaking(text="", speaking_speed=1.0, textPath='temp/myFile.txt', audioPath='temp/audio.mp3'):
    '''
    Generates speech from the given text and saves it as an MP3 file. Also writes the text content to a UTF-8 encoded file excluding sentences with quotes.

    Args:
        text (str): The text to convert to speech.
        speaking_speed (float): The speed of speech generation.

    Returns:
        str: The filename of the generated audio file.
    '''

    # Synthesize speech
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speaking_speed
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Write the audio content to a file
    with open(audioPath, "wb") as audio_file:
        audio_file.write(response.audio_content)
    print(f'Audio content written to file "{audioPath}"')

    # Write sentences to a text file
    with open(textPath, "w", encoding='utf-8') as output_file:
        output_file.writelines(sentence + "\n"for sentence in text.split())

    return audioPath

async def checkAnswer(answer: str='', answerPath='temp/answer.txt'):
    '''
    Makes an API requrest to the QBReader API to verify whether or not an answer is correct.

    Args:
        answer (str): The user's answer to the question.
        answerPath (str): The path to the file containing the answer.

    Returns:
        tuple: A tuple containing the sanitized question and answer retrieved from the API.
    '''

    url = 'https://www.qbreader.org/api/check-answer'
    with open(answerPath, 'r', encoding='utf-8') as answers:
        file = answers.readlines()
        answerLine = file[1].replace('\n', '')
        displayAnswer = answerLine.strip().replace('<b>', '**').replace('</b>', '**').replace('<u>', '__').replace('</u>', '__')
    params = {
        'answerline' : answerLine,
        'givenAnswer' : answer
    }
    encoded_params = urllib.parse.urlencode(params, safe=",")
    response = requests.get(url, params=encoded_params)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        correct = data['directive']
        print(correct)
        return correct, displayAnswer
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
