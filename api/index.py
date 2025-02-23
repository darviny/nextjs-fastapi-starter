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

# Agent IDs
LEAD_AGENT = os.environ.get("ELEVENLABS_LEAD_AGENT_ID")
CO_AGENT_1 = os.environ.get("ELEVENLABS_CO_AGENT_1_ID")

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
        
    def get_transcript(self, agent_id: str) -> Optional[Any]:
        if not self.client:
            return None
        conversation = getLatestConversation(self.client, agent_id)
        if conversation:
            print(f"Conversation ID: {conversation.conversation_id}")
            return getTranscript(self.client, conversation.conversation_id, agent_id)
        return None

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

def getTranscript(client, conversation_id, agent_id):
    try:
        # Get details for the specific conversation
        conversation_detail = client.conversational_ai.get_conversation(
            conversation_id=conversation_id
        )
        if conversation_detail and conversation_detail.transcript:
            # Join all messages into a single string
            transcript_text = "\n".join(
                f"{message.role}: {message.message}" 
                for message in conversation_detail.transcript
            )
            return transcript_text
        return None
    except Exception as e:
        print(f"Error getting transcript: {str(e)}")
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
        
        # Initialize ElevenLabs client
        elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=500, 
                detail="ElevenLabs API key not configured"
            )
            
        elevenlabs_manager = ElevenLabsManager(elevenlabs_api_key)
        transcript = elevenlabs_manager.get_transcript(LEAD_AGENT)
        
        # Use transcript or fallback
        message_content = transcript if transcript else "write a haiku about ai"
        print(f"Using message content: {message_content}")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call with the message content
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": message_content}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        
        # Update the agent's prompt
        if not elevenlabs_manager.update_prompt(
            agent_id=LEAD_AGENT,
            prompt_text=ai_response
        ):
            raise HTTPException(
                status_code=500, 
                detail="Failed to update agent prompt"
            )
        
        # Get the latest message after update
        latest_transcript = elevenlabs_manager.get_transcript(LEAD_AGENT)
        
        return {
            "message": "Hello from FastAPI 3",
            "ai_response": ai_response,
            "latest_message": latest_transcript,
            "status": "ElevenLabs agent updated successfully"
        }
        
    except Exception as e:
        print(f"Error in hello_fast_api3: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
def test_elevenlabs_functions():
    # Get API key from environment variable
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable not set")
        return

    # Initialize ElevenLabs manager
    manager = ElevenLabsManager(api_key)
    if not manager.client:
        print("Failed to initialize client")
        return

    # Test with lead agent
    agent_id = LEAD_AGENT
    if not agent_id:
        print("Error: ELEVENLABS_LEAD_AGENT_ID environment variable not set")
        return
    
    # Test getLatestConversation
    print("\nTesting getLatestConversation:")
    conversation = getLatestConversation(manager.client, agent_id)
    if conversation:
        print(f"Latest conversation ID: {conversation.conversation_id}")
    else:
        print("No conversation found")

    # Test getTranscript
    print("\nTesting getTranscript:")
    if conversation:  # Using conversation from getLatestConversation
        transcript = getTranscript(manager.client, conversation.conversation_id, agent_id)
        if transcript:
            print("Full transcript:")
            print(transcript)
        else:
            print("No transcript found")
    else:
        print("Cannot get transcript without conversation ID")
        
    # Test getEvals
    print("\nTesting getEvals:")
    evals = getEvals(manager.client, agent_id)
    if evals:
        print("Evaluation results from most recent conversation:")
        for eval in evals:
            print(eval)
    else:
        print("No evaluation results found")
        
    # Test getDataCollections
    print("\nTesting getDataCollections:")
    data_results = getDataCollections(manager.client, agent_id)
    if data_results:
        print("Data collection results from most recent conversation:")
        for result in data_results:
            print(result)
    else:
        print("No data collection results found")

if __name__ == "__main__":
    test_elevenlabs_functions()