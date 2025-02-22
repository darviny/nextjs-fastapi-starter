from fastapi import FastAPI

from elevenlabs import ElevenLabs
from elevenlabs import ConversationalConfig
from elevenlabs import AgentConfig
from elevenlabs import PromptAgent

### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}

@app.get("/api/py/helloFastApi3")
def hello_fast_api2():
    return {"message": "Hello from FastAPI 3"}
    client = ElevenLabs(api_key="sk_66480812455c0900881599664d023ac3a46fec1d51358d0f")        
    client.conversational_ai.update_agent(
        agent_id="hR7KugGQ4M5SrgTyTrm2",
        conversation_config=ConversationalConfig(
            agent=AgentConfig(
                prompt=PromptAgent(
                    prompt="hello 2"
                )
            )
        )
    )
