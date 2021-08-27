import os, sys
import time

import json
from enum import Enum
import datetime
import shutil

import watchdog.events
import watchdog.observers
import git

from dateutil.parser import parse as date_parse

import psutil

import audio_metadata as audiometa

import upload
import config

import boolparse

try:
    import pynotifier
    def notify(title, value, urgency="low"):
        n = pynotifier.Notification(
            title = title,
            description = value,
            app_name = 'vcvmon',
            duration = 2, #not that notify-osd cares
            urgency=urgency,
            )
        n.send()

except ImportError as e:
    print(f'Note: {e}')
    print(f'Notifications will not be displated')
    def notify(*args, **kwargs):
        pass

class State(Enum):
    IDLE=1
    RECORDING=2
    FINALIZING=3


class EventHandler(watchdog.events.FileSystemEventHandler):

    pending_exts = ['.pcm'];
    complete_exts = ['.wav', '.mp3', '.ogg']

    loud = True

    def __init__(self, patch_dir):
        super().__init__()

        self.patch_dir = patch_dir
        self.clear()

        self.patch_repo = git.Repo(config.VCV_PATCH_DIR)

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

    def get_commit_tag(self, uptime):
        prefix = 'AUTO'
        tname = time.strftime('%Y%m%d%H%M%S', time.localtime(uptime))
        name = f'{prefix}_{tname}'
        tags = [x.name for x in self.patch_repo.tags]
        hits = list(filter(lambda x: x.startswith(name), tags))
        if len(hits) == 0: return name
        idx = 1
        while f'{name}_{idx}' in hits:
            idx += 1
 
        newname = f'{name}_{idx}'

        print(f'Warning: commit tag {name} already exists. Using {newname}')
        return newname


    def start_watching(self, newpath):
        self.start_time = time.time()

        time.sleep(0.5) #give things time to settle

        recording_path = newpath
        recording_base, _ = os.path.splitext(newpath)
        recording_dir, recording_filename = os.path.split(newpath)

        self.patch_path = self.find_patch(newpath)
        print(f'Using patch file {self.patch_path}')
        patchdata = json.load(open(self.patch_path, 'r'))
        modules = patchdata['modules']
        metafiles = list(filter(lambda x: x['model'] == 'MetadataFiles', modules))
        metamains = list(filter(lambda x: x['model'] == 'MetadataMain', modules))
        if len(metamains) == 0:
            print(f'Error: No MetadataMain instance detected. Ignoring recording.')
            return

        metamain = metamains[0]
        if len(metamains) > 1:
            print(f'Warning: patch contains multiple MetadataMain instances. Using:')
            print(metamain)

        uname = time.strftime('%Y-%m-%d_%H%M%S', time.localtime(self.start_time))
        self.upload = upload.Upload(config.VCV_TEMP_DIR, uname)

        self.upload.prepare()

        #Load main metadata

        self.upload.data['desc'] = metamain['description']
        time_source = metamain['time_source']
        if time_source == 'trigger':
            uptime = metamain['trigger_time']
        elif time_source == 'override':
            uptime = date_parse(metamain['override_time']).timestamp()
        elif time_source == 'file':
            uptime = int(os.path.getctime(newpath))
        elif time_source == 'error':
            print(f'Warning: metadata time source was error. Defaulting to file creation time.')
            uptime = int(os.path.getctime(newpath))
        else:
            print(f'Warning: metadata time source {time_source} not recognized. Defaulting to file creation time.')
            uptime = int(os.path.getctime(newpath))

        self.upload.data['date'] = uptime

        #There's nothing for setting this in the module, but it will always be CC0
        self.upload.data['license'] = 8

        def split_tags(text):
            res = text.split(',')
            res = [x.strip() for x in res]
            return res

        self.upload.data['tags'] = split_tags(metamain['tags'])
        self.upload.data['authors'] = split_tags(metamain['authors'])

        self.upload.add_tag('vcv rack')

        #Commit and tag the patch file
        #Doing this before loading files metadata to ensure that other patch repo
        #Files all share the same commit, the patch file comes first
        commit_tag = self.get_commit_tag(self.upload.data['date'])
        
        index = self.patch_repo.index
        index.add([self.patch_path])
        self.newcommit = index.commit(f'Automated commit generated for pending recording file {recording_filename}')
        self.newtag = self.patch_repo.create_tag(commit_tag)

        self.upload.add_git(self.patch_path)

        #Load files metadata

        for fileinfo in metafiles:
            file_type = fileinfo['file_type']
            file_paths = fileinfo['files'].strip().split('\n')
            file_paths = map(lambda x: x.strip(), file_paths)
            file_paths = list(filter(lambda x: len(x) > 0, file_paths))
            if file_type == 'file':
                for path in file_paths:
                    self.upload.add_file(path, cache=True) 
            elif file_type == 'image':
                for path in file_paths:
                    self.upload.add_image(path, cache=True) 
            elif file_type == 'git':
                for path in file_paths:
                    try:
                        self.upload.add_git(path) 
                    except git.exc.InvalidGitRepositoryError as e:
                        print(f'Warning: {path} is not a valid git repo')
                        raise

        #Add tag-associated images
        tagparse = boolparse.TagAlgebra(self.upload.data['tags'])
        for expr, images in config.VCV_TAG_IMAGES.items():
            if tagparse.parse(expr, True):
                print(f'Automatically adding images for {expr}')
                for image in images:
                    self.upload.add_image(image, cache=True)
 
        #Commit patch repo
        #Identify the patch and extract metadatas
        #Create file upload object
        #Copy attachments to intermediate location

        self.recording_path = recording_path
        self.recording_base = recording_base

        self.state = State.RECORDING

        print(f'Started watching pending recording: {self.recording_path}')
        notify(f'Started watching', f'{self.recording_path}')

    def validate(self, newpath):
        try:
            metadata = audiometa.load(newpath)
            duration = metadata['streaminfo']['duration']
            if duration < config.VCV_MIN_LENGTH:
                print(f'Duration {duration:.1f} < {config.VCV_MIN_LENGTH} s for recording {newpath}. Not adding to queue.')
                return False
        except Exception as e:
            print(f'Failed to validate recording due to an exception: {e}')
            return False
        return True

    def wait_for_file(self, path):
        """
        Wait until there are no other processes touching a file.
        """
        delay = 0.25

        print(f'Waiting for file size to stop changing')
        last_size = os.path.getsize(path)
        time.sleep(delay)
        while os.path.getsize(path) != last_size:
            last_size = os.path.getsize(path)
            print(f'  ... {last_size}')
            time.sleep(delay)
        print(f'Finished waiting')

    def finish_watching(self, newpath):
        print(f'Detected completed recording: {newpath}')
        path_base, filename = os.path.split(newpath)

        self.wait_for_file(newpath)
