"""
Groq API servisi - Hem Whisper hem Llama işlemlerini içerir
"""
import streamlit as st
import groq
import json
import tempfile
import os
from pathlib import Path


def get_client():
    """Groq client'ını başlatır"""
    return groq.Groq(api_key=st.secrets["GROQ_API_KEY"])


def transcribe(audio_bytes, file_extension="wav") -> str:
    """
    Ses dosyasını Groq Whisper ile texte çevirir

    Args:
        audio_bytes: Ses dosyasının byte verisi
        file_extension: Dosya uzantısı (wav, mp3, m4a vb.)

    Returns:
        str: Algılanan metin
    """
    client = get_client()

    # Tıbbi terim prompt'u - sarı alan için
    medical_prompt = (
        "Dispne, takikardi, bradikardi, hipertansiyon, hipotansiyon, göğüs ağrısı, palpitasyon, "
        "karın ağrısı, akut abdomen, dispepsi, hematemez, melena, hematokezya, rektal kanama, kusma, ishal, "
        "disfaji, odinofaji, vertigo, baş dönmesi, senkop, presenkop, inme, TIA, hemiparezi, afazi, diploji, "
        "baş ağrısı, migren, böbrek taşı, kolik, hematüri, disürü, polakiüri, oligüri, retansiyon, hiperglisemi, "
        "hipoglisemi, ketoasidoz, ateş, titreme, sepsis, menenjit, ense sertliği, fotofobi, KOAH, astım, pnömoni, "
        "ral, ronküs, wheezing, hırıltı, troponin, D-dimer, EKG, oksijen saturasyonu, aspirin, klopidogrel, "
        "heparin, varfarin, metoprolol, amlodipin, ramipril, metformin, insülin, seftriakson, sefazolin, levofloksasin"
    )

    # Geçici dosya oluştur
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
        temp_file.write(audio_bytes)
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                language="tr",
                response_format="text",
                prompt=medical_prompt
            )
        return transcription
    finally:
        # Geçici dosyayı sil
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def structure_text(raw_text: str) -> dict:
    """
    Ham metni Groq Llama ile yapılandırılmış JSON'a dönüştürür

    Args:
        raw_text: Yapılandırılacak ham metin

    Returns:
        dict: Yapılandırılmış veri (JSON şemasına göre)
    """
    if not raw_text or not raw_text.strip():
        return {
            "yas": "Belirtilmemiş",
            "cinsiyet": "Belirtilmemiş",
            "sikayet": "Belirtilmemiş",
            "hikaye": "Belirtilmemiş",
            "kronik_hastaliklar": "Belirtilmemiş",
            "kullanilan_ilaclar": "Belirtilmemiş",
            "ozgecmis": "Belirtilmemiş",
            "soygecmis": "Belirtilmemiş",
            "fizik_muayene": "Belirtilmemiş",
            "laboratuvar": "Belirtilmemiş",
            "goruntuleme": "Belirtilmemiş",
            "_error": "Boş metin"
        }

    client = get_client()

    system_prompt = """Sen uzman bir tıbbi sekreter asistansın. Doktorun sesli muayene notlarını yapılandırılmış bir formata dönüştüreceksin.

KURALLAR:
- Doktorun söylemediği bilgiyi UYDURMA.
- Eksik alanları 'Belirtilmemiş' olarak bırak.
- Tıbbi terminolojiyi koru.

KRİTİK KURAL:
- Laboratuvar ve görüntüleme sonuçlarına ASLA 'yüksek', 'düşük', 'anormal' gibi tıbbi yorumlar ekleme.
- Sadece doktorun söylediği ham bulguyu ve değeri yaz (Örn: 'Troponin: 0.15', 'EKG: ST depresyonu').
- Öneri veya plan yazma.

Sadece JSON döndür, başka metin ekleme.

JSON şeması:
{
  "yas": "...",
  "cinsiyet": "...",
  "sikayet": "...",
  "hikaye": "...",
  "kronik_hastaliklar": "...",
  "kullanilan_ilaclar": "...",
  "ozgecmis": "...",
  "soygecmis": "...",
  "fizik_muayene": "...",
  "laboratuvar": "...",
  "goruntuleme": "..."
}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        if not response.choices or not response.choices[0].message.content:
            return {
                "yas": "Belirtilmemiş",
                "cinsiyet": "Belirtilmemiş",
                "sikayet": "Belirtilmemiş",
                "hikaye": "Belirtilmemiş",
                "kronik_hastaliklar": "Belirtilmemiş",
                "kullanilan_ilaclar": "Belirtilmemiş",
                "ozgecmis": "Belirtilmemiş",
                "soygecmis": "Belirtilmemiş",
                "fizik_muayene": "Belirtilmemiş",
                "laboratuvar": "Belirtilmemiş",
                "goruntuleme": "Belirtilmemiş",
                "_error": "Boş API yanıtı"
            }

        content = response.choices[0].message.content.strip()

        if not content:
            return {
                "yas": "Belirtilmemiş",
                "cinsiyet": "Belirtilmemiş",
                "sikayet": "Belirtilmemiş",
                "hikaye": "Belirtilmemiş",
                "kronik_hastaliklar": "Belirtilmemiş",
                "kullanilan_ilaclar": "Belirtilmemiş",
                "ozgecmis": "Belirtilmemiş",
                "soygecmis": "Belirtilmemiş",
                "fizik_muayene": "Belirtilmemiş",
                "laboratuvar": "Belirtilmemiş",
                "goruntuleme": "Belirtilmemiş",
                "_error": "Boş içerik"
            }

        # Markdown kod bloklarını temizle
        if content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        parsed = json.loads(content)

        # Gerekli alanları kontrol et ve eksikleri doldur
        required_fields = ["yas", "cinsiyet", "sikayet", "hikaye", "kronik_hastaliklar", "kullanilan_ilaclar", "ozgecmis", "soygecmis", "fizik_muayene", "laboratuvar", "goruntuleme"]
        for field in required_fields:
            if field not in parsed or not parsed[field]:
                parsed[field] = "Belirtilmemiş"

        return parsed

    except json.JSONDecodeError as e:
        return {
            "yas": "Belirtilmemiş",
            "cinsiyet": "Belirtilmemiş",
            "sikayet": "Belirtilmemiş",
            "hikaye": "Belirtilmemiş",
            "kronik_hastaliklar": "Belirtilmemiş",
            "kullanilan_ilaclar": "Belirtilmemiş",
            "ozgecmis": "Belirtilmemiş",
            "soygecmis": "Belirtilmemiş",
            "fizik_muayene": "Belirtilmemiş",
            "laboratuvar": "Belirtilmemiş",
            "goruntuleme": "Belirtilmemiş",
            "_raw_text": raw_text,
            "_error": f"JSON parse hatası: {str(e)}"
        }
    except Exception as e:
        return {
            "yas": "Belirtilmemiş",
            "cinsiyet": "Belirtilmemiş",
            "sikayet": "Belirtilmemiş",
            "hikaye": "Belirtilmemiş",
            "kronik_hastaliklar": "Belirtilmemiş",
            "kullanilan_ilaclar": "Belirtilmemiş",
            "ozgecmis": "Belirtilmemiş",
            "soygecmis": "Belirtilmemiş",
            "fizik_muayene": "Belirtilmemiş",
            "laboratuvar": "Belirtilmemiş",
            "goruntuleme": "Belirtilmemiş",
            "_raw_text": raw_text,
            "_error": f"API hatası: {str(e)}"
        }
