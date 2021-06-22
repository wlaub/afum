
import PySimpleGUI as sg
import widgets

class Layout():

    file_height = 2
    file_width = 80

    meta_lock_uploaded = {'lock': ['uploaded']}

    def __init__(self, app):
        self.app = app

    def get_queue(self):
        result = sg.Column( expand_y = True,
            layout=[
                [sg.Text('Pending uploads:')],
                [sg.Listbox(key = 'queue', 
                        values = self.app.queue.keys(), 
                        default_values = list(self.app.queue.keys())[0], 
                        size = (20, 20),
                        select_mode = sg.LISTBOX_SELECT_MODE_SINGLE,
                        enable_events = True,
                        )
                    ],
                [sg.Column( expand_x =True, pad=(0,0), vertical_alignment='bottom',
                    layout=[[sg.Button('Refresh', key='refresh_queue', enable_events=True)]],
                    )
                    ],
                ]
            )

        return result

    def get_form(self):
        license_values = list(self.app.api.licenses.values())
        result = sg.Column( expand_y = True,
            layout=[ 
                [sg.Text('Title:')], 
                [widgets.VInput(key = 'name', enable_events=True, metadata=self.meta_lock_uploaded)],
                [sg.Text('Recording:'), sg.Text('', s=(50,1), key='audiometa')], 
                [   widgets.VInput(key = 'recording', metadata=self.meta_lock_uploaded, enable_events=True), 
                    sg.FileBrowse('Browse', key='recording_browse', 
                        enable_events=True, metadata=self.meta_lock_uploaded)],
                [sg.Text('Time:')], 
                [widgets.VInput(key = 'date', enable_events=True, metadata=self.meta_lock_uploaded)],
                [sg.Text('Description:')], 
                [sg.Multiline(key = 'desc', expand_x = True, size=(0,5), enable_events=True, metadata=self.meta_lock_uploaded)],
                [sg.Column( expand_x = True, expand_y = True, pad=(0,0), layout=[
                    [sg.Text('Tags:')],
                    [
                        widgets.DListbox(
                            values=[], 
                            enable_events=True, 
                            select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                            size = (20,10),
                            key = 'tags_list',
                            metadata=self.meta_lock_uploaded 
                            )
                    ],
                    [   widgets.VInput(key='new_tag', size=(1,1), metadata=self.meta_lock_uploaded), 
                        sg.Button('Add', key = 'tags_list+listbox_add+new_tag', 
                            enable_events=True, metadata=self.meta_lock_uploaded)]
                    ]),
                 sg.Column( expand_x = True, expand_y = True, pad=(0,0), layout=[
                    [sg.Text('Authors')],
                    [
                        widgets.DListbox(
                            values=[], 
                            enable_events=True, 
                            select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                            size = (20,10),
                            key = 'authors_list',
                            metadata=self.meta_lock_uploaded
                            )
                    ],
                    [   widgets.VInput(key='new_author', size=(1,1), metadata=self.meta_lock_uploaded), 
                        sg.Button('Add', key = 'authors_list+listbox_add+new_author', 
                            enable_events=True, metadata=self.meta_lock_uploaded)]
                    ])
                ],
                [sg.Text('License:')],
                [sg.Combo(
                    values = license_values,
                    default_value = self.app.api.licenses[8],
                    readonly=True,
                    key = 'license',
                    metadata=self.meta_lock_uploaded
                    )],
                [   sg.Text('Upload URL:'), 
                    sg.Text('', key='url_text', enable_events=True, auto_size_text=True, size=(len(self.app.upload_url)+20,1), text_color = 'blue'),],
 
                [   sg.Button('Upload', key='upload_button', metadata=self.meta_lock_uploaded), 
                    sg.Button('Save', key='save_button', metadata=self.meta_lock_uploaded),
                    sg.Button('Reload', key='reload_button', metadata=self.meta_lock_uploaded),
                    sg.Button('Revert', key='revert_button', metadata=self.meta_lock_uploaded),
                    sg.Button('Delete', key='delete_button', ), 
                    ],
            ]
            )
        return result

    def get_files(self):
            #Files
        result = sg.Column( expand_y=True,
        layout = [
            [sg.Text('Images'), sg.Button('Browse', key='image_browse', metadata=self.meta_lock_uploaded)],
            [widgets.DListbox(
                values = [], 
                size=(self.file_width,self.file_height), 
                enable_events = True, 
                select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                key='image_list',
                metadata=self.meta_lock_uploaded)],
            [sg.Text('Files'), sg.Button('Browse', key='file_browse', metadata=self.meta_lock_uploaded)],
            [widgets.DListbox(
                values = [], 
                size=(self.file_width,self.file_height), 
                enable_events = True, 
                select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                key='file_list', 
                metadata=self.meta_lock_uploaded)],
            [sg.Text('Repositories')],
            [
                widgets.RepoTable(
                    values = [],
                    width = 62,
                    num_rows = 3,
                    headings = ["test","test","test"],
                    key='repo_table', 
                    metadata=self.meta_lock_uploaded
                )
            ],
        ]
        )
        return result

    def get_missing(self):

        result = sg.Column( expand_y = True,
            layout = [
                [sg.Text('Missing Tags:')],
                [widgets.ValidListbox(
                    values = [],
                    size = (20,1),
                    select_mode = sg.LISTBOX_SELECT_MODE_EXTENDED,
                    key = 'missing_tags_list',
                    )],
                [sg.Column(
                    layout=[[sg.Button('Create', key='missing_tags_button', enable_events=True)]],
                     expand_x =True, pad=(0,0), vertical_alignment='bottom')
                ],
            ]
        )
        return result
           

    def get_bottom(self):
        result = [ 
            [sg.Text(f'Host: {self.app.api.base_url}')],
            [sg.Multiline(key='console', size = (20,10))],
        ]
        return result

    def get_layout(self):
        return [
            [self.get_queue(), self.get_form(), self.get_files(), self.get_missing()],
            *self.get_bottom()
        ]
        

