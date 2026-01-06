
import streamlit as st
import requests

st.set_page_config(page_title="AI Interview Assessor", layout="wide")


try:
    #  ketika di Streamlit Cloud, akan ambil dari Secrets
    SERVER_URL = st.secrets["backend_url"]
except:
    # ketika di Laptop (Lokal)
    SERVER_URL = "secret"

# CSS Styling
st.markdown("""
<style>
    .score-card { font-size: 80px; font-weight: bold; text-align: center; color: #4CAF50; }
    .stTextArea textarea { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# Session State Setup 
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'last_result' not in st.session_state:
    st.session_state.last_result = None

def start_evaluation():
    st.session_state.is_processing = True

DAFTAR_PERTANYAAN = [
    "apa nilai nilai (values) yang penting dalam hidupmu? Jelaskan!",
    "Apa tiga kelebihan teratasmu/terkuatmu? Jelaskan!",
    "Apa tiga kelemahan/kekurangan teratasmu dan bagaimana kamu mengatasinya? Jelaskan!",
    "Apa yang menjadi passion-mu? Aktivitas apa yang kamu lakukan yang berkaitan dengan passion tersebut?",
    "Topik seperti apa yang kamu sukai untuk didiskusikan dengan orang lain?",
    "Proyek komunitas atau kegiatan sosial apa yang pernah kamu ikuti sebelumnya? Ceritakan!",
    "Bagaimana caramu menghadapi orang-orang yang memiliki keyakinan, pendapat, atau prinsip yang berbeda darimu?",
    "Apa yang akan kamu lakukan jika local project ini tidak memenuhi harapanmu?",
    "Jika kamu menjadi presiden sebuah LSM (NGO) di Indonesia dan bebas memilih isu sosial yang ingin ditangani, isu apa yang akan kamu fokuskan? (lihat dari isu sosial terkini di Indonesia)",
    "Kriteria seperti apa yang kamu inginkan dari rekan kerjamu? jelaskan alasannya!",
    "Bagaimana reaksimu jika ada kesalahan yang terjadi di dalam projectmu (konteks kamu menjadi presiden LSM dan kamu melaksanakan project sosial terkait isu sosial terkini di indonesia) dan kesalahan itu berasal dari rekan kerjamu? apa langkah yang akan kamu lakukan untuk mengatasi masalah tersebut?"
]

# Halaman utama
st.title("🤖 AI Interview Assessor")
# st.caption(f"Backend: {SERVER_URL}") # untuk debug
st.markdown("---")

st.subheader("1. Input Data Wawancara")
col1, col2 = st.columns([1, 2])

with col1:
    selected_question = st.selectbox("Pertanyaan:", DAFTAR_PERTANYAAN)

with col2:
    user_answer = st.text_area("Jawaban Kandidat:", height=200, placeholder="Jawaban...")

# Button Logic
st.button(
    "🔍 Evaluasi Jawaban", 
    type="primary", 
    use_container_width=True,
    disabled=st.session_state.is_processing, 
    on_click=start_evaluation              
)

if st.session_state.is_processing:
    if selected_question == "Pilih pertanyaan..." or not user_answer:
        st.warning("⚠️ Lengkapi data pertanyaan dan jawaban!")
        st.session_state.is_processing = False 
        st.rerun() 
    else:
        # placeholder untuk container output/error 
        result_container = st.empty()
        
        try:
            with st.spinner("Sedang Menganalisis... (Bisa memakan waktu 30-60 detik)"):
                # membersihkan URL dari slash di akhir
                endpoint = f"{SERVER_URL.rstrip('/')}/evaluate"
                payload = {"question": selected_question, "answer": user_answer}
                
                # Backend Request
                response = requests.post(endpoint, json=payload, timeout=600)
                
                # Status Cek Code HTTP
                if response.status_code == 200:
                    try:
                        # Parsing JSON
                        st.session_state.last_result = response.json()
                        st.session_state.is_processing = False
                        st.rerun() # Refresh untuk tampilkan hasil
                    except requests.exceptions.JSONDecodeError:
                        st.error("❌ Server merespon, tapi format data rusak (Bukan JSON).")
                        with st.expander("Lihat Respon Mentah Server"):
                            st.code(response.text)
                        st.session_state.last_result = None
                
                elif response.status_code == 404:
                    st.error(f"❌ URL Salah (404 Not Found).")
                    st.warning(f"Sistem mencoba menghubungi: `{endpoint}`. Pastikan URL Ngrok di update.")
                    st.session_state.last_result = None
                    
                elif response.status_code == 500:
                    st.error("❌ Terjadi Error Internal di Server Python (500).")
                    with st.expander("Detail Error dari Server"):
                        st.write(response.text)
                    st.session_state.last_result = None
                
                else:
                    st.error(f"❌ Server menolak dengan status: {response.status_code}")
                    st.write(response.text)
                    st.session_state.last_result = None

        except requests.exceptions.ConnectionError:
            st.error("🚫 Gagal Terhubung ke Server!")
            st.warning("""
            **Kemungkinan Penyebab:**
            1. Server Python (Backend) belum dinyalakan.
            2. Ngrok belum dijalankan.
            3. URL Ngrok di `app.py` atau `secrets.toml` sudah kadaluarsa (ganti dengan yang baru).
            """)
            st.session_state.last_result = None

        except requests.exceptions.Timeout:
            st.error("⏳ Waktu Habis (Timeout)!")
            st.warning("Server terlalu sibuk atau antrian penuh. Silakan coba tekan tombol Evaluasi lagi dalam 1 menit.")
            st.session_state.last_result = None

        except Exception as e:
            st.error("❌ Terjadi Kesalahan Tak Terduga")
            with st.expander("Lihat Detail Teknis"):
                st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")
            st.session_state.last_result = None
        
        # Reset state processing agar tombol bisa ditekan lagi
        st.session_state.is_processing = False

# Halanan Hasil
if st.session_state.last_result:
    data = st.session_state.last_result
    st.divider()
    st.subheader("2. Hasil Penilaian")
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        st.markdown("### Score")
        st.markdown(f"<div class='score-card'>{data.get('score', 0)}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("### Reasoning")
        st.info(data.get('reason', '-'))
    with c3:
        st.markdown("### Improvement")
        st.success(data.get('improvement', '-'))

st.markdown("---")