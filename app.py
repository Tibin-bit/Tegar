import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Global AI E-Waste Detector Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "detection_history" not in st.session_state:
    st.session_state.detection_history = []

# ---------------------------------------------------------
# 2. PENANGANAN API KEY OTOMATIS (DARI SECRETS ATAU SIDEBAR)
# ---------------------------------------------------------
api_key = ""
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
    api_key = st.secrets["GEMINI_API_KEY"]

with st.sidebar:
    st.title("⚡ AI Core Settings")
    st.caption("Universal E-Waste Detection System")
    
    if api_key:
        st.success("🟢 API Key Otomatis Terhubung!")
    else:
        api_key = st.text_input("Masukkan Gemini API Key:", type="password", help="Masukkan API Key jika belum disimpan di Secrets")
    
    st.markdown("---")
    st.markdown("### 📋 Standar Klasifikasi")
    st.info("Menggunakan pedoman **UN Global E-Waste Monitor** (Standar PBB).")
    st.markdown("---")
    st.caption("v4.0 Final — Ultra Stable Engine")

# ---------------------------------------------------------
# 3. FUNGSI ANALISIS GAMBAR (STRICT JSON + MODEL FAST)
# ---------------------------------------------------------
def analyze_ewaste(image, key):
    genai.configure(api_key=key)
    
    # Penguncian format JSON Murni dari Google AI
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json"
    }
    
    prompt = """
    Bertindaklah sebagai Ahli Sampah Elektronik (E-Waste Specialist).
    Analisis gambar sampah elektronik ini berdasarkan standar UN Global E-Waste Monitor.
    Kembalikan data persis sesuai struktur JSON berikut:
    {
        "nama_objek": "Nama spesifik perangkat elektronik",
        "kategori_un": "Salah satu Kategori UN E-Waste",
        "deskripsi": "Deskripsi singkat perangkat",
        "tingkat_bahaya": "Tinggi / Sedang / Rendah",
        "skor_bahaya": 8,
        "bahan_berbahaya": ["Bahan 1", "Bahan 2"],
        "potensi_logam_mulia": {
            "Emas (Au)": "Ada / Tidak ada / Tinggi",
            "Tembaga (Cu)": "Ada / Tinggi"
        },
        "instruksi_penanganan": [
            "Langkah 1 penanganan",
            "Langkah 2 daur ulang"
        ],
        "dapat_didaur_ulang_persen": 75
    }
    """
    
    candidate_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    last_err = ""
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            response = model.generate_content([prompt, image])
            if response and response.text:
                data = json.loads(response.text)
                return data, model_name, None
        except Exception as e:
            last_err = str(e)
            continue
            
    return None, None, f"Gagal memproses gambar: {last_err}"

# ---------------------------------------------------------
# 4. TAMPILAN UTAMA APLIKASI
# ---------------------------------------------------------
st.title("⚡ Global AI E-Waste Detector Pro")
st.markdown("Sistem Pengenal & Analisis Bahaya Sampah Elektronik Berbasis Vision AI")

tab1, tab2 = st.tabs(["🔍 Analisis E-Waste", "📊 Dashboard & Riwayat"])

with tab1:
    col_input, col_output = st.columns([1, 1.2], gap="medium")
    
    with col_input:
        st.subheader("1. Pilih Sumber Gambar")
        source = st.radio("Metode Input:", ["Kamera Langsung 📷", "Unggah Berkas 📁"], horizontal=True)
        
        input_image = None
        if "Kamera" in source:
            cam_file = st.camera_input("Ambil Foto Perangkat E-Waste")
            if cam_file:
                input_image = Image.open(cam_file)
        else:
            uploaded_file = st.file_uploader("Pilih gambar perangkat (JPG, PNG, WEBP):", type=["jpg", "jpeg", "png", "webp"])
            if uploaded_file:
                input_image = Image.open(uploaded_file)
                
        if input_image:
            st.image(input_image, caption="Gambar Siap Dianalisis", use_container_width=True)
            analyze_btn = st.button("🚀 Jalankan Analisis AI Universal", type="primary", use_container_width=True)

    with col_output:
        st.subheader("2. Hasil Deteksi & Analisis Mendalam")
        
        if 'analyze_btn' in locals() and analyze_btn:
            if not api_key:
                st.error("⚠️ **API Key Belum Diisi!** Masukkan Gemini API Key pada menu sidebar di sebelah kiri atau simpan di Streamlit Secrets.")
            elif input_image is None:
                st.warning("⚠️ **Gambar Belum Ada!** Ambil foto atau unggah gambar e-waste terlebih dahulu.")
            else:
                with st.spinner("⚡ Menganalisis gambar e-waste secara cepat..."):
                    data, used_model, err = analyze_ewaste(input_image, api_key)
                    
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        st.session_state.detection_history.append({
                            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "nama": data.get("nama_objek", "Tidak diketahui"),
                            "kategori": data.get("kategori_un", "Umum"),
                            "bahaya": data.get("tingkat_bahaya", "Sedang"),
                            "daur_ulang": data.get("dapat_didaur_ulang_persen", 0),
                            "model": used_model
                        })
                        
                        st.success(f"✅ **Berhasil Dianalisis** (Model: `{used_model}`)")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Perangkat", data.get("nama_objek", "-"))
                        m2.metric("Tingkat Bahaya", data.get("tingkat_bahaya", "-"), delta=f"Skor {data.get('skor_bahaya', 0)}/10", delta_color="inverse")
                        m3.metric("Daur Ulang", f"{data.get('dapat_didaur_ulang_persen', 0)}%")
                        
                        st.markdown("---")
                        st.markdown(f"**📂 Kategori UN:** `{data.get('kategori_un', '-')}`")
                        st.markdown(f"**📝 Deskripsi:** {data.get('deskripsi', '-')}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("🚨 **Bahan Berbahaya:**")
                            for bahan in data.get("bahan_berbahaya", []):
                                st.write(f"- {bahan}")
                                
                        with col_b:
                            st.markdown("💎 **Potensi Logam Mulia:**")
                            lm = data.get("potensi_logam_mulia", {})
                            for k, v in lm.items():
                                st.write(f"- **{k}:** {v}")
                                
                        st.markdown("---")
                        st.markdown("🛠️ **Instruksi Penanganan:**")
                        for idx, step in enumerate(data.get("instruksi_penanganan", []), 1):
                            st.write(f"**{idx}.** {step}")

with tab2:
    st.subheader("📊 Rekapitulasi Deteksi E-Waste")
    if len(st.session_state.detection_history) > 0:
        df = pd.DataFrame(st.session_state.detection_history)
        st.dataframe(df, use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, names="kategori", title="Distribusi Kategori UN E-Waste", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(df, x="nama", y="daur_ulang", color="bahaya", title="Persentase Daur Ulang per Objek")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Belum ada riwayat deteksi. Lakukan analisis di Tab 1 terlebih dahulu.")
