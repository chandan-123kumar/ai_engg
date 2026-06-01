import asyncio
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, trace

load_dotenv()

instructions = ["You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

"You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

"You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."]

def create_agent(name, instruction):
    return Agent(name=name, instructions=instruction, model="gpt-4o-mini")

professional_agent = create_agent("Professional Agent", instructions[0])

# implemet all three agents and run them in parallel to compare their outputs

#conver all the agents to tools and then create a meta agent that uses the tools to get the output from all three agents and then compares the outputs and gives the best one as the final output


#create a an email formattter agent which convert the output to html format and then send


async def invoke_agent(professional_agent, input):
    result = Runner.run_streamed(professional_agent, input=input)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)




if __name__ == "__main__":
    asyncio.run(invoke_agent(professional_agent, "Write a cold sales email"))




