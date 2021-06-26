import os
import time
import math

import shutil
import datetime
import threading

import webbrowser

import upload
import config
from tttweb.uploader.tttapi import TTTAPI
from tttweb.uploader import uploader
import secrets

import audio_metadata as audiometa

import PySimpleGUI as sg
import tkinter as tk
import tkfilebrowser as tkfb

import widgets
import layout
import audio

up = upload.Upload(config.UPLOAD_DIR, 'delete_me')

up.save()
"""
api = TTTAPI(config.UPLOAD_URL, (secrets.user, secrets.password))
res = api.get_name('prometheusIIrev01bringup_musescore_202102121736_1U.004.mp3')
print(res)

res = api.get_recording_name('prometheusIIrev01bringup_musescore_202102121736_1U.004.mp3')
print(res)
res = api.get_recording_name('xxx')
print(res)
"""


class App():

    DATEFMT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, upload_dir, upload_url, auth):
        self.upload_url = upload_url
        self.upload_dir = upload_dir
        self.auth = auth
        self.queue = {}

        self.get_queue()
        self.upload_sel = None
        
        self.audio = audio.AudioManager()

        self.audio_thread_exit = threading.Event()
        self.audio_thread = threading.Thread(target = self.audio_status)

        self.api = TTTAPI(self.upload_url, auth)
        self.uploaded = False
        self.dry = False #if True, then api create calls should do a dry run

        self.layout = layout.Layout(self).get_layout()

        self.browse_paths = {k: None for k in ['image_list', 'file_list']}

    def set_pos(self, value):
        if self.audio_thread_exit.is_set(): return
        if value != self.window['playback_progress'].Widget.get():
            self.window['playback_progress'].update(value)
        self.window['play'].set_playing(self.audio.is_playing)

    def audio_status(self):
        while not self.audio_thread_exit.is_set():
            pos = self.audio.get_pos()
            self.window.write_event_value('audio_tick', pos)
            time.sleep(.2)

    def get_queue(self):
        self.queue = {}
        dirs = os.listdir(self.upload_dir)
        for name in dirs:
            if name in self.queue.keys(): continue
            try:
                up = upload.Upload(self.upload_dir, name)
            except Exception as e:
                print(f'Failed to load item {name}: {e}')
                continue
            self.queue[name] = up
        
    def update_queuebox(self):
        box = self.window['queue']

        new_vals = self.queue.keys()

        box.update(values = new_vals)
        
        if self.upload_sel in new_vals:
            box.set_value([self.upload_sel])
            self.update_form(self.upload_sel, force=True)
        else:
            self.upload_sel = None
            self.clear_form()
            self.set_form_locked(True)
        

    def delete_upload(self):
        if self.upload_sel == None: return

        res = sg.popup_yes_no('Are you sure about that?')
        if res != 'Yes': return

        shutil.rmtree(os.path.join(self.upload_dir, self.upload_sel))

        del self.queue[self.upload_sel]
        self.upload_sel = None
        self.update_queuebox()

    def revert_upload(self):
        if self.upload_sel == None: return

        up = self.queue[self.upload_sel]
        up.revert()
        self.update_form(self.upload_sel,force = True)

    def reload_upload(self):
        if self.upload_sel == None: return

        up = self.queue[self.upload_sel]
        up.load()
        self.update_form(self.upload_sel,force = True)



    def print(self, *args, **kwargs):
        self.window['console'].print(*args, **kwargs)

    def expand_ui(self):
        for key in ['name', 'recording', 'date', 'desc', 'refresh_queue', 'console', 'new_tag', 'tags_list', 'authors_list', 'new_author', 'repo_table', 'missing_tags_button', 'license' ,'playback_progress']:
            self.window[key].expand(expand_x = True)
        for key in ['queue', 'file_list', 'repo_table', 'image_list', 'missing_tags_list']:
            self.window[key].expand(expand_y = True)

    def set_form_locked(self, locked = False):
        for key, elem in self.window.key_dict.items():
            if elem.metadata == None: continue
            if 'uploaded' in elem.metadata.get('lock', []):
                elem.update(disabled = locked)

    def add_files(self, key):
