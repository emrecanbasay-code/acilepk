"""
SAYFA 2: VERI ISLEMLERI
BOLUM 1: VERI GONDER - SAYFA 1'DEN GELEN METNI FIRESTORE'A KAYDEDER VE 4 HANELI KOD URETIR
BOLUM 2: VERI AL - 4 HANELI KOD ILE VERIYI FIRESTORE'DAN CEKER
"""
import streamlit as st
import time
from services.firestore_service import save_record, get_record


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
    page_title="Veri İşlemleri",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .stMarkdown {
        color: #fafafa;
    }
    textarea {
        min-height: 80px !important;
    }
    @media (max-width: 768px) {
        .stColumns {
            flex-direction: column !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("💾 VERI ISLEMLERI")
st.markdown("---")

# Session state baslatma - Sayfa 1 ile senkronize
if "formatted_text" not in st.session_state:
    st.session_state.formatted_text = ""
if "retrieved_text" not in st.session_state:
    st.session_state.retrieved_text = ""
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "send_text" not in st.session_state:
    st.session_state.send_text = ""


def update_send_text():
    st.session_state.send_text = st.session_state.send_text_area

# TAB LAYOUT: VERI GONDER VE VERI AL
tab1, tab2 = st.tabs(["📤 VERI GONDER", "📥 VERI AL"])

# ============================================
# TAB 1: VERI GONDER
# ============================================
with tab1:
    st.header("📤 VERI GONDER VE KOD AL")

    st.info("""
    ℹ️ **BILGI:** SAYFA 1'DEN (MUAYENE KAYDI) FORMATLANAN METIN OTOMATIK OLARAK BURAYA AKTARILIR.
    ISTerseniz burada son duzenlemeyi yapabilirsiniz.
    """)

    # Sayfa 1'den gelen metni goster ve düzenlenebilir yap
    if st.session_state.formatted_text and not st.session_state.send_text:
        st.session_state.send_text = st.session_state.formatted_text

    send_text = st.text_area(
        "GONDERILECEK METIN",
        value=st.session_state.send_text,
        height=300,
        key="send_text_area",
        placeholder="METNI BURAYA YAZIN VEYA SAYFA 1'DEN FORMATLANMIS METIN BEKLEYIN...",
        on_change=update_send_text
    )

    # Mobil uyumlu kolonlar
    if is_mobile():
        col2 = st.columns(1)[0]
    else:
        col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🚀 GONDER VE KOD AL", type="primary", use_container_width=True):
            if not send_text.strip():
                st.error("⚠️ GONDERILECEK METIN BOS!")
            else:
                try:
                    start_time = time.time()
                    with st.spinner("💾 VERI KAYDEDILIOYOR, KOD URETILIOYOR..."):
                        code = save_record(send_text)
                        elapsed = time.time() - start_time
                        st.session_state.generated_code = code

                    st.success(f"✅ VERI BASARIYLA KAYDEDILDI! ({elapsed:.1f}s)")
                    st.toast(f"Kayıt: {elapsed:.1f}s", icon="💾")
                    st.balloons()

                except Exception as e:
                    st.error(f"❌ KAYIT HATASI: {str(e)}")

    # Olusturulan kodu goster
    if st.session_state.generated_code:
        st.markdown("---")
        st.markdown("### 🎯 ERISIM KODUNUZ")

        # HTML/CSS ile dikkat cekici kod kutusu
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
            border: 3px solid #00d4ff;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            margin: 20px 0;
        ">
            <div style="
                font-size: 80px;
                font-weight: bold;
                color: #00d4ff;
                letter-spacing: 15px;
                font-family: 'Courier New', monospace;
                text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
            ">
                {st.session_state.generated_code}
            </div>
            <div style="
                color: #ffffff;
                font-size: 18px;
                margin-top: 15px;
            ">
                BU KODU NOT EDIN VEYA PAYLASIN
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.warning("⚠️ LUTFEN BU KODU KAYDEDIN. KODU KAYBEDERSENIZ VERIYE ERISILEMEZSINIZ!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 YENI KAYIT OLUSTUR"):
                st.session_state.generated_code = ""
                st.session_state.formatted_text = ""
                st.session_state.send_text = ""
                st.rerun()

# ============================================
# TAB 2: VERI AL
# ============================================
with tab2:
    st.header("📥 KOD ILE VERI AL")

    st.info("""
    ℹ️ **BILGI:** 4 HANELI ERISIM KODUNU GIREREK KAYDEDILMIS MUAYENE VERISINI CEKEBILIRSINIZ.
    """)

    # Mobil uyumlu kolonlar
    if is_mobile():
        col2 = st.columns(1)[0]
    else:
        col1, col2, col1 = st.columns([1, 2, 1])

    with col2:
        code_input = st.text_input(
            "🔑 ERISIM KODU",
            max_chars=4,
            placeholder="XXXX",
            key="code_input_field",
            help="4 HANELI KODU GIRIN"
        )

        if st.button("🔍 SORGULA", type="secondary", use_container_width=True):
            if not code_input:
                st.error("⚠️ LUTFEN BIR KOD GIRIN!")
            elif len(code_input) != 4 or not code_input.isdigit():
                st.error("⚠️ KOD 4 HANELI BIR SAYI OLMALIDIR!")
            else:
                start_time = time.time()
                with st.spinner("🔍 VERI ARANIYOR..."):
                    try:
                        retrieved = get_record(code_input)
                        elapsed = time.time() - start_time
                        if retrieved:
                            st.session_state.retrieved_text = retrieved
                            st.success(f"✅ KOD {code_input} ICIN VERI BULUNDU! ({elapsed:.1f}s)")
                            st.toast(f"Sorgu: {elapsed:.1f}s", icon="🔍")
                        else:
                            st.error(f"❌ KOD {code_input} ICIN VERI BULUNAMADI!")
                            st.session_state.retrieved_text = ""
                    except Exception as e:
                        st.error(f"❌ SORGU HATASI: {str(e)}")

    # Cekilen metni goster
    if st.session_state.retrieved_text:
        st.markdown("---")
        st.subheader("📄 CEKILEN VERI - ASAGIDAKI METNI SECIP KOPYALAYIN")

        # Kod blogu ile kopyalamayi kolaylastir
        st.code(st.session_state.retrieved_text, language=None, wrap_lines=True)

        # Indirme butonu
        st.download_button(
            label="📥 .TXT OLARAK INDIR",
            data=st.session_state.retrieved_text,
            file_name=f"muayene_{code_input if code_input else 'kayit'}.txt",
            mime="text/plain",
            use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 TEMIZLE"):
                st.session_state.retrieved_text = ""
                st.session_state.send_text = ""
                st.rerun()

# Sayfa alt bilgi
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>VERI ISLEMLERI SAYFASI | SOL MENUDEN MUAYENE KAYDI SAYFASINA DONEBILIRSINIZ</small>
</div>
""", unsafe_allow_html=True)
