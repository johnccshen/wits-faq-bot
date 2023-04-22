import ast  # for converting embeddings saved as strings back to arrays
import os

import openai  # for calling the OpenAI API
import pandas as pd  # for storing text and embeddings data
import tiktoken  # for counting tokens
from scipy import spatial  # for calculating vector similarities for search

openai.api_key = os.getenv('OPENAI_WITS_API_KEY')
# models
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"

embeddings_path = "src/embedding_v2.csv"

df = pd.read_csv(embeddings_path)
# convert embeddings from CSV str type back to list type
df['embedding'] = df['embedding'].apply(ast.literal_eval)


# search function
def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 10
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response["data"][0]["embedding"]
    strings_and_relatednesses = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:top_n], relatednesses[:top_n]


def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def query_message(
    query: str,
    df: pd.DataFrame,
    model: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatednesses = strings_ranked_by_relatedness(query, df)
    introduction = 'The following is a conversation with an AI assistant. ' \
                   'The assistant is helpful, creative, clever, and very friendly.' \
                   '運用以下的FAQ來回答問題，並附上聯絡人資訊。' \
                   '如果無法利用FAQ來回答問題，請回答：(很抱歉，我無法回答以上問題，請聯絡8855。\n' \
                   'Sorry it is out of my knowledge. Please contact 8855 for further assistance)'
    question = f"\n\nQuestion: {query}"
    message = introduction
    for string in strings:
        next_article = f'\n\nFAQ:\n"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question


def ask(
        query: str,
        df: pd.DataFrame = df,
        model: str = GPT_MODEL,
        token_budget: int = 4096 - 500,
        print_message: bool = False,
        try_answer: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, df, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        # {"role": "system", "content": "You answer questions about the 2022 Winter Olympics."},
        {"role": "system", "content": "回答有關FAQ的問題"},
        {"role": "user", "content": message},
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0
    )
    response_message = response["choices"][0]["message"]["content"]
    if '很抱歉，我無法回答以上問題，請聯絡8855。' in response_message and try_answer:
        try_answer_questions = [
            {"role": "system", "content": "以下是一個和AI助理的對話，這個助理非常的有同理心、有創造力並非常友善"},
            {"role": "system", "content": "請問我能如何協助你？"},
            {"role": "user", "content": query},
        ]
        try_answer_response = openai.ChatCompletion.create(
            model=model,
            messages=try_answer_questions,
            temperature=0.8
        )
        try_answer_message = try_answer_response["choices"][0]["message"]["content"]

        response_message = try_answer_message + "\n\n如以上回答無法幫助到你，請撥打 +886-2-7745-8888#8855，將有專人為您服務。"
    elif 'Sorry it is out of my knowledge. Please contact 8855 for further assistance' in response_message and try_answer:
        try_answer_questions = [
            {"role": "system", "content": "'The following is a conversation with an AI assistant. "
                                          "The assistant is helpful, creative, clever, and very friendly.'"},
            {"role": "system", "content": "How can I help you"},
            {"role": "user", "content": query},
        ]
        try_answer_response = openai.ChatCompletion.create(
            model=model,
            messages=try_answer_questions,
            temperature=0.8
        )
        try_answer_message = try_answer_response["choices"][0]["message"]["content"]
        response_message = try_answer_message + \
                           "\n\nIf the above answer can't help you, please contact +886-2-7745-8888#8855 for further assistance."

    return response_message
