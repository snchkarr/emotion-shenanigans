from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

class Agent:
    def __init__(self):  # Removed vector_db parameter
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            openai_api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        # Simple filler tool
        @tool
        def filler_tool(query: str) -> str:
            """A simple tool that responds to queries."""
            return f"I understand you're asking about: {query}"
        
        self.tools = [filler_tool]
        
        # System prompt
        system_prompt = """
        You are a helpful assistant. Be concise and friendly.
        """
        
        # Create agent
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )
    
    def ask(self, prompt, history=None):
        """Simple ask method"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.agent.invoke({"messages": messages})
            
            logging.info("Response generated")
            
            if response and "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif hasattr(last_message, 'text'):
                    return last_message.text
                else:
                    return str(last_message)
            
            return "Sorry, I couldn't generate a response."
            
        except Exception as e:
            logging.error(f"Error in ask: {str(e)}")
            try:
                simple_response = self.llm.invoke(prompt)
                return simple_response.content
            except Exception as fallback_error:
                logging.error(f"Fallback error: {str(fallback_error)}")
                return f"Sorry, an error occurred: {str(e)}"
    
    def clear_history(self):
        """Placeholder for compatibility"""
        pass