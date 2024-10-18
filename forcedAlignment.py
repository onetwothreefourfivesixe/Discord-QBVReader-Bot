# coding=utf-8
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from aeneas.language import Language
from aeneas.syncmap import SyncMapFormat
from aeneas.task import TaskConfiguration
from aeneas.textfile import TextFileFormat
import aeneas.globalconstants as gc
import fetchQuestions as mc
import pandas as pd

async def generateSyncMap(audio_file_path="temp/audio.mp3", text_file_path="temp/myFile.txt", sync_map_file_path="temp/syncmap.json", question_numbers='', subjects='', reading_speed=1.0, guildId=0, channelId=0):
    '''
    Generates a synchronized map file for the provided audio and text files, based on fetched question content and reading speed.

    Args:
        audio_file_path (str): The path to the audio file.
        text_file_path (str): The path to the text file.
        sync_map_file_path (str): The path to save the synchronized map file.
        question_numbers (str): Comma-separated question numbers to fetch.
        subjects (str): Comma-separated subjects to fetch questions from.
        reading_speed (float): The speed at which the text is read.

    Returns:
        None
    '''
    try:
        # Fetch and save the audio file
        tossup, answer, displayAnswer = mc.fetchQuestion(question_numbers, subjects)
        mc.saveSpeaking(tossup, reading_speed, text_file_path, audio_file_path)
        
        # Configure task
        config = TaskConfiguration()
        config[gc.PPN_TASK_LANGUAGE] = Language.ENG
        config[gc.PPN_TASK_IS_TEXT_FILE_FORMAT] = TextFileFormat.PLAIN
        config[gc.PPN_TASK_OS_FILE_FORMAT] = SyncMapFormat.JSON
        task = Task()
        task.configuration = config
        
        # Set file paths
        task.audio_file_path_absolute = audio_file_path
        task.text_file_path_absolute = text_file_path
        task.sync_map_file_path_absolute = sync_map_file_path

        # Process task
        ExecuteTask(task).execute()

        # Print produced sync map
        task.output_sync_map_file()

        with open(f"temp/{guildId}-{channelId}answer.txt", "w", encoding="utf-8") as answerFile:
            answerFile.write(answer + '\n')
            answerFile.write(displayAnswer)
            return True
    except Exception as e:
        print(f"Error occurred: {e}")
        return False