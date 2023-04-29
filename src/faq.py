import ast
import structlog
import pandas as pd
from scipy import spatial
from . import EMBEDDING_PATH, GPT_MODEL, EMBEDDING_MODEL
import openai
import tiktoken
from googletrans import Translator

language_short_name = {'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan', 'sq': 'Albanian',
                       'am': 'Amharic', 'ar': 'Arabic',
                       'an': 'Aragonese', 'hy': 'Armenian', 'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan',
                       'ay': 'Aymara', 'az': 'Azerbaijani', 'ba': 'Bashkir',
                       'bm': 'Bambara', 'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bh': 'Bihari languages',
                       'bi': 'Bislama', 'bo': 'Tibetan', 'bs': 'Bosnian',
                       'br': 'Breton', 'bg': 'Bulgarian', 'my': 'Burmese', 'ca': 'Catalan; Valencian', 'cs': 'Czech',
                       'ch': 'Chamorro', 'ce': 'Chechen', 'zh': 'Chinese',
                       'cu': 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic',
                       'cv': 'Chuvash', 'kw': 'Cornish', 'co': 'Corsican',
                       'cr': 'Cree', 'cy': 'Welsh', 'cs': 'Czech', 'da': 'Danish', 'de': 'German',
                       'dv': 'Divehi; Dhivehi; Maldivian', 'nl': 'Dutch; Flemish', 'dz': 'Dzongkha',
                       'el': 'Greek-Modern (1453-)', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian',
                       'eu': 'Basque', 'ee': 'Ewe', 'fo': 'Faroese', 'fa': 'Persian',
                       'fj': 'Fijian', 'fi': 'Finnish', 'fr': 'French', 'fy': 'Western Frisian', 'ff': 'Fulah',
                       'Ga': 'Georgian', 'gd': 'Gaelic; Scottish Gaelic', 'ga': 'Irish',
                       'gl': 'Galician', 'gv': 'Manx', 'el': 'Greek-Modern (1453-)', 'gn': 'Guarani', 'gu': 'Gujarati',
                       'ht': 'Haitian; Haitian Creole', 'ha': 'Hausa',
                       'he': 'Hebrew', 'hz': 'Herero', 'hi': 'Hindi', 'ho': 'Hiri Motu', 'hr': 'Croatian',
                       'hu': 'Hungarian', 'hy': 'Armenian', 'ig': 'Igbo', 'is': 'Icelandic',
                       'io': 'Ido', 'ii': 'Sichuan Yi; Nuosu', 'iu': 'Inuktitut', 'ie': 'Interlingue; Occidental',
                       'ia': 'Interlingua (International Auxiliary Language Association)', 'id': 'Indonesian',
                       'ik': 'Inupiaq', 'is': 'Icelandic', 'it': 'Italian',
                       'jv': 'Javanese', 'ja': 'Japanese', 'kl': 'Kalaallisut; Greenlandic', 'kn': 'Kannada',
                       'ks': 'Kashmiri', 'ka': 'Georgian', 'kr': 'Kanuri', 'kk': 'Kazakh',
                       'km': 'Central Khmer', 'ki': 'Kikuyu; Gikuyu', 'rw': 'Kinyarwanda', 'ky': 'Kirghiz; Kyrgyz',
                       'kv': 'Komi', 'kg': 'Kongo', 'ko': 'Korean',
                       'kj': 'Kuanyama; Kwanyama', 'ku': 'Kurdish', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian',
                       'li': 'Limburgan; Limburger; Limburgish', 'ln': 'Lingala',
                       'lt': 'Lithuanian', 'lb': 'Luxembourgish; Letzeburgesch', 'lu': 'Luba-Katanga', 'lg': 'Ganda',
                       'mk': 'Macedonian', 'mh': 'Marshallese',
                       'ml': 'Malayalam', 'mi': 'Maori', 'mr': 'Marathi', 'ms': 'Malay', 'Mi': 'Micmac',
                       'mk': 'Macedonian', 'mg': 'Malagasy', 'mt': 'Maltese',
                       'mn': 'Mongolian', 'mi': 'Maori', 'ms': 'Malay', 'my': 'Burmese', 'na': 'Nauru',
                       'nv': 'Navajo; Navaho', 'nr': 'Ndebele-South; South Ndebele',
                       'nd': 'Ndebele-North; North Ndebele', 'ng': 'Ndonga', 'ne': 'Nepali', 'nl': 'Dutch; Flemish',
                       'nn': 'Norwegian Nynorsk; Nynorsk:Norwegian',
                       'nb': 'Bokmål-Norwegian; Norwegian Bokmål', 'no': 'Norwegian', 'oc': 'Occitan (post 1500)',
                       'oj': 'Ojibwa', 'or': 'Oriya', 'om': 'Oromo',
                       'os': 'Ossetian; Ossetic', 'pa': 'Panjabi; Punjabi', 'fa': 'Persian', 'pi': 'Pali',
                       'pl': 'Polish', 'pt': 'Portuguese', 'ps': 'Pushto; Pashto',
                       'qu': 'Quechua', 'rm': 'Romansh', 'ro': 'Romanian; Moldavian; Moldovan', 'rn': 'Rundi',
                       'ru': 'Russian', 'sg': 'Sango', 'sa': 'Sanskrit',
                       'si': 'Sinhala; Sinhalese', 'sk': 'Slovak', 'sk': 'Slovak', 'sl': 'Slovenian',
                       'se': 'Northern Sami', 'sm': 'Samoan', 'sn': 'Shona', 'sd': 'Sindhi',
                       'so': 'Somali', 'st': 'Sotho-Southern', 'es': 'Spanish; Castilian', 'sq': 'Albanian',
                       'sc': 'Sardinian', 'sr': 'Serbian', 'ss': 'Swati',
                       'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'ty': 'Tahitian', 'ta': 'Tamil',
                       'tt': 'Tatar', 'te': 'Telugu', 'tg': 'Tajik', 'tl': 'Tagalog',
                       'th': 'Thai', 'bo': 'Tibetan', 'ti': 'Tigrinya', 'to': 'Tonga (Tonga Islands)', 'tn': 'Tswana',
                       'ts': 'Tsonga', 'tk': 'Turkmen', 'tr': 'Turkish',
                       'tw': 'Twi', 'ug': 'Uighur; Uyghur', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek',
                       've': 'Venda', 'vi': 'Vietnamese', 'vo': 'Volapük', 'cy': 'Welsh',
                       'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba',
                       'za': 'Zhuang; Chuang', 'zh': 'Chinese', 'zu': 'Zulu'}


