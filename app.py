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
    conn = sqlite3.connect('database_plagiarisme_baru.db')
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
# 4. INTERFACE LOGIN / REGISTER MULTI-ROLE
# ==========================================
if not st.session_state.logged_in:
    st.title("👨‍🏫 Semantic Plagiarism Portal")
    st.write("Selamat datang di sistem pengecekan kemiripan tugas berbasis AI IndoBERT.")
    
    tab1, tab2 = st.tabs(["Masuk Akun", "Registrasi Akun Baru"])
    
    with tab1:
        user_input = st.text_input("Username / NPM / NIDN:")
        pass_input = st.text_input("Password:", type="password")
        if st.button("Masuk Ke Dashboard"):
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
        reg_role = st.selectbox("Pilih Tipe Akun:", ["Mahasiswa", "Dosen"])
        reg_user = st.text_input("Buat Username (NPM untuk Mahasiswa / NIDN untuk Dosen):")
        reg_nama = st.text_input("Nama Lengkap:")
        reg_pass = st.text_input("Buat Password Akun:", type="password", key="reg_pass")
        
        if reg_role == "Mahasiswa":
            st.caption("✨ Akun Mahasiswa akan otomatis aktif setelah mendaftar.")
        else:
            st.caption("⚠️ Akun Dosen memerlukan aktivasi manual dari Superadmin setelah diajukan.")
            
        if st.button("Daftar Sekarang"):
            if reg_user and reg_nama and reg_pass:
                if register_user(reg_user, reg_pass, reg_nama, reg_role):
                    if reg_role == "Mahasiswa":
                        st.success("Pendaftaran berhasil! Akun Anda sudah AKTIF. Silakan pindah ke tab 'Masuk Akun' untuk login.")
                    else:
                        st.success("Pendaftaran Dosen berhasil diajukan! Harap hubungi Superadmin untuk aktivasi.")
                else:
                    st.warning("Username/NPM/NIDN tersebut sudah terdaftar di sistem.")
            else:
                st.error("Semua kolom registrasi wajib diisi!")

