import asyncio

import pandas as pd
from src.faq import ask


excel_path = "src/data/2023-qa.xlsx"
df = pd.read_excel(excel_path)


async def get_answer(question):
    try:
        print("= " * 10)
        print(question)
        status, ans = await ask(question)
        print(ans)
        print()
        result = {'question': question, "status": status, 'answer': ans}
    except Exception as e:
        result = {'question': question, "status": False, 'answer': f"Failed to answer {e}"}
    return result


async def save(tasks):
    answers = asyncio.gather(*tasks)
    return answers


async def main():
    questions = [row['詢問內容摘要'] for _, row in df.iterrows()]
    tasks = [get_answer(question) for question in questions]
    answers = await save(tasks)
    df_eval = pd.DataFrame(answers)
    df_eval.to_csv('src/data/async_evaluation.csv', index=False)


if __name__ == "__main__":
    asyncio.run(main())
