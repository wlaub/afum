import os, sys
import time

from enum import Enum

import watchdog.events
import watchdog.observers

import config


class State(Enum):
    IDLE=1
    RECORDING=2
    FINALIZING=3


class EventHandler(watchdog.events.FileSystemEventHandler):

    pending_exts = ['.pcm'];
    complete_exts = ['.wav', '.mp3', '.ogg']

    def __init__(self, patch_dir):
        super().__init__()

        self.patch_dir = patch_dir
        self.state = State.IDLE
        self.recording_base = None    
        self.recording_path = None

        self.find_patch('')


    def find_patch(self, path):
        """
        Either find the patch file matching the name in the recording path
        or return the most recently modified patch file.
        """
        files = os.listdir(self.patch_dir)
        files = filter(lambda x: x[-4:]=='.vcv', files)
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(self.patch_dir, x)), reverse=True)

        for filename in files:
            base, _ = os.path.splitext(filename)
            if base in path:
                return os.path.join(self.patch_dir,filename)

        print(f'Warning: No patch file matches recording path {path}. Falling back to most recent.') 
        filename = os.path.join(self.patch_dir,files[0])

        thresh = 600
        age = time.time() - os.path.getmtime(filename)
        if age > thresh:
            print(f'Warning: most recent patch file {filename} is {age} s old.')

        return filename

    def start_watching(self, path):
        self.recording_path = path
        self.recording_base, _ = os.path.splitext(path)
        self.state = State.RECORDING

        patchname = self.find_patch(path)

        #Save the time
        #Commit patch repo
        #Identify the patch and extract metadatas
        #Create file upload object
        #Copy attachments to intermediate location

        print(f'Started watching pending recording: {self.recording_path}')
        print(f'Using patch file {patchname}')

    def finish_watching(self, path):
        print(f'Detected completed recording: {path}')
        #Check recording length
        #Push repos
        #Finalize upload object and copy temp folder over to uploads directory
        #Delete temp folder
        self.state = State.IDLE
        self.recording_base = None    
        self.recording_path = None

    def abort_watching(self, path):
        #undo commit
        self.state = State.IDLE
        self.recording_base = None    
        self.recording_path = None

    def on_created(self, event):
        super().on_created(event)
        print(f'Event: {event}')

        path = event.src_path
        base, ext = os.path.splitext(path)
        
        if self.state in [State.IDLE, State.FINALIZING]:
            if ext in self.pending_exts:
                self.start_watching(path)
        elif self.state in [State.RECORDING, State.FINALIZING]:
            if base == self.recording_base:
                self.finish_watching(path)



    def on_deleted(self, event):
        super().on_deleted(event)
        print(f'Event: {event}')

        if self.state == State.RECORDING:
            path = event.src_path()
            if path == self.recording_path:
                self.state = State.FINALIZING



rec_path = '/media/wlaub/Archive/Patches'
patch_dir = '/home/wlaub/.Rack/patches'

handler = EventHandler(patch_dir)
obs = watchdog.observers.Observer()
obs.schedule(handler, rec_path)

obs.start()

try:
    while obs.isAlive():
        obs.join(1)
except KeyboardInterrupt:
    obs.stop()

obs.join()

