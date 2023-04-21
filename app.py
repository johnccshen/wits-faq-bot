from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage   # 載入 TextSendMessage 模組
import os
import json
from src.utils import ask
app = Flask(__name__)


LINE_TOKEN = os.getenv('LINE_TOKEN')
LINE_SECRET_KEY = os.getenv('LINE_SECRET_KEY')


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
        query = json_data['events'][0]['message']['text']
        msg_type = json_data['events'][0]['message']['type']  # 取得 LINe 收到的訊息類型
        if msg_type == 'text':
            if query.startswith('黑姑 '):
                msg = ask(query.split('黑姑 ')[1], try_answer=True)
                text_message = TextSendMessage(text=msg)          # 設定回傳同樣的訊息
                line_bot_api.reply_message(tk, text_message)       # 回傳訊息
    except Exception as e:
        tk = json_data['events'][0]['replyToken']   # 取得 reply token
        text_message = TextSendMessage(f'黑姑壞了 {e}')  # 設定回傳同樣的訊息
        line_bot_api = LineBotApi(LINE_TOKEN)
        line_bot_api.reply_message(tk, text_message)  # 回傳訊息
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # print(ask('怎麼請假', try_answer=True))
