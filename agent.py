# agent.py
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
import os
from dotenv import load_dotenv
import logging
from vector_db import VectorDB

load_dotenv()
logging.basicConfig(level=logging.INFO)

class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        self.vector_db = VectorDB()
        
        @tool
        def search_knowledge(query: str) -> str:
            """Поиск в базе знаний психологических концепций."""
            logging.info(f"🔧 TOOL CALLED: search_knowledge with query: {query}")
            results = self.vector_db.search(query)
            logging.info(f"🔧 TOOL RESULT: found {len(results)} results")
            return "\n".join(results) if results else "Информация не найдена."
        
        @tool
        def filler_tool(query: str) -> str:
            """Вспомогательный инструмент."""
            logging.info(f"🔧 TOOL CALLED: filler_tool with query: {query}")
            return f"Я понимаю, вы спрашиваете о: {query}"
        
        self.tools = [search_knowledge, filler_tool]
        
        system_prompt = """
        Ты психологический ассистент. Отвечай кратко и дружелюбно на русском языке.
        """
        
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )
    
    def ask(self, prompt, history=None):
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.agent.invoke({"messages": messages})
            
            logging.info("✅ Response generated")
            
            if response and "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif hasattr(last_message, 'text'):
                    return last_message.text
                else:
                    return str(last_message)
            
            return "Извините, не удалось сгенерировать ответ."
            
        except Exception as e:
            logging.error(f"❌ Error in ask: {str(e)}")
            try:
                simple_response = self.llm.invoke(prompt)
                return simple_response.content
            except Exception as fallback_error:
                logging.error(f"❌ Fallback error: {str(fallback_error)}")
                return f"Извините, произошла ошибка: {str(e)}"
    
    def clear_history(self):
        pass