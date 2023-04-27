import pandas as pd
from src.faq_bot import FaqBot


excel_path = "data/2023-qa.xlsx"
df = pd.read_excel(excel_path)


if __name__ == "__main__":
    answers = []
    bot = FaqBot()
    for ind, row in df.iterrows():
        q = row['詢問內容摘要']
        try:
            print("= "*5 + str(ind) + " ="*5)
            print(q)
            status, ans = bot.ask(q)
            print(ans)
            print()
            answers.append({'question': q, "status": status, 'answer': ans})
        except Exception as e:
            print(f"Question {ind} failed to process")
            answers.append({'question': ind, "status": False, 'answer': "Failed to answer"})

    df_eval = pd.DataFrame(answers)
    df_eval.to_csv('data/evaluation.csv', index=False)
