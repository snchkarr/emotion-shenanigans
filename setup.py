import sqlite3

# Setup SQLite only
conn = sqlite3.connect('survey.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS questions
             (id INTEGER PRIMARY KEY, text TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS answers
             (user_id INTEGER, question_id INTEGER, answer TEXT)''')

questions = [
    "How do you handle stressful situations?",
    "What motivates you the most in life?",
    "How do you make important decisions?"
]

# Clear existing questions if any
c.execute("DELETE FROM questions")
c.executemany('INSERT INTO questions (text) VALUES (?)', [(q,) for q in questions])
conn.commit()
conn.close()

print("Setup complete - SQLite database created")