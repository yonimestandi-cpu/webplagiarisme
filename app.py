import streamlit as st
import sqlite3
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
import os

# ==========================================
# 1. KONFIGURASI CORE AI & MODEL
# ==========================================
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
# 2. FUNGSI EKSTRAKSI & DATABASE
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
    conn = sqlite3.connect('kampus_repository.db')
    cursor = conn.cursor()
    cursor.execute("SELECT penulis, judul, isi_teks FROM dokumen_alumni")
    data = cursor.fetchall()
    conn.close()
    return data

def simpan_ke_database(penulis, judul, isi_teks):
    conn = sqlite3.connect('kampus_repository.db')
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
# 3. SIDEBAR NAVIGATION (MENU)
# ==========================================
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", [
    "🔍 Cek Plagiarisme PDF", 
    "➕ Input Acuan via Web", 
    "📁 Folder Scanner Otomatis"
])


# ==========================================
# HALAMAN 1: CEK PLAGIARISME
# ==========================================
if menu == "🔍 Cek Plagiarisme PDF":
    st.title("📊 Semantic Plagiarism Dashboard")
    st.subheader("Analisis Kemiripan Dokumen Berbasis IndoBERT")
    
    file_diunggah = st.file_uploader("Unggah skripsi mahasiswa (.pdf) untuk diuji:", type=["pdf"])
    
    col_cek1, col_cek2 = st.columns(2)
    with col_cek1:
        tombol_mulai = st.button("Mulai Analisis")
    with col_cek2:
        if st.button("🔄 Bersihkan Halaman", key="btn_reset_cek"):
            st.rerun()
            
    if tombol_mulai:
        if file_diunggah:
            with st.spinner("Mengekstrak dan menganalisis teks..."):
                teks_uji = ekstrak_teks_dari_pdf(file_diunggah)
                
                if teks_uji.strip() == "":
                    st.error("File PDF kosong atau berupa hasil scan gambar.")
                else:
                    database_alumni = ambil_data_alumni()
                    vektor_uji = get_embedding(teks_uji)
                    hasil_list = []
                    skor_tertinggi = 0
                    
                    for penulis, judul, isi_teks in database_alumni:
                        vektor_asal = get_embedding(isi_teks)
                        skor_kemiripan = cosine_similarity(vektor_uji, vektor_asal)
                        persentase = skor_kemiripan.item() * 100
                        
                        if persentase >= 70:
                            kategori = "🔴 Plagiarisme Tinggi"
                        elif persentase >= 40:
                            kategori = "🟡 Plagiarisme Sedang"
                        else:
                            kategori = "🟢 Kemiripan Rendah"
                            
                        if persentase > skor_tertinggi:
                            skor_tertinggi = persentase
                        
                        hasil_list.append({
                            "Penulis/Sumber": penulis,
                            "Judul Dokumen": judul,
                            "Tingkat Kemiripan": f"{persentase:.2f}%",
                            "Status": kategori
                        })
                        
                    st.success("Analisis Selesai!")
                    st.metric(label="Skor Kemiripan Tertinggi", value=f"{skor_tertinggi:.2f}%")
                    st.dataframe(pd.DataFrame(hasil_list))
        else:
            st.warning("Unggah file PDF terlebih dahulu.")


# ==========================================
# HALAMAN 2: INPUT ACUAN VIA WEB
# ==========================================
elif menu == "➕ Input Acuan via Web":
    st.title("➕ Tambah Dokumen Pembanding")
    st.write("Gunakan halaman ini untuk memasukkan dokumen acuan baru secara massal.")
    
    penulis_default = st.text_input("Label Sumber / Tahun (Contoh: Dokumen Alumni (2026)):")
    list_file_acuan = st.file_uploader("Unggah PDF Acuan (Bisa pilih banyak file):", 
                                       type=["pdf"], accept_multiple_files=True, key="acuan_massal")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        tombol_simpan = st.button("Simpan Dokumen")
    with col_input2:
        if st.button("🔄 Reset Form", key="btn_reset_input"):
            st.rerun()
            
    if tombol_simpan:
        if penulis_default and list_file_acuan:
            counter_berhasil = 0
            counter_duplikat = 0
            
            with st.spinner("Sedang memproses seluruh file PDF..."):
                for file_acuan in list_file_acuan:
                    teks_acuan = ekstrak_teks_dari_pdf(file_acuan)
                    judul_otomatis = file_acuan.name.replace(".pdf", "")
                    berhasil = simpan_ke_database(penulis_default, judul_otomatis, teks_acuan)
                    if berhasil:
                        counter_berhasil += 1
                    else:
                        counter_duplikat += 1
            
            if counter_berhasil > 0:
                st.success(f"Sukses! {counter_berhasil} dokumen baru berhasil disimpan.")
            if counter_duplikat > 0:
                st.warning(f"{counter_duplikat} dokumen dilewati karena judulnya duplikat.")
        else:
            st.error("Mohon isi label sumber dan pilih file PDF!")


# ==========================================
# HALAMAN 3: FOLDER SCANNER
# ==========================================
elif menu == "📁 Folder Scanner Otomatis":
    st.title("📁 Batch Folder Scanner & Ingestion")
    st.write("Unggah banyak file PDF sekaligus lewat browser untuk otomatis diarsipkan secara fisik dan digital.")
    
    list_upload_massal = st.file_uploader(
        "Pilih atau seret semua file PDF alumni di sini:", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="folder_upload_massal"
    )
    
    col_scan1, col_scan2 = st.columns(2)
    with col_scan1:
        tombol_pindai = st.button("Pindai & Sinkronisasi")
    with col_scan2:
        if st.button("🔄 Reset Halaman", key="btn_reset_scan"):
            st.rerun()
            
    if tombol_pindai:
        if list_upload_massal:
            folder_target = "kumpulan_skripsi"
            if not os.path.exists(folder_target):
                os.makedirs(folder_target)
                
            counter_tersimpan = 0
            counter_duplikat = 0
            
            with st.spinner("Menyinkronkan data..."):
                for file_pdf in list_upload_massal:
                    path_simpan_fisik = os.path.join(folder_target, file_pdf.name)
                    with open(path_simpan_fisik, "wb") as f:
                        f.write(file_pdf.getbuffer())
                    
                    teks_pdf = ekstrak_teks_dari_pdf(file_pdf)
                    judul_clean = file_pdf.name.replace(".pdf", "")
                    berhasil = simpan_ke_database("Sistem Scanner (2026)", judul_clean, teks_pdf)
                    
                    if berhasil:
                        counter_tersimpan += 1
                    else:
                        counter_duplikat += 1
            
            st.success(f"⚡ Sinkronisasi Berhasil! {counter_tersimpan} dokumen masuk database.")
            if counter_duplikat > 0:
                st.warning(f"ℹ️ {counter_duplikat} dokumen dilewati karena duplikat.")
                
            st.write("### 🗄️ Status Repositori Database Saat Ini:")
            conn = sqlite3.connect('kampus_repository.db')
            df_sekarang = pd.read_sql_query("SELECT penulis, judul FROM dokumen_alumni", conn)
            conn.close()
            st.dataframe(df_sekarang)
        else:
            st.error("Silakan masukkan file-file PDF terlebih dahulu!")