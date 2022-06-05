from fastapi import Request, UploadFile
import hashlib
from pathlib import Path
from google.cloud import storage
from google.cloud.storage import Blob
from google.oauth2 import service_account


class File_Size_Checker:
    limit: int 
    def __init__(self, max_upload_size: int) -> None:
        self.limit = max_upload_size
        print('Max size', max_upload_size)

    async def __call__(self, req: Request): 
        content_length = int(req.headers['content-length'])
        if content_length < self.limit:
            print('content size', content_length)
        else:
            print('too large')    


def upload_to_gcs(file: UploadFile):
    content = file.file.read()
    contentType = file.content_type
    hasher =hashlib.md5()
    hasher.update(content)
    digest = hasher.hexdigest()

    project = 'hkshopu'
    bucket_name = "hkshopu.appspot.com"
    # service_key = 'hkshopu-8c719ce2e5fb.json'
    service_key = Path.cwd().joinpath('./hkshopu-8c719ce2e5fb.json')

    credentials = service_account.Credentials.from_service_account_file(service_key)
    client = storage.Client(project=project,credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    # blob = bucket.blob('refactor/aaa.jpg')
        
    blob = Blob('refactor/'+ digest, bucket)
    file.file.seek(0)
    blob.upload_from_file(file_obj=file.file, content_type=contentType)
    print('url', blob.public_url)
    return blob.public_url

def shop_code_generator(code: str):
    colnum = 0
    power = 1
    for i in range(len(code)-1,-1,-1):
        ch = code[i]
        colnum += (ord(ch)-ord('A')+1)*power
        power *= 26

    colnum+=1
    next_code = ''
    while(not(colnum//26 == 0 and colnum % 26 == 0)):
        temp = 25
        if(colnum % 26 == 0):
            next_code += chr(temp+65)
        else:
            next_code += chr(colnum % 26 - 1 + 65)

        colnum //= 26
    #倒序輸出拼寫的字串
    return next_code[::-1]   



