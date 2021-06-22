import math

import PySimpleGUI as sg

def popup_new_tag(tagname):
    window = sg.Window(f'Create new tag: {tagname}',
    [
        [sg.Text(f'New tag: {tagname}')],
        [sg.Text('Tag Description:')],
        [sg.Multiline( key = 'desc', size=(80,16))],
        [sg.Column([[]], expand_x=True),sg.Button('Abort', key='abort', enable_events=True), sg.Button('Skip', key='cancel', enable_events=True), sg.Button('Create', key='create', enable_events=True)],
    ]
    )

    
    event,values = window.read()
    try:
        description = window['desc'].get().strip('\n')
    except Exception as e:
        event = 'error'
        description = str(e)
    window.close()
    del window

    return event, {'name': tagname, 'description': description}


class PlayButton(sg.Button):
    chars = {
        'play': '\u25b6',
        'pause': '\u25a0',
        'stop': '\u25a0'
        }
    
    def __init__(self, **kwargs):
        kwargs['button_text'] = self.chars['play']
        super().__init__(**kwargs)

    def pause(self):
        self.update(text=self.chars['play'])
    def play(self):
        self.update(text=self.chars['pause'])

    def set_playing(self, is_playing):
        if is_playing:
            self.play()
        else:
            self.pause()

class ValidMixin():

    def set_valid(self, valid):
        self.valid = valid
        if not valid:
            self.BackgroundColor = '#ffcccc'
        else:
            self.BackgroundColor = 'white'
        self.Widget.configure(background=self.BackgroundColor)

class ValidListbox(sg.Listbox, ValidMixin):
    pass

class VInput(sg.Input, ValidMixin): pass

class DListbox(sg.Listbox, ValidMixin):

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


class RepoTable(sg.Table):
    
    def __init__(self, **kwargs):
        kwargs['headings'] = ['Repo', 'File', 'Commit']

        width = kwargs.pop('width')
        repo_check_width = 8
        repo_width = int(math.ceil((width-repo_check_width)/2))
        repo_remote_width = width - repo_check_width - repo_width
        repo_col_widths = [repo_remote_width, repo_width, repo_check_width]
        kwargs['col_widths'] = repo_col_widths
       
        kwargs['auto_size_columns'] = False
        kwargs['justification'] = 'left'
        kwargs['background_color'] = sg.theme_input_background_color()
        kwargs['text_color'] = sg.theme_input_text_color()
        kwargs['selected_row_colors'] = ['white', 'black']

        self.disabled = True

        super().__init__(**kwargs)

    def setup(self):
        self.bind('<Delete>', '+listbox_delete')

    def update(self, **kwargs):
        self.disabled = kwargs.pop('disabled', self.disabled)
        super().update(**kwargs)

    def update_dict(self, **kwargs):
        items = kwargs.pop('values')
        result = []
        for item in items:
            result.append([
                item['repo'],
                item['filename'],
                item['commit'],
                ])

        kwargs['values'] = result
        super().update(**kwargs)

    def get_row_values(self):
        return self.Values

    def get_upload_data(self):
        result = []
        for repo, filename, commit in self.get_row_values():
            result.append({
                'repo': repo,
                'filename': filename,
                'commit': commit
                })
        return result

    def delete_selection(self):
        if self.disabled: return
        selection = self.SelectedRows
        values = self.get_row_values()
        remove = [values[x] for x in selection]
        for item in remove: values.remove(item)
        self.update(values = values)



