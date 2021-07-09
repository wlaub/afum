import os

UPLOAD_DIR = os.path.expanduser('~/projects/afum/uploads')

#UPLOAD_URL = 'http://127.0.0.1:8000'
UPLOAD_URL = 'https://techtech.technology'

#VCVMON

#Where to look for patch files
VCV_PATCH_DIR = os.path.expanduser('~/.Rack/patches')
#Where to watch for recordings
VCV_RECORD_DIR = '/media/wlaub/Archive/Patches'
#Where to store upload packages during recording
VCV_TEMP_DIR = os.path.expanduser('~/projects/afum/temp_uploads')
#Minimum length in seconds of a recording. Discard anything longer
VCV_MIN_LENGTH = 10