def num_tokens(text: str, model: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def calculate_cost(self, query: str, model: str):
    token = num_tokens(query, model)
    return self.cost_per_1k_token * token / 1000


def embedding(query, model: str = EMBEDDING_MODEL):
    return openai.Embedding.create(
        model=model,
        input=query,
    )


def completion(messages, temperature: float = 0, model: str = GPT_MODEL):
    return openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )


def translate(message, language, model="text-davinci-003"):
    prompt = f"Translate {message} into {language}:\n\n"
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=1,
        max_tokens=4097,
        top_p=0.2,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response["choices"][0]["text"]


class FaqAnswerBot:
    def __init__(self, text, top_n=15):
        self.logger = structlog.getLogger()
        self.question = text
        self.language = self.detect_text_language()
        self.embedding_df = pd.read_csv(EMBEDDING_PATH)
        self.embedding_df['embedding'] = self.embedding_df['embedding'].apply(ast.literal_eval)
        self.top_n_recommended, self.top_n_relatatednesses = self.strings_ranked_by_relatedness(
            text, self.embedding_df, top_n=top_n
        )
        self.feedback = "很抱歉，我無法回答以上問題，請聯絡02-7745-8855，將有專人為您服務。" \
            if self.language == "Chinese" else "Sorry it is out of my knowledge. Please contact 02-7745-8855 for further assistance"

    def detect_text_language(self):
        translator = Translator()
        lang = translator.detect(self.question)
        self.logger.info(language_short_name[lang.lang])
        return language_short_name[lang.lang]

    @staticmethod
    def strings_ranked_by_relatedness(
            query: str,
            df: pd.DataFrame,
            relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
            top_n: int = 15
    ) -> tuple[list[str], list[float]]:
        """Returns a list of strings and relatednesses, sorted from most related to least."""
        query_embedding_response = embedding(query)
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
            model: str,
            token_budget: int
    ) -> str:
        """Return a message for GPT, with relevant source texts pulled from a dataframe."""

        introduction = f'The following is a conversation with an AI assistant. ' \
                       f'The assistant is helpful, creative, clever, and very friendly.' \
                       f'運用以下的FAQ來回答問題，並附上聯絡人資訊。' \
                       f'如果無法利用FAQ來回答問題，請回答：{self.feedback}\n)'
        question = f"\n\nQuestion: {query}"
        message = introduction
        for string, relatatedness in zip(self.top_n_recommended, self.top_n_relatatednesses):
            next_article = f'\n\nFAQ:\n"""\n{string}\n"""'
            if num_tokens(message + next_article + question, model=model) > token_budget:
                break
            else:
                message += next_article
        return message + question

    def answer(
            self,
            model: str = GPT_MODEL,
            token_budget: int = 4096 - 500,
            print_message: bool = False,
            recommend_question_cnt=2
    ) -> (bool, str):
        """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
        is_succeed = True
        message = self.query_message(query=self.question, model=model, token_budget=token_budget)
        if print_message:
            print(message)
        messages = [
            {"role": "system", "content": "回答有關FAQ的問題"},
            {"role": "user", "content": message},
        ]
        response = completion(messages)
        response_message = response["choices"][0]["message"]["content"]
        if self.feedback in response_message:
            is_succeed = False
        if is_succeed:
            recommend_strings = "\nThese are referencing FAQ"
        else:
            recommend_strings = "\nThese are the recommended FAQ"
        try:
            for ind, recommend in enumerate(self.top_n_recommended[:recommend_question_cnt]):
                question = recommend.split('\n')[0].split("Question:")[1]
                ans = recommend.split('\n')[1]
                self.logger.info(f"About to translate {question}")
                transcribed_question = translate(question,
                                                 language=self.language) if self.language != "Chinese" else question
                self.logger.info(f"About to translate {ans}")
                transcribed_ans = translate(ans, language=self.language) if self.language != "Chinese" else ans
                recommend_strings += f"\nRecommend Ans {ind + 1}:\n{transcribed_question}\n{transcribed_ans}"
        except Exception as e:
            self.logger.error(e)
            recommend_strings = ""
        response_message += recommend_strings
        return is_succeed, response_message

    # def general_ask(self, query):
    #     if 'answer in english' in query:
    #         try_answer_questions = [
    #             {"role": "system", "content": "'The following is a conversation with an AI assistant. "
    #                                           "The assistant is helpful, creative, clever, and very friendly.'"},
    #             {"role": "system", "content": "How can I help you"},
    #             {"role": "user", "content": query},
    #         ]
    #         cost, try_answer_response = self.openai_completion_service.completion_async(try_answer_questions,
    #                                                                                     temperature=0.8,
    #                                                                                     model='text-davinci-003')
    #         self.total_cost += cost
    #         try_answer_message = try_answer_response["choices"][0]["message"]["content"]
    #         response_message = try_answer_message + \
    #                            "\n\nIf the above answer can't help you, please contact +886-2-7745-8888#8855 for further assistance."
    #     else:
    #         try_answer_questions = [
    #             {"role": "system", "content": "以下是一個和AI助理的對話，這個助理非常的有同理心、有創造力並非常友善"},
    #             {"role": "system", "content": "請問我能如何協助你？"},
    #             {"role": "user", "content": query},
    #         ]
    #         cost, try_answer_response = self.openai_completion_service.completion_async(try_answer_questions,
    #                                                                                     temperature=0.8)
    #         self.total_cost += cost
    #         try_answer_message = "無法從FAQ中尋找到解答，幫你擴大搜索範圍\n"
    #         try_answer_message += try_answer_response["choices"][0]["message"]["content"]
    #         response_message = try_answer_message + "\n\n如以上回答無法幫助到你，請撥打 +886-2-7745-8855，將有專人為您服務。"
    #     return response_message
