import openai
import ast
import pandas as pd
from scipy import spatial
from . import GPT_MODEL, EMBEDDING_MODEL, EMBEDDING_PATH
from .faq import num_tokens
from asyncer import asyncify


df_embedding = pd.read_csv(EMBEDDING_PATH)
# convert embeddings from CSV str type back to list type
df_embedding['embedding'] = df_embedding['embedding'].apply(ast.literal_eval)


def calculate_cost(query: str, model: str, cost_per_1k_token: float):
    token = num_tokens(query, model)
    return cost_per_1k_token * token / 1000


async def embedding_async(query: str, model: str = EMBEDDING_MODEL):
    query_response = await asyncify(openai.Embedding.create)(
        model=model,
        input=query,
    )
    return query_response


async def completion_async(messages, temperature: float = 0, model: str = GPT_MODEL):
    message_string = ''
    for line in messages:
        message_string += str(line)
    query_response = await asyncify(openai.ChatCompletion.create)(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return query_response


async def strings_ranked_by_relatedness(
        query: str,
        df: pd.DataFrame,
        relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
        top_n: int = 50
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = await embedding_async(query)
    query_embedding = query_embedding_response["data"][0]["embedding"]
    strings_and_relatednesses = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:top_n], relatednesses[:top_n]


async def query_message(
        query: str,
        df: pd.DataFrame,
        model: str,
        token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatednesses = await strings_ranked_by_relatedness(query, df)
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


async def ask(
        query: str,
        df: pd.DataFrame = df_embedding,
        model: str = GPT_MODEL,
        token_budget: int = 4096 - 500,
        print_message: bool = False,
) -> (bool, str):
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    is_succeed = True
    message = await query_message(query, df, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "回答有關FAQ的問題"},
        {"role": "user", "content": message},
    ]
    response = await completion_async(messages)
    response_message = response["choices"][0]["message"]["content"]
    if '很抱歉，我無法回答以上問題，請聯絡8855。' in response_message:
        is_succeed = False
    elif 'Sorry it is out of my knowledge. Please contact 8855 for further assistance' in response_message:
        is_succeed = False
    return is_succeed, response_message


async def general_ask(query):
    if 'answer in english' in query:
        try_answer_questions = [
            {"role": "system", "content": "'The following is a conversation with an AI assistant. "
                                          "The assistant is helpful, creative, clever, and very friendly.'"},
            {"role": "system", "content": "How can I help you"},
            {"role": "user", "content": query},
        ]
        try_answer_response = await completion_async(try_answer_questions, temperature=0.8)
        try_answer_message = try_answer_response["choices"][0]["message"]["content"]
        response_message = try_answer_message + \
                           "\n\nIf the above answer can't help you, please contact +886-2-7745-8888#8855 for further assistance."
    else:
        try_answer_questions = [
            {"role": "system", "content": "以下是一個和AI助理的對話，這個助理非常的有同理心、有創造力並非常友善"},
            {"role": "system", "content": "請問我能如何協助你？"},
            {"role": "user", "content": query},
        ]
        cost, try_answer_response =await completion_async(try_answer_questions, temperature=0.8)
        try_answer_message = try_answer_response["choices"][0]["message"]["content"]
        response_message = try_answer_message + "\n\n如以上回答無法幫助到你，請撥打 +886-2-7745-8888#8855，將有專人為您服務。"
    return response_message
