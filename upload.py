import os, time

import json

import shutil

import git

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
        self.name = name
        self.set_basedir(basedir)

        self.filedir = os.path.join(self.directory, self._FILEDIR)
        self.imagedir = os.path.join(self.directory, self._IMAGEDIR)

        if os.path.exists(self.directory):
            self.load()

    def set_basedir(self, basedir):
        self.basedir = basedir
        self.directory = os.path.join(basedir, self.name)

    def get_filename(self):
        return os.path.join(self.directory, f'data.json')

    def add_tag(self, tag):
        if not tag in self.data['tags']:
            self.data['tags'].append(tag)

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
            return path
        else:
            newpath = os.path.join(cachedir, filename)
            if newpath in filelist: return
            shutil.copyfile(path, newpath)
            filelist.append(newpath)
            return newpath

    def set_recording(self, path, cache=False):
        """
        Set the recording to the given file, and cache it locally if cache
        is True
        """
        newpath = self.add_file_generic(path, self.directory, [], cache)
        self.data['recording'] = newpath
    
    def add_file(self, path, cache=False):
        return self.add_file_generic(path, self.filedir, self.data['attachments'], cache)

    def add_image(self, path, cache=False):
        return self.add_file_generic(path, self.imagedir, self.data['images'], cache)

    def add_git(self, path):
        """
        Extract the relevant git metadata and add a repo attachment representing
        the given path.
        """
        basename, filename = os.path.split(path)
        repo = git.Repo(basename, search_parent_directories=True)
        remote = repo.remote().url
        relpath = os.path.relpath(path, repo.working_dir)

        base_commit = repo.head.commit
        commit = base_commit.hexsha
        for tag in repo.tags:
            if tag.commit == base_commit:
                commit = tag.name
                break

        commit_data = {
            'repo': remote,
            'filename': relpath,
            'commit': commit
        }
        
        if not commit_data in self.data['repo_attachments']:
            self.data['repo_attachments'].append(commit_data)

    def move(self, newdir):
        """
        Moving entails updating the paths of any cached files to point at the
        new location.
        """
        newpath = shutil.move(self.directory, newdir)

        def replace(name):
            if not self.directory in name: return name
            relpath = os.path.relpath(name, self.basedir)
            return os.path.join(newdir, relpath)

        for key in ['attachments', 'images']:
            self.data[key] = list(map(replace, self.data[key]))

        self.data['recording'] = replace(self.data['recording'])

        self.directory = newpath

        self.save(write_orig = True)
            
        return newpath


    def load(self):
        filename = self.get_filename()
        raw = open(filename, 'r').read()
        self.data = json.loads(raw)

    def revert(self):
        filename = self.get_filename()+'.orig'
        raw = open(filename, 'r').read()
        self.data = json.loads(raw)

    def prepare(self):
         if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            os.makedirs(self.filedir)
            os.makedirs(self.imagedir)

    def save(self, write_orig = False):
        filename = self.get_filename()
        orig_filename = self.get_filename()+'.orig'

        self.prepare()

        if write_orig or not os.path.exists(orig_filename):
            json.dump(self.data, open(f'{filename}.orig', 'w'))
       
        json.dump(self.data, open(filename, 'w'))

