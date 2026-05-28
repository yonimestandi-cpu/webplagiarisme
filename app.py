import streamlit as st
import sqlite3
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
import os

# ==========================================
# 1. INITIALISASI DATABASE & MODEL AI
# ==========================================
def init_db():
    conn = sqlite3.connect('database_baru.db')
    cursor = conn.cursor()
    # Tabel Dokumen Pembanding
    cursor.execute('''CREATE TABLE IF NOT EXISTS dokumen_alumni 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, penulis TEXT, judul TEXT, isi_teks TEXT)''')
    # Tabel Pengguna/Akun
    cursor.execute('''CREATE TABLE IF NOT EXISTS pengguna 
                      (username TEXT PRIMARY KEY, password TEXT, nama TEXT, role TEXT, status TEXT)''')
    
    # Buat Akun Master Superadmin jika belum ada
    cursor.execute("SELECT username FROM pengguna WHERE username = 'superadmin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO pengguna VALUES ('superadmin', 'master123', 'Pemilik Sistem', 'Superadmin', 'Aktif')")
        # Contoh Akun Dosen Default untuk simulasi awal
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
    conn = sqlite3.connect('database_baru.db')
    cursor = conn.cursor()
    cursor.execute("SELECT penulis, judul, isi_teks FROM dokumen_alumni")
    data = cursor.fetchall()
    conn.close()
    return data

