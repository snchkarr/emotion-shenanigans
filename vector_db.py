# vector_db.py
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import logging
import threading

logging.basicConfig(level=logging.INFO)

class VectorDB:
    _model = None
    _model_lock = threading.Lock()
    
    def __init__(self, db_path='vectors.db'):
        with VectorDB._model_lock:
            if VectorDB._model is None:
                self._load_model()
            self.model = VectorDB._model
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._check_tables()
    
    def _load_model(self):
        model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        model_dir = "models"
        local_model_path = os.path.join(model_dir, model_name)
        
        if os.path.exists(local_model_path):
            logging.info(f"Загрузка модели из {local_model_path}")
            VectorDB._model = SentenceTransformer(local_model_path)
        else:
            logging.info(f"Скачивание модели {model_name}...")
            VectorDB._model = SentenceTransformer(model_name)
            os.makedirs(model_dir, exist_ok=True)
            VectorDB._model.save(local_model_path)
            logging.info(f"Модель сохранена в {local_model_path}")
    
    def _check_tables(self):
        """Проверяет существование таблиц, если их нет - выводит ошибку"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        documents_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recommendations'")
        recommendations_exists = cursor.fetchone() is not None
        
        if not documents_exists or not recommendations_exists:
            missing = []
            if not documents_exists:
                missing.append("documents")
            if not recommendations_exists:
                missing.append("recommendations")
            raise RuntimeError(
                f"❌ Таблицы {', '.join(missing)} не найдены. "
                f"Пожалуйста, сначала запустите setup.py для создания базы данных."
            )
    
    def _embed(self, text):
        embedding = self.model.encode(text)
        return embedding.astype(np.float32)
    
    def add_document(self, text, category=None):
        """Добавляет документ в таблицу documents"""
        embedding = self._embed(text)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents (text, embedding, category) VALUES (?, ?, ?)",
            (text, embedding.tobytes(), category)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def add_recommendation(self, text, condition=None):
        """Добавляет рекомендацию в таблицу recommendations"""
        embedding = self._embed(text)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO recommendations (text, embedding, condition) VALUES (?, ?, ?)",
            (text, embedding.tobytes(), condition)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def add_documents_batch(self, documents, category=None):
        """Добавляет несколько документов в таблицу documents"""
        ids = []
        for doc in documents:
            doc_id = self.add_document(doc, category)
            ids.append(doc_id)
        return ids
    
    def add_recommendations_batch(self, recommendations, condition=None):
        """Добавляет несколько рекомендаций в таблицу recommendations"""
        ids = []
        for rec in recommendations:
            rec_id = self.add_recommendation(rec, condition)
            ids.append(rec_id)
        return ids
    
    def search(self, query, top_k=3, table='documents'):
        """
        Поиск в указанной таблице
        table: 'documents' (общие знания) или 'recommendations' (рекомендации)
        """
        query_embedding = self._embed(query)
        cursor = self.conn.cursor()
        
        if table == 'documents':
            cursor.execute("SELECT id, text, embedding FROM documents")
        else:
            cursor.execute("SELECT id, text, embedding FROM recommendations")
            
        rows = cursor.fetchall()
        
        if not rows:
            return []
        
        similarities = []
        for doc_id, text, emb_bytes in rows:
            doc_embedding = np.frombuffer(emb_bytes, dtype=np.float32)
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-8
            )
            similarities.append((similarity, text))
        
        similarities.sort(reverse=True)
        return [text for _, text in similarities[:top_k]]