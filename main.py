import upload
import config

up = upload.Upload(config.UPLOAD_DIR, 'test')


up.save()
