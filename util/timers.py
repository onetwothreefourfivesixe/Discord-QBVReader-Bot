import asyncio
import time
from discord.ext.commands import Context

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
                await asyncio.sleep(0.5)  # Check every second if still paused
            else:
                print(f"Timer: {self.seconds_passed} second(s)")
                await asyncio.sleep(0.5)  # Wait for 1 second
                self.seconds_passed += 0.5

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