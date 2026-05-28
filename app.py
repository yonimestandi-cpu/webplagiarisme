<think>
The user wants to update the Streamlit application interface to be more "fresh", "simple", and "attractive" without changing the logical functionality or existing menu structure.

Here's the plan:
1.  Keep all logic (Database, AI Model, Authentication, Menu structures) exactly the same.
2.  Use `st.set_page_config` to set a title, icon, and layout.
3.  Use custom CSS to improve the visual appeal:
    *   Modern fonts.
    *   Better spacing/rounding on elements.
    *   Color scheme adjustments (maybe a cleaner blue/teal/white theme).
    *   Custom styling for buttons and inputs.
4.  Enhance specific UI components:
    *   Use `st.tabs` more visually.
    *   Use `st.columns` for better layout in metrics.
    *   Add emojis and nice headers.
    *   Use `st.success`, `st.warning`, `st.info` more creatively.
5.  Add a Sidebar visualization improvement (collapsible expander).

*Constraint Checklist & Confidence Score:*
1. Fix display? Yes.
2. More interesting? Yes.
3. Don't change logic? Yes.
4. Don't change menus? Yes.
5. Keep imports? Yes.
Confidence Score: 5/5

*Mental Sandbox Simulation:*
- I will inject CSS via `st.markdown(..., unsafe_allow_html=True)`.
- I will add `st.set_page_config(layout="wide")`.
- The CSS will target `.stButton>button`, inputs, and containers to make them look cleaner.
- I will wrap the authentication section in a "Card" looking container using columns or containers.

*Code Modification Strategy:*
- Add `st.set_page_config` at the very top.
- Add CSS styling block.
- Re-organize the Login/Register section to look like a centered card.
- Re-organize the Dashboard Sidebar.
- Improve `st.metric` usage in the plagiarism result section.
- Add a Footer or Sidebar info.

Let's write the code.
</think>entu, saya akan memodifikasi tampilan antarmuka (GUI) agar terlihat lebih modern, bersih, dan segar tanpa mengubah satu pun logika backend atau struktur menu kamu.

Berikut adalah kode yang sudah ditingkatkan tampilannya:

