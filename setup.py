import sqlite3
import csv
import os
from vector_db import VectorDB

# Пути к файлам
DOCUMENTS_CSV = 'vector_data/documents.csv'
RECOMMENDATIONS_CSV = 'vector_data/recommendations.csv'
QUESTIONS_CSV = 'regular_data/questions.csv'

def load_questions_from_csv():
    """Загружает вопросы из CSV файла"""
    questions = []
    with open(QUESTIONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row['text'])
    return questions

def load_documents_from_csv():
    """Загружает документы из CSV файла"""
    documents = []
    with open(DOCUMENTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            documents.append(row['text'])
    return documents

def load_recommendations_from_csv():
    """Загружает рекомендации из CSV файла"""
    recommendations = []
    with open(RECOMMENDATIONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recommendations.append(row['text'])
    return recommendations

# Setup SQLite для вопросов опроса
conn = sqlite3.connect('survey.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS questions
             (id INTEGER PRIMARY KEY, text TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS answers
             (user_id INTEGER, question_id INTEGER, answer TEXT)''')

# Загружаем и вставляем вопросы
questions = load_questions_from_csv()
c.execute("DELETE FROM questions")
c.executemany('INSERT INTO questions (text) VALUES (?)', [(q,) for q in questions])
conn.commit()
conn.close()

# Setup vector DB
db = VectorDB()

# Создаем таблицы в vector DB
cursor = db.conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        text TEXT,
        embedding BLOB,
        category TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY,
        text TEXT,
        embedding BLOB,
        condition TEXT
    )
''')
db.conn.commit()

# Загружаем и вставляем документы
documents = load_documents_from_csv()
for doc in documents:
    db.add_document(doc)

# Загружаем и вставляем рекомендации
recommendations = load_recommendations_from_csv()
for rec in recommendations:
    db.add_recommendation(rec)

print(f"✅ Загружено вопросов: {len(questions)}")
print(f"✅ Загружено документов: {len(documents)}")
print(f"✅ Загружено рекомендаций: {len(recommendations)}")
print("✅ База данных успешно создана")