#        time.sleep(0.5) #it needs some time to settle after being created

        self.upload.data['name'] = filename
        self.upload.set_recording(newpath, cache=True)

        self.upload.save(write_orig = True)

        #Validate the recording file
        if self.validate(self.upload.data['recording']):
            print(f'Moving upload package')
            new_dir = self.upload.move(config.UPLOAD_DIR)
            print(f'Pushing patches repository')
            try:
                origin = self.patch_repo.remote()
                origin.push()
                origin.push(self.newtag)
            except Exception as e:
                print(f'Error: Failed to push patches repo: {e}')        
            else:
                print(f'Finished generating upload package at {new_dir}') 
            #Push the patches repo

        print(f'Finished processing new recording {filename}')
        notify(f'Finished processing', f'new recording {filename}')
            
        self.clear() 

    def abort_watching(self, path):
        #undo commit
        self.clear()

    def clear(self):
        self.state = State.IDLE
        self.recording_base = None    
        self.recording_path = None
        self.newcommit = None
        self.newtag = None
        self.upload = None
       

    def on_created(self, event):
        super().on_created(event)
        if self.loud:
            print(f'Event: {event}')

        path = event.src_path
        base, ext = os.path.splitext(path)
        
        if self.state in [State.IDLE, State.FINALIZING]:
            if ext in self.pending_exts:
                try:
                    self.start_watching(path)
                except Exception as e:
                    print(f'Error: Failed to start watching because {e}')
                    notify(f"Error", f"Failed to start watching because {e}")
        elif self.state in [State.RECORDING, State.FINALIZING]:
            if base == self.recording_base:
                self.finish_watching(path)



    def on_deleted(self, event):
        super().on_deleted(event)
        if self.loud:
            print(f'Event: {event}')

        if self.state == State.RECORDING:
            path = event.src_path
            if path == self.recording_path:
                print(f'Warning: pending recording {path} vanished without creating a recognized recording file.')
                self.state = State.FINALIZING


handler = EventHandler(config.VCV_PATCH_DIR)
obs = watchdog.observers.Observer()
obs.schedule(handler, config.VCV_RECORD_DIR)

obs.start()

try:
    while obs.is_alive():
        obs.join(1)
except KeyboardInterrupt:
    obs.stop()

obs.join()

