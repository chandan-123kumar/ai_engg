from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    print(f"Getting weather for {city}...")
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[get_weather],
    system_prompt="You are a helpful assistant for math problems",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is 2+2?"}]}
)
print(result["messages"][-1].content_blocks)


