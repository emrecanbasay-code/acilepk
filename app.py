"""
SAYFA 1: Muayene Kaydı
Doktor sesini kaydeder -> Groq Whisper ile texte çevrilir ->
Groq Llama ile yapılandırılmış JSON'a parse edilir ->
Her alan düzenlenebilir kutularda gösterilir ->
Metni formatla ve Sayfa 2'ye aktarır
"""
import streamlit as st
import streamlit.components.v1 as components
import time
from services.groq_service import transcribe, structure_text


def turkish_upper(text: str) -> str:
    """Turkce karakterli buyuk harfe cevirir"""
    if not text:
        return text
    # Turkce karakter ozel durumlar
    text = text.replace("i", "İ")
    text = text.replace("ı", "I")
    text = text.replace("ş", "Ş")
    text = text.replace("ğ", "Ğ")
    text = text.replace("ü", "Ü")
    text = text.replace("ö", "Ö")
    text = text.replace("ç", "Ç")
    return text.upper()


def is_mobile() -> bool:
    """Mobil cihaz kontrolü"""
    return st.width() < 768 if hasattr(st, 'width') else False

st.set_page_config(
    page_title="Hasta Muayene Asistanı",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode CSS
st.markdown("""
<style>
    /* Dark mode renkleri */
    .stApp {
        background-color: #0e1117;
    }
    .stMarkdown {
        color: #fafafa;
    }
    /* Text area optimize */
    textarea {
        min-height: 80px !important;
    }
    /* Mobil uyumluluk */
    @media (max-width: 768px) {
        .stColumns {
            flex-direction: column !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🩺 Ses Tabanlı Hasta Muayene Asistanı")
st.markdown("---")

# Session state başlatma
if "struct_data" not in st.session_state:
    st.session_state.struct_data = {}
if "raw_transcription" not in st.session_state:
    st.session_state.raw_transcription = ""
if "formatted_text" not in st.session_state:
    st.session_state.formatted_text = ""
# Sayfa 2 ile paylasılacak degiskenler
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "retrieved_text" not in st.session_state:
    st.session_state.retrieved_text = ""

st.header("📝 MUAYENE KAYDI")

# Sekmeler: Ses / Manuel Metin
tab_ses, tab_manuel = st.tabs(["🎙️ SESLİ KAYIT", "⌨️ MANUEL METIN GIRISI"])

with tab_ses:
    # Ses giris bolumu - mobil uyumlu
    if is_mobile():
        st.subheader("🎙️ SESLİ KAYIT")
        audio_file = st.audio_input("DOKTORUN SESINI KAYDEDIN...", label_visibility="visible")

        st.subheader("📁 DOSYA YUKLE")
        uploaded_file = st.file_uploader(
            "VEYA SES DOSYASI YUKLEYIN",
            type=["wav", "mp3", "m4a", "ogg", "flac", "webm"]
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎙️ SESLİ KAYIT")
            audio_file = st.audio_input("DOKTORUN SESINI KAYDEDIN...", label_visibility="visible")

        with col2:
            st.subheader("📁 DOSYA YUKLE")
            uploaded_file = st.file_uploader(
                "VEYA SES DOSYASI YUKLEYIN",
                type=["wav", "mp3", "m4a", "ogg", "flac", "webm"]
            )

with tab_manuel:
    st.subheader("⌨️ MANUEL METIN GIRISI")
    manual_text = st.text_area(
        "MUAYENE BILGILERINI YAZIN...",
        placeholder="Hastanın şikayeti, hikayesi, fizik muayene bulgularını buraya yazın...",
        height=200,
        help="Ses kaydı ortamı müsait değilse muayene bilgilerini buraya manuel olarak yazabilirsiniz."
    )

# İşle butonu
st.markdown("---")

if st.button("🚀 ISLE VE YAPILANDIR", type="primary", use_container_width=True):
    transcription = None

    # Manuel metin kontrolü
    if manual_text and manual_text.strip():
        transcription = manual_text.strip()
        st.info("📝 MANUEL METIN ISLENIYOR...")

    # Ses kaydı/dosya kontrolü
    elif audio_file is not None or uploaded_file is not None:
        audio_bytes = None
        file_extension = "wav"

        if audio_file is not None:
            audio_bytes = audio_file.read()
            file_extension = "wav"
        elif uploaded_file is not None:
            audio_bytes = uploaded_file.read()
            file_extension = uploaded_file.name.split(".")[-1]

        # Whisper ile transkripsiyon - süreli
        with st.spinner("🎙️ SES YAZYA CEVIRILIYOR..."):
            try:
                start_time = time.time()
                transcription = transcribe(audio_bytes, file_extension)
                elapsed = time.time() - start_time
                st.session_state.raw_transcription = transcription
                st.success(f"✅ SES BASARIYLA YAZYA CEVRILDI! ({elapsed:.1f}s)")
                st.toast(f"Transkripsiyon: {elapsed:.1f}s", icon="🎙️")
            except Exception as e:
                st.error(f"❌ TRANSKRIPSIYON HATASI: {str(e)}")
                st.stop()
    else:
        st.error("⚠️ LUTFEN MANUEL METIN GIRIN VEYA SES KAYDEDIN/DOSYA YUKLEYIN!")
        st.stop()

    # Llama ile yapilandirma (manuel metin veya transkripsiyon) - süreli
    with st.spinner("🧠 METIN YAPILANDIRILIYOR..."):
        try:
            start_time = time.time()
            structured = structure_text(transcription)
            elapsed = time.time() - start_time
            st.session_state.struct_data = structured
            st.success(f"✅ METIN BASARIYLA YAPILANDIRILDI! ({elapsed:.1f}s)")
            st.toast(f"Yapılandırma: {elapsed:.1f}s", icon="🧠")
            st.balloons()
        except Exception as e:
            st.error(f"❌ YAPILANDIRMA HATASI: {str(e)}")
            st.stop()

# Yapilandirilmis veriyi goster
if st.session_state.struct_data:
    st.markdown("---")
    st.header("📋 YAPILANDIRILMIS VERI (DUZENLENEBILIR)")

    data = st.session_state.struct_data

    # Duzenlenebilir alanlar - mobil uyumlu
    mobile = is_mobile()

    if mobile:
        # Mobilde tek kolon
        st.session_state.struct_data["yas"] = st.number_input(
            "YAS",
            min_value=0,
            max_value=150,
            value=int(data.get("yas", "Belirtilmemiş")) if str(data.get("yas", "")).isdigit() else 0,
            step=1,
            key="yas_input"
        )

        st.session_state.struct_data["cinsiyet"] = st.selectbox(
            "CINSIYET",
            options=["Belirtilmemiş", "Erkek", "Kadın"],
            index=["Belirtilmemiş", "Erkek", "Kadın"].index(data.get("cinsiyet", "Belirtilmemiş")) if data.get("cinsiyet") in ["Belirtilmemiş", "Erkek", "Kadın"] else 0,
            key="cinsiyet_select"
        )

        st.session_state.struct_data["sikayet"] = st.text_area(
            "ŞIKAYET",
            value=data.get("sikayet", "BELIRTILMEMIS"),
            height=60,
            key="sikayet_area"
        )
        st.session_state.struct_data["hikaye"] = st.text_area(
            "HIKAYE",
            value=data.get("hikaye", "BELIRTILMEMIS"),
            height=80,
            key="hikaye_area"
        )
        st.session_state.struct_data["kronik_hastaliklar"] = st.text_area(
            "KRONIK HASTALIKLAR",
            value=data.get("kronik_hastaliklar", "BELIRTILMEMIS"),
            height=60,
            key="kronik_area"
        )
        st.session_state.struct_data["kullanilan_ilaclar"] = st.text_area(
            "KULLANILAN ILACLAR",
            value=data.get("kullanilan_ilaclar", "BELIRTILMEMIS"),
            height=60,
            key="ilaclar_area"
        )
        st.session_state.struct_data["ozgecmis"] = st.text_area(
            "OZGECMIS",
            value=data.get("ozgecmis", "BELIRTILMEMIS"),
            height=60,
            key="ozgecmis_area"
        )
        st.session_state.struct_data["soygecmis"] = st.text_area(
            "SOYGECMIS",
            value=data.get("soygecmis", "BELIRTILMEMIS"),
            height=60,
            key="soygecmis_area"
        )
        st.session_state.struct_data["fizik_muayene"] = st.text_area(
            "FIZIK MUAYENE",
            value=data.get("fizik_muayene", "BELIRTILMEMIS"),
            height=80,
            key="fizik_area"
        )
        st.session_state.struct_data["laboratuvar"] = st.text_area(
            "LABORATUVAR",
            value=data.get("laboratuvar", "BELIRTILMEMIS"),
            height=60,
            key="lab_area"
        )
        st.session_state.struct_data["goruntuleme"] = st.text_area(
            "GORUNTULEME",
            value=data.get("goruntuleme", "BELIRTILMEMIS"),
            height=60,
            key="goruntuleme_area"
        )
    else:
        # Desktopta iki kolon
        col1, col2 = st.columns(2)

        with col1:
            st.session_state.struct_data["yas"] = st.number_input(
                "YAS",
                min_value=0,
                max_value=150,
                value=int(data.get("yas", "Belirtilmemiş")) if str(data.get("yas", "")).isdigit() else 0,
                step=1,
                key="yas_input"
            )

            st.session_state.struct_data["cinsiyet"] = st.selectbox(
                "CINSIYET",
                options=["Belirtilmemiş", "Erkek", "Kadın"],
                index=["Belirtilmemiş", "Erkek", "Kadın"].index(data.get("cinsiyet", "Belirtilmemiş")) if data.get("cinsiyet") in ["Belirtilmemiş", "Erkek", "Kadın"] else 0,
                key="cinsiyet_select"
            )

            st.session_state.struct_data["sikayet"] = st.text_area(
                "ŞIKAYET",
                value=data.get("sikayet", "BELIRTILMEMIS"),
                height=80,
                key="sikayet_area"
            )

            st.session_state.struct_data["hikaye"] = st.text_area(
                "HIKAYE",
                value=data.get("hikaye", "BELIRTILMEMIS"),
                height=100,
                key="hikaye_area"
            )

            st.session_state.struct_data["kronik_hastaliklar"] = st.text_area(
                "KRONIK HASTALIKLAR",
                value=data.get("kronik_hastaliklar", "BELIRTILMEMIS"),
                height=80,
                key="kronik_area"
            )

            st.session_state.struct_data["kullanilan_ilaclar"] = st.text_area(
                "KULLANILAN ILACLAR",
                value=data.get("kullanilan_ilaclar", "BELIRTILMEMIS"),
                height=80,
                key="ilaclar_area"
            )

            st.session_state.struct_data["ozgecmis"] = st.text_area(
                "OZGECMIS",
                value=data.get("ozgecmis", "BELIRTILMEMIS"),
                height=80,
                key="ozgecmis_area"
            )

        with col2:
            st.session_state.struct_data["soygecmis"] = st.text_area(
                "SOYGECMIS",
                value=data.get("soygecmis", "BELIRTILMEMIS"),
                height=80,
                key="soygecmis_area"
            )

            st.session_state.struct_data["fizik_muayene"] = st.text_area(
                "FIZIK MUAYENE",
                value=data.get("fizik_muayene", "BELIRTILMEMIS"),
                height=100,
                key="fizik_area"
            )

            st.session_state.struct_data["laboratuvar"] = st.text_area(
                "LABORATUVAR",
                value=data.get("laboratuvar", "BELIRTILMEMIS"),
                height=80,
                key="lab_area"
            )

            st.session_state.struct_data["goruntuleme"] = st.text_area(
                "GORUNTULEME",
                value=data.get("goruntuleme", "BELIRTILMEMIS"),
                height=80,
                key="goruntuleme_area"
            )

    st.markdown("---")

    # Metni formatla butonu
    if st.button("📋 METNI YAPILANDIR VE KOPYALA", type="primary", use_container_width=True):
        data = st.session_state.struct_data

        # Alan tanımları ve sıralaması
        fields = [
            ("YAS", str(data.get('yas', 'Belirtilmemiş'))),
            ("CINSIYET", data.get('cinsiyet', 'Belirtilmemiş')),
            ("ŞIKAYET", data.get('sikayet', 'Belirtilmemiş')),
            ("HIKAYE", data.get('hikaye', 'Belirtilmemiş')),
            ("KRONIK HASTALIKLAR", data.get('kronik_hastaliklar', 'Belirtilmemiş')),
            ("KULLANILAN ILACLAR", data.get('kullanilan_ilaclar', 'Belirtilmemiş')),
            ("OZGECMIS", data.get('ozgecmis', 'Belirtilmemiş')),
            ("SOYGECMIS", data.get('soygecmis', 'Belirtilmemiş')),
            ("FIZIK MUAYENE", data.get('fizik_muayene', 'Belirtilmemiş')),
            ("LABORATUVAR", data.get('laboratuvar', 'Belirtilmemiş')),
            ("GORUNTULEME", data.get('goruntuleme', 'Belirtilmemiş'))
        ]

        # Sadece dolu alanları ekle (Belirtilmemiş değilse)
        parts = []
        for label, value in fields:
            if value and str(value).strip().lower() not in ['belirtilmemiş', 'belirtildi̇lmemi̇ş', 'belirtildi̇lmemiş']:
                parts.append(f"{label}\n{turkish_upper(str(value))}")

        # Metni oluştur
        formatted = "DEĞERLİ MESLEKTAŞIM;\n\n" + "\n\n".join(parts)

        st.session_state.formatted_text = formatted
        st.success("✅ METIN KOPYALAMAYA HAZIR VE SAYFA 2'YE AKTARILDI!")
        st.balloons()

# Formatli metni goster
if st.session_state.formatted_text:
    st.markdown("---")
    st.subheader("📄 FORMATLI METIN - ASAGIDAKI METNI SECIP KOPYALAYIN")

    # Kod blogu olarak goster - kopyalamasi daha kolay
    st.code(st.session_state.formatted_text, language=None, wrap_lines=True)

    st.info("👉 BU METNI GONDERMEK ICIN SOL MENUDEN **VERI ISLEMLERI** SAYFASINA GIDIN")

# Sayfa alt bilgi
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>MUAYENE KAYDI SAYFASI | SOL MENUDEN VERI ISLEMLERI SAYFASINA GECIS YAPABILIRSINIZ</small>
</div>
""", unsafe_allow_html=True)

# Enter ile sonraki kutucuğa geçme JavaScript'i
components.html("""
<script>
    // Enter basınca sonraki text_area'ya geç
    function attachEnterHandler() {
        const textareas = document.querySelectorAll('textarea[data-testid="stTextArea"]');
        textareas.forEach((textarea, index) => {
            if (!textarea.hasAttribute('data-enter-handler')) {
                textarea.setAttribute('data-enter-handler', 'true');
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const allTextareas = document.querySelectorAll('textarea[data-testid="stTextArea"]');
                        const currentIndex = Array.from(allTextareas).indexOf(textarea);
                        const nextTextarea = allTextareas[currentIndex + 1];
                        if (nextTextarea) {
                            nextTextarea.focus();
                            nextTextarea.select();
                        }
                    }
                });
            }
        });
    }

    // Sayfa yüklendiğinde ve DOM değiştiğinde çalıştır
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachEnterHandler);
    } else {
        attachEnterHandler();
    }

    // Dinamik eklenen alanlar için observer
    const observer = new MutationObserver(attachEnterHandler);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", height=0)
