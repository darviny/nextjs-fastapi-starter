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
        self.client = self.init_client(api_key)
    
    def init_client(self, api_key: str) -> Optional[ElevenLabs]:
        try:
            return ElevenLabs(api_key=api_key)
        except Exception as e:
            print(f"Error initializing client: {str(e)}")
            return None
            
    def update_prompt(self, agent_id: str, prompt_text: str) -> bool:
        if not self.client:
            return False
        return updatePrompt(self.client, agent_id, prompt_text)
        
    def get_latest_message(self, agent_id: str) -> Optional[str]:
        if not self.client:
            return None
        messages = getMessages(self.client, agent_id)
        if not messages:
            return None
        return messages[-1]

def createAgent(client, name, prompt_text="hello"):
	try:
		agent = client.conversational_ai.create_agent(
			name=name,
			conversation_config=ConversationalConfig(
				agent=AgentConfig(
					prompt=PromptAgent(
						prompt=prompt_text
					)
				)
			)
		)
		return agent.agent_id
	except Exception as e:
		print(f"Error creating agent: {str(e)}")
		return None

def updatePrompt(client, agent_id, prompt_text="hello"):
	try:
		client.conversational_ai.update_agent(
			agent_id=agent_id,
			conversation_config=ConversationalConfig(
				agent=AgentConfig(
					prompt=PromptAgent(
						prompt=prompt_text
					)
				)
			)
		)
		return True
	except Exception as e:
		print(f"Error updating prompt: {str(e)}")
		return False

def getTranscript(client, conversation_id, agent_id):
	try:
		# Get conversation history
		conversation_history = client.conversational_ai.get_conversations(
			agent_id=agent_id
		)

		# Get details for the specific conversation
		conversation_detail = client.conversational_ai.get_conversation(
			conversation_id=conversation_id
		)
		return conversation_detail
	except Exception as e:
		print(f"Error getting transcript: {str(e)}")
		return None

def getLatestConversation(client, agent_id):
	try:
		# Get conversation history
		conversations = client.conversational_ai.get_conversations(
			agent_id=agent_id
		)
		
		# Get the most recent conversation (first in the list)
		if hasattr(conversations, 'conversations') and conversations.conversations:
			latest_conversation = conversations.conversations[0]
			return client.conversational_ai.get_conversation(
				conversation_id=latest_conversation.conversation_id
			)
		return None
	except Exception as e:
		print(f"Error getting latest conversation: {str(e)}")
		return None

def getMessages(client, agent_id: str) -> Optional[list[str]]:
    try:
        conversation = getLatestConversation(client, agent_id)
        if not conversation or not conversation.transcript:
            return None
            
        # Return messages with role prefixes
        messages = [f"{message.role}: {message.message}" for message in conversation.transcript]
        return messages
        
    except Exception as e:
        print(f"Error getting conversation messages: {str(e)}")
        return None

def getEvals(client, agent_id):
	try:
		conversation = getLatestConversation(client, agent_id)
		if not conversation or not conversation.analysis or not conversation.analysis.evaluation_criteria_results:
			return None
			
		# Return just the evaluation criteria IDs in a list
		evals = list(conversation.analysis.evaluation_criteria_results.keys())
		return evals
		
	except Exception as e:
		print(f"Error getting conversation evaluations: {str(e)}")
		return None

def getDataCollections(client, agent_id):
	try:
		conversation = getLatestConversation(client, agent_id)
		if not conversation or not conversation.analysis or not conversation.analysis.data_collection_results:
			return None
			
		# Return just the data collection IDs in a list
		results = list(conversation.analysis.data_collection_results.keys())
		return results
		
	except Exception as e:
		print(f"Error getting data collection results: {str(e)}")
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
        
        # Initialize ElevenLabs client first to get messages
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=500, 
                detail="ElevenLabs API key not configured"
            )
            
        elevenlabs_manager = ElevenLabsManager(elevenlabs_api_key)
        messages = elevenlabs_manager.get_latest_message("hR7KugGQ4M5SrgTyTrm2")
        
        if not messages:
            messages = "write a haiku about ai"  # fallback content
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call with the messages
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": messages}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        
        # Update the agent's prompt
        if not elevenlabs_manager.update_prompt(
            agent_id="hR7KugGQ4M5SrgTyTrm2",
            prompt_text=ai_response
        ):
            raise HTTPException(
                status_code=500, 
                detail="Failed to update agent prompt"
            )
        
        # Get the latest message after update
        latest_message = elevenlabs_manager.get_latest_message("hR7KugGQ4M5SrgTyTrm2")
        
        return {
            "message": "Hello from FastAPI 3",
            "ai_response": ai_response,
            "latest_message": latest_message,
            "status": "ElevenLabs agent updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))