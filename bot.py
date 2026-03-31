import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import os
from dotenv import load_dotenv
from database import Database
from agent import Agent

load_dotenv()

class VKBot:
    def __init__(self):
        self.vk = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
        self.longpoll = VkLongPoll(self.vk)
        self.db = Database()
        self.agent = Agent()
        self.survey_active = {}
        self.chat_unlocked = {}
        self.survey_answers = {}
        
    def send_msg(self, user_id, msg):
        self.vk.method('messages.send', {'user_id': user_id, 'message': msg, 'random_id': 0})
    
    def start_survey(self, user_id):
        questions = self.db.get_questions()
        self.survey_active[user_id] = {"questions": questions, "current": 0, "answers": []}
        self.send_msg(user_id, questions[0][1])
    
    def handle_survey_answer(self, user_id, text):
        survey = self.survey_active[user_id]
        q_id, q_text = survey["questions"][survey["current"]]
        survey["answers"].append((q_id, text))
        
        # Move to next question
        next_idx = survey["current"] + 1
        if next_idx < len(survey["questions"]):
            _, next_q = survey["questions"][next_idx]
            self.send_msg(user_id, next_q)
            survey["current"] += 1
        else:
            # Survey complete
            self.db.save_answers(user_id, survey["answers"])
            
            # Format answers for analysis
            answers_text = "\n".join([f"Q{idx+1}: {answer}" for idx, (q_id, answer) in enumerate(survey["answers"])])
            
            prompt = f"""
                Ты психологический ассистент. Отвечай на русском языке, дружелюбно и бережно.

                ## Анализ ответов
                Проанализируй ответы на вопросы и опиши:
                - Ключевые наблюдения (уровень тревоги, сон, поддержка, стресс)
                - Возможные признаки состояний (используй мягкие формулировки: "возможно", "обратите внимание")
                - 2-3 конкретные рекомендации, связанные с ответами пользователя

                ## Инструмент search_knowledge
                При использовании этого инструмента:
                - НЕ ищи дословно текст вопроса или ответа
                - СФОРМИРУЙ обобщающий запрос по ключевым паттернам из ответов пользователя

                Не ставь клинический диагноз. При серьезных признаках рекомендую обратиться к специалисту.
                """
                                    
            response = self.agent.ask(prompt)
            self.send_msg(user_id, response)
            self.chat_unlocked[user_id] = True
            del self.survey_active[user_id]
    
    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                text = event.text.lower()
                
                if user_id not in self.survey_active:
                    if text == "survey":
                        self.start_survey(user_id)
                    elif self.chat_unlocked.get(user_id, False):
                        response = self.agent.ask(text)
                        self.send_msg(user_id, response)
                    else:
                        self.send_msg(user_id, "Type 'survey' to take the personality survey first")
                else:
                    self.handle_survey_answer(user_id, text)

if __name__ == "__main__":
    bot = VKBot()
    bot.run()