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
ANNOUNCE_AGENT = os.environ.get("ELEVENLABS_ANNOUNCE_AGENT_ID")

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

def makePrompt(base_prompt: str, transcript: Optional[str] = None) -> str:
    if not transcript:
        return base_prompt
    return f"{base_prompt}\n\nPrevious conversation:\n{transcript}"

def makeSystemPrompt(base_prompt: str, ai_response: Optional[str] = None) -> str:
    if not ai_response:
        return base_prompt
    return f"{base_prompt}\n\n{ai_response}"

app = FastAPI()

@app.get("/api/py/helloFastApi")
async def hello_fast_api() -> Dict[str, Any]:
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
            
        # Check for agent IDs
        if not LEAD_AGENT or not CO_AGENT_1 or not ANNOUNCE_AGENT:
            raise HTTPException(
                status_code=500,
                detail="Agent IDs not configured"
            )
            
        elevenlabs_manager = ElevenLabsManager(elevenlabs_api_key)
        if not elevenlabs_manager.client:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize ElevenLabs client"
            )
            
        transcript = elevenlabs_manager.get_transcript(LEAD_AGENT)
        print(f"Retrieved transcript: {transcript}")
        
        # Combine base prompt with transcript
        base_prompt = "Based on the previous conversation, analyze the conversation for the user's personaity and politcaling leaning, give asummary of their personality and political leaning in this format, and their implications: Decide if he is a communist? PERSONALITY INSIGHTS\nConfidence Level: [Low/Medium/High]\n\nCore Traits:\n- Communication: [Brief/Detailed] & [Formal/Casual]\n- Decision Style: [Analytical/Intuitive]\n- Engagement: [Surface/Deep]\n\nPOLITICAL INDICATORS\nConfidence: [Low/Medium/High]\n\nPolitical Compass:\n- Economic (L/R): [-10 to +10]\n- Social (Lib/Auth): [-10 to +10]\n\nKey Views:\n- Economic Stance: [Description]\n- Social Position: [Description]. Give specific examples that lead to the conclusion."
        message_content = makePrompt(base_prompt, transcript)
        print(f"Using message content: {message_content}")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call with the message content
        completion = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "user", "content": message_content}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        print(f"Generated AI response: {ai_response}")
        
        # Update the agent's prompt
        system_prompt = "You are a friendly and dramatic announcer. Don't ask any questions, your role is give the user a summary of their personality and politcal leaning. Make sure to give a summary of the previous conversation and the user's personality and political leaning, especially if they are a communist or not, and the examples that lead to the conclusion. At the end, tell the user to click the continue button if he wants answer more questions and get more accurate and refined results. Here are the previous conversation: "
        formatted_prompt = makeSystemPrompt(system_prompt, ai_response)
        print(f"Updating agent with prompt: {formatted_prompt}")
        
        if not elevenlabs_manager.update_prompt(
            agent_id=ANNOUNCE_AGENT,
            prompt_text=formatted_prompt
        ):
            raise HTTPException(
                status_code=500, 
                detail="Failed to update agent prompt"
            )
        
        # Get the latest message after update
        latest_transcript = elevenlabs_manager.get_transcript(LEAD_AGENT)
        
        return {
            "message": "Hello from FastAPI",
            "ai_response": ai_response,
            "latest_message": latest_transcript,
            "status": "ElevenLabs agent updated successfully"
        }
        
    except Exception as e:
        print(f"Error in hello_fast_api: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Combine base prompt with transcript
        #base_prompt = "Based on the previous conversation, analyze the conversation for the user's personaity and politcaling leaning, give asummary of their personality and political leaning in this format, and their implications: Decide if he is a communist? PERSONALITY INSIGHTS\nConfidence Level: [Low/Medium/High]\n\nCore Traits:\n- Communication: [Brief/Detailed] & [Formal/Casual]\n- Decision Style: [Analytical/Intuitive]\n- Engagement: [Surface/Deep]\n\nPOLITICAL INDICATORS\nConfidence: [Low/Medium/High]\n\nPolitical Compass:\n- Economic (L/R): [-10 to +10]\n- Social (Lib/Auth): [-10 to +10]\n\nKey Views:\n- Economic Stance: [Description]\n- Social Position: [Description]. Give specific examples that lead to the conclusion."
        base_prompt = "Using my previous answers, create ten more extreme version of the questions asked that amplifies my apparent values and beliefs. If my answer shows concern for community welfare, shared resources, and collective responsibility, intensify those themes to the point of absurdity. If my answer emphasizes individual rights, private property, and personal responsibility, strengthen those aspects to the point of absurdity. The follow-up questions should feel like a natural progression of my own stated views, just taken to a more radical and absurb change."
        message_content = makePrompt(base_prompt, transcript)
        print(f"Using message content: {message_content}")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Make OpenAI API call with the message content
        completion = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "user", "content": message_content}
            ]
        )
        
        ai_response = completion.choices[0].message.content
        
        # Update the agent's prompt
        #system_prompt = "You are a friendly and efficient announcer. Don't be too chatty. Your role is give the user a summary of their personality and politcal leaning. Make sure to give a summary of the conversation and the user's personality and political leaning, especially if they are a communist or not, and the examples that lead to the conclusion."
        system_prompt = "You are a friendly and efficient interviewer. Your role is to be asking all the questions out of the following questions. Ask them the questions straight away, one question at a time, don't hesitate. At the end of the conversation, tell the user to click the continue button if he wants to answer more questions and get more accurate and refined results. Or he can get a summary of his political leanings by clicking the result button."
        if not elevenlabs_manager.update_prompt(
            agent_id=CO_AGENT_1,
            prompt_text=makeSystemPrompt(system_prompt, ai_response)
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