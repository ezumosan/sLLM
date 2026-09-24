import ollama
import time
import os
import csv
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
            "seed": seed
        }
    )
    return response["message"]["content"]

#logの保存を定義
def save_log(
    model,
    input_question,
    temperature,
    repeat_penalty,
    num_predict,
    seed,
    ans1,
    ans2,
    time_taken,
):
  filepath = "../../results/logs/2sLLM_log.csv"
  os.makedirs(os.path.dirname(filepath), exist_ok=True)
  file_exists = os.path.isfile(filepath)

  with open(filepath, mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    if not file_exists:
      writer.writerow([
          "Model",
          "Input Question",
          "Temperature",
          "Repeat Penalty",
          "Num Predict",
          "Seed",
          "Answer from Ollama",
          "Feedback from Ollama",
          "Time Taken (seconds)",
      ])
    writer.writerow([
        model,
        input_question,
        temperature,
        repeat_penalty,
        num_predict,
        seed,
        ans1,
        ans2,
        time_taken,
    ])
    print(f"Log saved to {filepath}")

#プログラム実行の部分(メイン)

user_question = input("Please enter your question: ")
repeat_num = int(input("How many times do you want to repeat the process? "))

for i in range(repeat_num):
    print(f"Iteration {i + 1}/{repeat_num}")
    

    user_query = run_ollama(
        system_prompt="You are a helpful assistant. Please answer the user's question to the best of your ability. The answer should be in 512 tokens. If it exceeds 512 tokens, it won't be available for the user.",
        user_prompt=user_question
    )
    print("Answer from Ollama:", user_query)
    print("------------------------------")
    start_time = time.perf_counter()
    critic_prompt = (
        f"質問: {user_question}\n回答: {user_query}\n上記の内容を検証してください。"
    )
    model_feedback = run_ollama(
        system_prompt=(
            "You are a strict, objective fact-checker. Examine the provided answer against the question and identify any factual errors.The answer should be in 512 tokens. If it exceeds 512 tokens, it won't be available for the user."
        ),
        user_prompt=critic_prompt,
    )
    print("Feedback from Ollama:", model_feedback)

    print("------------------------------")

    end_time = time.perf_counter()
    print("Time taken: {:.2f} seconds".format(end_time - start_time))

    print("------------------------------")
    save_log(use_model, user_question, temperature_model, repeat_penalty_model, num_predict_model, seed_model, user_query, model_feedback, end_time - start_time)