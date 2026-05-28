import streamlit as st
import sqlite3
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
import os

# ==========================================
# CUSTOM UI THEME & DESIGN INJECTION (CSS RED GRADIENT)
# ==========================================
st.set_page_config(
    page_title="Semantic Plagiarism Portal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mengubah tampilan dasar via CSS Injection dengan tema Merah Gradasi Profesional
st.markdown("""
    <style>
    /* Mengubah font dan background utama */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #fcfcfd;
    }
    
    /* Mempercantik Sidebar (Professional Dark Red/Burgundy Theme) */
    [data-testid="stSidebar"] {
        background-color: #1e0505 !important;
        color: #ffffff !important;
        border-right: 1px solid #3b0a0a;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span {
        color: #f8fafc !important;
    }
    
    /* Desain Radio Button Sidebar dengan Gradasi Merah Elegan */
    div[data-testid="stRadio"] label {
        background-color: #2d0d0d !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #4a1515 !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stRadio"] label:hover {
        background-color: #4a1515 !important;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #dc2626 !important;
        background-image: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%) !important;
        border-color: #ef4444 !important;
    }

    /* Mempercantik Tombol Utama dengan Gradasi Merah Menyala */
    .stButton>button {
        background-image: linear-gradient(135deg, #991b1b 0%, #dc2626 100%);
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(153, 27, 27, 0.2);
        width: 100%;
    }
    .stButton>button:hover {
        background-image: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%);
        transform: translateY(-1px);
        color: white;
        box-shadow: 0 6px 10px -1px rgba(153, 27, 27, 0.4);
    }
    
    /* Tombol Keluar khusus warna merah gelap solid */
    div.sidebar-logout button {
        background-image: none !important;
        background-color: #7f1d1d !important;
    }
    div.sidebar-logout button:hover {
        background-color: #991b1b !important;
    }

    /* Mempercantik Kartu Metric & Konten */
    div[data-testid="stMetricValue"] {
        font-size: 36px !important;
        font-weight: 800 !important;
        color: #1e293b !important;
    }
    
    /* Desain Kotak File Uploader */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #fca5a5 !important;
        border-radius: 12px !important;
        background-color: #fff5f5 !important;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 1. INITIALISASI DATABASE & MODEL AI
# ==========================================
def init_db():
    conn = sqlite3.connect('database_plagiarisme_baru.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS dokumen_alumni 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, penulis TEXT, judul TEXT, isi_teks TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pengguna 
                      (username TEXT PRIMARY KEY, password TEXT, nama TEXT, role TEXT, status TEXT)''')
    
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
# 4. INTERFACE LOGIN / REGISTER (TEMA MERAH GRADASI)
# ==========================================
if not st.session_state.logged_in:
    col_centered = st.columns([1, 1.8, 1])[1]
    with col_centered:
        # Header Judul dengan efek warna Merah Gradasi via CSS text-gradient
        st.markdown("""
            <h1 style='text-align: center; font-weight: 800; background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                🎯 Plagiarisme Portal
            </h1>
        """, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 30px;'>Pemeriksaan dokumen cerdas bertenaga Deep Learning IndoBERT</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 Masuk Akun", "📝 Daftar Baru"])
        
        with tab1:
            user_input = st.text_input("Username / ID Pengguna:")
            pass_input = st.text_input("Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Masuk"):
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
            reg_role = st.selectbox("Saya adalah:", ["Mahasiswa", "Dosen"])
            reg_user = st.text_input("NPM Mahasiswa / NIDN Dosen:")
            reg_nama = st.text_input("Nama Lengkap:")
            reg_pass = st.text_input("Buat Password:", type="password", key="reg_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Daftar Sekarang"):
                if reg_user and reg_nama and reg_pass:
                    if register_user(reg_user, reg_pass, reg_nama, reg_role):
                        if reg_role == "Mahasiswa":
                            st.success("Sukses! Akun Mahasiswa langsung AKTIF. Silakan login pada tab Masuk.")
                        else:
                            st.success("Sukses diajukan! Menunggu aktivasi Superadmin.")
                    else:
                        st.warning("ID tersebut sudah terdaftar.")
                else:
                    st.error("Semua kolom wajib diisi!")

# ==========================================
# 5. DASHBOARD UTAMA (SETELAH LOGIN)
# ==========================================
else:
    if "superadmin" in str(st.session_state.username).lower():
        st.session_state.nama = "Pemilik Sistem (Master)"
        st.session_state.role = "Superadmin"
        st.session_state.status = "Aktif"

    # Profile Widget di Sidebar dengan Aksen Gelap Burgundy
    st.sidebar.markdown(f"""
        <div style="background-color: #2d0d0d; padding: 15px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #4a1515;">
            <p style="margin: 0; font-size: 12px; color: #fca5a5 !important; text-transform: uppercase; font-weight: bold;">User Profile</p>
            <h4 style="margin: 5px 0 0 0; color: #ffffff !important; font-size: 16px;">{st.session_state.nama}</h4>
            <span style="display: inline-block; background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%); color: white !important; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-top: 8px; font-weight: bold;">{st.session_state.role}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigasi Menu
    if st.session_state.role == "Superadmin":
        list_menu = ["🔍 Cek Plagiarisme", "📁 Upload Massal Kelas", "⚙️ Aktivasi Akun Dosen", "➕ Input Database Acuan"]
    elif st.session_state.role == "Dosen":
        list_menu = ["🔍 Cek Plagiarisme", "📁 Upload Massal Kelas"]
    else:
        list_menu = ["🔍 Cek Plagiarisme"]
        
    menu = st.sidebar.radio("NAVIGASI UTAMA", list_menu)
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-logout">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 Keluar Aplikasi"):
        st.session_state.logged_in = False
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------
    # MENU 1: CEK PLAGIARISME
    # ------------------------------------------
    if menu == "🔍 Cek Plagiarisme":
        st.markdown("<h2 style='color: #1e293b; font-weight: 700;'>🔍 Analisis Semantik Dokumen</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b;'>Unggah tugas kuliah format PDF untuk menguji kecocokan kontekstual dengan pangkalan data.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.session_state.status == "Pending":
            st.warning("⚠️ Akses ditangguhkan sementara. Hubungi Superadmin untuk aktivasi.")
        else:
            file_diunggah = st.file_uploader("", type=["pdf"])
            
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                tombol_mulai = st.button("Mulai Deteksi AI")
                
            if tombol_mulai and file_diunggah:
                with st.spinner("Model NLP IndoBERT sedang membaca konteks bahasa..."):
                    teks_uji = ekstrak_teks_dari_pdf(file_diunggah)
                    if teks_uji.strip() == "":
                        st.error("File PDF tidak berisi teks digital.")
                    else:
                        database_alumni = ambil_data_alumni()
                        if len(database_alumni) == 0:
                            st.warning("Database acuan kosong. Silakan isi data terlebih dahulu.")
                        else:
                            vektor_uji = get_embedding(teks_uji)
                            hasil_list = []
                            skor_tertinggi = 0
                            
                            for penulis, judul, isi_teks in database_alumni:
                                vektor_asal = get_embedding(isi_teks)
                                skor_kemiripan = cosine_similarity(vektor_uji, vektor_asal)[0][0]
                                persentase = skor_kemiripan.item() * 100
                                
                                kategori = "🔴 Tinggi" if persentase >= 70 else "🟡 Sedang" if persentase >= 40 else "🟢 Rendah"
                                if persentase > skor_tertinggi: skor_tertinggi = persentase
                                
                                hasil_list.append({"Sumber Data": penulis, "Kategori/Mata Kuliah": judul, "Kemiripan Konteks": f"{persentase:.2f}%", "Status": kategori})
                                
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Tampilan visual ringkasan berbentuk card modern dengan alert dinamis
                            card_color = "#fef2f2" if skor_tertinggi >= 70 else "#fef9c3" if skor_tertinggi >= 40 else "#f0fdf4"
                            text_color = "#991b1b" if skor_tertinggi >= 70 else "#854d0e" if skor_tertinggi >= 40 else "#166534"
                            
                            st.markdown(f"""
                                <div style="background-color: {card_color}; border-left: 5px solid {text_color}; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                                    <p style="margin: 0; font-size: 14px; color: {text_color}; font-weight: bold; text-transform: uppercase;">Hasil Analisis Tertinggi</p>
                                    <h1 style="margin: 5px 0 0 0; color: {text_color}; font-weight: 800; font-size: 42px;">{skor_tertinggi:.2f}%</h1>
                                    <p style="margin: 5px 0 0 0; color: #475569; font-size: 14px;">Kesimpulan: Berkas terindikasi <b>{kategori}</b> meniru dokumen referensi di database.</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            st.subheader("📋 Rincian Matriks Perbandingan Semantik")
                            st.dataframe(pd.DataFrame(hasil_list), use_container_width=True)

    # ------------------------------------------
    # MENU 2: UPLOAD MASSAL KELAS
    # ------------------------------------------
    elif menu == "📁 Upload Massal Kelas":
        st.markdown("<h2 style='color: #1e293b; font-weight: 700;'>📁 Ingesti Data Kolektif</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        label_kelas = st.text_input("Nama Mata Kuliah / Nama Kelas Pembanding:")
        list_upload_massal = st.file_uploader("Unggah sekaligus berkas tugas satu kelas (.pdf):", type=["pdf"], accept_multiple_files=True)
        
        if st.button("Simpan Data Massal") and label_kelas and list_upload_massal:
            counter = 0
            with st.spinner("Mengekstrak berkas kelas..."):
                for file_pdf in list_upload_massal:
                    nama_mhs = file_pdf.name.replace(".pdf", "").replace("_", " ")
                    teks_pdf = ekstrak_teks_dari_pdf(file_pdf)
                    simpan_ke_database(nama_mhs, label_kelas, teks_pdf)
                    counter += 1
            st.success(f"🔥 Berhasil menyuntikkan {counter} dokumen ke kelas '{label_kelas}'.")

    # ------------------------------------------
    # MENU 3: MANAJEMEN IZIN DOSEN
    # ------------------------------------------
    elif menu == "⚙️ Aktivasi Akun Dosen":
        st.markdown("<h2 style='color: #1e293b; font-weight: 700;'>⚙️ Manajemen Akses Staf Dosen</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        conn = sqlite3.connect('database_plagiarisme_baru.db')
        cursor = conn.cursor()
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            user_target = st.text_input("ID Dosen / Username Target:")
        with col_act2:
            status_baru = st.selectbox("Set Otorisasi:", ["Aktif", "Pending"])
            
        if st.button("Terapkan Hak Akses"):
            cursor.execute("UPDATE pengguna SET status = ? WHERE username = ? AND role = 'Dosen'", (status_baru, user_target))
            conn.commit()
            st.success(f"Status '{user_target}' sukses diubah ke {status_baru}!")
            st.rerun()
            
        st.markdown("<br><br><h4>Daftar Registrasi Akun Staf Pengajar</h4>", unsafe_allow_html=True)
        df_user = pd.read_sql_query("SELECT username as 'NIDN/Username', nama as 'Nama Staf', status as 'Status Izin' FROM pengguna WHERE role = 'Dosen'", conn)
        conn.close()
        st.dataframe(df_user, use_container_width=True)

    # ------------------------------------------
    # MENU 4: INPUT DATABASE ACUAN
    # ------------------------------------------
    elif menu == "➕ Input Database Acuan":
        st.markdown("<h2 style='color: #1e293b; font-weight: 700;'>➕ Pangkalan Data Khusus Alumni/Skripsi</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        pen
