import openai
from . import GPT_MODEL, EMBEDDING_MODEL, num_tokens


class OpenAIService:
    def __init__(self, cost_per_1k_token):
        self.cost_per_1k_token = cost_per_1k_token

    def calculate_cost(self, query: str, model: str):
        token = num_tokens(query, model)
        return self.cost_per_1k_token * token / 1000


class OpenAIEmbeddingService(OpenAIService):
    def embedding(self, query, model: str = GPT_MODEL):
        cost = self.calculate_cost(query, model)
        query_response = openai.Embedding.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        return cost, query_response


class OpenAICompletionService(OpenAIService):
    def completion(self, messages, temperature: float = 0, model: str = GPT_MODEL):
        message_string = ''
        for line in messages:
            message_string += str(line)
        cost = self.calculate_cost(message_string, model)
        query_response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return cost, query_response