# ==========================================
# 5. DASHBOARD UTAMA (SETELAH LOGIN)
# ==========================================
else:
    # Perbaikan Otomatis Identitas Khusus Superadmin agar Teks Tanda Kurung Hilang
    if "superadmin" in str(st.session_state.username).lower():
        st.session_state.nama = "Pemilik Sistem (Master)"
        st.session_state.role = "Superadmin"
        st.session_state.status = "Aktif"

    st.sidebar.title("⚙️ Panel Kontrol")
    st.sidebar.write(f"**Nama:** {st.session_state.nama}")
    st.sidebar.write(f"**Hak Akses:** {st.session_state.role}")
    st.sidebar.write(f"**Status Izin:** {st.session_state.status}")
    
    # LOGIKA NAVIGASI MENU BERDASARKAN ROLE
    if st.session_state.role == "Superadmin":
        list_menu = [
            "🔍 Cek Plagiarisme Tugas Mahasiswa", 
            "📁 Upload Massal Tugas Kelas",
            "⚙️ Aktivasi Izin Akun Dosen", 
            "➕ Input Database Acuan"
        ]
    elif st.session_state.role == "Dosen":
        list_menu = [
            "🔍 Cek Plagiarisme Tugas Mahasiswa", 
            "📁 Upload Massal Tugas Kelas"
        ]
    else:  # Jika Mahasiswa
        list_menu = [
            "🔍 Cek Plagiarisme Tugas Mahasiswa"
        ]
        
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navigasi Fitur:", list_menu)
    
    if st.sidebar.button("🚪 Keluar dari Aplikasi"):
        st.session_state.logged_in = False
        st.rerun()

    # ------------------------------------------
    # MENU 1: CEK TUGAS / PLAGIARISME (Bisa diakses Semua Role)
    # ------------------------------------------
    if menu == "🔍 Cek Plagiarisme Tugas Mahasiswa":
        st.title("📊 Pemeriksaan Tingkat Kemiripan Dokumen")
        
        if st.session_state.status == "Pending":
            st.warning("⚠️ Akses Ditangguhkan! Akun Anda belum diaktifkan oleh Superadmin.")
        else:
            st.write("Silakan unggah file PDF untuk dianalisis tingkat kemiripan semantiknya dengan database kampus.")
            file_diunggah = st.file_uploader("Pilih file tugas (.pdf):", type=["pdf"])
            
            col_cek1, col_cek2 = st.columns(2)
            with col_cek1:
                tombol_mulai = st.button("Mulai Analisis Semantik")
            with col_cek2:
                if st.button("🔄 Bersihkan Halaman"): st.rerun()
                    
            if tombol_mulai and file_diunggah:
                with st.spinner("Model IndoBERT sedang mengalkulasi kecocokan makna..."):
                    teks_uji = ekstrak_teks_dari_pdf(file_diunggah)
                    if teks_uji.strip() == "":
                        st.error("Berkas PDF tidak terbaca atau kosong.")
                    else:
                        database_alumni = ambil_data_alumni()
                        if len(database_alumni) == 0:
                            st.warning("Database pembanding masih kosong. Hubungi dosen/admin untuk mengisi data acuan terlebih dahulu.")
                        else:
                            vektor_uji = get_embedding(teks_uji)
                            hasil_list = []
                            skor_tertinggi = 0
                            
                            for penulis, judul, isi_teks in database_alumni:
                                vektor_asal = get_embedding(isi_teks)
                                skor_kemiripan = cosine_similarity(vektor_uji, vektor_asal)[0][0]
                                persentase = skor_kemiripan.item() * 100
                                
                                kategori = "🔴 Plagiarisme Tinggi" if persentase >= 70 else "🟡 Plagiarisme Sedang" if persentase >= 40 else "🟢 Kemiripan Rendah"
                                if persentase > skor_tertinggi: skor_tertinggi = persentase
                                
                                hasil_list.append({"Nama Pengunggah/Sumber": penulis, "Mata Kuliah/Judul": judul, "Kemiripan Semantik": f"{persentase:.2f}%", "Kesimpulan": kategori})
                                
                            st.success("Pemeriksaan Selesai!")
                            st.metric(label="Skor Kemiripan Tertinggi", value=f"{skor_tertinggi:.2f}%")
                            st.dataframe(pd.DataFrame(hasil_list))

    # ------------------------------------------
    # MENU 2: UPLOAD MASSAL TUGAS KELAS (Dosen & Superadmin Only)
    # ------------------------------------------
    elif menu == "📁 Upload Massal Tugas Kelas":
        st.title("📁 Batch Ingestion (Upload Kolektif Satu Kelas)")
        
        if st.session_state.status == "Pending":
            st.warning("⚠️ Akses Ditangguhkan!")
        else:
            label_kelas = st.text_input("Nama Mata Kuliah & Kelas:")
            list_upload_massal = st.file_uploader("Pilih semua file PDF tugas mahasiswa sekaligus:", type=["pdf"], accept_multiple_files=True)
            
            if st.button("Proses & Masukkan ke Database") and label_kelas and list_upload_massal:
                counter = 0
                with st.spinner("Menyimpan data kelas..."):
                    for file_pdf in list_upload_massal:
                        nama_mhs = file_pdf.name.replace(".pdf", "").replace("_", " ")
                        teks_pdf = ekstrak_teks_dari_pdf(file_pdf)
                        simpan_ke_database(nama_mhs, label_kelas, teks_pdf)
                        counter += 1
                st.success(f"⚡ Sukses! {counter} tugas kelas '{label_kelas}' berhasil dimasukkan ke database pembanding.")

    # ------------------------------------------
    # MENU 3: MANAJEMEN IZIN DOSEN (SUPERADMIN ONLY)
    # ------------------------------------------
    elif menu == "⚙️ Aktivasi Izin Akun Dosen":
        st.title("⚙️ Otorisasi Akun Dosen Baru")
        
        conn = sqlite3.connect('database_plagiarisme_baru.db')
        cursor = conn.cursor()
        
        user_target = st.text_input("Masukkan Username/NIDN Dosen:")
        status_baru = st.selectbox("Tentukan Izin Akses:", ["Aktif", "Pending"])
        
        if st.button("Perbarui Status Izin Dosen"):
            cursor.execute("UPDATE pengguna SET status = ? WHERE username = ? AND role = 'Dosen'", (status_baru, user_target))
            conn.commit()
            st.success(f"Akun Dosen '{user_target}' sekarang berstatus: {status_baru}!")
            st.rerun()
            
        st.subheader("📋 Daftar Akun Dosen Terdaftar")
        df_user = pd.read_sql_query("SELECT username as 'NIDN/Username', nama as 'Nama Lengkap', status as 'Status Izin' FROM pengguna WHERE role = 'Dosen'", conn)
        conn.close()
        st.dataframe(df_user)

    # ------------------------------------------
    # MENU 4: INPUT DATA ACUAN KAMPUS (SUPERADMIN ONLY)
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
