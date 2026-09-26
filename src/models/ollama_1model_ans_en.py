import ollama
import time
import os
import csv
import re
from datetime import datetime
#モデルのデフォルトパラメータを操作
#正式のモデル名はOllamaのドキュメントを参照すること。
use_model = "phi3.5"  
temperature_model = 0.1
repeat_penalty_model = 1.15
num_predict_model = 512
seed_model = -1
#Ollama実行の関数を定義。
def run_ollama(
        system_prompt, 
        user_prompt, 
        model=use_model, 
        temperature=temperature_model, 
        repeat_penalty=repeat_penalty_model, 
        num_predict=num_predict_model,
        seed=seed_model
        ):
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": temperature,
            "repeat_penalty": repeat_penalty,
            "num_predict": num_predict,
            "seed": seed,
            "stop": ["\n\n", "\n", "User:"]
        }
    )
    return response["message"]["content"]

# <ans>タグから回答を抽出する関数
def extract_answer(raw_output):
    match = re.search(r"<ans>(.*?)</ans>", raw_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # stopで</ans>が切られた場合のフォールバック
    match_open = re.search(r"<ans>(.*)", raw_output, re.DOTALL)
    if match_open:
        return match_open.group(1).strip()
    return raw_output.strip()

# 評価ログの保存を定義
def save_eval_log(
    timestamp,
    model,
    input_question,
    extracted_answer,
    raw_output,
    seed,
    time_taken,
):
  filepath = os.path.join(os.path.dirname(__file__), "..", "..", "results" , "logs", "1model_ans_accuracy" , "1model_ans_en_log.csv")
  filepath = os.path.normpath(filepath)
  os.makedirs(os.path.dirname(filepath), exist_ok=True)
  file_exists = os.path.isfile(filepath)

  with open(filepath, mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    if not file_exists:
      writer.writerow([
          "Timestamp",
          "Model",
          "Input Question",
          "Extracted Answer",
          "Raw Output",
          "Seed",
          "Time Taken (seconds)",
      ])
    writer.writerow([
        timestamp,
        model,
        input_question,
        extracted_answer,
        raw_output,
        seed,
        f"{time_taken:.2f}",
    ])
    print(f"Log saved to {filepath}")

#プログラム実行の部分(メイン)

user_question = input("Please enter your question: ")
repeat_num = int(input("How many times do you want to repeat the process? "))

for i in range(repeat_num):
    print(f"Iteration {i + 1}/{repeat_num}")
    start_time = time.perf_counter()

    user_query = run_ollama(
        system_prompt="""You are a precise question-answering assistant.
Answer the user's question directly and concisely.

Rules:
1. Extract ONLY the core answer (entity, person's name, year, or term) in English and enclose it inside <ans> and </ans> tags.
2. Do NOT output full sentences, preambles, or explanations. Only the tagged entity.
3. If you don't know the answer, respond nothing.

Example:
User: Who was the first president of the United States?
Assistant: <ans>George Washington</ans>
User: Where is the Eiffel Tower located?
Assistant: <ans>Paris, France</ans>
""",
        user_prompt=user_question
    )

    end_time = time.perf_counter()
    time_taken = end_time - start_time
    extracted = extract_answer(user_query)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Extracted Answer: {extracted}")
    print(f"Raw Output: {user_query}")
    print(f"Time taken: {time_taken:.2f} seconds")
    print("------------------------------")

    save_eval_log(timestamp, use_model, user_question, extracted, user_query, seed_model, time_taken)