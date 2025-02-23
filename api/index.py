# Imports consolidated and organized
from fastapi import FastAPI, HTTPException
from elevenlabs import (
    ElevenLabs, 
    ConversationalConfig,
    AgentConfig, 
    PromptAgent
)
from openai import OpenAI
import os
from typing import Optional, Dict, Any

class ElevenLabsManager:
    def __init__(self, api_key: str):
        self.client = self._init_client(api_key)
        
    def _init_client(self, key: str) -> Optional[ElevenLabs]:
        try:
            return ElevenLabs(api_key=key)
        except Exception as e:
            print(f"Error initializing client: {str(e)}")
            return None
            
    def create_agent(self, name: str, prompt_text: str = "hello") -> Optional[str]:
        try:
            agent = self.client.conversational_ai.create_agent(
                name=name,
                conversation_config=self._create_config(prompt_text)
            )
            return agent.agent_id
        except Exception as e:
            print(f"Error creating agent: {str(e)}")
            return None
            
    def update_prompt(self, agent_id: str, prompt_text: str = "hello") -> bool:
        try:
            if not self.client:
                print("Client not initialized")
                return False
            self.client.conversational_ai.update_agent(
                agent_id=agent_id,
                conversation_config=self._create_config(prompt_text)
            )
            return True
        except Exception as e:
            print(f"Error updating prompt: {str(e)}")
            return False
            
    @staticmethod
    def _create_config(prompt_text: str) -> ConversationalConfig:
        return ConversationalConfig(
            agent=AgentConfig(
                prompt=PromptAgent(prompt=prompt_text)
            )
        )

    def get_latest_conversation(self, agent_id: str):
        try:
            if not self.client:
                print("Client not initialized")
                return None
            # Get conversation history
            conversations = self.client.conversational_ai.get_conversations(
                agent_id=agent_id
            )
            
            # Get the most recent conversation (first in the list)
            if hasattr(conversations, 'conversations') and conversations.conversations:
                latest_conversation = conversations.conversations[0]
                return self.client.conversational_ai.get_conversation(
                    conversation_id=latest_conversation.conversation_id
                )
            return None
        except Exception as e:
            print(f"Error getting latest conversation: {str(e)}")
            return None

    def get_latest_message(self, agent_id: str) -> Optional[str]:
        try:
            conversation = self.get_latest_conversation(agent_id)
            if not conversation or not conversation.transcript:
                return None
                
            # Find the most recent user message
            for message in reversed(conversation.transcript):
                if message.role != 'agent':
                    return message.message
                    
            return None
            
        except Exception as e:
            print(f"Error getting recent message: {str(e)}")
            return None

app = FastAPI()

@app.get("/api/py/helloFastApi")
async def hello_fast_api() -> Dict[str, str]:
    return {"message": "Hello from FastAPI"}

@app.get("/api/py/helloFastApi3")
async def hello_fast_api3() -> Dict[str, Any]:
    try:
        # Initialize OpenAI client
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured"
            )
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "write a haiku about ai"}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        
        # Initialize ElevenLabs client
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=500, 
                detail="ElevenLabs API key not configured"
            )
            
        elevenlabs_manager = ElevenLabsManager(elevenlabs_api_key)
        
        # Update the hardcoded agent's prompt
        if not elevenlabs_manager.update_prompt(
            agent_id="hR7KugGQ4M5SrgTyTrm2",
            prompt_text=ai_response
        ):
            raise HTTPException(
                status_code=500, 
                detail="Failed to update agent prompt"
            )
        
        # Get the latest message
        latest_message = elevenlabs_manager.get_latest_message("hR7KugGQ4M5SrgTyTrm2")
        
        return {
            "message": "Hello from FastAPI 3",
            "ai_response": ai_response,
            "latest_message": latest_message,
            "status": "ElevenLabs agent updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))