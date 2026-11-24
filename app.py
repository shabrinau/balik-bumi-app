"""
Balik Bumi - Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung
Mockup interaktif untuk Carbon 2026 Business Plan Competition (Tim Hore, Telkom University).

Jalankan dengan:
    pip install streamlit plotly pandas numpy
    streamlit run app.py

Seluruh data pada aplikasi ini adalah data ilustrasi simulasi. Angka model mengikuti skenario dasar
presentasi final dan RAB Skema 3. Angka bertanda [CEK] di kode belum terverifikasi terhadap RAB.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ----------------------------------------------------------------------------
# Konfigurasi halaman
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Balik Bumi - Hub Sisa Pangan Bandung",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Konstanta model (skenario dasar presentasi final)
# ----------------------------------------------------------------------------
HALAMAN = ["Landing Page", "Dashboard Mitra", "Dashboard Operasional"]

KREM = "#FAF9F5"
HUTAN = "#1B4332"
DAUN = "#2D6A4F"
KOPI = "#5C4033"
AMBER = "#D97706"
BORDER = "#E5E0D8"
DAUN_MUDA = "#95D5B2"

EF_TPA = 0.7496  # kg CO2e per kg, proksi US EPA (2024)
EF_KOMPOS = 0.19  # kg CO2e per kg, IPCC (2006)
EF_TRANSPORT = 18.7 / 819  # = 0,0228 kg CO2e per kg (18,7 t CO2e / 819 t dialihkan selama 36 bulan)
KET_EF_TRANSPORT = (
    "dihitung dari ±81.000 km selama 36 bulan, Carry 10 km/liter, bensin 2,31 kg CO₂/liter (batas atas)"
)
EF_BERSIH = EF_TPA - EF_KOMPOS - EF_TRANSPORT

HARGA_KOMPOS = 2000  # Rp per kg
HARGA_PELET = 4000  # Rp per kg
HARI_PER_BULAN = 30
BATAS_TOLAK = 3.0  # persen

# Tarif layanan per tingkat (marginal) per bulan, Rp per kg. Batas atas tiap tingkat dalam kg per bulan.
BATAS_TINGKAT = [400, 1500, None]
TARIF_JALUR = {
    "Kontrak 3 tahun": [1493, 1393, 896],
    "Tanpa kontrak (promosi)": [1598, 1491, 959],
}
JALUR_UTAMA = "Kontrak 3 tahun"
LABEL_TINGKAT = ["0–400 kg per bulan", "401–1.500 kg per bulan", "Di atas 1.500 kg per bulan"]

PAKET_KAFE = {"jumlah": 40, "kg_hari": 12}
PAKET_RESTO_HOTEL = {"jumlah": 15, "kg_hari": 41}

PROMO_DISKON = "Diskon 50% selama 3 bulan untuk 10 mitra pilot"
DISKON_PILOT = 0.5
BULAN_PILOT = 3

# Investasi dan indikator skenario dasar (presentasi final), juta rupiah
INVESTASI_AWAL_JUTA = 140.5
INVESTASI_TOTAL_36_JUTA = 212.2
BELANJA_LANJUTAN_JUTA = 71.7
MODAL_KERJA_JUTA = 22.6
DANA_PUNCAK_JUTA = 234.8  # 140,5 + 71,7 + 22,6 (dibulatkan ±235 juta)
BULAN_DANA_PUNCAK = 11
BEP_BULAN = 10
PAYBACK_BULAN = 32
LABA_TAHUN3_JUTA = 120.3
ROI_TAHUN3 = LABA_TAHUN3_JUTA / INVESTASI_TOTAL_36_JUTA * 100  # ±57%
PANGSA_LAYANAN_TAHUN3 = 76  # persen

# Dampak 3 tahun (presentasi final)
DAMPAK_TON_DIALIHKAN = 819
DAMPAK_KOTOR_TON = 614.2  # catatan: 819 x 0,7496 = 613,9; selisih kecil karena pembulatan berat
DAMPAK_BERSIH_TON = 439.8

HARI_SINGKAT = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
HARI_PANJANG = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN_PANJANG = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
BULAN_SINGKAT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

KECAMATAN = [
    "Andir", "Antapani", "Arcamanik", "Astanaanyar", "Babakan Ciparay", "Bandung Kidul",
    "Bandung Kulon", "Bandung Wetan", "Batununggal", "Bojongloa Kaler", "Buahbatu",
    "Cibeunying Kaler", "Cibeunying Kidul", "Cicendo", "Cidadap", "Coblong", "Kiaracondong",
    "Lengkong", "Regol", "Sukajadi", "Sukasari", "Sumur Bandung", "Ujungberung",
]

MITRA = {
    "Kopi Tuku-Tuku Dago": {
        "jenis": "Kafe", "kode": "TTD", "kopi": 20.0, "dapur": 17.0, "tolak": 0.012,
        "seed": 11, "area": "Dago, Coblong", "rute": "Rute 1 (Dago - Dipatiukur - Riau)",
    },
    "Bistro Braga Heritage": {
        "jenis": "Restoran", "kode": "BBH", "kopi": 12.0, "dapur": 53.0, "tolak": 0.036,
        "seed": 23, "area": "Braga, Sumur Bandung", "rute": "Rute 2 (Braga - Asia Afrika - Pasirkaliki)",
    },
    "Hotel Cipaganti Asri": {
        "jenis": "Hotel", "kode": "HCA", "kopi": 28.0, "dapur": 124.0, "tolak": 0.026,
        "seed": 37, "area": "Cipaganti, Cicendo", "rute": "Rute 3 (Buahbatu - Setiabudi - Sukajadi)",
    },
}

CATATAN_TEMUAN = [
    "Tercampur sedotan plastik {w} kg",
    "Tulang besar dan cangkang {w} kg",
    "Kantong plastik dan tisu {w} kg",
    "Sisa busuk melebihi batas mutu {w} kg",
    "Tercampur kemasan saus sachet {w} kg",
]

# Volume hub (skenario dasar presentasi final, bulan ke-12 simulasi)
MITRA_AKTIF = 29
TARGET_MITRA = 55
VOLUME_HARIAN_HUB = 577  # kg per hari = 29 mitra x 19,9 kg
TARGET_VOLUME_HARIAN = 1095  # kg per hari, SOM bulan ke-24

# ----------------------------------------------------------------------------
# CSS kustom
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: #FAF9F5; color: #25322B; }
h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', system-ui, sans-serif !important; color: #1B4332; letter-spacing: -0.01em; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1180px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #1B4332; }
section[data-testid="stSidebar"] * { color: #F1F5EC; }
section[data-testid="stSidebar"] hr { border-color: #2D6A4F; }
.bb-side-brand { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.6rem; color: #FFFFFF; line-height: 1.1; margin-bottom: 4px; }
.bb-side-sub { font-size: 0.85rem; color: #CFE3D6 !important; margin-bottom: 18px; }
.bb-side-note { font-size: 0.8rem; color: #CFE3D6 !important; margin-top: 18px; line-height: 1.5; }
.bb-nav-brand { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.45rem; color: #1B4332; display: flex; align-items: center; gap: 10px; padding-top: 6px; }
.bb-nav-sub { font-family: 'Inter', sans-serif; font-weight: 500; font-size: 0.95rem; color: #5C4033; }
.bb-logo { display: inline-block; width: 30px; height: 30px; border-radius: 50%; background: #2D6A4F; position: relative; }
.bb-logo::after { content: ''; position: absolute; left: 8px; top: 8px; width: 14px; height: 12px; background: #FAF9F5; border-radius: 0 100% 0 100%; }
.bb-nav-line { border-bottom: 1px solid #E5E0D8; margin: 8px 0 28px 0; }
.bb-chip { display: inline-block; padding: 6px 14px; border-radius: 999px; background: #D8F3DC; color: #1B4332; font-weight: 600; font-size: 0.85rem; margin-bottom: 14px; }
.bb-hero-title { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 3.1rem; line-height: 1.05; color: #1B4332; margin: 0 0 16px 0; letter-spacing: -0.02em; }
.bb-hero-sub { font-size: 1.1rem; line-height: 1.6; color: #44504A; margin: 0 0 22px 0; max-width: 560px; }
.bb-card { background: #FFFFFF; border: 1px solid #E5E0D8; border-radius: 16px; padding: 20px 22px; box-shadow: 0 4px 14px rgba(27, 67, 50, 0.07); height: 100%; }
.bb-card h4 { margin: 0 0 8px 0; font-size: 1.15rem; }
.bb-card p { margin: 0; color: #44504A; line-height: 1.55; font-size: 0.95rem; }
.bb-metrik-label { font-size: 0.85rem; color: #5B635D; margin-bottom: 4px; font-weight: 500; }
.bb-metrik-nilai { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 2rem; line-height: 1.15; color: #1B4332; }
.bb-metrik-ket { font-size: 0.82rem; color: #5B635D; margin-top: 4px; line-height: 1.4; }
.bb-stat-besar { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 2.3rem; line-height: 1.1; color: #1B4332; margin-bottom: 4px; }
.bb-sumber { font-size: 0.78rem; color: #6B736D; margin-top: 10px; }
.bb-angka-langkah { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 0.95rem; color: #D97706; margin-bottom: 6px; }
.bb-bagian { font-size: 0.85rem; font-weight: 600; color: #2D6A4F; margin: 44px 0 4px 0; text-transform: uppercase; letter-spacing: 0.06em; }
.bb-h2 { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 2.1rem; line-height: 1.15; color: #1B4332; margin: 0 0 20px 0; letter-spacing: -0.01em; }
.bb-badge { display: inline-block; padding: 5px 14px; border-radius: 999px; font-weight: 600; font-size: 0.85rem; }
.bb-badge-hijau { background: #D8F3DC; color: #1B4332; }
.bb-badge-amber { background: #FEF3C7; color: #92400E; }
.bb-badge-abu { background: #EFEBE0; color: #44504A; }
.bb-rumus { background: #F4F1E8; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.bb-rumus-label { font-size: 0.8rem; color: #5B635D; margin-bottom: 4px; }
.bb-rumus-isi { font-weight: 600; color: #1B4332; font-size: 1rem; }
.bb-harga { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 3.2rem; color: #FFFFFF; line-height: 1.05; }
.bb-gelap { background: #1B4332; border-radius: 18px; padding: 28px 30px; color: #E9F2EA; height: 100%; }
.bb-gelap p, .bb-gelap li { color: #E9F2EA; line-height: 1.6; }
.bb-gelap h4 { color: #FFFFFF; margin: 0 0 10px 0; }
.bb-footer { background: #1F2A24; color: #D5DDD7; border-radius: 16px; padding: 28px 30px; margin-top: 48px; line-height: 1.7; }
.bb-footer b { color: #FFFFFF; }
.bb-label-ilustrasi { display: inline-block; font-size: 0.8rem; font-weight: 600; color: #92400E; background: #FEF3C7; border-radius: 999px; padding: 4px 12px; }
.bb-alert-judul { font-weight: 600; color: #1B4332; }
.bb-alert-isi { font-size: 0.9rem; color: #44504A; margin-top: 2px; }
.bb-bar-luar { height: 8px; border-radius: 999px; background: #EDE9E0; overflow: hidden; margin-top: 8px; }
.bb-bar-isi { height: 100%; background: #2D6A4F; border-radius: 999px; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { width: 100%; border-radius: 999px; font-weight: 600; min-height: 2.8rem; border: 1.5px solid #1B4332; color: #1B4332; background: #FFFFFF; }
.stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p { color: #1B4332; font-weight: 600; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #2D6A4F; background: #F0F5EF; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] { background: #1B4332; color: #FFFFFF; border-color: #1B4332; }
.stButton > button[kind="primary"] p, .stFormSubmitButton > button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p { color: #FFFFFF; }
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { background: #2D6A4F; border-color: #2D6A4F; }
section[data-testid="stSidebar"] .stButton > button { background: #D97706; border-color: #D97706; }
section[data-testid="stSidebar"] .stButton > button p { color: #1F1305 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #E5E0D8; }
.stTabs [data-baseweb="tab"] { font-weight: 600; color: #5C4033; padding: 10px 18px; }
.stTabs [aria-selected="true"] { color: #1B4332; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #D97706; }
div[data-testid="stForm"] { background: #FFFFFF; border: 1px solid #E5E0D8; border-radius: 16px; padding: 22px; box-shadow: 0 4px 14px rgba(27, 67, 50, 0.07); }
div[data-testid="stDataFrame"] { border: 1px solid #E5E0D8; border-radius: 12px; overflow: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Fungsi bantu: format angka Indonesia, HTML, tabel, grafik
# ----------------------------------------------------------------------------
def angka(x, desimal=1):
    """Format angka gaya Indonesia: titik untuk ribuan, koma untuk desimal."""
    teks = f"{x:,.{desimal}f}"
    return teks.replace(",", "#").replace(".", ",").replace("#", ".")


def rupiah(x):
    tanda = "-" if x < 0 else ""
    return f"{tanda}Rp{angka(abs(x), 0)}"


def juta(x, desimal=1):
    """Format nilai yang sudah dalam satuan juta rupiah."""
    tanda = "-" if x < 0 else ""
    return f"{tanda}Rp{angka(abs(x), desimal)} juta"


def hitung_tagihan(kg_bulan, jalur=JALUR_UTAMA):
    """Tagihan layanan per bulan (Rp), dihitung per tingkat (marginal) pada kg per bulan."""
    sisa = max(float(kg_bulan), 0.0)
    batas_bawah = 0.0
    total = 0.0
    for batas, tarif in zip(BATAS_TINGKAT, TARIF_JALUR[jalur]):
        if sisa <= 0:
            break
        lebar = sisa if batas is None else min(sisa, batas - batas_bawah)
        total += lebar * tarif
        sisa -= lebar
        if batas is not None:
            batas_bawah = batas
    return total


def tarif_efektif(kg_bulan, jalur=JALUR_UTAMA):
    """Tarif rata-rata efektif (Rp per kg) pada volume bulanan tertentu."""
    return hitung_tagihan(kg_bulan, jalur) / kg_bulan if kg_bulan > 0 else 0.0


def tgl_pendek(d):
    return f"{HARI_SINGKAT[d.weekday()]}, {d.day} {BULAN_SINGKAT[d.month - 1]} {d.year}"


def h(html):
    """Render blok HTML tanpa baris kosong agar tidak dibaca sebagai blok kode Markdown."""
    teks = " ".join(baris.strip() for baris in html.strip().splitlines() if baris.strip())
    st.markdown(teks, unsafe_allow_html=True)


def _versi_streamlit():
    bagian = st.__version__.split(".")
    try:
        return int(bagian[0]), int(bagian[1])
    except (ValueError, IndexError):
        return 1, 0


def _lebar_penuh():
    if _versi_streamlit() >= (1, 50):
        return {"width": "stretch"}
    return {"use_container_width": True}


def tabel(df, tinggi=None):
    opsi = {"hide_index": True}
    opsi.update(_lebar_penuh())
    if tinggi:
        opsi["height"] = tinggi
    st.dataframe(df, **opsi)


def grafik(fig, key):
    opsi = {"key": key, "config": {"displayModeBar": False}}
    opsi.update(_lebar_penuh())
    st.plotly_chart(fig, **opsi)


def gaya(fig, judul, tinggi=340):
    fig.update_layout(
        title=dict(text=judul, x=0, xanchor="left"),
        height=tinggi,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color="#2B3A32"),
        title_font=dict(family="Bricolage Grotesque, sans-serif", size=17, color=HUTAN),
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(family="Inter, sans-serif", color=HUTAN)),
        separators=",.",
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER)
    fig.update_yaxes(gridcolor="#EDE9E0", zerolinecolor=BORDER)
    return fig


def kartu_metrik(label, nilai, ket="", warna=DAUN, latar="#FFFFFF"):
    return (
        f'<div class="bb-card" style="background:{latar};border-top:4px solid {warna};">'
        f'<div class="bb-metrik-label">{label}</div>'
        f'<div class="bb-metrik-nilai">{nilai}</div>'
        f'<div class="bb-metrik-ket">{ket}</div>'
        f"</div>"
    )


def bar_progres(persen):
    lebar = max(0, min(100, persen))
    return f'<div class="bb-bar-luar"><div class="bb-bar-isi" style="width:{lebar:.0f}%;"></div></div>'


# ----------------------------------------------------------------------------
# Navigasi (st.session_state)
# ----------------------------------------------------------------------------
def pindah_halaman(tujuan):
    st.session_state["nav_menu"] = tujuan


def buka_form():
    st.session_state["nav_menu"] = "Landing Page"
    st.session_state["scroll_form"] = True


def gulir_ke_form():
    """Gulirkan halaman ke form pendaftaran lewat skrip kecil yang berjalan di iframe tersembunyi."""
    skrip = """
    <script>
    const doc = window.parent.document;
    let el = doc.getElementById('daftar-pilot');
    if (!el) {
        const judul = Array.from(doc.querySelectorAll('h2'));
        el = judul.find(function (x) { return x.textContent.indexOf('Form Pendaftaran Pilot') !== -1; });
    }
    if (el) { setTimeout(function () { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }, 250); }
    </script>
    """
    if hasattr(st, "iframe"):
        st.iframe(skrip, height=1)
    else:
        import streamlit.components.v1 as components

        components.html(skrip, height=0)


def render_sidebar():
    with st.sidebar:
        h(
            """
            <div class="bb-side-brand">Balik Bumi</div>
            <div class="bb-side-sub">Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung</div>
            """
        )
        st.radio("Navigasi halaman", HALAMAN, key="nav_menu", label_visibility="collapsed")
        st.write("")
        st.button("Daftar Pilot", key="sidebar_daftar", on_click=buka_form)
        h(
            """
            <div class="bb-side-note">
            Tim Hore, Telkom University<br>
            Carbon 2026 Business Plan Competition<br>
            From Waste to Wealth
            </div>
            """
        )


# ----------------------------------------------------------------------------
# Data simulasi mitra
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def data_mitra(nama):
    profil = MITRA[nama]
    rs = np.random.RandomState(profil["seed"])
    semua_hari = pd.date_range("2027-08-02", "2027-08-27")
    tanggal = [d.date() for d in semua_hari if d.weekday() in (0, 2, 4)]
    baris = []
    for i, d in enumerate(tanggal):
        tren = 1 + 0.012 * i
        kopi = round(profil["kopi"] * tren * rs.uniform(0.9, 1.1), 1)
        dapur = round(profil["dapur"] * tren * rs.uniform(0.9, 1.1), 1)
        masuk = kopi + dapur
        if rs.rand() < 0.3:
            persen = 0.0
        else:
            persen = max(0.0, rs.normal(profil["tolak"] * 1.4, profil["tolak"] * 0.9))
        ditolak = round(masuk * persen, 1)
        rasio = ditolak / masuk if masuk else 0.0
        if ditolak == 0:
            status = "Lolos"
            catatan = "Tidak ada temuan"
        else:
            if rasio <= BATAS_TOLAK / 100:
                status = "Lolos"
            elif rasio <= 0.06:
                status = "Lolos dengan catatan"
            else:
                status = "Perlu perbaikan pemilahan"
            catatan = CATATAN_TEMUAN[rs.randint(0, len(CATATAN_TEMUAN))].format(w=angka(ditolak, 1))
        baris.append(
            {
                "tanggal": d,
                "minggu": i // 3,
                "kopi": kopi,
                "dapur": dapur,
                "masuk": round(masuk, 1),
                "ditolak": ditolak,
                "status": status,
                "catatan": catatan,
            }
        )
    df = pd.DataFrame(baris)

    kopi_total = float(df["kopi"].sum())
    dapur_total = float(df["dapur"].sum())
    masuk_total = float(df["masuk"].sum())
    ditolak_total = float(df["ditolak"].sum())
    dialihkan = masuk_total - ditolak_total
    persen_tolak = ditolak_total / masuk_total * 100

    mingguan = df.groupby("minggu")[["kopi", "dapur"]].sum().reset_index()

    faktor = [0.55, 0.68, 0.79, 0.88, 0.95, 1.0]
    bulan_label = ["Mar 2027", "Apr 2027", "Mei 2027", "Jun 2027", "Jul 2027", "Agu 2027"]
    bulan_nomor = [3, 4, 5, 6, 7, 8]
    berat_bulanan = [dialihkan * f for f in faktor]
    co2_bulanan = [b * EF_BERSIH for b in berat_bulanan]

    return {
        "profil": profil,
        "df": df,
        "kopi_total": kopi_total,
        "dapur_total": dapur_total,
        "masuk_total": masuk_total,
        "ditolak_total": ditolak_total,
        "dialihkan": dialihkan,
        "persen_tolak": persen_tolak,
        "kotor": dialihkan * EF_TPA,
        "bersih": dialihkan * EF_BERSIH,
        "mingguan": mingguan,
        "bulan_label": bulan_label,
        "bulan_nomor": bulan_nomor,
        "berat_bulanan": berat_bulanan,
        "co2_bulanan": co2_bulanan,
    }


def id_sertifikat(nama, nomor_bulan, urut):
    kode = MITRA[nama]["kode"]
    return f"BB-QR-2027{nomor_bulan:02d}-{kode}-{100 + urut:04d}"


def laporan_txt(nama, d):
    p = d["profil"]
    sertifikat = id_sertifikat(nama, 8, 5)
    garis = "=" * 66
    baris = [
        "LAPORAN KEPATUHAN BULANAN PENGELOLAAN SISA PANGAN",
        "Balik Bumi - Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung",
        garis,
        f"Mitra               : {nama} ({p['jenis']})",
        f"Area                : {p['area']}",
        f"Rute penjemputan    : {p['rute']}",
        "Periode             : Agustus 2027 (penjemputan 2 sampai 27 Agustus)",
        f"ID Sertifikat QR    : {sertifikat}",
        "",
        "RINGKASAN BERAT",
        "-" * 66,
        f"Ampas kopi dijemput         : {angka(d['kopi_total'])} kg",
        f"Sisa dapur dijemput         : {angka(d['dapur_total'])} kg",
        f"Total bahan masuk           : {angka(d['masuk_total'])} kg",
        f"Bahan ditolak inspeksi      : {angka(d['ditolak_total'])} kg ({angka(d['persen_tolak'])}%)",
        f"Total dialihkan dari TPA    : {angka(d['dialihkan'])} kg",
        "",
        "ESTIMASI EMISI (CO2e)",
        "-" * 66,
        f"Emisi kotor dihindari       : {angka(d['kotor'])} kg CO2e",
        f"Emisi bersih dihindari      : {angka(d['bersih'])} kg CO2e",
        "",
        "METODE PERHITUNGAN",
        "-" * 66,
        "Emisi kotor  = W layak x EF TPA",
        "Emisi bersih = W layak x (EF TPA - EF kompos - EF transportasi)",
        f"EF TPA        = {angka(EF_TPA, 4)} kg CO2e/kg (proksi US EPA, 2024)",
        f"EF kompos     = {angka(EF_KOMPOS, 2)} kg CO2e/kg (IPCC, 2006)",
        f"EF transport  = {angka(EF_TRANSPORT, 4)} kg CO2e/kg (dihitung dari sekitar 81.000 km selama 36 bulan,",
        "                Carry 10 km/liter, bensin 2,31 kg CO2/liter, batas atas)",
        "Angka merupakan estimasi, bukan kredit karbon.",
        "",
        "STATUS KEPATUHAN: Patuh - Terverifikasi QR",
        "",
        "Catatan: dokumen ini adalah simulasi untuk presentasi Carbon 2026.",
        "Seluruh data adalah data ilustrasi, bukan data nyata.",
    ]
    return "\n".join(baris)


def laporan_csv(d):
    df = d["df"].copy()
    keluar = pd.DataFrame(
        {
            "tanggal": df["tanggal"].astype(str),
            "ampas_kopi_kg": df["kopi"],
            "sisa_dapur_kg": df["dapur"],
            "ditolak_kg": df["ditolak"],
            "dialihkan_kg": (df["masuk"] - df["ditolak"]).round(1),
            "status_kualitas": df["status"],
            "catatan_inspeksi": df["catatan"],
        }
    )
    return keluar.to_csv(index=False).encode("utf-8-sig")


# ----------------------------------------------------------------------------
# Data simulasi operasional
# ----------------------------------------------------------------------------
RUTE_INFO = {
    "Rute 1": {"nama": "Dago - Dipatiukur - Riau", "mulai": (7, 30), "langkah": 15},
    "Rute 2": {"nama": "Braga - Asia Afrika - Pasirkaliki", "mulai": (8, 0), "langkah": 15},
    "Rute 3": {"nama": "Buahbatu - Setiabudi - Sukajadi", "mulai": (8, 30), "langkah": 20},
}

TITIK_JEMPUT = {
    "Rute 1": [
        "Kopi Tuku-Tuku Dago", "Warung Kopi Dipatiukur Raya", "Rumah Makan Riau Sentosa",
        "Kedai Teras Dago Atas", "Resto Dipatiukur 21", "Kafe Riau Junction",
        "Roastery Simpang Dago", "Kopi dan Roti Cisitu", "Kantin Dago Pakar", "Bistro Riau Garden",
    ],
    "Rute 2": [
        "Bistro Braga Heritage", "Kedai Asia Afrika 88", "Pasirkaliki Roast and Eat",
        "Kopi Braga Permai", "Resto Alun-Alun Sentral", "Kafe Naripan 12",
        "Hotel Braga Lestari", "Warung Kopi Pasar Baru", "Dapur Kota Lama",
    ],
    "Rute 3": [
        "Hotel Cipaganti Asri", "Kopi Buahbatu Corner", "Resto Setiabudi Garden",
        "Sukajadi Cafe Rumahan", "Kedai Gegerkalong 5", "Bistro Buahbatu Hijau",
        "Kafe Pasteur Rindang", "Dapur Sukajadi Asri", "Hotel Setiabudi Permai",
    ],
}


@st.cache_data(show_spinner=False)
def data_rute():
    rs = np.random.RandomState(5)
    batas_selesai = 9 * 60 + 45  # simulasi waktu sekarang 09.45 WIB
    baris = []
    for kode, info in RUTE_INFO.items():
        jam0, menit0 = info["mulai"]
        sudah_dp = False
        for i, nama in enumerate(TITIK_JEMPUT[kode]):
            total_menit = jam0 * 60 + menit0 + i * info["langkah"]
            jam, menit = divmod(total_menit, 60)
            if "Hotel" in nama:
                berat = int(rs.randint(120, 151))
            elif any(k in nama for k in ("Resto", "Bistro", "Rumah Makan", "Dapur")):
                berat = int(rs.randint(45, 81))
            else:
                berat = int(rs.randint(20, 46))
            if total_menit < batas_selesai:
                status = "Selesai"
            elif not sudah_dp:
                status = "Dalam perjalanan"
                sudah_dp = True
            else:
                status = "Menunggu"
            baris.append(
                {
                    "rute": kode,
                    "Nama Mitra": nama,
                    "Zona Rute": f"{kode}: {info['nama']}",
                    "Jadwal": f"{jam:02d}.{menit:02d} WIB",
                    "Estimasi Berat (kg)": berat,
                    "Status Penjemputan": status,
                }
            )
    return pd.DataFrame(baris)


@st.cache_data(show_spinner=False)
def data_batch():
    baris = [
        ("K-009", "2 Des 2027", "Ampas kopi 60% + sisa sayur 40%", 29, 38, 7.4, "Siap Panen"),
        ("K-010", "18 Des 2027", "Ampas kopi 55% + sisa sayur 45%", 31, 41, 7.2, "Siap Panen"),
        ("K-011", "4 Jan 2028", "Ampas kopi 60% + sisa sayur 40%", 36, 46, 7.1, "Pematangan"),
        ("K-012", "14 Jan 2028", "Ampas kopi 50% + sisa makanan nabati 50%", 39, 50, 6.9, "Pematangan"),
        ("K-013", "24 Jan 2028", "Ampas kopi 65% + sisa sayur 35%", 58, 55, 6.6, "Termofilik"),
        ("K-014", "1 Feb 2028", "Ampas kopi 55% + sisa makanan nabati 45%", 68, 57, 6.4, "Termofilik"),
        ("K-015", "8 Feb 2028", "Ampas kopi 60% + sisa sayur 40%", 43, 58, 6.3, "Mesofilik"),
        ("K-016", "15 Feb 2028", "Ampas kopi 50% + sisa makanan nabati 50%", 39, 59, 6.2, "Mesofilik"),
    ]
    return pd.DataFrame(
        baris,
        columns=["Kode Batch", "Tanggal Mulai", "Jenis Bahan", "Suhu (°C)", "Kadar Air (%)", "pH", "Status"],
    )


@st.cache_data(show_spinner=False)
def data_hub_mingguan():
    rs = np.random.RandomState(9)
    total = np.linspace(2780, VOLUME_HARIAN_HUB * 7, 8)
    total = total * rs.uniform(0.97, 1.03, size=8)
    total[-1] = VOLUME_HARIAN_HUB * 7
    kopi = total * 0.42
    dapur = total - kopi
    label = [f"Mgg {i}" for i in range(1, 9)]
    return label, kopi, dapur


@st.cache_data(show_spinner=False)
def data_keuangan():
    # [CEK] Seluruh blok ini belum dihitung dari RAB Skema 3 (file RAB belum tersedia saat pembaruan).
    # Yang berasal dari instruksi: tarif per tingkat, 2 orang digaji pada bulan 8-17, sewa hub Rp80 juta per tahun
    # pada tahun 1, 29 mitra dan 577 kg/hari pada bulan 12, paket kafe 12 kg/hari dan resto/hotel 41 kg/hari.
    kg_kafe = PAKET_KAFE["kg_hari"] * HARI_PER_BULAN
    kg_rh = PAKET_RESTO_HOTEL["kg_hari"] * HARI_PER_BULAN
    # Komposisi mitra bulan 12 diturunkan dari 29 mitra dan 577 kg/hari (12 kg/hari kafe, 41 kg/hari resto/hotel).
    n_kafe = (PAKET_RESTO_HOTEL["kg_hari"] * MITRA_AKTIF - VOLUME_HARIAN_HUB) / (
        PAKET_RESTO_HOTEL["kg_hari"] - PAKET_KAFE["kg_hari"]
    )
    n_rh = MITRA_AKTIF - n_kafe
    layanan = (n_kafe * hitung_tagihan(kg_kafe) + n_rh * hitung_tagihan(kg_rh)) / 1e6
    total = layanan / (PANGSA_LAYANAN_TAHUN3 / 100)  # [CEK] pangsa tahun 3 dipakai untuk bulan 12
    pelet = total * 0.025  # [CEK] porsi pelet belum dari RAB
    kompos = total - layanan - pelet
    upah_per_orang = 5.211446  # [CEK] UMK + 10% dari dokumen sebelumnya, belum dicek ke RAB
    sewa = 80 / 12  # sewa hub Rp80 juta per tahun pada tahun 1
    biaya_rincian = [
        ("Sewa hub", sewa),
        ("Upah tenaga lapangan (2 orang dibayar)", 2 * upah_per_orang),
        ("BBM dan perawatan armada", 2.80),  # [CEK]
        ("Bahan pengisi dan kemasan", 2.30),  # [CEK]
        ("Uji mutu dan laboratorium", 1.20),  # [CEK]
        ("Sistem dan dashboard", 0.50),  # [CEK]
        ("Administrasi dan lain-lain", 1.00),  # [CEK]
    ]
    biaya = sum(x[1] for x in biaya_rincian)
    jumlah_mitra = [19, 21, 23, 25, 27, 29]  # [CEK] bulan 7-12, naik merata menuju 29 mitra pada bulan 12
    pendapatan_seri = [total * m / MITRA_AKTIF for m in jumlah_mitra]
    variabel = biaya - sewa - 2 * upah_per_orang
    biaya_seri = [
        sewa + (2 * upah_per_orang if i > 0 else 0.0) + variabel * m / MITRA_AKTIF  # [CEK]
        for i, m in enumerate(jumlah_mitra)
    ]
    return {
        "total": total,
        "layanan": layanan,
        "kompos": kompos,
        "pelet": pelet,
        "biaya": biaya,
        "ebitda": total - biaya,
        "biaya_rincian": biaya_rincian,
        "bulan": ["Sep", "Okt", "Nov", "Des", "Jan", "Feb"],
        "pendapatan_seri": pendapatan_seri,
        "biaya_seri": biaya_seri,
        "n_kafe": n_kafe,
        "n_resto_hotel": n_rh,
    }


# ----------------------------------------------------------------------------
# HALAMAN 1: Landing page
# ----------------------------------------------------------------------------
def halaman_landing():
    # Navbar
    kolom_nav = st.columns([5, 1.6])
    with kolom_nav[0]:
        h(
            """
            <div class="bb-nav-brand"><span class="bb-logo"></span>Balik Bumi
            <span class="bb-nav-sub">— Hub Sisa Pangan Bandung</span></div>
            """
        )
    with kolom_nav[1]:
        st.button("Daftar Pilot", key="nav_daftar", type="primary", on_click=buka_form)
    h('<div class="bb-nav-line"></div>')

    # Hero
    ringkas = data_mitra("Kopi Tuku-Tuku Dago")
    kiri, kanan = st.columns([1.15, 1], gap="large")
    with kiri:
        h('<div class="bb-chip">Hub pengolahan sisa pangan terpadu, Kota Bandung</div>')
        h('<h1 class="bb-hero-title">Sisa kopi dan sisa dapur kafemu, kembali ke bumi</h1>')
        h(
            """
            <p class="bb-hero-sub">Balik Bumi menjemput ampas kopi dan sisa makanan dari kafe, restoran, dan hotel di
            Kota Bandung setiap Senin, Rabu, dan Jumat. Setiap penjemputan ditimbang dan dipindai lewat kode QR, sehingga
            laporan berat dan jejak karbon (CO₂e) tersaji otomatis setiap bulan sebagai bukti kepatuhan.</p>
            """
        )
        tombol_a, tombol_b = st.columns(2)
        with tombol_a:
            st.button(
                "Lihat Dashboard Mitra", key="hero_mitra", type="primary",
                on_click=pindah_halaman, args=("Dashboard Mitra",),
            )
        with tombol_b:
            st.button(
                "Lihat Dashboard Operasional", key="hero_ops",
                on_click=pindah_halaman, args=("Dashboard Operasional",),
            )
    with kanan:
        h(
            f"""
            <div class="bb-card" style="padding:26px;">
            <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;align-items:baseline;">
            <div style="font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.2rem;color:{HUTAN};">Contoh Laporan Kepatuhan Bulanan</div>
            <div style="font-size:0.82rem;color:#5B635D;">Kopi Tuku-Tuku Dago · Agustus 2027</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0;">
            <div style="background:#F4F1E8;border-radius:12px;padding:14px;">
            <div class="bb-metrik-label">Sisa pangan dialihkan</div>
            <div class="bb-metrik-nilai" style="font-size:1.7rem;">{angka(ringkas['dialihkan'])} kg</div>
            </div>
            <div style="background:#D8F3DC;border-radius:12px;padding:14px;">
            <div class="bb-metrik-label" style="color:#1B4332;">CO₂e bersih dihindari</div>
            <div class="bb-metrik-nilai" style="font-size:1.7rem;">{angka(ringkas['bersih'])} kg</div>
            </div>
            </div>
            <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;">
            <span class="bb-badge bb-badge-hijau">Patuh Larangan Sampah Organik TPA</span>
            <span style="font-size:0.78rem;color:#6B736D;">Data ilustrasi simulasi</span>
            </div>
            </div>
            """
        )

    # Fakta dan urgensi regulasi
    h('<div class="bb-bagian">Mengapa sekarang</div>')
    h('<div class="bb-h2">Larangannya sudah ada. Yang belum ada adalah cara mudah mematuhinya.</div>')
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        h(
            """
            <div class="bb-card"><div class="bb-stat-besar">709,73 ton/hari</div>
            <span class="bb-badge bb-badge-amber">44,52%</span>
            <p style="margin-top:10px;">komposisi sampah Kota Bandung adalah sisa makanan, dari total 1.594,18 ton sampah per hari.</p>
            <div class="bb-sumber">BPS Kota Bandung via detikJabar, 2023</div></div>
            """
        )
    with k2:
        h(
            """
            <div class="bb-card"><div class="bb-stat-besar">50–60%</div>
            <span class="bb-badge bb-badge-amber">±874 ton/hari</span>
            <p style="margin-top:10px;">timbulan sampah kafe dan restoran merupakan sampah organik. Kawasan komersial Bandung menghasilkan sekitar 874 ton sampah organik per hari.</p>
            <div class="bb-sumber">Liputan6, 2024; BandungBergerak, 2024</div></div>
            """
        )
    with k3:
        h(
            """
            <div class="bb-card"><div class="bb-stat-besar">Sejak 2023</div>
            <span class="bb-badge bb-badge-amber">TPA penuh Okt 2026</span>
            <p style="margin-top:10px;">Larangan organik ke TPA Sarimukti (Instruksi Gubernur Jabar No. 02/PBLS.04/DLH) menuntut bukti kepatuhan pelaku usaha kuliner, sementara TPA diprediksi penuh pada Oktober 2026.</p>
            <div class="bb-sumber">BandungBergerak, 2024; Berita Bandung, 2026</div></div>
            """
        )

    # Manfaat layanan
    h('<div class="bb-bagian">Untuk kafe, restoran, dan hotel</div>')
    h('<div class="bb-h2">Kamu pilah. Kami jemput, olah, dan buktikan.</div>')
    manfaat = [
        ("Bukti Kepatuhan Regulasi", "Laporan bulanan dan verifikasi QR siap audit sebagai bukti pengalihan sampah organik dari TPA."),
        ("Dapur Lebih Bersih dan Higienis", "Penjemputan rutin 3x seminggu (Senin, Rabu, Jumat) mencegah bau dan lindi menumpuk di area dapur."),
        ("Bahan Laporan ESG dan Branding Hijau", "Data terukur untuk komunikasi keberlanjutan kepada pelanggan, jejaring hotel, dan waralaba."),
        ("Tanpa Kelola Sendiri", "Tidak perlu lahan kompos atau tenaga tambahan di lokasi kafe dan restoran. Cukup pilah dua jenis bin."),
    ]
    for kolom, (judul, isi) in zip(st.columns(4, gap="medium"), manfaat):
        with kolom:
            h(f'<div class="bb-card"><h4>{judul}</h4><p>{isi}</p></div>')

    # Cara kerja
    h('<div class="bb-bagian">Cara kerja</div>')
    h('<div class="bb-h2">Empat langkah dari dapur sampai laporan.</div>')
    langkah = [
        ("01", "Pilah di Sumber", "Pisahkan ampas kopi dan sisa dapur bersih dari plastik dan bahan anorganik ke dalam dua bin berlabel QR."),
        ("02", "Jemput dan Timbang Digital", "Kurir menjemput Senin, Rabu, dan Jumat, lalu mencatat berat per kategori dengan memindai kode QR."),
        ("03", "Olah di Hub Balik Bumi", "Bahan diperiksa ulang dan diolah menjadi kompos, media tanam, dan pelet pakan uji coba."),
        ("04", "Terima Laporan dan Dashboard", "Akses berat yang dialihkan dan reduksi emisi CO₂e secara real-time melalui dashboard mitra."),
    ]
    for kolom, (no, judul, isi) in zip(st.columns(4, gap="medium"), langkah):
        with kolom:
            h(f'<div class="bb-card"><div class="bb-angka-langkah">LANGKAH {no}</div><h4>{judul}</h4><p>{isi}</p></div>')

    # Produk dan roadmap
    h('<div class="bb-bagian">Produk dan roadmap inovasi</div>')
    h('<div class="bb-h2">Mulai sederhana, tumbuh bertahap.</div>')
    produk = [
        ("Fase 1", "bb-badge-hijau", "Kompos dan Media Tanam",
         "Hasil fermentasi aerob ampas kopi dan sisa makanan nabati untuk pertanian urban dan lanskap.",
         "Harga jual Rp2.000/kg"),
        ("Fase 1 · Uji coba", "bb-badge-amber", "Pelet Pakan Ternak",
         "Dari fraksi sisa pangan nabati terpilih. Status: tahap uji coba dan penyesuaian regulasi edar, hanya untuk peternak mitra pilot.",
         "Harga jual Rp4.000/kg"),
        ("Fase 2 · Ekspansi", "bb-badge-abu", "Maggot BSF, Ekstraksi, dan Biochar",
         "Budidaya maggot BSF mulai bulan ke-13, serta ekstraksi ampas kopi dan biochar lewat skema maklon laboratorium mulai bulan ke-19.",
         "Dijalankan setelah syarat lanjut terpenuhi"),
    ]
    for kolom, (fase, kelas, judul, isi, meta) in zip(st.columns(3, gap="medium"), produk):
        with kolom:
            h(
                f"""
                <div class="bb-card"><span class="bb-badge {kelas}">{fase}</span>
                <h4 style="margin-top:12px;">{judul}</h4><p>{isi}</p>
                <div class="bb-sumber" style="font-size:0.88rem;color:#1B4332;font-weight:600;">{meta}</div></div>
                """
            )

    # Metodologi emisi
    h('<div class="bb-bagian">Metodologi laporan</div>')
    h('<div class="bb-h2">Setiap angka emisi punya rumus dan sumber.</div>')
    m_kiri, m_kanan = st.columns([1.1, 1], gap="large")
    with m_kiri:
        h(
            f"""
            <div class="bb-rumus"><div class="bb-rumus-label">Emisi kotor dihindari (kg CO₂e)</div>
            <div class="bb-rumus-isi">W layak × EF TPA</div></div>
            <div class="bb-rumus" style="background:#D8F3DC;"><div class="bb-rumus-label" style="color:#1B4332;">Emisi bersih dihindari (kg CO₂e)</div>
            <div class="bb-rumus-isi">W layak × (EF TPA − EF kompos − EF transportasi)</div></div>
            <p style="color:#44504A;line-height:1.6;">W layak adalah berat bahan yang diterima dan diolah. EF TPA = {angka(EF_TPA, 4)} kg CO₂e per kg
            (proksi US EPA, 2024). EF kompos = {angka(EF_KOMPOS, 2)} kg CO₂e per kg (IPCC, 2006). EF transportasi = {angka(EF_TRANSPORT, 4)} kg CO₂e per kg,
            {KET_EF_TRANSPORT}. Faktor EPA berasal dari kondisi TPA di
            Amerika Serikat sehingga angka ini kemungkinan konservatif, dan akan diganti faktor nasional bila tersedia.</p>
            """
        )
    with m_kanan:
        h(
            f"""
            <div class="bb-card"><h4>Contoh: 1 ton bahan layak</h4>
            <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid {BORDER};"><span>Emisi kotor dihindari</span><b>{angka(1000 * EF_TPA, 0)} kg CO₂e</b></div>
            <div style="display:flex;justify-content:space-between;padding:10px 0;"><span>Emisi bersih dihindari</span><b>{angka(1000 * EF_BERSIH, 0)} kg CO₂e</b></div>
            <div class="bb-sumber">Angka ditampilkan sebagai estimasi dan bukan kredit karbon.</div></div>
            """
        )
    st.write("")
    h('<div style="font-weight:600;color:#1B4332;font-size:1.1rem;margin:6px 0 8px 0;">Dampak 3 tahun</div>')
    dm1, dm2, dm3 = st.columns(3, gap="medium")
    with dm1:
        h(kartu_metrik("Dialihkan dari TPA", f"{angka(DAMPAK_TON_DIALIHKAN, 0)} ton", "Total selama 36 bulan", warna=DAUN))
    with dm2:
        h(kartu_metrik("Emisi kotor dihindari", f"{angka(DAMPAK_KOTOR_TON, 1)} t CO₂e", "W layak × EF TPA", warna=KOPI))
    with dm3:
        h(kartu_metrik("Emisi bersih dihindari", f"{angka(DAMPAK_BERSIH_TON, 1)} t CO₂e", "Setelah dikurangi proses pengomposan dan transportasi",
                       warna=HUTAN, latar="#D8F3DC"))
    st.write("")
    t1, t2 = st.columns(2)
    with t1:
        st.button(
            "Buka Dashboard Mitra", key="met_mitra", type="primary",
            on_click=pindah_halaman, args=("Dashboard Mitra",),
        )
    with t2:
        st.button(
            "Buka Dashboard Operasional", key="met_ops",
            on_click=pindah_halaman, args=("Dashboard Operasional",),
        )

    # Tarif dan promo
    h('<div class="bb-bagian">Tarif dan promo pilot</div>')
    h('<div class="bb-h2">Bayar per kilogram yang kami olah, makin banyak makin murah.</div>')
    kontrak = TARIF_JALUR["Kontrak 3 tahun"]
    promosi = TARIF_JALUR["Tanpa kontrak (promosi)"]
    p_kiri, p_kanan = st.columns(2, gap="medium")
    with p_kiri:
        h(
            f"""
            <div class="bb-gelap"><h4>Kontrak 3 tahun</h4>
            <div class="bb-harga">Rp{angka(kontrak[0], 0)}<span style="font-size:1.2rem;font-weight:500;"> /kg, tingkat pertama</span></div>
            <p style="margin-top:12px;">Tarif terendah untuk mitra yang berkomitmen 3 tahun. Tarif turun per tingkat volume bulanan hingga
            Rp{angka(kontrak[2], 0)}/kg di atas 1.500 kg per bulan.</p>
            <p style="margin-top:8px;">Sudah termasuk bin berlabel QR, jemput terjadwal Senin, Rabu, Jumat, penimbangan digital, dan laporan bulanan.</p></div>
            """
        )
    with p_kanan:
        h(
            f"""
            <div class="bb-card" style="border:2px solid {HUTAN};"><span class="bb-badge bb-badge-hijau">Fleksibel</span>
            <h4 style="margin-top:12px;font-size:1.5rem;">Tanpa kontrak (promosi)</h4>
            <div class="bb-metrik-nilai" style="margin:6px 0;">Rp{angka(promosi[0], 0)}<span style="font-size:1rem;color:#5B635D;font-weight:500;"> /kg, tingkat pertama</span></div>
            <p>Tanpa ikatan jangka panjang dengan tarif promosi, turun per tingkat hingga Rp{angka(promosi[2], 0)}/kg di atas 1.500 kg per bulan.
            Fasilitas layanan sama dengan jalur kontrak.</p></div>
            """
        )
    st.write("")
    h('<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Tabel tarif per tingkat (dihitung per bulan, bertingkat)</div>')
    tabel(
        pd.DataFrame(
            {
                "Volume per bulan": LABEL_TINGKAT,
                "Kontrak 3 tahun (Rp/kg)": [angka(x, 0) for x in kontrak],
                "Tanpa kontrak, promosi (Rp/kg)": [angka(x, 0) for x in promosi],
            }
        )
    )
    st.caption(
        "Tarif berlaku per tingkat: setiap kilogram dihitung sesuai tingkat tempat kilogram itu berada, bukan satu tarif untuk seluruh volume."
    )

    kg_kafe = PAKET_KAFE["kg_hari"] * HARI_PER_BULAN
    kg_rh = PAKET_RESTO_HOTEL["kg_hari"] * HARI_PER_BULAN
    st.write("")
    pk1, pk2 = st.columns(2, gap="medium")
    with pk1:
        h(
            f"""
            <div class="bb-card"><span class="bb-badge bb-badge-hijau">Paket Kafe</span>
            <h4 style="margin-top:12px;">{PAKET_KAFE['jumlah']} kafe · ±{PAKET_KAFE['kg_hari']} kg per hari</h4>
            <div class="bb-metrik-nilai">{rupiah(round(hitung_tagihan(kg_kafe), -3))}<span style="font-size:1rem;color:#5B635D;font-weight:500;"> /bulan</span></div>
            <p style="margin-top:8px;">Contoh kafe dengan {PAKET_KAFE['kg_hari']} kg per hari ({angka(kg_kafe, 0)} kg per bulan) pada jalur kontrak 3 tahun.
            Jalur tanpa kontrak: {rupiah(round(hitung_tagihan(kg_kafe, 'Tanpa kontrak (promosi)'), -3))} per bulan.</p></div>
            """
        )
    with pk2:
        h(
            f"""
            <div class="bb-card"><span class="bb-badge bb-badge-amber">Paket Resto &amp; Hotel</span>
            <h4 style="margin-top:12px;">{PAKET_RESTO_HOTEL['jumlah']} mitra · ±{PAKET_RESTO_HOTEL['kg_hari']} kg per hari</h4>
            <div class="bb-metrik-nilai">{rupiah(round(hitung_tagihan(kg_rh), -3))}<span style="font-size:1rem;color:#5B635D;font-weight:500;"> /bulan</span></div>
            <p style="margin-top:8px;">Tarif turun per volume: pada {angka(kg_rh, 0)} kg per bulan tarif efektif jalur kontrak sekitar
            Rp{angka(tarif_efektif(kg_rh), 0)}/kg, dan menjadi sekitar Rp{angka(tarif_efektif(15000), 0)}/kg untuk hotel besar
            500 kg per hari.</p></div>
            """
        )
    st.write("")
    h(
        f"""
        <div class="bb-card" style="border:2px solid {AMBER};"><span class="bb-badge bb-badge-amber">Promo Pilot</span>
        <h4 style="margin-top:12px;font-size:1.5rem;">Diskon 50% selama 3 bulan</h4>
        <p>Untuk 10 mitra pilot pertama di Bandung. Pilot menguji kesediaan membayar, volume per mitra, dan rendemen kompos
        sebelum perluasan ke {TARGET_MITRA} mitra pada bulan ke-24.</p></div>
        """
    )

    # Form pendaftaran
    h('<div class="bb-bagian">Bergabung</div>')
    h('<h2 class="bb-h2" id="daftar-pilot">Form Pendaftaran Pilot</h2>')
    h(
        """
        <p style="color:#44504A;max-width:720px;">Cocok untuk kafe, restoran, dan hotel di Kota Bandung yang menghasilkan minimal
        10 kg sisa pangan per hari dan bersedia memilah di sumber.</p>
        """
    )
    form_pendaftaran()

    if st.session_state.get("scroll_form"):
        st.session_state["scroll_form"] = False
        gulir_ke_form()

    # Footer
    h(
        """
        <div class="bb-footer">
        <b style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.3rem;">Balik Bumi</b><br>
        Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung<br>
        Tim Hore, Telkom University · Carbon 2026 Business Plan Competition<br><br>
        <b>Email:</b> [EMAIL TIM]<br>
        <b>WhatsApp:</b> [NO. WHATSAPP]<br>
        <b>Alamat hub:</b> [ALAMAT HUB]<br><br>
        <span style="font-size:0.85rem;color:#AEB9B1;">Catatan: seluruh data pada dashboard adalah ilustrasi simulasi
        skenario dasar presentasi final Carbon 2026 dan bukan data operasional nyata.</span>
        </div>
        """
    )


def form_pendaftaran():
    with st.form("form_pilot", clear_on_submit=False):
        c1, c2 = st.columns(2)
        nama_usaha = c1.text_input("Nama Usaha", placeholder="Contoh: Kopi Senja Dago")
        jenis = c2.selectbox("Jenis Usaha", ["Kafe", "Restoran", "Hotel"])
        nama_pic = c1.text_input("Nama PIC", placeholder="Nama penanggung jawab")
        wa = c2.text_input("Nomor WhatsApp", placeholder="08xx xxxx xxxx")
        kecamatan = c1.selectbox("Kecamatan di Bandung", KECAMATAN, index=KECAMATAN.index("Coblong"))
        alamat = c2.text_input("Alamat Lengkap", placeholder="Nama jalan dan nomor")
        volume = c1.number_input(
            "Estimasi Volume Sisa Pangan (kg/hari)", min_value=1, max_value=1000, value=20, step=1,
        )
        c2.info(f"Promo pilot: {PROMO_DISKON}.")
        setuju = st.checkbox(
            "Kami bersedia memilah ampas kopi dan sisa dapur di sumber serta mengikuti evaluasi pilot 3 bulan."
        )
        kirim = st.form_submit_button("Kirim Pendaftaran Pilot", type="primary")

    if not kirim:
        return

    galat = []
    if not nama_usaha.strip():
        galat.append("Nama usaha wajib diisi.")
    if not nama_pic.strip():
        galat.append("Nama PIC wajib diisi.")
    digit_wa = "".join(ch for ch in wa if ch.isdigit())
    if len(digit_wa) < 9:
        galat.append("Nomor WhatsApp belum valid (minimal 9 digit).")
    if not setuju:
        galat.append("Centang pernyataan kesediaan memilah dan mengikuti evaluasi pilot.")
    if galat:
        st.error("Pendaftaran belum dapat dikirim:\n\n" + "\n".join(f"- {g}" for g in galat))
        return

    bulanan_kg = volume * HARI_PER_BULAN
    biaya_normal = hitung_tagihan(bulanan_kg, JALUR_UTAMA)
    biaya_normal_tanpa_kontrak = hitung_tagihan(bulanan_kg, "Tanpa kontrak (promosi)")
    biaya_pilot = biaya_normal * BULAN_PILOT * (1 - DISKON_PILOT)
    hemat = biaya_normal * BULAN_PILOT - biaya_pilot
    layak = bulanan_kg * (1 - BATAS_TOLAK / 100)
    co2_bulanan = layak * EF_BERSIH

    st.success(
        f"Pendaftaran {nama_usaha.strip()} ({jenis}) berhasil dikirim (simulasi). Tim Balik Bumi akan menghubungi "
        f"{nama_pic.strip()} melalui WhatsApp {wa.strip()} untuk menjadwalkan survei lokasi di {kecamatan}."
    )
    if volume < 10:
        st.info("Kriteria mitra pilot adalah minimal 10 kg per hari. Tim kami tetap akan menghubungi Anda untuk penjajakan.")

    ringkasan = pd.DataFrame(
        {
            "Ringkasan pendaftaran": [
                "Nama usaha", "Jenis usaha", "Penanggung jawab", "WhatsApp", "Lokasi", "Volume", "Promo pilot",
            ],
            "Isian": [
                nama_usaha.strip(), jenis, nama_pic.strip(), wa.strip(),
                f"{alamat.strip() + ', ' if alamat.strip() else ''}{kecamatan}, Bandung",
                f"{angka(volume, 0)} kg per hari", PROMO_DISKON,
            ],
        }
    )
    tabel(ringkasan)
    s1, s2, s3 = st.columns(3)
    with s1:
        h(kartu_metrik("Tagihan normal per bulan (kontrak 3 tahun)", rupiah(biaya_normal),
                       f"{angka(bulanan_kg, 0)} kg per bulan, per tingkat · efektif Rp{angka(tarif_efektif(bulanan_kg), 0)}/kg. "
                       f"Tanpa kontrak: {rupiah(biaya_normal_tanpa_kontrak)}"))
    with s2:
        h(kartu_metrik("Tagihan 3 bulan pilot (diskon 50%)", rupiah(biaya_pilot), f"Penghematan promo {rupiah(hemat)}", warna=AMBER))
    with s3:
        h(kartu_metrik("CO₂e bersih dihindari per bulan", f"{angka(co2_bulanan, 0)} kg", "Asumsi 3% bahan ditolak, faktor EPA dan IPCC"))
    st.caption("Simulasi ini hanya ilustrasi dan tidak menyimpan data pendaftaran.")


# ----------------------------------------------------------------------------
# HALAMAN 2: Dashboard Mitra
# ----------------------------------------------------------------------------
def halaman_mitra():
    atas = st.columns([3, 2.2, 1.3])
    with atas[0]:
        h('<h1 style="margin:0;font-size:2.2rem;">Dashboard Mitra</h1>')
        h('<span class="bb-label-ilustrasi">Data ilustrasi untuk simulasi mitra</span>')
    with atas[1]:
        nama = st.selectbox("Profil mitra", list(MITRA.keys()), key="mitra_terpilih")
    with atas[2]:
        st.write("")
        st.button("Kembali ke Landing Page", key="mitra_kembali", on_click=pindah_halaman, args=("Landing Page",))

    d = data_mitra(nama)
    p = d["profil"]
    h(
        f"""
        <div style="margin:14px 0 10px 0;color:#44504A;font-size:0.95rem;">
        <b style="color:{HUTAN};">{nama}</b> · {p['jenis']} · {p['area']} · {p['rute']} · Periode Agustus 2027
        </div>
        """
    )

    tab_beranda, tab_jemput, tab_laporan = st.tabs(["Beranda", "Penjemputan", "Laporan & CO₂e"])

    with tab_beranda:
        tombol_tolak = "Perlu perhatian: di atas batas target 3%" if d["persen_tolak"] > BATAS_TOLAK else "Di bawah batas target 3%"
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        with m1:
            h(kartu_metrik("Total dialihkan bulan ini", f"{angka(d['dialihkan'])} kg",
                           f"dari {angka(d['masuk_total'])} kg yang dijemput"))
        with m2:
            h(kartu_metrik("Sampah ditolak / kontaminasi", f"{angka(d['ditolak_total'])} kg · {angka(d['persen_tolak'])}%",
                           tombol_tolak, warna=AMBER))
        with m3:
            h(kartu_metrik("Emisi CO₂e bersih dihindari", f"{angka(d['bersih'])} kg",
                           f"Emisi kotor {angka(d['kotor'])} kg CO₂e (estimasi)", warna=HUTAN, latar="#D8F3DC"))
        with m4:
            h(kartu_metrik("Status kepatuhan", "Patuh — Terverifikasi QR", "Pemilahan organik terpenuhi bulan ini"))
        st.write("")

        g1, g2 = st.columns(2, gap="medium")
        with g1:
            mg = d["mingguan"]
            minggu = [f"Minggu {i + 1}" for i in range(len(mg))]
            fig = go.Figure()
            fig.add_bar(
                name="Sisa makanan (dapur)", x=minggu, y=mg["dapur"].round(1), marker_color=DAUN,
                hovertemplate="%{x}<br>Sisa makanan: %{y:,.1f} kg<extra></extra>",
            )
            fig.add_bar(
                name="Ampas kopi", x=minggu, y=mg["kopi"].round(1), marker_color=KOPI,
                hovertemplate="%{x}<br>Ampas kopi: %{y:,.1f} kg<extra></extra>",
            )
            fig.update_layout(barmode="group", yaxis_title="Berat dijemput (kg)")
            grafik(gaya(fig, "Volume dijemput per minggu: sisa makanan vs ampas kopi"), "mitra_mingguan")
        with g2:
            kum_berat = np.cumsum(d["berat_bulanan"])
            kum_co2 = np.cumsum(d["co2_bulanan"])
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(
                go.Scatter(
                    x=d["bulan_label"], y=np.round(kum_berat, 1), name="Akumulasi sampah dialihkan (kg)",
                    mode="lines+markers", line=dict(color=DAUN, width=3), marker=dict(size=8),
                    hovertemplate="%{x}<br>Dialihkan: %{y:,.1f} kg<extra></extra>",
                ),
                secondary_y=False,
            )
            fig2.add_trace(
                go.Scatter(
                    x=d["bulan_label"], y=np.round(kum_co2, 1), name="Akumulasi CO₂e bersih (kg)",
                    mode="lines+markers", line=dict(color=AMBER, width=3, dash="dot"), marker=dict(size=8),
                    hovertemplate="%{x}<br>CO₂e bersih: %{y:,.1f} kg<extra></extra>",
                ),
                secondary_y=True,
            )
            fig2.update_yaxes(title_text="Sampah dialihkan (kg)", secondary_y=False)
            fig2.update_yaxes(title_text="CO₂e bersih (kg)", secondary_y=True, showgrid=False)
            grafik(gaya(fig2, "Tren 6 bulan: akumulasi pengalihan dan reduksi CO₂e"), "mitra_tren")

        h(
            """
            <div class="bb-card" style="margin-bottom:12px;"><b style="color:#1B4332;">Unduh Laporan Kepatuhan Bulanan</b>
            <p style="margin-top:4px;">Berisi ringkasan berat, bahan ditolak, estimasi CO₂e, faktor emisi, dan ID sertifikat QR.</p></div>
            """
        )
        u1, u2 = st.columns(2)
        with u1:
            st.download_button(
                "Unduh Laporan Kepatuhan Bulanan (.txt)", data=laporan_txt(nama, d).encode("utf-8"),
                file_name=f"laporan_kepatuhan_{p['kode']}_2027-08.txt", mime="text/plain",
                key=f"unduh_txt_{p['kode']}", type="primary",
            )
        with u2:
            st.download_button(
                "Unduh Data Penjemputan (.csv)", data=laporan_csv(d),
                file_name=f"data_penjemputan_{p['kode']}_2027-08.csv", mime="text/csv",
                key=f"unduh_csv_{p['kode']}",
            )

    with tab_jemput:
        j1, j2 = st.columns([1, 1.4], gap="medium")
        with j1:
            h(
                f"""
                <div class="bb-gelap"><div style="font-size:0.85rem;color:#CFE3D6;">Jadwal Penjemputan Berikutnya</div>
                <div style="font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.9rem;color:#FFFFFF;line-height:1.15;margin:6px 0;">Senin, 30 Agustus 2027</div>
                <p>Pukul 08.00–10.00 WIB · {p['rute']}</p>
                <p style="margin-top:8px;">Jadwal tetap: Senin, Rabu, Jumat. Siapkan dua bin berlabel QR: ampas kopi dan sisa dapur.</p></div>
                """
            )
        with j2:
            df = d["df"]
            jumlah_lolos = int((df["status"] == "Lolos").sum())
            jumlah_catatan = int((df["status"] != "Lolos").sum())
            h(
                f"""
                <div class="bb-card"><h4>Ringkasan inspeksi bulan ini</h4>
                <div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0;">
                <span class="bb-badge bb-badge-hijau">{len(df)} penjemputan</span>
                <span class="bb-badge bb-badge-hijau">{jumlah_lolos} lolos</span>
                <span class="bb-badge bb-badge-amber">{jumlah_catatan} dengan catatan</span></div>
                <p>Bahan ditolak total {angka(d['ditolak_total'])} kg ({angka(d['persen_tolak'])}% dari bahan masuk). Pemilahan yang rapi
                menjaga mutu kompos dan menghindarkan penyesuaian tarif.</p></div>
                """
            )
        st.write("")
        df = d["df"]
        tampil = pd.DataFrame(
            {
                "Tanggal": [tgl_pendek(x) for x in df["tanggal"]],
                "Berat Ampas Kopi (kg)": [angka(x, 1) for x in df["kopi"]],
                "Berat Sisa Dapur (kg)": [angka(x, 1) for x in df["dapur"]],
                "Berat Ditolak (kg)": [angka(x, 1) for x in df["ditolak"]],
                "Status Kualitas": df["status"],
                "Catatan Inspeksi": df["catatan"],
            }
        ).iloc[::-1].reset_index(drop=True)
        h('<div style="font-weight:600;color:#1B4332;margin-bottom:6px;">Riwayat penjemputan dan inspeksi kualitas</div>')
        tabel(tampil, tinggi=460)

    with tab_laporan:
        h('<div style="font-weight:600;color:#1B4332;font-size:1.1rem;margin-bottom:4px;">Kalkulator simulasi emisi CO₂e</div>')
        st.caption("Geser berat sisa pangan layak olah per bulan untuk melihat estimasi emisi yang dihindari.")
        standar_kopi = int(min(3000, max(0, round(d["kopi_total"] / 10) * 10)))
        standar_dapur = int(min(3000, max(0, round(d["dapur_total"] / 10) * 10)))
        s1, s2 = st.columns(2)
        with s1:
            berat_kopi = st.slider(
                "Berat ampas kopi layak olah (kg/bulan)", 0, 3000, standar_kopi, step=10, key=f"kalk_kopi_{p['kode']}",
            )
        with s2:
            berat_dapur = st.slider(
                "Berat sisa dapur layak olah (kg/bulan)", 0, 3000, standar_dapur, step=10, key=f"kalk_dapur_{p['kode']}",
            )
        berat = berat_kopi + berat_dapur
        kotor = berat * EF_TPA
        proses = berat * EF_KOMPOS
        transport = berat * EF_TRANSPORT
        bersih = berat * EF_BERSIH
        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            h(kartu_metrik("Emisi kotor dihindari", f"{angka(kotor, 1)} kg", f"{angka(berat, 0)} kg × {angka(EF_TPA, 4)}", warna=KOPI))
        with c2:
            h(kartu_metrik("Emisi proses pengomposan", f"{angka(proses, 1)} kg", f"{angka(berat, 0)} kg × {angka(EF_KOMPOS, 2)} (IPCC)", warna=AMBER))
        with c3:
            h(kartu_metrik("Emisi transportasi jemput", f"{angka(transport, 1)} kg", f"{angka(berat, 0)} kg × {angka(EF_TRANSPORT, 4)}", warna=AMBER))
        with c4:
            h(kartu_metrik("Emisi CO₂e bersih dihindari", f"{angka(bersih, 1)} kg", "W layak × (EF TPA − EF kompos − EF transportasi)", warna=HUTAN, latar="#D8F3DC"))
        st.caption(
            f"Catatan: emisi transportasi {KET_EF_TRANSPORT}. Faktor EPA berasal dari kondisi TPA di Amerika Serikat, "
            f"dan angka ini adalah estimasi, bukan kredit karbon."
        )
        fig3 = go.Figure(
            go.Bar(
                x=["Emisi kotor (jika ke TPA)", "Emisi proses pengomposan", "Emisi transportasi jemput", "Emisi CO₂e bersih dihindari"],
                y=[kotor, proses, transport, bersih],
                marker_color=[KOPI, AMBER, "#F0B14B", DAUN],
                text=[f"{angka(v, 1)} kg" for v in (kotor, proses, transport, bersih)],
                textposition="outside",
                hovertemplate="%{x}<br>%{y:,.1f} kg CO₂e<extra></extra>",
            )
        )
        fig3.update_layout(yaxis_title="kg CO₂e", showlegend=False)
        grafik(gaya(fig3, "Rincian emisi hasil simulasi", tinggi=340), f"mitra_kalkulator_{p['kode']}")

        h('<div style="font-weight:600;color:#1B4332;font-size:1.1rem;margin:14px 0 6px 0;">Arsip laporan bulanan</div>')
        arsip = []
        for i in range(len(d["bulan_label"]) - 1, -1, -1):
            nomor_bulan = d["bulan_nomor"][i]
            arsip.append(
                {
                    "Bulan": f"{BULAN_PANJANG[nomor_bulan - 1]} 2027",
                    "Total Berat Dialihkan (kg)": angka(d["berat_bulanan"][i], 1),
                    "CO₂e Bersih (kg CO₂e)": angka(d["co2_bulanan"][i], 1),
                    "ID Sertifikat QR": id_sertifikat(nama, nomor_bulan, i + 1),
                }
            )
        tabel(pd.DataFrame(arsip))


# ----------------------------------------------------------------------------
# HALAMAN 3: Dashboard Operasional
# ----------------------------------------------------------------------------
def halaman_operasional():
    atas = st.columns([4, 1.3])
    with atas[0]:
        h('<h1 style="margin:0;font-size:2.2rem;">Dashboard Operasional</h1>')
        h('<span class="bb-label-ilustrasi">Data ilustrasi operasional &amp; proyeksi finansial skenario dasar</span>')
    with atas[1]:
        st.write("")
        st.button("Kembali ke Landing Page", key="ops_kembali", on_click=pindah_halaman, args=("Landing Page",))
    h(
        """
        <div style="margin:14px 0 10px 0;color:#44504A;font-size:0.95rem;">
        Tampilan internal tim Balik Bumi · Periode Februari 2028 (bulan ke-12 pada skenario dasar presentasi final)
        </div>
        """
    )

    tab_beranda, tab_rute, tab_produksi, tab_keuangan = st.tabs(
        ["Beranda", "Rute & Jemput", "Produksi", "Keuangan & Sensitivitas"]
    )

    with tab_beranda:
        # [CEK] Kapasitas bulan 12 (1 sopir/kendaraan per 800 kg/hari, 1 operator per 400 kg/hari, 1 sopir dan 2 operator)
        # belum diverifikasi ke RAB Skema 3.
        armada = VOLUME_HARIAN_HUB / (1 * 800) * 100
        operator = VOLUME_HARIAN_HUB / (2 * 400) * 100
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        with m1:
            h(
                f"""
                <div class="bb-card" style="border-top:4px solid {DAUN};"><div class="bb-metrik-label">Mitra aktif</div>
                <div class="bb-metrik-nilai">{MITRA_AKTIF} <span style="font-size:1rem;color:#5B635D;font-weight:500;">/ {TARGET_MITRA}</span></div>
                {bar_progres(MITRA_AKTIF / TARGET_MITRA * 100)}
                <div class="bb-metrik-ket">Target SOM 55 mitra pada bulan ke-24</div></div>
                """
            )
        with m2:
            h(
                f"""
                <div class="bb-card" style="border-top:4px solid {DAUN};"><div class="bb-metrik-label">Volume harian hub</div>
                <div class="bb-metrik-nilai">{angka(VOLUME_HARIAN_HUB, 0)} <span style="font-size:1rem;color:#5B635D;font-weight:500;">kg/hari</span></div>
                {bar_progres(VOLUME_HARIAN_HUB / TARGET_VOLUME_HARIAN * 100)}
                <div class="bb-metrik-ket">Target {angka(TARGET_VOLUME_HARIAN, 0)} kg/hari pada bulan ke-24</div></div>
                """
            )
        with m3:
            h(kartu_metrik("Persentase kontaminasi / ditolak", "2,6%", "Batas target ≤ 3% dari bahan masuk", warna=AMBER))
        with m4:
            h(
                f"""
                <div class="bb-card" style="border-top:4px solid {DAUN};"><div class="bb-metrik-label">Utilisasi armada &amp; operator</div>
                <div class="bb-metrik-nilai" style="font-size:1.5rem;">Armada {angka(armada, 0)}% · Operator {angka(operator, 0)}%</div>
                {bar_progres(operator)}
                <div class="bb-metrik-ket">Kapasitas terpasang: 1 sopir dan 2 operator</div></div>
                """
            )
        st.write("")
        g_kiri, g_kanan = st.columns([1.35, 1], gap="medium")
        with g_kiri:
            label, kopi, dapur = data_hub_mingguan()
            fig = go.Figure()
            fig.add_bar(
                name="Sisa dapur", x=label, y=np.round(dapur, 0), marker_color=DAUN,
                hovertemplate="%{x}<br>Sisa dapur: %{y:,.0f} kg<extra></extra>",
            )
            fig.add_bar(
                name="Ampas kopi", x=label, y=np.round(kopi, 0), marker_color=KOPI,
                hovertemplate="%{x}<br>Ampas kopi: %{y:,.0f} kg<extra></extra>",
            )
            fig.update_layout(barmode="stack", yaxis_title="Volume masuk (kg per minggu)")
            grafik(gaya(fig, "Volume masuk per minggu menurut kategori (8 minggu terakhir)"), "ops_mingguan")
        with g_kanan:
            h('<div style="font-weight:600;color:#1B4332;font-size:1.05rem;margin:6px 0 10px 0;">Perlu Perhatian</div>')
            peringatan = [
                ("Kontaminasi", "bb-badge-amber", "Bistro Braga Heritage",
                 "Penolakan di atas 3% pada 3 penjemputan berturut-turut. Jadwalkan pelatihan pemilahan."),
                ("Produksi", "bb-badge-amber", "Batch #14 (K-014)",
                 "Suhu tumpukan 68 °C mendekati batas atas 70 °C. Balik tumpukan dan tambah bahan pengisi."),
                ("Mitra", "bb-badge-abu", "Perpanjangan promo pilot",
                 "Peninjauan perpanjangan promo pilot untuk 2 mitra dijadwalkan Jumat ini."),
                ("Stok", "bb-badge-abu", "Kompos karung 25 kg",
                 "Sisa 62 karung siap jual. Jadwalkan pengemasan dari Batch K-010."),
            ]
            for tingkat, kelas, judul, isi in peringatan:
                h(
                    f"""
                    <div class="bb-card" style="padding:14px 16px;margin-bottom:10px;">
                    <span class="bb-badge {kelas}" style="font-size:0.75rem;padding:3px 10px;">{tingkat}</span>
                    <div class="bb-alert-judul" style="margin-top:6px;">{judul}</div>
                    <div class="bb-alert-isi">{isi}</div></div>
                    """
                )

    with tab_rute:
        rute_df = data_rute()
        kolom_rute = st.columns(3, gap="medium")
        for kolom, (kode, info) in zip(kolom_rute, RUTE_INFO.items()):
            sub = rute_df[rute_df["rute"] == kode]
            selesai = int((sub["Status Penjemputan"] == "Selesai").sum())
            total = len(sub)
            with kolom:
                h(
                    f"""
                    <div class="bb-card"><div style="font-weight:600;color:{HUTAN};">{kode}: {info['nama']}</div>
                    <div class="bb-metrik-nilai" style="font-size:1.6rem;margin-top:6px;">{selesai} dari {total} titik</div>
                    {bar_progres(selesai / total * 100)}
                    <div class="bb-metrik-ket">{angka(selesai / total * 100, 0)}% selesai · simulasi pukul 09.45 WIB</div></div>
                    """
                )
        st.write("")
        pilihan = st.selectbox("Filter rute", ["Semua rute"] + [f"{k}: {v['nama']}" for k, v in RUTE_INFO.items()], key="filter_rute")
        tampil = rute_df.drop(columns=["rute"])
        if pilihan != "Semua rute":
            tampil = tampil[tampil["Zona Rute"] == pilihan]
        tampil = tampil.copy()
        total_berat = int(tampil["Estimasi Berat (kg)"].sum())
        tampil["Estimasi Berat (kg)"] = tampil["Estimasi Berat (kg)"].map(lambda x: angka(x, 0))
        h('<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Titik jemput hari ini (Rabu)</div>')
        tabel(tampil.reset_index(drop=True), tinggi=420)
        st.caption(
            f"Total estimasi berat pada tampilan ini {angka(total_berat, 0)} kg. Volume harian hub dihitung rata-rata 7 hari, "
            f"sehingga hari penjemputan (Senin, Rabu, Jumat) lebih besar dari rata-rata harian."
        )

    with tab_produksi:
        s1, s2, s3 = st.columns(3, gap="medium")
        with s1:
            h(kartu_metrik("Stok kompos matang", "3.840 kg", "Siap uji mutu dan pengemasan", warna=DAUN))
        with s2:
            h(kartu_metrik("Media tanam siap kemas", "1.250 kg", "Kemasan 5 kg dan karung 25 kg", warna=KOPI))
        with s3:
            h(kartu_metrik("Pelet pakan uji coba", "180 kg", "Hanya untuk peternak mitra pilot", warna=AMBER))
        st.write("")
        batch = data_batch()
        warna_status = {"Mesofilik": "#95D5B2", "Termofilik": AMBER, "Pematangan": DAUN, "Siap Panen": HUTAN}
        fig = go.Figure(
            go.Bar(
                x=batch["Kode Batch"], y=batch["Suhu (°C)"],
                marker_color=[warna_status[s] for s in batch["Status"]],
                text=batch["Status"], textposition="outside",
                hovertemplate="%{x}<br>Suhu: %{y} °C<extra></extra>",
            )
        )
        fig.add_hline(
            y=70, line_dash="dash", line_color=KOPI,
            annotation_text="Batas atas suhu 70 °C", annotation_position="top left",
        )
        fig.update_layout(yaxis_title="Suhu tumpukan (°C)", showlegend=False, yaxis_range=[0, 85])
        grafik(gaya(fig, "Suhu tumpukan per batch kompos"), "ops_suhu_batch")
        h('<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Monitoring batch produksi</div>')
        tampil_batch = batch.copy()
        tampil_batch["pH"] = tampil_batch["pH"].map(lambda x: angka(x, 1))
        tabel(tampil_batch)
        st.caption("Uji mutu tiap batch: kadar air, pH, rasio C/N, benda asing, dan logam berat dengan acuan SNI 19-7030-2004.")

    with tab_keuangan:
        k = data_keuangan()
        f1, f2, f3, f4 = st.columns(4, gap="medium")
        with f1:
            h(kartu_metrik("Pendapatan bulanan", juta(k["total"]),
                           f"Layanan {angka(k['layanan'] / k['total'] * 100, 0)}% · kompos {angka(k['kompos'] / k['total'] * 100, 1)}% · pelet {angka(k['pelet'] / k['total'] * 100, 1)}%"))
        with f2:
            h(kartu_metrik("Biaya operasional", juta(k["biaya"]), "Sewa hub, upah, armada, bahan, sistem", warna=KOPI))
        with f3:
            h(kartu_metrik("EBITDA bulanan", juta(k["ebitda"]), "Pendapatan dikurangi biaya operasional", warna=HUTAN, latar="#D8F3DC"))
        with f4:
            h(kartu_metrik("Tarif layanan (kontrak 3 tahun)", f"Rp{angka(TARIF_JALUR[JALUR_UTAMA][0], 0)} → Rp{angka(TARIF_JALUR[JALUR_UTAMA][2], 0)}/kg",
                           "Turun per tingkat volume bulanan", warna=AMBER))
        st.write("")
        c_kiri, c_kanan = st.columns([1.5, 1], gap="medium")
        with c_kiri:
            fig = go.Figure()
            fig.add_bar(
                name="Pendapatan", x=k["bulan"], y=np.round(k["pendapatan_seri"], 1), marker_color=DAUN,
                hovertemplate="%{x}<br>Pendapatan: Rp%{y:,.1f} juta<extra></extra>",
            )
            fig.add_bar(
                name="Biaya operasional", x=k["bulan"], y=np.round(k["biaya_seri"], 1), marker_color=KOPI,
                hovertemplate="%{x}<br>Biaya: Rp%{y:,.1f} juta<extra></extra>",
            )
            ebitda_seri = np.array(k["pendapatan_seri"]) - np.array(k["biaya_seri"])
            fig.add_trace(
                go.Scatter(
                    name="EBITDA", x=k["bulan"], y=np.round(ebitda_seri, 1), mode="lines+markers",
                    line=dict(color=AMBER, width=3), marker=dict(size=8),
                    hovertemplate="%{x}<br>EBITDA: Rp%{y:,.1f} juta<extra></extra>",
                )
            )
            fig.update_layout(barmode="group", yaxis_title="Juta rupiah")
            grafik(gaya(fig, "Pendapatan vs biaya, 6 bulan terakhir (Sep 2027 - Feb 2028)"), "ops_keuangan")
        with c_kanan:
            donat = go.Figure(
                go.Pie(
                    labels=["Biaya layanan (per tingkat)", "Kompos (Rp2.000/kg)", "Pelet (Rp4.000/kg)"],
                    values=[k["layanan"], k["kompos"], k["pelet"]],
                    hole=0.55, marker=dict(colors=[DAUN, KOPI, AMBER]), sort=False,
                    textinfo="percent", hovertemplate="%{label}<br>Rp%{value:,.1f} juta<extra></extra>",
                )
            )
            grafik(gaya(donat, "Komposisi pendapatan bulanan"), "ops_donat")
        with st.expander("Rincian biaya operasional bulanan"):
            tabel(pd.DataFrame(
                [(nama, juta(nilai, 2)) for nama, nilai in k["biaya_rincian"]] + [("Total biaya operasional", juta(k["biaya"], 2))],
                columns=["Komponen biaya", "Nilai per bulan"],
            ))

        # Indikator kelayakan skenario dasar dan tabel skenario dari presentasi final.
        # [CEK] Slider penyesuaian tarif dihapus: model arus kas bulanan belum bisa direplikasi karena RAB Skema 3 belum tersedia.
        h('<div class="bb-bagian" style="margin-top:30px;">Kelayakan dan sensitivitas</div>')
        h('<div class="bb-h2" style="font-size:1.6rem;">Indikator skenario dasar dan hasil skenario uji</div>')
        i1, i2, i3 = st.columns(3, gap="medium")
        with i1:
            h(kartu_metrik("Investasi awal", f"±Rp{int(INVESTASI_AWAL_JUTA + 0.5)} juta",
                           f"Rp{angka(INVESTASI_AWAL_JUTA, 1)} juta sebelum operasi", warna=KOPI))
        with i2:
            h(kartu_metrik("Total investasi 36 bulan", juta(INVESTASI_TOTAL_36_JUTA),
                           "Investasi awal, belanja lanjutan, dan modal kerja", warna=KOPI))
        with i3:
            h(kartu_metrik("Kebutuhan dana puncak", f"±Rp{angka(DANA_PUNCAK_JUTA, 0)} juta",
                           f"Bulan ke-{BULAN_DANA_PUNCAK}: modal awal 141 + belanja lanjutan {angka(BELANJA_LANJUTAN_JUTA, 1)} "
                           f"+ modal kerja {angka(MODAL_KERJA_JUTA, 1)} (juta rupiah)", warna=AMBER))
        st.write("")
        sm1, sm2, sm3 = st.columns(3, gap="medium")
        with sm1:
            h(kartu_metrik("Laba bersih tahun ke-3", juta(LABA_TAHUN3_JUTA), "Skenario dasar presentasi final",
                           warna=HUTAN, latar="#D8F3DC"))
        with sm2:
            h(kartu_metrik("ROI tahun ke-3", f"±{angka(ROI_TAHUN3, 0)}%",
                           f"Laba tahun ke-3 ÷ total investasi 36 bulan ({juta(INVESTASI_TOTAL_36_JUTA)})"))
        with sm3:
            h(kartu_metrik("Titik impas dan pengembalian modal", f"BEP bulan ke-{BEP_BULAN} · payback bulan ke-{PAYBACK_BULAN}",
                           "Horizon model 36 bulan", warna=KOPI))
        st.success(
            f"Skenario dasar: titik impas operasional bulan ke-{BEP_BULAN}, pengembalian modal pada bulan ke-{PAYBACK_BULAN}, "
            f"laba bersih tahun ke-3 {juta(LABA_TAHUN3_JUTA)}, dan pangsa pendapatan layanan tahun ke-3 {PANGSA_LAYANAN_TAHUN3}%."
        )

        h('<div style="font-weight:600;color:#1B4332;margin:14px 0 6px 0;">Skenario uji dari presentasi final</div>')
        skenario = pd.DataFrame(
            {
                "Skenario": [
                    "Skenario dasar",
                    "Tarif kontrak turun 10%",
                    "Tarif kafe Rp1.426/kg (turun 4,5%)",
                    "Volume resto dan hotel 30 kg/hari",
                    "Biaya naik 5% per tahun",
                    "Tanpa pelet",
                ],
                "Hasil": [
                    f"Payback bulan ke-{PAYBACK_BULAN} · BEP bulan ke-{BEP_BULAN} · laba tahun ke-3 {juta(LABA_TAHUN3_JUTA)}",
                    "Payback lewat 36 bulan",
                    "Payback tepat bulan ke-36",
                    "Payback lewat 36 bulan",
                    "Kas bulan ke-36 sebesar -Rp21 juta",
                    f"Payback ±bulan ke-{PAYBACK_BULAN}",
                ],
            }
        )
        tabel(skenario)
        st.caption(
            "Hanya hasil yang tertulis di presentasi final yang ditampilkan di sini. Tidak ada angka antar skenario yang diinterpolasi."
        )


# ----------------------------------------------------------------------------
# Kendali utama
# ----------------------------------------------------------------------------
def main():
    if "nav_menu" not in st.session_state:
        st.session_state["nav_menu"] = HALAMAN[0]
    if "scroll_form" not in st.session_state:
        st.session_state["scroll_form"] = False
    render_sidebar()
    halaman = st.session_state["nav_menu"]
    st.session_state["halaman"] = halaman
    if halaman == "Dashboard Mitra":
        halaman_mitra()
    elif halaman == "Dashboard Operasional":
        halaman_operasional()
    else:
        halaman_landing()


main()
