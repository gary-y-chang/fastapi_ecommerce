import os
import pickle
from utils import upload_tools
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from mimetypes import guess_type as guess_mime_type
from bs4 import BeautifulSoup
from google.cloud import storage
from google.oauth2 import service_account
from google.cloud.storage import Blob
import re

SCOPES = ['https://mail.google.com/']

def gmail_authenticate():
    #/*
    # google cloud storage
    project = 'hkshopu'
    bucket_name = "hkshopu_dev"
    service_key = 'utils/hkshopu-8c719ce2e5fb.json'
    credentials = service_account.Credentials.from_service_account_file(service_key)
    client = storage.Client(project=project,credentials=credentials)
    bucket = client.get_bucket(bucket_name)
    #*/
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    token_pickle = "token.pickle"
    if Blob(token_pickle, bucket).exists():
        blob = bucket.get_blob(token_pickle)
        with blob.open("rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('utils/client_secret_349041949227-o4nq65m87706hkrdbe84cn1qev379oh7.apps.googleusercontent.com.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run        
        with blob.open("wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

# utility functions
def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)
def parse_parts(service, parts, folder_name, msg):
    """
    Utility function that parses the content of an email partition
    """
    parts_content = {}
    if parts:
        for part in parts:
            filename = part.get("filename")
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            file_size = body.get("size")
            part_headers = part.get("headers")
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                counter = 0
                while 'parts_' + counter in parts_content:
                    counter += 1
                parts_content['parts_' + counter] = parse_parts(service, part.get("parts"), folder_name, msg)
            if mimeType == "text/plain":
                # if the email part is text plain
                if data:
                    pass
                    #text = urlsafe_b64decode(data).decode()
                    #print(text)
                    #parts_content += text
                    #parts_content['plain_text'] = text
            elif mimeType == "text/html":
                # if the email part is an HTML content
                # save the HTML file and optionally open it in the browser
                if not filename:
                    filename = "index.html"
                # filepath = os.path.join('tmp', folder_name, filename)
                # print("Saving HTML to", filepath)
                # parts_content += "Saving HTML to" + filepath + '\n'
                # if not os.path.isdir('tmp'):
                #     os.mkdir(folder_name)
                # with open(filepath, "wb") as f:
                #     f.write(urlsafe_b64decode(data))
                # file_url = upload_file_from_path(filepath, mimeType)
                # parts_content += "Saving HTML to" + file_url + '\n'
                #parts_content += urlsafe_b64decode(data).decode()
                # parsing data
                html_str = urlsafe_b64decode(data).decode()
                soup = BeautifulSoup(html_str,features="html.parser")
                #rating_selector = "table tbody tr td font table tbody tr td table tbody tr td table tbody tr td font"
                selector = 'font'
                # content = []
                # for i in soup.select(rating_selector):
                #     for j in i.text.split(','):
                #         content += j.strip()
                # content = [re.sub('[\n\t\r +]+', ' ', i.text) for i in soup.select(rating_selector)]#[0]
                matches = ['Account Nickname', 'As of', 'Credit Amount', 'Paying Bank', 'Reference Number', 'Hang Seng Bank Limited']
                parts_content['parsed_html_data'] = {}
                for i in soup.select(selector):
                    snippet = re.sub('[\n\t\r +]+', ' ', i.text)
                    if all(x in snippet for x in matches):
                        for match_str in matches:
                            replaced_str = snippet.split(match_str)[0]
                            if any(y in replaced_str for y in matches):
                                key, value = [z for z in replaced_str.split(':', 1)]
                                parts_content['parsed_html_data'][key] = value.strip()
                            #parts_content['html_data'].append(replaced_str)
                            snippet = snippet.replace(replaced_str,'')

                # print(type(soup))
                # print(len(soup.select(rating_selector)))
                # print(filtered_content)
                #parts_content['html_data'] = filtered_content
            # else:
            #     # attachment other than a plain text or HTML
            #     for part_header in part_headers:
            #         part_header_name = part_header.get("name")
            #         part_header_value = part_header.get("value")
            #         if part_header_name == "Content-Disposition":
            #             if "attachment" in part_header_value:
            #                 # we get the attachment ID 
            #                 # and make another request to get the attachment itself
            #                 #print("Saving the file:", filename, "size:", get_size_format(file_size))
            #                 parts_content += "Saving the file:" + filename + "size:" + get_size_format(file_size) + '\n'
            #                 attachment_id = body.get("attachmentId")
            #                 attachment = service.users().messages() \
            #                             .attachments().get(id=attachment_id, userId='me', messageId=msg['id']).execute()
            #                 data = attachment.get("data")
            #                 #filepath = os.path.join('tmp', folder_name, filename)
            #                 if data:
            #                     # with open(filepath, "wb") as f:
            #                     #     f.write(urlsafe_b64decode(data)) 
            #                     # file_url = upload_file_from_path(filepath, mimeType)
            #                     # parts_content += "Saving HTML to" + file_url + '\n'
            #                     parts_content += urlsafe_b64decode(data)
    return parts_content
def read_message(service, message_id):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text parts
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it under the folder created as index.html
        - Downloads any file that is attached to the email and saves it in the folder created
    """
    msg = service.users().messages().get(userId='me', id=message_id['id'], format='full').execute()
    # parts can be the message body, or attachments
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    body = payload.get('body')
    folder_name = "email" + os.sep
    mail_data = {}
    if headers:
        # this section prints email basic info & creates a folder for the email
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name.lower() == 'from':
                # we print the From address
                #print("From:", value)
                mail_data["From"] = value
                #mail_data += "From: " + value + '\n'
            if name.lower() == "to":
                # we print the To address
                #print("To:", value)
                mail_data["To"] = value
                #mail_data += "To: " + value + '\n'
            if name.lower() == "subject":
                # make a directory with the name of the subject
                folder_name += clean(value)
                # we will also handle emails with the same subject name
                # folder_counter = 0
                # while os.path.isdir(folder_name):
                #     folder_counter += 1
                #     # we have the same folder name, add a number next to it
                #     if folder_name[-1].isdigit() and folder_name[-2] == "_":
                #         folder_name = f"{folder_name[:-2]}_{folder_counter}"
                #     elif folder_name[-2:].isdigit() and folder_name[-3] == "_":
                #         folder_name = f"{folder_name[:-3]}_{folder_counter}"
                #     else:
                #         folder_name = f"{folder_name}_{folder_counter}"
                # os.mkdir(folder_name)
                #print("Subject:", value)
                mail_data["Subject"] = value                
                #mail_data += "Subject: " + value + '\n'
            if name.lower() == "date":
                # we print the date when the message was sent
                #print("Date:", value)
                mail_data["Date"] = value
                #mail_data += "Date: " + value + '\n'
    # if 'data' in body:
    #     print(urlsafe_b64decode(body['data']).decode())
    # else: print()
    if not parts:
        parts = []
        parts.append(payload)
        #print(urlsafe_b64decode(body.get("data")).decode())
    # if message_id['id'] == '17ac22ae16b61f9d':
    mail_data['body'] = parse_parts(service, parts, folder_name, msg)
    #mail_data += parse_parts(service, parts, folder_name, msg) + '\n'
    #print("="*50)
    #mail_data += "="*50+'\n'
    #file_path = os.sep + os.path.join('tmp', folder_name)
    
    # folder_counter = 0    
    # while os.path.exists(file_path):
    #     folder_counter += 1
    #     # we have the same folder name, add a number next to it
    #     if file_path[-1].isdigit() and file_path[-2] == "_":
    #         file_path = f"{file_path[:-2]}_{folder_counter}"
    #     elif file_path[-2:].isdigit() and file_path[-3] == "_":
    #         file_path = f"{file_path[:-3]}_{folder_counter}"
    #     else:
    #         file_path = f"{file_path}_{folder_counter}"        
    # with open(file_path, "w") as f:
    #     f.write(mail_data)
    # upload_file_from_path(file_path, 'text/plain')
    return mail_data