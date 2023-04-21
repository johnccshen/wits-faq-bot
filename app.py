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
    print(json_data)
    try:
        line_bot_api = LineBotApi(LINE_TOKEN)
        handler = WebhookHandler(LINE_SECRET_KEY)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        tk = json_data['events'][0]['replyToken']   # 取得 reply token
        if tk.startswith('黑姑 '):
            msg = ask('黑姑 '.split('黑姑 ')[0], try_answer=True)
            text_message = TextSendMessage(text=msg)          # 設定回傳同樣的訊息
            line_bot_api.reply_message(tk, text_message)       # 回傳訊息
    except Exception as e:
        print(e)
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
