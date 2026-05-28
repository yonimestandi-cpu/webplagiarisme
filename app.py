# =========================================================
# 🎨 CUSTOM UI / MODERN STYLE
# =========================================================
st.set_page_config(
    page_title="Semantic Plagiarism Portal",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>

/* ===== GLOBAL ===== */
html, body, [class*="css"]{
    font-family: 'Poppins', sans-serif;
}

.main {
    background: linear-gradient(135deg, #f5f7ff 0%, #eef2ff 100%);
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] *{
    color: white !important;
}

section[data-testid="stSidebar"] .stRadio > div{
    gap: 10px;
}

section[data-testid="stSidebar"] label{
    background: rgba(255,255,255,0.06);
    padding: 12px 14px;
    border-radius: 14px;
    transition: 0.3s;
}

section[data-testid="stSidebar"] label:hover{
    background: rgba(255,255,255,0.14);
    transform: translateX(4px);
}

/* ===== TITLE ===== */
.main-title{
    font-size: 42px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 5px;
}

.sub-title{
    color: #6b7280;
    font-size: 17px;
    margin-bottom: 30px;
}

/* ===== CARD ===== */
.custom-card{
    background: white;
    padding: 25px;
    border-radius: 24px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

/* ===== BUTTON ===== */
.stButton > button{
    width: 100%;
    border-radius: 14px;
    border: none;
    padding: 12px 20px;
    font-weight: 700;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    transition: 0.3s;
}

.stButton > button:hover{
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(99,102,241,0.3);
}

/* ===== INPUT ===== */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"]{
    border-radius: 14px !important;
    border: 1px solid #dbeafe !important;
    padding: 10px !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"]{
    background: white;
    border-radius: 20px;
    padding: 20px;
    border: 2px dashed #c7d2fe;
}

/* ===== METRIC ===== */
[data-testid="metric-container"]{
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.04);
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"]{
    background: white;
    padding: 15px;
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.04);
}

/* ===== ALERT ===== */
.stSuccess, .stWarning, .stError, .stInfo{
    border-radius: 16px !important;
}

/* ===== HERO SECTION ===== */
.hero-box{
    background: linear-gradient(135deg,#4f46e5,#7c3aed);
    padding: 40px;
    border-radius: 28px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 15px 40px rgba(99,102,241,0.3);
}

.hero-title{
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
}

.hero-desc{
    font-size: 18px;
    opacity: 0.95;
}

/* ===== TAB ===== */
.stTabs [data-baseweb="tab-list"]{
    gap: 10px;
}

.stTabs [data-baseweb="tab"]{
    background: white;
    border-radius: 12px 12px 0 0;
    padding: 10px 18px;
}

/* ===== ANIMATION ===== */
@keyframes fadeIn{
    from{
        opacity:0;
        transform:translateY(10px);
    }
    to{
        opacity:1;
        transform:translateY(0);
    }
}

.custom-card,
.hero-box,
[data-testid="metric-container"]{
    animation: fadeIn 0.5s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO SECTION LOGIN
# =========================================================
if not st.session_state.logged_in:

    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">🧠 Semantic Plagiarism Portal</div>
        <div class="hero-desc">
            Sistem pemeriksaan kemiripan tugas berbasis Artificial Intelligence 
            menggunakan IndoBERT untuk mendeteksi plagiarisme semantik secara modern, cepat, dan akurat.
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# SIDEBAR MODERN
# =========================================================
if st.session_state.logged_in:

    st.sidebar.markdown("""
    <div style='text-align:center; padding:10px 0 20px 0;'>
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='90'>
        <h2 style='margin-top:10px;'>AI Campus Portal</h2>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# DASHBOARD HEADER
# =========================================================
if st.session_state.logged_in:

    st.markdown(f"""
    <div class="hero-box">
        <div class="hero-title">👋 Selamat Datang, {st.session_state.nama}</div>
        <div class="hero-desc">
            Role: <b>{st.session_state.role}</b> • 
            Status: <b>{st.session_state.status}</b><br>
            Nikmati pengalaman pemeriksaan dokumen yang lebih modern dan interaktif.
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# WRAP CONTENT DALAM CARD
# =========================================================

# CONTOH:
# GANTI:
# st.title("📊 Pemeriksaan Tingkat Kemiripan Dokumen")

# MENJADI:
st.markdown("""
<div class="custom-card">
    <h2>📊 Pemeriksaan Tingkat Kemiripan Dokumen</h2>
    <p>
        Unggah dokumen PDF untuk dianalisis menggunakan teknologi AI Semantic Similarity.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TAMPILAN LOGIN MODERN
# =========================================================

# Tambahkan sebelum tab login/register
if not st.session_state.logged_in:

    colA, colB, colC = st.columns([1,2,1])

    with colB:
        st.markdown("""
        <div class="custom-card">
            <h2 style='text-align:center;'>🚀 Portal Akademik AI</h2>
            <p style='text-align:center;color:gray;'>
                Platform pemeriksaan tugas modern untuk mahasiswa & dosen.
            </p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# METRIC TAMBAHAN AGAR LEBIH MODERN
# =========================================================

# Setelah login dashboard
if st.session_state.logged_in:

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📄 Total Dokumen", "1.2K+")

    with col2:
        st.metric("🧠 AI Model", "IndoBERT")

    with col3:
        st.metric("⚡ Status Sistem", "Aktif")

# =========================================================
# FOOTER MODERN
# =========================================================
st.markdown("""
<hr style="margin-top:50px;">

<div style='text-align:center; color:gray; padding-bottom:20px;'>
    <b>Semantic Plagiarism Portal</b><br>
    Powered by IndoBERT • Streamlit • SQLite • AI Semantic Detection
</div>
""", unsafe_allow_html=True)
