from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv()

SYSTEM_PROMPT = """You are a literary data assistant.

## Capabilities

- `fetch_text_from_url`: loads document text from a URL into the conversation.
Do not guess line counts or positions—ground them in tool results from the saved file.
"""

from tool import fetch_text_from_url

agent = create_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is 2+2?"}]}
)
print(result["messages"][-1].content_blocks)



model = init_chat_model(
    "gemini-3.1-pro-preview",
    model_provider="google-genai",
    temperature=0.5,
    timeout=600,
    max_tokens=25000,
    streaming=True,
)


