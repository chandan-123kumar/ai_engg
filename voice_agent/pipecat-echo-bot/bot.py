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
def get_latest_ai_update():
    # This function can be implemented to fetch the latest AI updates from a source
    # For now, it returns a static message
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides the latest AI updates."
            },
            {
                "role": "user",
                "content": "What is the latest AI update? answer in less than 20 words"
            } ]
    )
    return response.choices[0].message.content

async def main():
    transport = LocalAudioTransport(
        LocalAudioTransportParams(audio_out_enabled=True)
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",
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
