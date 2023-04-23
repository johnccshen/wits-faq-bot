from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage   # 載入 TextSendMessage 模組
import os
import json
from src.faq_bot import FaqBot
app = Flask(__name__)


LINE_TOKEN = os.getenv('LINE_TOKEN')
LINE_SECRET_KEY = os.getenv('LINE_SECRET_KEY')
LEADING_STR_CHINESE = '黑姑 '
LEADING_STR_ENG = 'Hey Cool '


faq_bot = FaqBot()

@app.route("/lineBot", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
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
                msg = faq_bot.ask(query.split(LEADING_STR_CHINESE)[1], try_answer=True)
            elif query.startswith(LEADING_STR_ENG):
                question = query.split(LEADING_STR_ENG)[1] + 'and answer in English'
                msg = faq_bot.ask(question, try_answer=True)
            else:
                return 'OK'
            msg += f"\nCost: {faq_bot.total_cost:.6f}"
            text_message = TextSendMessage(text=msg)          # 設定回傳同樣的訊息
            line_bot_api.reply_message(tk, text_message)       # 回傳訊息
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

