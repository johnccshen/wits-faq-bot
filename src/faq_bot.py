import ast  # for converting embeddings saved as strings back to arrays
import structlog
import openai
import pandas as pd  # for storing text and embeddings data
from scipy import spatial  # for calculating vector similarities for search
from . import EMBEDDING_PATH, GPT_MODEL, num_tokens
from src.openai_service import OpenAIEmbeddingService, OpenAICompletionService

df_embedding = pd.read_csv(EMBEDDING_PATH)
# convert embeddings from CSV str type back to list type
df_embedding['embedding'] = df_embedding['embedding'].apply(ast.literal_eval)
logger = structlog.getLogger()


class FaqBot:
    def __init__(self):
        self.total_cost = 0
        self.openai_embedding_service = OpenAIEmbeddingService(0.004)
        self.openai_completion_service = OpenAICompletionService(0.002)

    def strings_ranked_by_relatedness(
            self,
            query: str,
            df: pd.DataFrame,
            relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
            top_n: int = 15
    ) -> tuple[list[str], list[float]]:
        """Returns a list of strings and relatednesses, sorted from most related to least."""
        cost, query_embedding_response = self.openai_embedding_service.embedding(query)
        self.total_cost += cost
        query_embedding = query_embedding_response["data"][0]["embedding"]
        strings_and_relatednesses = [
            (row["text"], relatedness_fn(query_embedding, row["embedding"]))
            for i, row in df.iterrows()
        ]
        strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
        strings, relatednesses = zip(*strings_and_relatednesses)
        return strings[:top_n], relatednesses[:top_n]

    def query_message(
            self,
            query: str,
            df: pd.DataFrame,
            model: str,
            token_budget: int
    ) -> str:
        """Return a message for GPT, with relevant source texts pulled from a dataframe."""
        strings, relatednesses = self.strings_ranked_by_relatedness(query, df)
        introduction = 'The following is a conversation with an AI assistant. ' \
                       'The assistant is helpful, creative, clever, and very friendly.' \
                       '運用以下的FAQ來回答問題，並附上聯絡人資訊。' \
                       '如果無法利用FAQ來回答問題，請回答：(很抱歉，我無法回答以上問題，請聯絡8855。' \
                       '\nSorry it is out of my knowledge. Please contact 8855 for further assistance)'
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
            self,
            query: str,
            df: pd.DataFrame = df_embedding,
            model: str = GPT_MODEL,
            token_budget: int = 4096 - 500,
            print_message: bool = False,
    ) -> (bool, str):
        """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
        is_succeed = True
        message = self.query_message(query, df, model=model, token_budget=token_budget)
        if print_message:
            print(message)
        messages = [
            {"role": "system", "content": "回答有關FAQ的問題"},
            {"role": "user", "content": message},
        ]
        cost, response = self.openai_completion_service.completion(messages)
        self.total_cost += cost
        response_message = response["choices"][0]["message"]["content"]
        if '很抱歉，我無法回答以上問題，請聯絡8855。' in response_message:
            is_succeed = False
        elif 'Sorry it is out of my knowledge. Please contact 8855 for further assistance' in response_message:
            is_succeed = False
        if not is_succeed:
            recommend_questions, _ = self.strings_ranked_by_relatedness(query, df, top_n=3)
            recommend_strings = "以下為你找尋最接近的FAQ"
            for ind, recommend in enumerate(recommend_questions):
                recommend_strings += f"\nRecommend Ans {ind+1}:\n{recommend}"
            if "Please contact 8855" in response_message:
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=f"Translate this into English:\n\n{recommend_strings}\n\n1.",
                    temperature=0.3,
                    max_tokens=100,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                logger.info(response)
            response_message += recommend_strings
        return is_succeed, response_message

    def general_ask(self, query):
        if 'answer in english' in query:
            try_answer_questions = [
                {"role": "system", "content": "'The following is a conversation with an AI assistant. "
                                              "The assistant is helpful, creative, clever, and very friendly.'"},
                {"role": "system", "content": "How can I help you"},
                {"role": "user", "content": query},
            ]
            cost, try_answer_response = self.openai_completion_service.completion(try_answer_questions, temperature=0.8, model='text-davinci-003')
            self.total_cost += cost
            try_answer_message = try_answer_response["choices"][0]["message"]["content"]
            response_message = try_answer_message + \
                               "\n\nIf the above answer can't help you, please contact +886-2-7745-8888#8855 for further assistance."
        else:
            try_answer_questions = [
                {"role": "system", "content": "以下是一個和AI助理的對話，這個助理非常的有同理心、有創造力並非常友善"},
                {"role": "system", "content": "請問我能如何協助你？"},
                {"role": "user", "content": query},
            ]
            cost, try_answer_response = self.openai_completion_service.completion(try_answer_questions, temperature=0.8)
            self.total_cost += cost
            try_answer_message = "無法從FAQ中尋找到解答，幫你擴大搜索範圍\n"
            try_answer_message += try_answer_response["choices"][0]["message"]["content"]
            response_message = try_answer_message + "\n\n如以上回答無法幫助到你，請撥打 +886-2-7745-8855，將有專人為您服務。"
        return response_message
