import os
import time

import shutil

import webbrowser

import upload
import config
from tttweb.uploader.tttapi import TTTAPI
import secrets
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
import PySimpleGUI as sg
import tkinter as tk

class DListbox(sg.Listbox):

    def setup(self):
        self.bind('<Delete>', '+listbox_delete')
    
    def delete_selection(self):
        values = self.get_list_values()
        remove = self.get()
        for item in remove: values.remove(item)
        self.update(values)

    def add_items_unique(self, items):
        values = self.get_list_values()
        for item in items:
            if len(item) > 0 and  not item in values:
                values.append(item)
        self.update(values)

       
        


class App():

    DATEFMT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, upload_dir, upload_url, auth):
        self.upload_url = upload_url
        self.upload_dir = upload_dir
        self.queue = {}

        self.get_queue()
        self.upload_sel = None

        self.api = TTTAPI(self.upload_url, auth)

        file_height = 2
        file_width = 80

        input_width = 120

        self.layout = [
            [sg.Text(f'Host: {self.upload_url}'), ],
            [
            #upload queue
            sg.Column( expand_y = True,
            layout=[
                [sg.Text('Pending uploads:')],
            [
                sg.Listbox(key = 'queue', 
                    values = self.queue.keys(), 
                    default_values = list(self.queue.keys())[0], 
                    size = (20, 20),
                    select_mode = sg.LISTBOX_SELECT_MODE_SINGLE,
                    enable_events = True,
                    )
            ],
                [sg.Column(layout=[[sg.Button('Refresh', key='refresh_queue', enable_events=True)]], 
                    expand_x =True, pad=(0,0), vertical_alignment='bottom')]
            ]
            ),
            #Main form
            sg.Column( expand_y = True,
            layout=[ 
                [sg.Text('Title:')], [sg.Input(key = 'name', enable_events=True)],
                [sg.Text('Recording:')], [sg.Input(key = 'recording'), sg.FileBrowse('Browse', key='recording_browse', enable_events=True)],
                [sg.Text('Time:')], [sg.Input(key = 'date', enable_events=True)],
                [sg.Text('Description:')], [sg.Multiline(key = 'desc', expand_x = True, size=(0,5), enable_events=True)],
                [
                    sg.Column( expand_x = True, expand_y = True, layout=[
                    [sg.Text('Tags:')],
                    [
                        DListbox(
                            values=[], 
                            enable_events=True, 
                            select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                            size = (20,10),
                            key = 'tags_list',
                            )
                    ],
                    [ sg.Input(key='new_tag', size=(1,1)), sg.Button('Add', key = 'tags_list+listbox_add+new_tag', enable_events=True)]
                    ]),
                    sg.Column( expand_x = True, expand_y = True, layout=[
                    [sg.Text('Authors')],
                    [
                        DListbox(
                            values=[], 
                            enable_events=True, 
                            select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                            size = (20,10),
                            key = 'authors_list',
                            )
                    ],
                    [ sg.Input(key='new_author', size=(1,1)), sg.Button('Add', key = 'authors_list+listbox_add+new_author', enable_events=True)]
                    ])
                ],

                [sg.Text('Tags:')], [sg.Input(key = 'tags', enable_events=True)],
                [sg.Text('Authors:')], [sg.Input(key = 'authors', enable_events=True)],
                [   sg.Button('Upload', key='upload_button', disabled=True), 
                    sg.Button('Delete', key='delete_button', disabled=False), 
                    sg.Button('Revert', key='revert_button', disabled=True),
                    sg.Button('Save', key='save_button', disabled=True),
],
                [sg.Text('Upload URL:'), sg.Text('', key='url_text', enable_events=True, auto_size_text=True, size=(len(upload_url)+20,1), text_color = 'blue'),]
             ]
            ),
            #Files
            sg.Column( expand_y=True,
            layout = [
                [sg.Text('Images'), sg.Button('Browse', key='image_browse',)],
                [DListbox(
                    values = [], 
                    size=(file_width,file_height), 
                    enable_events = True, 
                    select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                    key='image_list')],
                [sg.Text('Files'), sg.Button('Browse', key='file_browse', )],
                [DListbox(
                    values = [], 
                    size=(file_width,file_height), 
                    enable_events = True, 
                    select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                    key='file_list')],
                [sg.Text('Repositories'), sg.Button('Browse', key='repo_browse')],
                [DListbox(
                    values = [], 
                    size=(file_width,file_height), 
                    enable_events = True, 
                    select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                    key='repo_list')],
            ]
            ),
           
        ],
            [sg.Multiline(key='console', size = (20,10))],
        ]

        self.browse_paths = {k: None for k in ['image_list', 'file_list', 'repo_list']}

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

    def print(self, *args, **kwargs):
        self.window['console'].print(*args, **kwargs)

    def expand_ui(self):
        for key in ['name', 'recording', 'date', 'desc', 'tags', 'authors', 'refresh_queue', 'console', 'new_tag', 'tags_list', 'authors_list', 'new_author']:
            self.window[key].expand(expand_x = True)
        for key in ['queue', 'file_list', 'repo_list', 'image_list']:
            self.window[key].expand(expand_y = True)

    def set_form_locked(self, locked = False):
        for key in ['upload_button', 'revert_button', 'save_button', 'recording_browse', 'file_browse', 'image_browse', 'repo_browse', 'name', 'recording', 'date', 'desc', 'tags_list', 'authors_list', 'tags_list+listbox_add+new_tag', 'new_tag', 'authors_list+listbox_add+new_author', 'new_author']:
            self.window[key].update(disabled = locked)

    def add_files(self, key):
        files = sg.tk.filedialog.askopenfilenames(initialdir = self.browse_paths[key], parent=self.window.TKroot)
        if len(files) == 0: return
        self.window[key].add_items_unique(files)
        self.browse_paths[key] = os.path.dirname(files[0])

    def delete_selection(self, key):
        element = self.window[key]
        values = element.get_list_values()
        remove = element.get()
        for item in remove: values.remove(item)
        element.update(values)

    def clear_form(self):
        for key in ['name', 'desc', 'recording', 'new_tag', 'new_author']:
            self.window[key].update('')
