from google.cloud.storage import Blob
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account
from decouple import config
import datetime
import math
import random
from os import path
from utils.util import get_project_root

DNS = 'https://storage.googleapis.com/'

config.encoding = 'utf-8'
debug_mode = config('DEBUG', cast=bool)
ROOT_DIR = get_project_root()

if debug_mode:
    project = 'hkshopu'
    bucket_name = "hkshopu.appspot.com"
    service_key = path.join(ROOT_DIR, 'hkshopu-8c719ce2e5fb.json')
else:
    project = 'peppy-booth-311912'
    bucket_name = "peppy-booth-311912.appspot.com"
    service_key = path.join(ROOT_DIR, 'peppy-booth-311912-0189bdb40f56.json')

def upload_file(FILE,destination_path,suffix=""):
    """
    * 傳入值:
    *   FILE                    =>      上傳的檔案
    *   destination_path        =>      要上傳的路徑
    *   suffix(optional)        =>      檔案名稱後綴詞
    * 回傳值:
    *   fileURL                 =>      檔案網址
    """
    if (suffix != ""):
        suffix = "_" + suffix
    now = datetime.datetime.now()
    rand_num = get_random_num()
    
    if FILE:
        splited = str(FILE.filename).split('.')
        fileName = ""
        for i in range(0,len(splited)-1):
            fileName += splited[i]
        fileExtension = splited[len(splited)-1]
        fileFullName = destination_path + fileName + '_' + now.strftime('%Y%m%d%H%M%S') + '_' + str(math.floor(now.timestamp())) + "_" + rand_num + suffix + '.' + fileExtension

        credentials = service_account.Credentials.from_service_account_file(service_key)
        client = storage.Client(project=project,credentials=credentials)
        bucket = client.get_bucket(bucket_name)
        while (Blob(fileFullName, bucket).exists()):
            now = datetime.datetime.now()
            rand_num = get_random_num()
            fileFullName = destination_path + fileName + '_' + now.strftime('%Y%m%d%H%M%S') + '_' + str(math.floor(now.timestamp())) + "_" + rand_num + suffix + '.' + fileExtension
            
        blob = Blob(fileFullName, bucket)
        blob.upload_from_file(file_obj=FILE.file, content_type=FILE.content_type)
        fileURL = DNS + bucket_name + '/' + fileFullName
    else:
        fileURL = ''
    
    return fileURL

def upload_multiple_files(FILES, destination_path=""):
    pass
def delete_file(db_file_path):
    """
    * 傳入值:
    *   db_file_path            =>      資料庫的DB路徑
    """
    
    file_path = db_file_path.replace(DNS+bucket_name+'/','')
    credentials = service_account.Credentials.from_service_account_file(service_key)
    client = storage.Client(project=project,credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    try:
        Blob(file_path, bucket).delete()
    except:
        pass
def get_random_num():
    """
    * 回傳值:
    *   rand_num        =>      12碼亂數
    """
    rand_num_list = []
    for j in range(12):
        rand_num_list.append(random.choice('0123456789'))
    rand_num = ''.join(rand_num_list)
    return rand_num
