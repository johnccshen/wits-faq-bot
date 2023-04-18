from pathlib import Path
import pandas as pd
import structlog
import subprocess
import shlex

SOURCE_DATA = Path('data/FAQ_JOHN_REVIEW.xlsx')
END = " END"

logger = structlog.getLogger()

if __name__ == "__main__":
    df = pd.read_excel(SOURCE_DATA)
    df['prompt'] = "q:" + df['Question'] + f"\n a:{END}"
    df['completion'] = " " + df['Answer'] + "\n\nContact:" + df["Contact/Phone/Mail"] + END
    df_train = df[['prompt', 'completion']]
    train_csv_filename = "data/train.csv"
    df_train.to_csv(train_csv_filename, index=False)
    cmd = f"openai tools fine_tunes.prepare_data -f {train_csv_filename}"
    subprocess.run(shlex.split(cmd))

