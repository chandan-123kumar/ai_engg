import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace

load_dotenv()




async def main():
    agent = Agent(name="Joker", instructions="you are a joker", model="gpt-4o-mini")
    with trace("tell me a joke"):
        result = await Runner.run(agent, "tell me a joke")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())




