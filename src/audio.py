import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import structlog
from gtts import gTTS


logger = structlog.getLogger()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
api_service_name = "drive"
api_version = "v3"


def upload_to_gdrive(file_path):
    try:
        # create drive api client
        service = build(api_service_name, api_version, developerKey=GOOGLE_API_KEY)
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
