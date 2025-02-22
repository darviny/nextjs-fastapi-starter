from fastapi import FastAPI, HTTPException
from elevenlabs import ElevenLabs
from elevenlabs import ConversationalConfig
from elevenlabs import AgentConfig
from elevenlabs import PromptAgent
from openai import OpenAI
import os

# Initialize FastAPI app - no need to modify docs_url for Vercel
app = FastAPI()

@app.get("/api/py/helloFastApi")
async def hello_fast_api():
    return {"message": "Hello from FastAPI"}

@app.get("/api/py/helloFastApi3")
async def hello_fast_api3():
    try:
        # Initialize OpenAI client - Vercel automatically loads environment variables
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call
        completion = await client.chat.completions.create(
            model="gpt-o3-mini",
            messages=[
                {"role": "user", "content": "write a haiku about ai"}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        
        # Initialize ElevenLabs client
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
            
        elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
        
        # Update ElevenLabs agent
        try:
            elevenlabs_client.conversational_ai.update_agent(
                agent_id="hR7KugGQ4M5SrgTyTrm2",
                conversation_config=ConversationalConfig(
                    agent=AgentConfig(
                        prompt=PromptAgent(
                            prompt="hello"
                        )
                    )
                )
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ElevenLabs API error: {str(e)}")
        
        return {
            "message": "Hello from FastAPI 3",
            "ai_response": ai_response,
            "status": "ElevenLabs agent updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))