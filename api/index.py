from fastapi import FastAPI
from elevenlabs import ElevenLabs
from elevenlabs import ConversationalConfig
from elevenlabs import AgentConfig
from elevenlabs import PromptAgent
from openai import OpenAI
import os

app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}

@app.get("/api/py/helloFastApi3")
def hello_fast_api2():
    # Get API key from environment variable
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"error": "API key not configured"}
        
    client = ElevenLabs(api_key=api_key)        
    try:
        client.conversational_ai.update_agent(
            agent_id="hR7KugGQ4M5SrgTyTrm2",
            conversation_config=ConversationalConfig(
                agent=AgentConfig(
                    prompt=PromptAgent(
                        prompt="hello"
                    )
                )
            )
        )
        return {"message": "Hello from FastAPI 3"}
    except Exception as e:
        return {"error": str(e)}