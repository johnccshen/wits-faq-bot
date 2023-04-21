from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage   # 載入 TextSendMessage 模組
import os
import json

app = Flask(__name__)

TOKEN = '+mqfvqIy7MMISHmF/5gUXuLeUqEcuoPI/6UYDAcSUaUhUEtJlArYjXhm/ivrMjGfCWdrKHj4DkvzM80cBjh8a/2LdKMBdf1ZoMF+PnGH2CB2XGYRzVfPrEXDPMAAjPYMZSAWNtPzM70Gm93IfT8n8QdB04t89/1O/w1cDnyilFU='
SECRET_KEY = '6959c926d74bad49790d84e158556528'


@app.route("/lineBot", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    print(json_data)
    try:
        line_bot_api = LineBotApi(TOKEN)
        handler = WebhookHandler(SECRET_KEY)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        tk = json_data['events'][0]['replyToken']   # 取得 reply token
        print(json_data)
        msg = json_data['events'][0]['message']['text']   # 取得使用者發送的訊息
        text_message = TextSendMessage(text=msg)          # 設定回傳同樣的訊息
        line_bot_api.reply_message(tk, text_message)       # 回傳訊息
    except Exception as e:
        print(e)
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
