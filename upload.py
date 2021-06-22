import os, time

import json

import shutil

class Upload():
    """
    Upload has the directory structure:
    name
        name.json
        name.json.orig
        recording.mp3
        images
            image.png
            etc
        files
            file.xxx
            etc

    name.json has the format
    {
        name: Title of the Recording,
        recording: recording.mp3,
        date: unix timestamp,
        desc: "The description",
        authors: [list, of, authors],
        license: [8],
        tags: [list, of, tags],
        images: [list, of, files],
        attachments: [list, of, files],
        repo_attachments: [
            {
            'repo': url,
            'commit': checksum,
            'filename': filename
            },
            ...
            ],
    }

    This whole json package can be passed to the uploader
    pretty much directly.
    This class facilites managing the directory structure 
    specified above, which provides a location to cache files
    that might change between creating a recording and
    uploading it, and also serves as a queue for recordings
    yet to be processed.
    """

    _FILEDIR  = 'files'
    _IMAGEDIR = 'images'

    def __init__(self, basedir, name):
        self.data = {
            'name': '',
            'recording': '',
            'date': 0,
            'desc': '',
            'authors': [],
            'tags': [],
            'images': [],
            'attachments': [],
            'repo_attachments': [],
            'license': 8,
            }
        self.basedir = basedir
        self.name = name
        self.directory = os.path.join(basedir, name)

        self.filedir = os.path.join(self.directory, self._FILEDIR)
        self.imagedir = os.path.join(self.directory, self._IMAGEDIR)

        if os.path.exists(self.directory):
            self.load()

    def get_filename(self):
        return os.path.join(self.directory, f'data.json')

    def add_file_generic(self, path, cachedir, filelist, cache):
        """
        Add the given file to the given filelist without
        creating duplicates.
        If cache is True, first copy the file to the given
        cachedir and use the new path.
        """
        basename, filename = os.path.split(path)
        if not cache:
            if path in filelist: return
            filelist.append(path)
        else:
            newpath = os.path.join(cachedir, filename)
            if newpath in filelist: return
            shutil.copyfile(path, newpath)
            filelist.append(newpath)
    
    def add_file(self, path, cache=False):
        return self.add_file_generic(path, self.filedir, self.attachments, cache)

    def add_image(self, path, cache=False):
        return self.add_file_generic(path, self.imagedir, self.images, cache)

    def load(self):
        filename = self.get_filename()
        raw = open(filename, 'r').read()
        self.data = json.loads(raw)

    def revert(self):
        filename = self.get_filename()+'.orig'
        raw = open(filename, 'r').read()
        self.data = json.loads(raw)

    def save(self):
        filename = self.get_filename()

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            os.makedirs(self.filedir)
            os.makedirs(self.imagedir)

            json.dump(self.data, open(f'{filename}.orig', 'w'))
       
        json.dump(self.data, open(filename, 'w'))