```python
import streamlit as st
import sqlite3
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
import os

# ==========================================
# 0. KONFIGURASI HALAMAN & DESAIN (BARU)
# ==========================================
st.set_page_config(
    page_title="Semantic Plagiarism Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Tampilan Segar & Modern
st.markdown("""
    <style>
        /* Import Font yang Bersih */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        /* Reset Dasar */
        .stApp {
            font-family: 'Poppins', sans-serif;
            background-color: #f8f9fa;
        }
        
        /* Kotak Utama (Card Effect) */
        .css-1r6slb0, .css-1wivb2w {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e0e0e0;
        }

        /* Styling Tombol Utama (Primary Button) */
        .stButton>button {
            background: linear-gradient(135deg, #4e54c8 0%, #8f94fb 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(78, 84, 200, 0.4);
        }

        /* Styling Tombol Secondary (Outline) */
        .stButton>button[kind="secondary"] {
            background: transparent;
            border: 2px solid #4e54c8;
            color: #4e54c8;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #f0f0f0;
        }
        
        /* Header Titles */
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 700;
        }
        
        /* Input Fields */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #ced4da;
            padding: 10px;
        }
        .stTextInput>div>div>input:focus {
            border-color: #8f94fb;
            box-shadow: 0 0 0 2px rgba(143, 148, 251, 0.2);
        }

        /* Metrics Styling */
        div[data-testid="stMetricValue"] {
            color: #4e54c8;
            font-weight: 700;
        }
        
        /* Tab Styling */
        .stTabs {
            background-color: transparent;
        }
        
        /* Alert/Warning Coloring */
        .stAlert {
            border-radius: 10px;
        }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. INITIALISASI DATABASE & MODEL AI
# ==========================================
def init_db():
    # Mengecek jika file database ada, jika tidak buat baru
    conn = sqlite3.connect('database_plagiarisme_baru.db')
    cursor = conn.cursor()
    # Tabel Dokumen Pembanding
    cursor.execute('''CREATE TABLE IF NOT EXISTS dokumen_alumni 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, penulis TEXT, judul TEXT, isi_teks TEXT)''')
    # Tabel Pengguna/Akun
    cursor.execute('''CREATE TABLE IF NOT EXISTS pengguna 
                      (username TEXT PRIMARY KEY, password TEXT, nama TEXT, role TEXT, status TEXT)''')
    
    # Cek & Buat Akun Master Superadmin
    cursor.execute("SELECT username FROM pengguna WHERE username = 'superadmin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO pengguna VALUES ('superadmin', 'master123', 'Pemilik Sistem', 'Superadmin', 'Aktif')")
        cursor.execute("INSERT INTO pengguna VALUES ('dosen1', 'dosen123', 'Dr. Irwan (Dosen NLP)', 'Dosen', 'Pending')")
    conn.commit()
    conn.close()

init_db()

@st.cache_resource
def load_indo_bert():
    tokenizer = AutoTokenizer.from_pretrained("indobenchmark/indobert-base-p1")
    model = AutoModel.from_pretrained("indobenchmark/indobert-base-p1")
    return tokenizer, model

tokenizer, model = load_indo_bert()

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.numpy()


# ==========================================
# 2. FUNGSI EKSTRAKSI & MANAJEMEN DATA
# ==========================================
def ekstrak_teks_dari_pdf(file_pdf):
    reader = PdfReader(file_pdf)
    teks_utuh = ""
    for halaman in reader.pages:
        teks_halaman = halaman.extract_text()
        if teks_halaman:
            teks_utuh += teks_halaman + "\n"
    return teks_utuh

def ambil_data_alumni():
    conn = sqlite3.connect('database_plagiarisme_baru.db')
    cursor = conn.cursor()
    cursor.execute("SELECT penulis, judul, isi_teks FROM dokumen_alumni")
    data = cursor.fetchall()
    conn.close()
    return data

def simpan_ke_database(penulis, judul, isi_teks):
    conn = sqlite3.connect('database_plagiarisme_baru.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM dokumen_alumni WHERE judul = ?", (judul,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO dokumen_alumni (penulis, judul, isi_teks) VALUES (?, ?, ?)", 
                       (penulis, judul, isi_teks))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ==========================================
# 3. SISTEM AUTENTIKASI (SESSION STATE)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.nama = ""
    st.session_state.role = ""
    st.session_state.status = ""

def login_user(username, password):
    conn = sqlite3.connect('database_plagiarisme_baru.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, nama, role, status FROM pengguna WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(username, password, nama, role):
    # Jika mahasiswa langsung Aktif, jika dosen otomatis Pending
    status_awal = "Aktif" if role == "Mahasiswa" else "Pending"
    try:
        conn = sqlite3.connect('database_plagiarisme_baru.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pengguna VALUES (?, ?, ?, ?, ?)", (username, password, nama, role, status_awal))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# ==========================================
# 4. INTERFACE LOGIN / REGISTER (DESAIN BARU)
# ==========================================
if not st.session_state.logged_in:
    # Membuat Layout Tengah Untuk Login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🛡️ Semantic Portal</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Selamat datang di sistem pengecekan tugas berbasis AI.</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Masuk Akun", "🆕 Registrasi"])
        
        with tab1:
            with st.form("form_login"):
                user_input = st.text_input("Username / NPM / NIDN")
                pass_input = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Masuk Ke Dashboard", use_container_width=True)
                
                if submit_login:
                    user_data = login_user(user_input, pass_input)
                    if user_data:
                        st.session_state.logged_in = True
                        st.session_state.username = str(user_data[0])
                        st.session_state.nama = str(user_data[1])
                        st.session_state.role = str(user_data[2])
                        st.session_state.status = str(user_data[3])
                        st.rerun()
                    else:
                        st.error("Akun tidak ditemukan atau password salah!")
                        
        with tab2:
            with st.form("form_register"):
                reg_role = st.selectbox("Pilih Tipe Akun:", ["Mahasiswa", "Dosen"])
                reg_user = st.text_input("Username (NPM/NIDN)")
                reg_nama = st.text_input("Nama Lengkap")
                reg_pass = st.text_input("Password", type="password")
                
                st.caption("📝 *Catatan: Akun Dosen memerlukan persetujuan Superadmin." if reg_role == "Dosen" else "✨ Akun Mahasiswa aktif langsung.")
                
                submit_reg = st.form_submit_button("Daftar Sekarang", use_container_width=True)
                
                if submit_reg:
                    if reg_user and reg_nama and reg_pass:
                        if register_user(reg_user, reg_pass, reg_nama, reg_role):
                            st.success("Pendaftaran berhasil! Silakan login.")
                        else:
                            st.warning("Username sudah terdaftar.")
                    else:
                        st.error("Data tidak boleh kosong!")

# ==========================================
# 5. DASHBOARD UTAMA (SETELAH LOGIN)
# ==========================================
else:
    # Perbaikan Otomatis Identitas Khusus Superadmin
    if "superadmin" in str(st.session_state.username).lower():
        st.session_state.nama = "Pemilik Sistem (Master)"
        st.session_state.role = "Superadmin"
        st.session_state.status = "Aktif"

    # SIDEBAR YANG LEBIH INTERAKTIF
    with st.sidebar:
        st.markdown("### 👤 Profil Pengguna")
        st.info(f"**Nama:** {st.session_state.nama}")
        st.success(f"**Role:** {st.session_state.role}")
        st.warning(f"**Status:** {st.session_state.status}")
        st.markdown("---")
        
        if st.session_state.role == "Superadmin":
            list_menu = [
                "🔍 Cek Plagiarisme", 
                "📂 Upload Massal Kelas",
                "🛠️ Aktivasi Akun Dosen", 
                "📚 Input Data Acuan"
            ]
        elif st.session_state.role == "Dosen":
            list_menu = [
                "🔍 Cek Plagiarisme", 
                "📂 Upload Massal Kelas"
            ]
        else: 
            list_menu = ["🔍 Cek Plagiarisme"]
            
        menu = st.radio("Pilih Menu:", list_menu)
        
        st.markdown("---")
        if st.button("🚪 Keluar (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ------------------------------------------
    # MENU 1: CEK TUGAS / PLAGIARISME
    # ------------------------------------------
    if menu == "🔍 Cek Plagiarisme":
        st.title("📊 Pemeriksaan Kemiripan Dokumen")
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                file_diunggah = st.file_uploader("Unggah file tugas (.pdf):", type=["pdf"])
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                tombol_mulai = st.button("⚡ Mulai Analisis", use_container_width=True)
                    
        if tombol_mulai and file_diunggah:
            with st.spinner("🤖 Model IndoBERT sedang menganalisis semantik..."):
                teks_uji = ekstrak_teks_dari_pdf(file_diunggah)
                if teks_uji.strip() == "":
                    st.error("❌ File tidak terbaca.")
                else:
                    database_alumni = ambil_data_alumni()
                    if len(database_alumni) == 0:
                        st.warning("📂 Database acuan kosong. Silakan hubungi admin.")
                    else:
                        vektor_uji = get_embedding(teks_uji)
                        hasil_list = []
                        skor_tertinggi = 0
                        
                        for penulis, judul, isi_teks in database_alumni:
                            vektor_asal = get_embedding(isi_teks)
                            skor_kemiripan = cosine_similarity(vektor_uji, vektor_asal)[0][0]
                            persentase = round(skor_kemiripan.item() * 100, 2)
                            
                            kategori = "🔴 Tinggi" if persentase >= 70 else "🟡 Sedang" if persentase >= 40 else "🟢 Rendah"
                            if persentase > skor_tertinggi: skor_tertinggi = persentase
                            
                            hasil_list.append({
                                "Sumber": penulis, 
                                "Judul_ACuan": judul, 
                                "Tingkat_Kemiripan": f"{persentase}%", 
                                " Kategori": kategori
                            })
                            
                        # Tampilan Hasil Cards
                        st.success("✅ Analisis Selesai!")
                        
                        # Metric Utama
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Skor Tertinggi", f"{skor_tertinggi}%")
                        m2.metric("Jumlah Data_ACuan", len(database_alumni))
                        m3.metric("Status", "Aman" if skor_tertinggi < 40 else "Waspada!")
                        
                        # Tabel DataFrame
                        st.dataframe(pd.DataFrame(hasil_list), use_container_width=True)

    # ------------------------------------------
    # MENU 2: UPLOAD MASSAL (DOSEN & SUPERADMIN)
    # ------------------------------------------
    elif menu == "📂 Upload Massal Kelas":
        st.title("📂 Batch Upload Tugas Kelas")
        
        label_kelas = st.text_input("Mata Kuliah / Nama Kelas")
        list_upload_massal = st.file_uploader("Pilih banyak file PDF sekaligus:", type=["pdf"], accept_multiple_files=True)
        
        if st.button("💾 Proses & Simpan ke Database"):
            if label_kelas and list_upload_massal:
                counter = 0
                for file_pdf in list_upload_massal:
                    nama_mhs = file_pdf.name.replace(".pdf", "").replace("_", " ")
                    teks_pdf = ekstrak_teks_dari_pdf(file_pdf)
                    simpan_ke_database(nama_mhs, label_kelas, teks_pdf)
                    counter += 1
                st.success(f"🎉 Berhasil! {counter} file telah disimpan.")
            else:
                st.error("Isi semua kolom!")

    # ------------------------------------------
    # MENU 3: MANAJEMEN IZIN DOSEN (SUPERADMIN)
    # ------------------------------------------
    elif menu == "🛠️ Aktivasi Akun Dosen":
        st.title("🛠️ Pengaturan Akun Dosen")
        
        c1, c2 = st.columns(2)
        with c1:
            user_target = st.text_input("Username/NIDN Dosen")
        with c2:
            status_baru = st.selectbox("Status Izin:", ["Aktif", "Pending"])
            
        if st.button("🔄 Update Status"):
            conn = sqlite3.connect('database_plagiarisme_baru.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE pengguna SET status = ? WHERE username = ? AND role = 'Dosen'", (status_baru, user_target))
            conn.commit()
            conn.close()
            st.success(f"Status {user_target} diubah!")
            st.rerun()
            
        # Tabel Data Dosen
        conn =
