import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

def get_response(user_input, chat_history=[]):
    """
    Generates a response using LangChain and OpenAI GPT-3.5 Turbo.
    
    Args:
        user_input: The user's message string.
        chat_history: List of previous messages for context.
        
    Returns:
        str: The AI's response.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        return "⚠️ I'm sorry, but the OpenAI API Key is missing. Please configure it in the '.env' file to enable the Guardian AI."

    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key
        )

        system_prompt = """
        You are 'Guardian AI', a specialized Security Expert and Tourist Guide for the CAN 2025 (Africa Cup of Nations) in Morocco.
        
        Your Mission:
        1. Assist fans with information regarding stadium logistics, local tourism, and tournament schedules.
        2. Provide expert security advice and monitoring insights.
        
        Languages:
        - You MUST respond in the language used by the user: Moroccan Darija, English, French, or Arabic.
        - If the user uses a mix (e.g., Darija/French), respond appropriately.
        
        Safety & Security Protocol:
        - If the user asks about weapons, violence, or how to bypass security, you MUST immediately stop any casual tone and provide strict security protocols. 
        - State clearly that weapons are strictly prohibited in all CAN 2025 venues and that any suspicious behavior will be reported to the Royal Moroccan Gendarmerie or local police.
        - Be firm, professional, and prioritize public safety above all else.
        
        Style:
        - Professional, helpful, and welcoming. 
        - Use your knowledge of Morocco's hospitality and CAN 2025 venues (e.g., Casablanca, Rabat, Tangier, Marrakech, Agadir, Fez).
        """

        messages = [SystemMessage(content=system_prompt)]
        
        # Add history if needed (optional for basic implementation but good for chat)
        for msg in chat_history:
            messages.append(msg)
            
        messages.append(HumanMessage(content=user_input))

        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        return f"❌ Error communicating with the Guardian AI: {str(e)}"
