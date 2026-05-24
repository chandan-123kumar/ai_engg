from dotenv import load_dotenv
import os
from openai import OpenAI
from pypdf import PdfReader
from pydantic import BaseModel
import requests
import gradio as gr




text_file = "src/doc/me.txt"
reader = PdfReader("src/doc/linkedin.pdf")
text = ""

class ProfileAnswer(BaseModel):
    know: bool
    answer: str

def dump_to_text():
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)    


def get_context():
    summery = ""
    with open(text_file, "r", encoding="utf-8") as f:
        summery = f.read()
    return summery
    


def send_to_pushOver(message):
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER"),
        "message": message
    }
    requests.post(url, data)

def record_question(message):
    return message


def get_structured_prompt(user_message: str) -> list[dict]:
    context = get_context()
    return [
        {"role": "system", "content": f"You are an assistant helping with questions about the chandan kumar with details here:\n\n{context}"},
        {"role": "user", "content": user_message}
        
    ]


def call_open_ai(message):
    client = OpenAI()
    response = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=get_structured_prompt(message),
        response_format=ProfileAnswer
    )
    return response.choices[0].message.parsed

    

def chat_with_ai(message, history):
    response = call_open_ai(message)
    if not response.know:
        send_to_pushOver("I don't know the answer to your question: " + message)
        return "request real chandan kumar to answer this question: " + message
    return response.answer


def main():
    load_dotenv()
    gr.ChatInterface(chat_with_ai).launch()
    

if __name__ == "__main__":
    main()