###        for key in ['tags', 'authors']:
###            self.window[key].update('')
        self.window['date'].update('')
        for key in ['image_list', 'file_list', 'repo_list', 'tags_list', 'authors_list']:
            self.window[key].update([])
        self.window['url_text'].update('')

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

        uploaded = self.uploaded

        self.set_form_locked(False) #Have to unlock the form to change it

        self.window['url_text'].update(url_text)

        for key in ['name', 'desc', 'recording']:
            newval = up.data[key]
            self.window[key].update(newval)
        self.window['date'].update(time.strftime(self.DATEFMT, time.localtime(up.data['date'])))
        for key, src in [('image_list', 'images'),('file_list', 'attachments'),('tags_list', 'tags'),('authors_list', 'authors')]:
            print(key, src, up.data[src])
            self.window[key].update(up.data[src])

        if uploaded: #This has to happen after updating the values or they won't
            self.set_form_locked(True)
            self.window['url_text'].set_cursor(cursor='hand2')
        else:
            self.window['url_text'].set_cursor(cursor='')



    def update_upload(self, upsel):
        up = self.queue[upsel]
        if self.uploaded: return

        for key in ['name', 'desc', 'recording']:
            up.data[key] = self.window[key].get().strip('\n')

        try:
            up.data['date'] = time.mktime(time.strptime(self.window['date'].get(), self.DATEFMT))
        except ValueError: pass

        for key, src in [('image_list', 'images'),('file_list', 'attachments'),('tags_list', 'tags'),('authors_list', 'authors')]:
            up.data[src] = self.window[key].get_list_values()

    def run(self):
        print(f'Starting app')
        self.window = window = sg.Window("AFUM", self.layout,)
        self.window.Finalize()

        for key in ['image_list', 'file_list', 'repo_list', 'tags_list', 'authors_list']:
            self.window[key].setup()

        self.update_queuebox()
        self.expand_ui()
        self.set_form_locked(True)
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
            elif event == 'delete_button':
                self.delete_upload()
            elif event == 'revert_button':
                self.revert_upload()
            elif event == 'image_browse':
                self.add_files('image_list')
            elif event == 'file_browse':
                self.add_files('file_list')
            elif event == 'repo_browse':
                self.add_files('repo_list')
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

                
        print(f'Ending app')
        window.close()

app = App(config.UPLOAD_DIR, config.UPLOAD_URL, (secrets.user, secrets.password))

app.run()

