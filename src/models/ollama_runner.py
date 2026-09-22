import ollama
import time
import os
import csv

start_time = time.perf_counter()
use_model = "phi3.5"  # You can change this to the desired model

def run_ollama(
        system_prompt, 
        user_prompt, 
        model=use_model, 
        temperature=0.1, 
        repeat_penalty=1.15, 
        num_predict=-1
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
            "num_predict": num_predict
        }
    )
    return response["message"]["content"]

def save_log(model,input_question, ans1, ans2, time_taken):
    filepath = "../../data/logs/2sLLM_log.csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Model", "Input Question", "Answer from Ollama", "Feedback from Ollama", "Time Taken (seconds)"])
        writer.writerow([model, input_question, ans1, ans2, time_taken])
        print(f"Log saved to {filepath}")

user_question = input("Please enter your question: ")

user_query = run_ollama(
    system_prompt="You are a helpful assistant. Please answer the user's question to the best of your ability.",
    user_prompt=user_question
)
print("Answer from Ollama:", user_query)
print("------------------------------")
model_feedback = run_ollama(
    system_prompt="You are a strict checker. Please verify the answer provided by the assistant and provide feedback.",
    user_prompt=user_query
)
print("Feedback from Ollama:", model_feedback)

print("------------------------------")

end_time = time.perf_counter()
print("Time taken: {:.2f} seconds".format(end_time - start_time))