def simpan_ke_database(penulis, judul, isi_teks):
    conn = sqlite3.connect('database_baru.db')
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
    conn = sqlite3.connect('database_baru.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, nama, role, status FROM pengguna WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_dosen(username, password, nama):
    try:
        conn = sqlite3.connect('database_baru.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pengguna VALUES (?, ?, ?, 'Dosen', 'Pending')", (username, password, nama))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# ==========================================
# 4. INTERFACE LOGIN / REGISTER DOSEN
# ==========================================
if not st.session_state.logged_in:
    st.title("👨‍🏫 Semantic Plagiarism Portal (Dosen & Pemeriksa)")
    st.write("Selamat datang di sistem pengecekan kemiripan tugas mahasiswa berbasis IndoBERT.")
    
    tab1, tab2 = st.tabs(["Masuk Akun Dosen", "Registrasi Akun Dosen Baru"])
    
    with tab1:
        user_input = st.text_input("NIDN / Username:")
        pass_input = st.text_input("Password:", type="password")
        if st.button("Masuk Ke Dashboard"):
            user_data = login_user(user_input, pass_input)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.username = str(user_data)
                st.session_state.nama = str(user_data)
                st.session_state.role = str(user_data)
                st.session_state.status = str(user_data)
                st.rerun()
            else:
                st.error("Akun tidak ditemukan atau password salah!")
                
    with tab2:
        reg_user = st.text_input("Buat Username / NIDN:")
        reg_nama = st.text_input("Nama Lengkap Dosen (Beserta Gelar):")
        reg_pass = st.text_input("Buat Password Akun:", type="password", key="reg_pass")
        if st.button("Ajukan Pendaftaran"):
            if reg_user and reg_nama and reg_pass:
                if register_dosen(reg_user, reg_pass, reg_nama):
                    st.success("Pendaftaran berhasil diajukan! Silakan hubungi Superadmin untuk aktivasi.")
                else:
                    st.warning("Username/NIDN tersebut sudah terdaftar.")
            else:
                st.error("Semua kolom registrasi wajib diisi!")

# ==========================================
# 5. DASHBOARD UTAMA (SETELAH LOGIN BERHASIL)
# ==========================================
else:
    st.sidebar.title("⚙️ Panel Kontrol")
    st.sidebar.write(f"**Nama:** {st.session_state.nama}")
    st.sidebar.write(f"**Hak Akses:** {st.session_state.role}")
    st.sidebar.write(f"**Status Izin:** {st.session_state.status}")
    
    # Pintasan deteksi: Jika username mengandung kata 'superadmin', langsung buka menu admin
    if "superadmin" in str(st.session_state.username).lower():
        list_menu = ["⚙️ Aktivasi Izin Akun Dosen", "➕ Input Database Acuan"]
        # Paksa perbaikan tampilan teks di sidebar agar rapi
        st.session_state.nama = "Pemilik Sistem (Master)"
        st.session_state.role = "Superadmin"
        st.session_state.status = "Aktif"
    else:
        list_menu = ["🔍 Cek Plagiarisme Tugas Mahasiswa", "📁 Upload Massal Tugas Kelas"]
        
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navigasi Fitur:", list_menu)
    
    if st.sidebar.button("🚪 Keluar dari Aplikasi"):
        st.session_state.logged_in = False
        st.rerun()

    # ------------------------------------------
    # LEVEL DOSEN: MENU 1 - CEK TUGAS MAHASISWA
    # ------------------------------------------
    if menu == "🔍 Cek Plagiarisme Tugas Mahasiswa":
        st.title("📊 Pemeriksaan Tugas Kuliah / Skripsi Mahasiswa")
        
        if st.session_state.status == "Pending":
            st.warning("⚠️ Akses Ditangguhkan! Akun Dosen Anda belum diaktifkan/diberi izin oleh Superadmin.")
        else:
            file_diunggah = st.file_uploader("Pilih file tugas (.pdf):", type=["pdf"])
            
            col_cek1, col_cek2 = st.columns(2)
            with col_cek1:
                tombol_mulai = st.button("Mulai Analisis Semantik")
            with col_cek2:
                if st.button("🔄 Bersihkan Halaman"): st.rerun()
                    
            if tombol_mulai and file_diunggah:
                with st.spinner("Model IndoBERT sedang mengalkulasi..."):
                    teks_uji = ekstrak_teks_dari_pdf(file_diunggah)
                    if teks_uji.strip() == "":
                        st.error("Berkas PDF tidak terbaca atau kosong.")
                    else:
                        database_alumni = ambil_data_alumni()
                        if len(database_alumni) == 0:
                            st.warning("Database pembanding masih kosong.")
                        else:
                            vektor_uji = get_embedding(teks_uji)
                            hasil_list = []
                            skor_tertinggi = 0
                            
                            for penulis, judul, isi_teks in database_alumni:
                                vektor_asal = get_embedding(isi_teks)
                                skor_kemiripan = cosine_similarity(vektor_uji, vektor_asal)
                                persentase = skor_kemiripan.item() * 100
                                
                                kategori = "🔴 Plagiarisme Tinggi" if persentase >= 70 else "🟡 Plagiarisme Sedang" if persentase >= 40 else "🟢 Kemiripan Rendah"
                                if persentase > skor_tertinggi: skor_tertinggi = persentase
                                
                                hasil_list.append({"Nama Mahasiswa/Sumber": penulis, "Judul/Materi Tugas": judul, "Tingkat Kemiripan Semantik": f"{persentase:.2f}%", "Kesimpulan": kategori})
                                
                            st.success("Pemeriksaan Selesai!")
                            st.metric(label="Skor Kemiripan Tertinggi yang Ditemukan", value=f"{skor_tertinggi:.2f}%")
                            st.dataframe(pd.DataFrame(hasil_list))

    # ------------------------------------------
    # LEVEL DOSEN: MENU 2 - UPLOAD MASSAL TUGAS KELAS
    # ------------------------------------------
    elif menu == "📁 Upload Massal Tugas Kelas":
        st.title("📁 Batch Ingestion (Upload Kolektif Satu Kelas)")
        
        if st.session_state.status == "Pending":
            st.warning("⚠️ Akses Ditangguhkan! Akun Dosen Anda belum diaktifkan.")
        else:
            label_kelas = st.text_input("Nama Mata Kuliah & Kelas:")
            list_upload_massal = st.file_uploader("Pilih semua file PDF tugas mahasiswa sekaligus:", type=["pdf"], accept_multiple_files=True)
            
            if st.button("Proses & Masukkan ke Database") and label_kelas and list_upload_massal:
                counter = 0
                with st.spinner("Menyimpan data..."):
                    for file_pdf in list_upload_massal:
                        nama_mhs = file_pdf.name.replace(".pdf", "").replace("_", " ")
                        teks_pdf = ekstrak_teks_dari_pdf(file_pdf)
                        simpan_ke_database(nama_mhs, label_kelas, teks_pdf)
                        counter += 1
                st.success(f"Berhasil! {counter} tugas kelas {label_kelas} disimpan ke database.")

    # ------------------------------------------
    # LEVEL SUPERADMIN: MENU 1 - MANAJEMEN IZIN DOSEN
    # ------------------------------------------
    elif menu == "⚙️ Aktivasi Izin Akun Dosen":
        st.title("⚙️ Otorisasi Akun Dosen Baru")
        st.write("Berikan izin aktif kepada dosen yang baru mendaftar agar mereka bisa menggunakan fitur AI.")
        
        conn = sqlite3.connect('database_baru.db')
        cursor = conn.cursor()
        
        user_target = st.text_input("Masukkan Username/NIDN Dosen:")
        status_baru = st.selectbox("Tentukan Izin Akses:", ["Aktif", "Pending"])
        
        if st.button("Perbarui Status Izin Dosen"):
            cursor.execute("UPDATE pengguna SET status = ? WHERE username = ? AND role = 'Dosen'", (status_baru, user_target))
            conn.commit()
            st.success(f"Akun Dosen '{user_target}' sekarang berstatus: {status_baru}!")
            st.rerun()
            
        st.subheader("📋 Daftar Akun Dosen Terdaftar")
        df_user = pd.read_sql_query("SELECT username as 'NIDN/Username', nama as 'Nama Lengkap', role as 'Jabatan', status as 'Status Izin' FROM pengguna WHERE role = 'Dosen'", conn)
        conn.close()
        st.dataframe(df_user)

    # ------------------------------------------
    # LEVEL SUPERADMIN: MENU 2 - INPUT DATA ACUAN KAMPUS
    # ------------------------------------------
    elif menu == "➕ Input Database Acuan":
        st.title("➕ Pangkalan Data Acuan Utama")
        
        penulis_default = st.text_input("Nama Alumni / Sumber Tahun:")
        list_file_acuan = st.file_uploader("Pilih PDF Skripsi Alumni:", type=["pdf"], accept_multiple_files=True)
        
        if st.button("Simpan ke Repositori") and penulis_default and list_file_acuan:
            for file_acuan in list_file_acuan:
                teks_acuan = ekstrak_teks_dari_pdf(file_acuan)
                judul_otomatis = file_acuan.name.replace(".pdf", "")
                simpan_ke_database(penulis_default, judul_otomatis, teks_acuan)
            st.success("Data arsip kampus berhasil ditambahkan.")
