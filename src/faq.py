import ast
import structlog
import pandas as pd
from scipy import spatial
from . import EMBEDDING_PATH, GPT_MODEL, EMBEDDING_MODEL
import openai
import tiktoken
from googletrans import Translator

language_short_name_list = [
    ('ab', 'Abkhaz'),
    ('aa', 'Afar'),
    ('af', 'Afrikaans'),
    ('ak', 'Akan'),
    ('sq', 'Albanian'),
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('an', 'Aragonese'),
    ('hy', 'Armenian'),
    ('as', 'Assamese'),
    ('av', 'Avaric'),
    ('ae', 'Avestan'),
    ('ay', 'Aymara'),
    ('az', 'Azerbaijani'),
    ('bm', 'Bambara'),
    ('ba', 'Bashkir'),
    ('eu', 'Basque'),
    ('be', 'Belarusian'),
    ('bn', 'Bengali'),
    ('bh', 'Bihari'),
    ('bi', 'Bislama'),
    ('bs', 'Bosnian'),
    ('br', 'Breton'),
    ('bg', 'Bulgarian'),
    ('my', 'Burmese'),
    ('ca', 'Catalan; Valencian'),
    ('ch', 'Chamorro'),
    ('ce', 'Chechen'),
    ('ny', 'Chichewa; Chewa; Nyanja'),
    ('zh', 'Chinese'),
    ('cv', 'Chuvash'),
    ('kw', 'Cornish'),
    ('co', 'Corsican'),
    ('cr', 'Cree'),
    ('hr', 'Croatian'),
    ('cs', 'Czech'),
    ('da', 'Danish'),
    ('dv', 'Divehi; Maldivian;'),
    ('nl', 'Dutch'),
    ('dz', 'Dzongkha'),
    ('en', 'English'),
    ('eo', 'Esperanto'),
    ('et', 'Estonian'),
    ('ee', 'Ewe'),
    ('fo', 'Faroese'),
    ('fj', 'Fijian'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('ff', 'Fula'),
    ('gl', 'Galician'),
    ('ka', 'Georgian'),
    ('de', 'German'),
    ('el', 'Greek, Modern'),
    ('gn', 'Guaraní'),
    ('gu', 'Gujarati'),
    ('ht', 'Haitian'),
    ('ha', 'Hausa'),
    ('he', 'Hebrew (modern)'),
    ('hz', 'Herero'),
    ('hi', 'Hindi'),
    ('ho', 'Hiri Motu'),
    ('hu', 'Hungarian'),
    ('ia', 'Interlingua'),
    ('id', 'Indonesian'),
    ('ie', 'Interlingue'),
    ('ga', 'Irish'),
    ('ig', 'Igbo'),
    ('ik', 'Inupiaq'),
    ('io', 'Ido'),
    ('is', 'Icelandic'),
    ('it', 'Italian'),
    ('iu', 'Inuktitut'),
    ('ja', 'Japanese'),
    ('jv', 'Javanese'),
    ('kl', 'Kalaallisut'),
    ('kn', 'Kannada'),
    ('kr', 'Kanuri'),
    ('ks', 'Kashmiri'),
    ('kk', 'Kazakh'),
    ('km', 'Khmer'),
    ('ki', 'Kikuyu, Gikuyu'),
    ('rw', 'Kinyarwanda'),
    ('ky', 'Kirghiz, Kyrgyz'),
    ('kv', 'Komi'),
    ('kg', 'Kongo'),
    ('ko', 'Korean'),
    ('ku', 'Kurdish'),
    ('kj', 'Kwanyama, Kuanyama'),
    ('la', 'Latin'),
    ('lb', 'Luxembourgish'),
    ('lg', 'Luganda'),
    ('li', 'Limburgish'),
    ('ln', 'Lingala'),
    ('lo', 'Lao'),
    ('lt', 'Lithuanian'),
    ('lu', 'Luba-Katanga'),
    ('lv', 'Latvian'),
    ('gv', 'Manx'),
    ('mk', 'Macedonian'),
    ('mg', 'Malagasy'),
    ('ms', 'Malay'),
    ('ml', 'Malayalam'),
    ('mt', 'Maltese'),
    ('mi', 'Māori'),
    ('mr', 'Marathi (Marāṭhī)'),
    ('mh', 'Marshallese'),
    ('mn', 'Mongolian'),
    ('na', 'Nauru'),
    ('nv', 'Navajo, Navaho'),
    ('nb', 'Norwegian Bokmål'),
    ('nd', 'North Ndebele'),
    ('ne', 'Nepali'),
    ('ng', 'Ndonga'),
    ('nn', 'Norwegian Nynorsk'),
    ('no', 'Norwegian'),
    ('ii', 'Nuosu'),
    ('nr', 'South Ndebele'),
    ('oc', 'Occitan'),
    ('oj', 'Ojibwe, Ojibwa'),
    ('cu', 'Old Church Slavonic'),
    ('om', 'Oromo'),
    ('or', 'Oriya'),
    ('os', 'Ossetian, Ossetic'),
    ('pa', 'Panjabi, Punjabi'),
    ('pi', 'Pāli'),
    ('fa', 'Persian'),
    ('pl', 'Polish'),
    ('ps', 'Pashto, Pushto'),
    ('pt', 'Portuguese'),
    ('qu', 'Quechua'),
    ('rm', 'Romansh'),
    ('rn', 'Kirundi'),
    ('ro', 'Romanian, Moldavan'),
    ('ru', 'Russian'),
    ('sa', 'Sanskrit (Saṁskṛta)'),
    ('sc', 'Sardinian'),
    ('sd', 'Sindhi'),
    ('se', 'Northern Sami'),
    ('sm', 'Samoan'),
    ('sg', 'Sango'),
    ('sr', 'Serbian'),
    ('gd', 'Scottish Gaelic'),
    ('sn', 'Shona'),
    ('si', 'Sinhala, Sinhalese'),
    ('sk', 'Slovak'),
    ('sl', 'Slovene'),
    ('so', 'Somali'),
    ('st', 'Southern Sotho'),
    ('es', 'Spanish; Castilian'),
    ('su', 'Sundanese'),
    ('sw', 'Swahili'),
    ('ss', 'Swati'),
    ('sv', 'Swedish'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('tg', 'Tajik'),
    ('th', 'Thai'),
    ('ti', 'Tigrinya'),
    ('bo', 'Tibetan'),
    ('tk', 'Turkmen'),
    ('tl', 'Tagalog'),
    ('tn', 'Tswana'),
    ('to', 'Tonga'),
    ('tr', 'Turkish'),
    ('ts', 'Tsonga'),
    ('tt', 'Tatar'),
    ('tw', 'Twi'),
    ('ty', 'Tahitian'),
    ('ug', 'Uighur, Uyghur'),
    ('uk', 'Ukrainian'),
    ('ur', 'Urdu'),
    ('uz', 'Uzbek'),
    ('ve', 'Venda'),
    ('vi', 'Vietnamese'),
    ('vo', 'Volapük'),
    ('wa', 'Walloon'),
    ('cy', 'Welsh'),
    ('wo', 'Wolof'),
    ('fy', 'Western Frisian'),
    ('xh', 'Xhosa'),
    ('yi', 'Yiddish'),
    ('yo', 'Yoruba'),
    ('za', 'Zhuang, Chuang'),
    ('zu', 'Zulu')
]

language_short_name_dict = {pair[0]: pair[1] for pair in language_short_name_list}


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
    prompt = f"Translate this into 1. {language}:\n\n{message}?\n\n1."
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=0.8,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
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
        self.logger.info('Start to detect language')
        lang = translator.detect(self.question)
        self.logger.info(language_short_name_dict.get(lang.lang, "Chinese"))
        return language_short_name_dict.get(lang.lang, "Chinese")

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
        question = f"\n\nQuestion: {query} and reply in {self.language}"
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
            recommend_question_cnt=3
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
        self.logger.info("Getting response from openai")
        response = completion(messages)
        response_message = response["choices"][0]["message"]["content"]
        if self.feedback not in response_message:
            placeholder = "Reference"
        else:
            placeholder = "Recommended"
        recommend_strings = f"\n\n{placeholder} FAQs:"
        try:
            for ind, recommend in enumerate(self.top_n_recommended[:recommend_question_cnt]):
                self.logger.info(recommend)
                ans = recommend.split('Answers:')[1].split("Contacts:")[0]
                question = ans.split('Questions:')[1]
                self.logger.info(f"About to translate {question}")
                transcribed_question = translate(question,
                                                 language=self.language) if self.language != "Chinese" else question
                self.logger.info(f"About to translate {ans}")
                transcribed_ans = translate(ans, language=self.language) if self.language != "Chinese" else ans
                recommend_strings += f"\n\n{placeholder} Ans {ind + 1}:\n{transcribed_question}\n{transcribed_ans}"
        except Exception as e:
            self.logger.error(e)
            recommend_strings = ""
        response_message += recommend_strings
        return is_succeed, response_message

