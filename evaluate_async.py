import asyncio
import timeit
import pandas as pd
from src.faq import ask
from src import GPT_MODEL


excel_path = "src/data/2023-qa.xlsx"
df = pd.read_excel(excel_path)


async def get_answer(question, retry=99):
    status = True
    retry_cnt = 0
    while status:
        try:
            print("= " * 10)
            print(question)
            status, ans = await ask(question, print_message=True)
            print(ans)
            print()
            result = {'question': question, "status": status, 'answer': ans}
            return result
        except Exception as e:
            print(e)
            await asyncio.sleep(60)
            result = {'question': question, "status": False, 'answer': f"Failed to answer {e}"}
            retry_cnt += 1
            if retry_cnt > retry:
                return result


async def main():
    questions = [row['questions'] for _, row in df.iterrows()]
    tasks = [get_answer(question) for question in questions]
    answers = await asyncio.gather(*tasks)
    df_eval = pd.DataFrame(answers)
    df_eval.to_csv(f'src/data/{GPT_MODEL}_async_evaluation.csv', index=False)


if __name__ == "__main__":
    tic = timeit.default_timer()
    asyncio.run(main())
    toc = timeit.default_timer()
    print(f"testing time: {toc - tic}s")
