from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ConfirmTemplate, MessageTemplateAction   # 載入 TextSendMessage 模組
import os
import json
import structlog
from src.faq_bot import FaqBot
app = Flask(__name__)
logger = structlog.getLogger()


LINE_TOKEN = os.getenv('LINE_TOKEN')
LINE_SECRET_KEY = os.getenv('LINE_SECRET_KEY')
LEADING_STR_CHINESE = '黑姑 '
LEADING_STR_ENG = 'Hey Cool '


faq_bot = FaqBot()

@app.route("/lineBot", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    logger.info(json_data)
    try:
        line_bot_api = LineBotApi(LINE_TOKEN)
        handler = WebhookHandler(LINE_SECRET_KEY)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        tk = json_data['events'][0]['replyToken']   # 取得 reply token
        if 'message' not in json_data['events'][0].keys():
            return 'OK'
        msg_type = json_data['events'][0]['message']['type']  # 取得 LINe 收到的訊息類型
        if msg_type == 'text':
            query = json_data['events'][0]['message']['text']
            if query.startswith(LEADING_STR_CHINESE):
                question = query.split(LEADING_STR_CHINESE)[1]
            elif query.startswith(LEADING_STR_ENG):
                question = query.split(LEADING_STR_ENG)[1] + 'and answer in English'
            else:
                return 'OK'
            is_success, msg = faq_bot.ask(question)
            if not is_success:
                general_ans = faq_bot.general_ask(question)
                msg += general_ans
            msg += f"\nOpenAI Cost: {faq_bot.total_cost:.6f}"
            text_message = TextSendMessage(text=msg, actions=['Yes', 'No'])
            confirm_message = ConfirmTemplate(
                title='ConfirmTemplate',
                text='Are you satisfied with the answer?',
                actions=[
                    MessageTemplateAction(
                        label='Yes',
                        text='yes',
                    ),
                    MessageTemplateAction(
                        label='N',
                        text='no'
                    )
                ]
            )
            line_bot_api.reply_message(tk, [text_message, confirm_message])       # 回傳訊息
    except Exception as e:
        tk = json_data['events'][0]['replyToken']   # 取得 reply token
        text_message = TextSendMessage(f'黑姑壞了 {e}')  # 設定回傳同樣的訊息
        line_bot_api = LineBotApi(LINE_TOKEN)
        line_bot_api.reply_message(tk, text_message)  # 回傳訊息
    finally:
        faq_bot.total_cost = 0
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # print(faq_bot.ask('Why my boss is stupid and answer in English', print_message=False, try_answer=True))
    # print(f"Cost: {faq_bot.total_cost:.6f}")

