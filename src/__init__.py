import openai
import os
import tiktoken

openai.api_key = os.getenv('OPENAI_WITS_API_KEY')
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_PATH = "src/embedding_v2.csv"


def num_tokens(text: str, model: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
