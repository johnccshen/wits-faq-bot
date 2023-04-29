from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ConfirmTemplate, TemplateSendMessage, PostbackTemplateAction
import os
import json
import structlog
import openai
from src.faq import FaqAnswerBot
app = Flask(__name__)
logger = structlog.getLogger()

LINE_TOKEN = os.getenv('LINE_TOKEN')
LINE_SECRET_KEY = os.getenv('LINE_SECRET_KEY')


def get_audio_text(event, line_bot_api):
    message_id = event['message']['id']
    audio_content = line_bot_api.get_message_content(message_id)
    audio_file = f"data/audio/audio-{message_id}.m4a"
    os.makedirs("data/audio", exist_ok=True)
    with open(audio_file, 'wb') as fd:
        for chunk in audio_content.iter_content():
            fd.write(chunk)
    logger.info(f"Write file to {audio_file}")
    with open(audio_file, "rb") as af:
        text = openai.Audio.transcribe(
            file=af,
            model="whisper-1",
            response_format="text",
            language="zh"
        )
    return text


@app.route("/lineBot", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    token = json_data['events'][0]['replyToken']  # 取得 reply token
    logger.info(json_data)
    try:
        line_bot_api = LineBotApi(LINE_TOKEN)
        handler = WebhookHandler(LINE_SECRET_KEY)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        events = json_data['events']
        for event in events:
            logger.info(event)
            if event.get('postback'):
                line_bot_api.reply_message(token, TextSendMessage(text=event['postback']['data']))
            if event.get('message'):
                reply_messages = []
                if event['message']['type'] == 'text':
                    question = event['message']['text']
                    logger.info(f"Get text question {question}")
                elif event['message']['type'] == 'audio':
                    question = get_audio_text(event, line_bot_api)
                    transcribed_msg = f"Get audio question: {question}"
                    logger.info(transcribed_msg)
                    line_bot_api.reply_message(token, TextSendMessage(transcribed_msg))
                else:
                    return 'OK'
                line_bot_api.reply_message(token, TextSendMessage("Processing...🤪"))
                faq_answer_bot = FaqAnswerBot(question)
                is_success, msg = faq_answer_bot.answer()
                reply_messages.append(TextSendMessage(text=msg))
                reply_messages.append(
                    TemplateSendMessage(
                        alt_text='Confirmation Message',    # 後台顯示
                        template=ConfirmTemplate(
                            title='ConfirmTemplate',
                            text='Are you satisfied with the answer?',
                            actions=[
                                PostbackTemplateAction(
                                    label='Yes',
                                    text='Yes',
                                    data='Glad you love it. 😎'
                                ),
                                PostbackTemplateAction(
                                    label='No, help me!',
                                    text='No, help me!',
                                    data='Send notification to the administrator.\n'
                                         'John will help you in person. Please wait.🙏🏾'
                                         'Relax first!🥳\nhttps://youtu.be/Jh4QFaPmdss'
                                )
                            ]
                        )
                    )
                )
                line_bot_api.reply_message(token, reply_messages)       # 回傳訊息
    except Exception as e:
        token = json_data['events'][0]['replyToken']   # 取得 reply token
        text_message = TextSendMessage(f'嘿咕壞了 {e}')  # 設定回傳同樣的訊息
        line_bot_api = LineBotApi(LINE_TOKEN)
        line_bot_api.reply_message(token, text_message)  # 回傳訊息
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # print(FaqAnswerBot('What can I do if I am sick').answer())