#        files = sg.tk.filedialog.askopenfilenames(initialdir = self.browse_paths[key], parent=self.window.TKroot)
        files = tkfb.askopenfilenames(initialdir = self.browse_paths[key], parent=self.window.TKroot)
        if len(files) == 0: return
        self.window[key].add_items_unique(files)
        self.browse_paths[key] = os.path.dirname(files[0])

    def clear_form(self):
        self.uploaded = False
        for key in ['name', 'desc', 'recording', 'new_tag', 'new_author']:
            self.window[key].update('')
        self.window['date'].update('')
        for key in ['image_list', 'file_list', 'tags_list', 'authors_list']:
            self.window[key].update([])
        self.window['repo_table'].update(values = [])
        self.window['url_text'].update('')

    def validate_recording(self):
        path = self.window['recording'].get()
        rec_valid = os.path.exists(path)

        infostring = ''
        if rec_valid:
            try:
                data = audiometa.load(path)
                length = round(data['streaminfo']['duration'])
                self.window['playback_progress'].update(range=(0,length))
                duration = datetime.timedelta(seconds=round(length))
                infostring = f'Length: {duration}'
                self.audio.load(path)
                self.window['play'].set_playing(self.audio.is_playing)
            except audiometa.exceptions.UnsupportedFormat:
                rec_valid = False
                infostring = 'Not a valid audio file'

        if not rec_valid:
            self.audio.clear()

        self.window['audiometa'].update(infostring)

        self.window['recording'].set_valid(rec_valid)

    def validate_files(self, key):
        elem = self.window[key]
        values = elem.get_list_values()
        
        elem.set_valid(True)
        for path in values:
            if not os.path.exists(path):
                elem.set_valid(False)

    def validate_date(self):
        elem = self.window['date']
        try:
            time.strptime(elem.get(), self.DATEFMT)
            elem.set_valid(True)
        except:
            elem.set_valid(False)

    def update_form(self, upsel, force = False):
        if not force and upsel == self.upload_sel: return
        self.upload_sel = upsel
        up = self.queue[upsel]

        url_text = 'File not yet uploaded'
        self.uploaded = False
        if len(up.data['recording']) > 0:
            res = self.api.get_recording_name(up.data['recording'])
            if len(res) > 0:
                res = res[0]
                url_text = res['absolute_url']
                self.uploaded = True
        self.validate_recording()

        uploaded = self.uploaded

        self.set_form_locked(False) #Have to unlock the form to change it

        self.window['url_text'].update(url_text)

        for key in ['name', 'desc', 'recording']:
            newval = up.data[key]
            self.window[key].update(newval)

        self.window['date'].update(time.strftime(self.DATEFMT, time.localtime(up.data['date'])))

        self.window['license'].update(self.api.licenses[up.data['license']], readonly=True)

        for key, src in [('image_list', 'images'),('file_list', 'attachments'),('tags_list', 'tags'),('authors_list', 'authors')]:
            print(key, src, up.data[src])
            self.window[key].update(up.data[src])

        for key in ['image_list', 'file_list']:
            self.validate_files(key)

        self.window['repo_table'].update_dict(values = up.data['repo_attachments'])

        if uploaded: #This has to happen after updating the values or they won't
            self.set_form_locked(True)
            self.window['url_text'].set_cursor(cursor='hand2')
        else:
            self.window['url_text'].set_cursor(cursor='')


    def update_tags(self):
        missing_list = self.window['missing_tags_list']
        if self.upload_sel == None:
            missing_list.update([])
            missing_list.set_valid(True)
        up = self.queue[self.upload_sel]
        tags = up.data['tags']
        found, missing = self.api.get_tags(tags)
        missing_list.update(missing)

        if len(missing) != 0:
            self.window['upload_button'].update(disabled = True)
            missing_list.set_valid(False)
        elif not self.uploaded:
            self.window['upload_button'].update(disabled = False)
            missing_list.set_valid(True)

    def remove_bad_authors(self):
        auths = self.window['authors_list'].get_list_values()
        found, missing = self.api.get_authors(auths)
        for bad in missing:
            self.print(f'!! Removing invalid author name {bad}')
            auths.remove(bad)
        self.window['authors_list'].update(values = auths)


    def update_upload(self, upsel):
        up = self.queue[upsel]
        if self.uploaded: return

        for key in ['name', 'desc', 'recording']:
            up.data[key] = self.window[key].get().strip('\n')

        try:
            up.data['date'] = time.mktime(time.strptime(self.window['date'].get(), self.DATEFMT))
        except ValueError: pass

        up.data['license'] = self.api.licenses_reverse[self.window['license'].get()]

        for key, src in [('image_list', 'images'),('file_list', 'attachments'),('tags_list', 'tags'),('authors_list', 'authors')]:
            up.data[src] = self.window[key].get_list_values()

        up.data['repo_attachments'] = self.window['repo_table'].get_upload_data()

    def validate_upload(self):

        up = self.queue[self.upload_sel]
        if self.uploaded: return False

        result = True

        for key, elem in self.window.key_dict.items():
            try:
                if not elem.valid:
                    self.print(f'{key} data is not valid')
                    result = False
            except: pass

        return result

    def do_upload(self):
        if self.upload_sel == None: return
        valid = self.validate_upload()
        if not valid: return

        self.print(f'Starting upload...')
    
        self.update_upload(self.upload_sel)
        data = self.queue[self.upload_sel].data
        up = uploader.Uploader(self.api.base_url, data, self.auth, tag_resolution='ignore')
        res = up.upload(dry=self.dry)

        if res.status_code > 299:
            self.print(f'Failed to upload file')
            self.print(f'{res.status_code}: {res.text}')
        else:
            self.print(f'File upload success')    
    
        self.update_form(self.upload_sel, force=True)


    def create_tags(self):
        new_tags = []
        tags = self.window['missing_tags_list'].get()
        if len(tags) == 0:
            tags = self.window['missing_tags_list'].get_list_values()

        for tagname in tags:
            event, res = widgets.popup_new_tag(tagname)
            if event == 'create':
                new_tags.append(res)
            elif event == 'abort': 
                self.print('Create tags aborted.')
                return
            elif event == 'cancel':
                self.print(f'Skipping tag {tagname}')
            elif event == 'error':
                self.print(f'Skipping tag {tagname} because: {res["description"]}')

        for res in new_tags:
            if len(res['description']) == 0:
                self.print(f'Skipping tag {res["name"]} with empty description')
                new_tags.remove(res)

        results = self.api.create_tags(new_tags, dry=self.dry)

        for status, obj in results:
            print(f'{status}: {obj}')
            if status == 201:
                self.print(f'Created new tag {obj["name"]}')
            else:
                self.print(f'Failed to create tag, {status} :{obj}')
        


    def run(self):
        print(f'Starting app')

        self.window = window = sg.Window("AFUM", self.layout, location=(0,0), 
#            use_ttk_buttons=True
            )
        self.window.Finalize()

        for key in ['image_list', 'file_list', 'repo_table', 'tags_list', 'authors_list']:
            self.window[key].setup()
        
        self.update_queuebox()
        self.expand_ui()
        self.clear_form()
        self.audio_thread.start()
        print(f'App started')
        while True:
            event, values = window.read()
            args = []
            if event != None:
                event, *args = event.split('+')
            print(event, args)

            if event == sg.WIN_CLOSED or event == 'Exit':
                break

            if self.upload_sel != None:
                self.update_upload(self.upload_sel)

            if event == 'queue':
                upsel = self.window['queue'].get()[0]
                self.update_form(upsel)
            elif event == 'refresh_queue':
                self.get_queue()
                self.update_queuebox()
            elif event == 'upload_button':
                self.do_upload()
            elif event == 'delete_button':
                self.delete_upload()
            elif event == 'revert_button':
                self.revert_upload()
            elif event == 'reload_button':
                self.reload_upload()
            elif event == 'image_browse':
                self.add_files('image_list')
            elif event == 'file_browse':
                self.add_files('file_list')
            elif 'listbox_delete' in args:
                window[event].delete_selection()
            elif len(args) > 1 and args[0] == 'listbox_add':
                source = window[args[1]]
                window[event].add_items_unique([source.get()])
                source.update('')
            elif event == 'save_button':
                self.queue[self.upload_sel].save()
            elif event == 'url_text':
                if self.uploaded:
                    webbrowser.open(self.window['url_text'].get(), new=2)
            elif event == 'missing_tags_button':
                self.create_tags() 

            if event in ['recording', 'queue']:
                self.validate_recording()

            if event == 'playback_progress':
                res = self.window['playback_progress'].Widget.get()
                self.audio.set_pos(res)

            if event == 'audio_tick':
                self.set_pos(values['audio_tick'])

            if event == 'play':
                self.audio.toggle_play()
                self.window['play'].set_playing(self.audio.is_playing)

            if event in ['image_list', 'file_list']:
                self.validate_files(event)
            if event == 'date':
                self.validate_date()

            if event in ['queue', 'tags_list', 'missing_tags_button']:
                self.update_tags()
            if event in ['queue', 'authors_list']:
                self.remove_bad_authors()
                
        print(f'Ending app')
        self.audio_thread_exit.set()
        self.audio_thread.join()
        print(f'Audio thread closed')
        
        window.close()

sg.theme('SystemDefault 1')

app = App(config.UPLOAD_DIR, config.UPLOAD_URL, (secrets.user, secrets.password))

app.run()

