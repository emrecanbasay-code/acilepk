"""
Google Cloud Firestore servisi - Veri kaydetme ve okuma işlemleri
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import random
from datetime import datetime, timedelta


def get_firestore_db():
    """Firestore veritabanı bağlantısını başlatır ve döndürür"""
    if not hasattr(st, 'firestore_db'):
        cred_dict = st.secrets["firebase"]
        cred = credentials.Certificate(cred_dict)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        st.firestore_db = firestore.client()

    return st.firestore_db


def generate_code() -> str:
    """
    4 haneli benzersiz sayısal kod üretir (1000-9999)

    Returns:
        str: 4 haneli kod
    """
    return str(random.randint(1000, 9999))


def save_record(text_data: str) -> str:
    """
    Metni Firestore'a kaydeder ve kodu döndürür

    Args:
        text_data: Kaydedilecek metin verisi

    Returns:
        str: Oluşturulan 4 haneli kod
    """
    db = get_firestore_db()

    # Benzersiz kod bulana kadar döngü
    max_attempts = 100
    for _ in range(max_attempts):
        code = generate_code()

        # Kodun daha önce kullanılıp kullanılmadığını kontrol et
        doc_ref = db.collection("muayene_kayitlari").document(code)
        doc = doc_ref.get()

        if not doc.exists:
            # Kod kullanılmıyor, kaydı oluştur
            # 24 saat sonra otomatik silmek için expireAt
            expire_at = datetime.now() + timedelta(hours=24)
            doc_ref.set({
                "text": text_data,
                "created_at": firestore.SERVER_TIMESTAMP,
                "expireAt": expire_at
            })
            return code

    # Yedek olarak timestamp ile benzersiz kod
    import time
    code = str(1000 + int(time.time()) % 9000)
    expire_at = datetime.now() + timedelta(hours=8)
    doc_ref = db.collection("muayene_kayitlari").document(code)
    doc_ref.set({
        "text": text_data,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expireAt": expire_at
    })
    return code


def get_record(code: str) -> str | None:
    """
    Kodla eşleşen metni döndürür

    Args:
        code: 4 haneli kod

    Returns:
        str | None: Bulunan metin veya None (kod bulunamazsa)
    """
    db = get_firestore_db()

    doc_ref = db.collection("muayene_kayitlari").document(code)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict().get("text")
    return None
