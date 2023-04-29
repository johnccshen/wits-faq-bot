import openai
import os

openai.api_key = os.getenv('OPENAI_WITS_API_KEY')
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_PATH = "src/embedding.csv"


