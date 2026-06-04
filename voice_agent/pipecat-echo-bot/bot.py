import asyncio
import os
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from openai import OpenAI
from pipecat.workers.base_worker import WorkerParams
from pipecat.frames.frames import TTSSpeakFrame, EndFrame
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.transports.local.audio import (
    LocalAudioTransport,
    LocalAudioTransportParams,
)

load_dotenv()


client = OpenAI()

def get_latest_ai_update(user_message: str = "Tell me about Chandan Kumar"):
    context = """
Contact
7233022562 (Home)
chandan.kumar.eee15@itbhu.ac.in
www.linkedin.com/in/chandan-kumar-100a78111 (LinkedIn)
Top Skills
Natural Language Processing (NLP)
Artificial Neural Networks
Network Security
Languages
English
Hindi
Certifications
Introduction to Generative AI
Advanced Data Structures in Java
Object Oriented Programming in Java
Asking for Feedback as an Employee
Problem Solving (Advanced) Certificate
Chandan Kumar
Senior Software Engineer at BrowserStack | LLMs, AI Agents & RAG
| Certified Quantum Computing and ML Engg (IIT Delhi)
Mumbai, Maharashtra, India
Summary
Experienced Software Engineer with a demonstrated history of
working in the financial services industry. Skilled in Data structure
and algorithm, Spring boot, Django, Machine learning enthusiastic,
Web Design, and Management. Strong engineering professional with
a Bachelor's in Electrical and Electronics Engineering from Indian
Institute of Technology (Banaras Hindu University), Varanasi.
Experience
BrowserStack
4 years 3 months
Senior Software Engineer(AI Integration)
October 2024 - Present (1 year 8 months)
Full Stack Engineer
March 2022 - September 2024 (2 years 7 months)
Mumbai, Maharashtra, India
J.P. Morgan
2 years 9 months
Associate Software Engineer
January 2022 - March 2022 (3 months)
Mumbai, Maharashtra, India
Software engineer 2
February 2021 - January 2022 (1 year)
Mumbai, Maharashtra, India
Software Engineer
July 2019 - February 2021 (1 year 8 months)
Mumbai Area, India
JPMorgan Chase & Co.
Summer Intern
May 2018 - July 2018 (3 months)
Mumbai Area, India
Education
Indian Institute of Technology (Banaras Hindu University), Varanasi
Bachelor's Degree, Electrical and Electronics Engineering (2015 - 2019)
Indian Institute of Technology, Delhi
Quantum computing and machine learning (July 2022 - January 2023)
BAL VIDYA NIKETAN
High School (2009 - 2014)
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are an assistant helping with questions about Chandan Kumar. Use the profile details below to answer questions always reply in Hindi language.\n\nRules:\n- For greetings (Hi, Hello), respond warmly and set know=True.\n- Set know=True if you can answer from the profile details.\n- Set know=False ONLY if the question cannot be answered from the profile details.\n\nProfile:\n{context}"},
            {"role": "user", "content": user_message},
        ]
    )
    return response.choices[0].message.content

async def main():
    transport = LocalAudioTransport(
        LocalAudioTransportParams(audio_out_enabled=True)
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="993f1a41-d89b-4e9f-a9c0-7290615c4038",
    )

    pipeline = Pipeline([
        tts,
        transport.output(),
    ])

    worker = PipelineWorker(pipeline, enable_rtvi=False)

    async def send_text():
        await asyncio.sleep(1)
        text = await asyncio.to_thread(get_latest_ai_update)
        await worker.queue_frame(TTSSpeakFrame(text))
        await asyncio.sleep(15)
        await worker.queue_frame(EndFrame())

    loop = asyncio.get_event_loop()
    await asyncio.gather(
        worker.run(WorkerParams(loop=loop)),
        send_text(),
    )


if __name__ == "__main__":
    asyncio.run(main())
