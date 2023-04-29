import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import structlog
from gtts import gTTS
import pathlib
current_path = pathlib.Path(__file__).parent.resolve()


logger = structlog.getLogger()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
api_service_name = "drive"
api_version = "v3"

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def upload_to_gdrive(file_path):
    """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        # create drive api client
        service = build(api_service_name, api_version, credentials=creds)
        file_metadata = {'name': file_path}
        logger.info(f"About to upload file {file_path}")
        media = MediaFileUpload(file_path)
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        logger.info(F'File ID: {file.get("id")}')

    except HttpError as error:
        logger.error(F'An error occurred: {error}')
        file = None
    return f'https://drive.google.com/open?id={file.get("id")}'


def text_to_speech(text, event_id):
    output_file = f"{event_id}.m4a"
    tts = gTTS(text=text, lang='zh')
    tts.save(output_file)
    return output_file


def generate_audio_and_upload(text, event_id):
    logger.info('starting starting covert text to speech')
    audio_file = text_to_speech(text, event_id)
    logger.info("upload file to google drive")
    url = upload_to_gdrive(audio_file)
    return url
