from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ConfirmTemplate, TemplateSendMessage, PostbackTemplateAction, AudioMessage
import os
import json
import structlog
from src.faq_bot import FaqBot
from audio import generate_audio_and_upload
import openai
app = Flask(__name__)
logger = structlog.getLogger()

LINE_TOKEN = os.getenv('LINE_TOKEN')
LINE_SECRET_KEY = os.getenv('LINE_SECRET_KEY')
LEADING_STR_CHINESE = '嘿咕'
LEADING_STR_ENG = 'hey cool'


faq_bot = FaqBot()


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
        for event in json_data['events']:
            logger.info(event)
            if event.get('postback'):
                line_bot_api.reply_message(token, TextSendMessage(text=event['postback']['data']))
            if event.get('message'):
                reply_messages = []
                if event['message']['type'] == 'text':
                    question = event['message']['text']
                    logger.info(f"Get text question {question}")
                elif event['message']['type'] == 'audio':
                    message_id = event['message']['id']
                    audio_content = line_bot_api.get_message_content(message_id)
                    audio_file = f"data/audio/audio-{message_id}.m4a"
                    os.makedirs("data/audio", exist_ok=True)
                    with open(audio_file, 'wb') as fd:
                        for chunk in audio_content.iter_content():
                            fd.write(chunk)
                    logger.info(f"Write file to {audio_file}")
                    with open(audio_file, "rb") as af:
                        question = openai.Audio.transcribe(
                            file=af,
                            model="whisper-1",
                            response_format="text",
                            language="zh"
                        )
                    transcribed_msg = f"Get audio question: {question}"
                    logger.info(transcribed_msg)
                    reply_messages.append(TextSendMessage(transcribed_msg))
                    reply_messages.append(AudioMessage(original_content_url=generate_audio_and_upload(
                        transcribed_msg,
                        message_id))
                    )

                else:
                    return 'OK'
                is_success, msg = faq_bot.ask(question)
                # if not is_success:
                #     msg = faq_bot.general_ask(question)
                # msg += f"\nOpenAI Cost: {faq_bot.total_cost:.6f}"
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
                                    text='yes',
                                    data='Glad you love it. 😎'
                                ),
                                PostbackTemplateAction(
                                    label='No, help me!',
                                    text='no',
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
    finally:
        faq_bot.total_cost = 0
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # print(faq_bot.ask('我明天要請個人假'))
    # print(f"Cost: {faq_bot.total_cost:.6f}")
