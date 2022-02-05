import os

UPLOAD_DIR = os.path.expanduser('~/projects/afum/uploads')

#UPLOAD_URL = 'http://127.0.0.1:8000'
UPLOAD_URL = 'https://techtech.technology'

#VCVMON

#Where to look for patch files
VCV_PATCH_DIR = os.path.expanduser('~/.Rack2/patches')
#Where to watch for recordings
VCV_RECORD_DIR = '/media/wlaub/Archive/Patches'
#Where to store upload packages during recording
VCV_TEMP_DIR = os.path.expanduser('~/projects/afum/temp_uploads')
#Minimum length in seconds of a recording. Discard anything longer
VCV_MIN_LENGTH = 7

#Automatically include images when the corresponding tags are presenti
#Boolean expressions maybe be used with &&, ||, ~~, and {,}
#This means that tags containing those strings may not be used
imgdir = os.path.expanduser('~/projects/afum/images')
VCV_TAG_IMAGES = {
'bldng': [os.path.join(imgdir, 'bldng1.png')],
'prometheus II && demo': [os.path.join(imgdir, 'prom2_rev01_dev.jpg')],
'prometheus II': [os.path.join(imgdir, 'prom2_rev01_demo.jpg')],
}

