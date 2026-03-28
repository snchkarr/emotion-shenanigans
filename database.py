import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('survey.db')
        
    def get_questions(self):
        c = self.conn.cursor()
        c.execute("SELECT id, text FROM questions ORDER BY id")
        return c.fetchall()
    
    def save_answers(self, user_id, answers):
        c = self.conn.cursor()
        c.execute("DELETE FROM answers WHERE user_id = ?", (user_id,))
        for q_id, answer in answers:
            c.execute("INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)",
                     (user_id, q_id, answer))
        self.conn.commit()
    
    def get_answers(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT question_id, answer FROM answers WHERE user_id = ? ORDER BY question_id", (user_id,))
        return c.fetchall()