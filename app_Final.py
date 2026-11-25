"""
Balik Bumi - Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung
Mockup interaktif untuk Carbon 2026 Business Plan Competition (Tim Hore, Telkom University).

Jalankan dengan:
    pip install streamlit plotly pandas numpy segno opencv-python-headless
    streamlit run app.py

Seluruh data pada aplikasi ini adalah data ilustrasi simulasi yang mengikuti proposal.
"""

import hashlib
import io
import textwrap
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import segno
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
# Konstanta model (mengikuti proposal)
# ----------------------------------------------------------------------------
HAL_KURIR = "Simulasi Kurir (Scan QR)"
HALAMAN = ["Landing Page", "Dashboard Mitra", "Dashboard Operasional", HAL_KURIR]

KREM = "#FAF9F5"
HUTAN = "#1B4332"
DAUN = "#2D6A4F"
KOPI = "#5C4033"
AMBER = "#D97706"
BORDER = "#E5E0D8"
DAUN_MUDA = "#95D5B2"

EF_TPA = 0.7496  # kg CO2e per kg, proksi US EPA (2024)
EF_KOMPOS = 0.19  # kg CO2e per kg, IPCC (2006)
EF_BERSIH = EF_TPA - EF_KOMPOS
EF_TRANSPORT = 0.02  # kg CO2e per kg, asumsi ilustrasi simulasi (tidak ada di proposal)

# Tarif berjenjang (Rp/kg, dihitung per tingkat volume bulanan). Sumber: PPT final.
BATAS_TINGKAT_KG = [400, 1500]
TARIF_KONTRAK = [1493, 1393, 896]
TARIF_PROMO = [1598, 1491, 959]
TARIF_DASAR = TARIF_KONTRAK[0]  # Rp per kg, tingkat pertama kontrak 3 tahun
JALUR_KONTRAK = "Kontrak 3 tahun (tarif terkunci)"
JALUR_PROMO = "Tanpa kontrak (tarif promosi)"
HARGA_KOMPOS = 2000  # Rp per kg
HARGA_PELET = 4000  # Rp per kg
HARI_PER_BULAN = 30.4
BATAS_TOLAK = 3.0  # persen
FAKTOR_BULANAN = [0.55, 0.68, 0.79, 0.88, 0.95, 1.0]


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

# Volume hub (skenario dasar proposal, bulan ke-12 simulasi)
MITRA_AKTIF = 28
TARGET_MITRA = 55
VOLUME_HARIAN_HUB = 557  # kg per hari = 28 mitra x 19,9 kg
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
.bb-kecil { font-size: 1.5rem; white-space: nowrap; }
.bb-tabel-saing { width: 100%; border-collapse: collapse; font-size: 0.9rem; background: #FFFFFF; border: 1px solid #E5E0D8; border-radius: 12px; }
.bb-tabel-saing th { text-align: left; background: #F5F2EC; color: #44504A; padding: 8px 10px; font-weight: 600; }
.bb-tabel-saing td { padding: 8px 10px; border-top: 1px solid #EDE9E0; vertical-align: top; color: #2B3A32; }
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
.bb-qr-card { background: #FFFFFF; border: 1px solid #E5E0D8; border-radius: 16px; padding: 16px; text-align: center; box-shadow: 0 4px 14px rgba(27, 67, 50, 0.07); }
.bb-qr-card img { display: block; margin: 8px auto; image-rendering: pixelated; }
.bb-hp-judul { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.35rem; color: #FFFFFF; margin: 4px 0; line-height: 1.2; }
.bb-hp-ket { font-size: 0.85rem; color: #E9F2EA; }
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


def biaya_layanan(kg_bulan, kontrak=True):
    """Biaya layanan per bulan (Rp), dihitung per tingkat volume."""
    tarif = TARIF_KONTRAK if kontrak else TARIF_PROMO
    total, bawah = 0.0, 0.0
    for batas, t in zip(BATAS_TINGKAT_KG + [float("inf")], tarif):
        kg = max(0.0, min(float(kg_bulan), batas) - bawah)
        total += kg * t
        bawah = batas
    return total


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


def grafik(fig, key, scroll=False):
    opsi = {"key": key, "config": {"displayModeBar": False, "scrollZoom": scroll}}
    opsi.update(_lebar_penuh())
    st.plotly_chart(fig, **opsi)


def gaya(fig, judul, tinggi=340):
    """Gaya grafik: judul dibungkus agar tidak terpotong, legend di atas plot agar tidak menabrak label sumbu."""
    baris_judul = textwrap.wrap(judul, 34) or [judul]
    nama_legend = [t.name or "" for t in fig.data if getattr(t, "showlegend", None) is not False and t.name]
    ada_legend = len(nama_legend) > 1
    baris_legend = 0
    if ada_legend:
        perkiraan_px = sum(len(n) + 6 for n in nama_legend) * 7
        baris_legend = min(3, -(-perkiraan_px // 320))
    tinggi_legend = (24 * baris_legend + 10) if ada_legend else 0
    tinggi_judul = 21 * len(baris_judul)
    atas = 28 + tinggi_judul + tinggi_legend + 10
    total = tinggi + (tinggi_judul - 21) + tinggi_legend + 12
    area_plot = max(120, total - atas - 40)
    fig.update_layout(
        title=dict(text="<br>".join(baris_judul), x=0, xanchor="left", y=1, yanchor="top", pad=dict(t=24)),
        height=total,
        margin=dict(l=10, r=10, t=atas, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color="#2B3A32"),
        title_font=dict(family="Bricolage Grotesque, sans-serif", size=16, color=HUTAN),
        legend=dict(orientation="h", yanchor="bottom", y=1 + 8 / area_plot, xanchor="left", x=0, traceorder="normal"),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(family="Inter, sans-serif", color=HUTAN)),
        separators=",.",
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER, automargin=True)
    fig.update_yaxes(gridcolor="#EDE9E0", zerolinecolor=BORDER, automargin=True)
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
        st.button("Reset simulasi kurir", key="sidebar_reset", on_click=reset_sim)
        h(
            """
            <div class="bb-side-note">
            Tim Hore, Telkom University<br>
            Carbon 2026 Business Plan Competition<br>
            From Waste to Wealth<br><br>
            Versi 25 Nov 2026 · v2 (PDF dan Excel)
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
    semua_hari = pd.date_range("2027-08-02", "2027-08-28")
    tanggal = [d.date() for d in semua_hari if d.weekday() in (0, 3, 5)]
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

    faktor = FAKTOR_BULANAN
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


def _tanggal_py(x):
    return pd.to_datetime(x).to_pydatetime()


def laporan_xlsx(nama, d):
    """Data penjemputan sebagai file Excel rapi: sheet Ringkasan dan sheet Penjemputan."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    p = d["profil"]
    df = d["df"].copy()
    hijau = PatternFill("solid", fgColor="1B4332")
    hijau_muda = PatternFill("solid", fgColor="D8F3DC")
    kuning = PatternFill("solid", fgColor="FFF1C7")
    abu = PatternFill("solid", fgColor="F5F2EC")
    tepi = Border(*(Side(style="thin", color="D9D3C7"),) * 4)
    putih_tebal = Font(name="Calibri", bold=True, color="FFFFFF", size=11)

    wb = Workbook()
    ws = wb.active
    ws.title = "Ringkasan"
    ws["A1"] = "Data Penjemputan Balik Bumi"
    ws["A1"].font = Font(name="Calibri", bold=True, size=15, color="1B4332")
    ws["A2"] = f"{nama} · {p['jenis']} · {p['area']} · {p['rute']}"
    ws["A3"] = "Periode Agustus 2027 · data ilustrasi untuk simulasi"
    ws["A2"].font = Font(name="Calibri", size=11, color="44504A")
    ws["A3"].font = Font(name="Calibri", size=10, italic=True, color="7A857F")
    for sel, teks in (("A5", "Ukuran"), ("B5", "Nilai")):
        ws[sel] = teks
        ws[sel].font = putih_tebal
        ws[sel].fill = hijau
        ws[sel].alignment = Alignment(horizontal="left" if sel == "A5" else "right")
        ws[sel].border = tepi
    ringkas = [
        ("Ampas kopi dijemput (kg)", d["kopi_total"], "#,##0.0"),
        ("Sisa dapur dijemput (kg)", d["dapur_total"], "#,##0.0"),
        ("Total bahan masuk (kg)", d["masuk_total"], "#,##0.0"),
        ("Bahan ditolak inspeksi (kg)", d["ditolak_total"], "#,##0.0"),
        ("Bahan ditolak (%)", d["persen_tolak"], "0.0"),
        ("Total dialihkan dari TPA (kg)", d["dialihkan"], "#,##0.0"),
        ("Emisi kotor dihindari (kg CO2e)", d["kotor"], "#,##0.0"),
        ("Emisi bersih dihindari (kg CO2e)", d["bersih"], "#,##0.0"),
    ]
    for i, (label, nilai, fmt) in enumerate(ringkas, start=6):
        ws.cell(row=i, column=1, value=label).border = tepi
        c = ws.cell(row=i, column=2, value=round(float(nilai), 1))
        c.number_format = fmt
        c.border = tepi
        c.alignment = Alignment(horizontal="right")
        if i % 2 == 0:
            ws.cell(row=i, column=1).fill = abu
            c.fill = abu
        if "bersih" in label or "dialihkan" in label:
            ws.cell(row=i, column=1).font = Font(name="Calibri", bold=True)
            c.font = Font(name="Calibri", bold=True)
    ws.cell(row=15, column=1, value="Emisi adalah estimasi, bukan kredit karbon. Faktor emisi: EF TPA 0,7496 (US EPA, 2024), EF kompos 0,19 (IPCC, 2006).").font = Font(name="Calibri", size=9, italic=True, color="7A857F")
    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 16
    ws.sheet_view.showGridLines = False

    w2 = wb.create_sheet("Penjemputan")
    kepala = ["Tanggal", "Ampas Kopi (kg)", "Sisa Dapur (kg)", "Ditolak (kg)", "Dialihkan (kg)", "Status Kualitas", "Catatan Inspeksi"]
    for j, teks in enumerate(kepala, start=1):
        c = w2.cell(row=1, column=j, value=teks)
        c.font = putih_tebal
        c.fill = hijau
        c.border = tepi
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    w2.row_dimensions[1].height = 24
    n = 0
    for i, (_, r) in enumerate(df.iterrows(), start=2):
        n = i
        nilai = [
            _tanggal_py(r["tanggal"]), round(float(r["kopi"]), 1), round(float(r["dapur"]), 1),
            round(float(r["ditolak"]), 1), round(float(r["masuk"] - r["ditolak"]), 1), str(r["status"]), str(r["catatan"]),
        ]
        for j, v in enumerate(nilai, start=1):
            c = w2.cell(row=i, column=j, value=v)
            c.border = tepi
            c.alignment = Alignment(vertical="top", wrap_text=(j == 7))
            if j == 1:
                c.number_format = "dd-mm-yyyy"
                c.alignment = Alignment(horizontal="center", vertical="top")
            elif 2 <= j <= 5:
                c.number_format = "#,##0.0"
                c.alignment = Alignment(horizontal="right", vertical="top")
        w2.cell(row=i, column=6).fill = hijau_muda if r["status"] == "Lolos" else kuning
    total = n + 1
    w2.cell(row=total, column=1, value="Total").font = Font(name="Calibri", bold=True)
    for j in range(2, 6):
        huruf = get_column_letter(j)
        c = w2.cell(row=total, column=j, value=f"=SUM({huruf}2:{huruf}{n})")
        c.number_format = "#,##0.0"
        c.font = Font(name="Calibri", bold=True)
        c.alignment = Alignment(horizontal="right")
    for j in range(1, 8):
        w2.cell(row=total, column=j).fill = abu
        w2.cell(row=total, column=j).border = tepi
    for kolom, lebar in zip("ABCDEFG", (13, 16, 16, 14, 16, 16, 52)):
        w2.column_dimensions[kolom].width = lebar
    w2.freeze_panes = "A2"
    w2.auto_filter.ref = f"A1:G{n}"
    w2.sheet_view.showGridLines = False

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _pdf_teks(s):
    s = str(s).replace("₂", "2").replace("→", "-").replace("≈", "~")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.encode("cp1252", "replace").decode("cp1252")


def laporan_pdf(nama, d):
    """Laporan kepatuhan bulanan dalam PDF (A4)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    p = d["profil"]
    df = d["df"]
    sertifikat = id_sertifikat(nama, 8, 5)
    hutan = colors.HexColor("#1B4332")
    daun = colors.HexColor("#2D6A4F")
    muda = colors.HexColor("#D8F3DC")
    abu = colors.HexColor("#F5F2EC")
    garis = colors.HexColor("#D9D3C7")
    teks = colors.HexColor("#2B3A32")

    st_normal = ParagraphStyle("n", fontName="Helvetica", fontSize=9.5, leading=13, textColor=teks)
    st_kecil = ParagraphStyle("k", parent=st_normal, fontSize=8, leading=11, textColor=colors.HexColor("#6B766F"))
    st_judul = ParagraphStyle("j", parent=st_normal, fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=hutan, spaceAfter=4)
    st_bagian = ParagraphStyle("b", parent=st_normal, fontName="Helvetica-Bold", fontSize=10.5, textColor=hutan, spaceBefore=8, spaceAfter=3)
    st_sel = ParagraphStyle("s", parent=st_normal, fontSize=9, leading=12)
    st_sel_b = ParagraphStyle("sb", parent=st_sel, fontName="Helvetica-Bold")
    st_kop = ParagraphStyle("kop", parent=st_normal, fontName="Helvetica-Bold", fontSize=13, textColor=colors.white, leading=16)
    st_kop2 = ParagraphStyle("kop2", parent=st_normal, fontSize=8.5, textColor=colors.HexColor("#CFE3D6"), leading=11)

    def P(t, gaya_=st_sel):
        return Paragraph(_pdf_teks(t), gaya_)

    def tabel_dua(baris, lebar=(7.2 * cm, 9.8 * cm)):
        t = Table([[P(a, st_sel_b), P(b)] for a, b in baris], colWidths=lebar)
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, abu]),
            ("GRID", (0, 0), (-1, -1), 0.4, garis),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        return t

    cerita = []
    kop = Table([[Paragraph("BALIK BUMI", st_kop)], [Paragraph("Hub Pengolahan Sisa Pangan Terpadu, Kota Bandung", st_kop2)]], colWidths=[17 * cm])
    kop.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), hutan), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                             ("TOPPADDING", (0, 0), (0, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 10)]))
    cerita += [kop, Spacer(1, 10), P("Laporan Kepatuhan Bulanan Pengelolaan Sisa Pangan", st_judul)]
    cerita.append(tabel_dua([
        ("Mitra", f"{nama} ({p['jenis']})"),
        ("Area", p["area"]),
        ("Rute penjemputan", p["rute"]),
        ("Periode", "Agustus 2027 (penjemputan 2 sampai 28 Agustus)"),
        ("ID Sertifikat QR", sertifikat),
    ]))

    cerita.append(P("Ringkasan berat", st_bagian))
    cerita.append(tabel_dua([
        ("Ampas kopi dijemput", f"{angka(d['kopi_total'])} kg"),
        ("Sisa dapur dijemput", f"{angka(d['dapur_total'])} kg"),
        ("Total bahan masuk", f"{angka(d['masuk_total'])} kg"),
        ("Bahan ditolak inspeksi", f"{angka(d['ditolak_total'])} kg ({angka(d['persen_tolak'])}%)"),
        ("Total dialihkan dari TPA", f"{angka(d['dialihkan'])} kg"),
    ]))

    cerita.append(P("Estimasi emisi (CO<sub>2</sub>e)".replace("<sub>", "").replace("</sub>", ""), st_bagian))
    cerita.append(tabel_dua([
        ("Emisi kotor dihindari", f"{angka(d['kotor'])} kg CO2e"),
        ("Emisi bersih dihindari", f"{angka(d['bersih'])} kg CO2e"),
    ]))

    status = Table([[P("STATUS KEPATUHAN: Patuh - Terverifikasi QR", ParagraphStyle("st", parent=st_sel_b, textColor=hutan, fontSize=10))]], colWidths=[17 * cm])
    status.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), muda), ("BOX", (0, 0), (-1, -1), 0.8, daun),
                                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    cerita += [Spacer(1, 8), status]

    baris = [[P(x, st_sel_b) for x in ("Tanggal", "Ampas kopi (kg)", "Sisa dapur (kg)", "Ditolak (kg)", "Status kualitas")]]
    for _, r in df.iterrows():
        baris.append([
            P(tgl_pendek(pd.to_datetime(r["tanggal"]).date())), P(angka(r["kopi"], 1)), P(angka(r["dapur"], 1)),
            P(angka(r["ditolak"], 1)), P(str(r["status"])),
        ])
    riwayat = Table(baris, colWidths=[3.6 * cm, 3.4 * cm, 3.4 * cm, 3.0 * cm, 3.6 * cm], repeatRows=1)
    riwayat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), muda),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, abu]),
        ("GRID", (0, 0), (-1, -1), 0.4, garis),
        ("ALIGN", (1, 0), (3, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    cerita.append(KeepTogether([P("Riwayat penjemputan", st_bagian), riwayat]))

    cerita.append(KeepTogether([
        P("Metode perhitungan", st_bagian),
        P(f"Emisi kotor = W layak x EF TPA. Emisi bersih = W layak x (EF TPA - EF kompos). EF TPA = {angka(EF_TPA, 4)} kg CO2e/kg "
          f"(proksi US EPA, 2024). EF kompos = {angka(EF_KOMPOS, 2)} kg CO2e/kg (IPCC, 2006). Angka merupakan estimasi, bukan kredit karbon."),
        Spacer(1, 8),
        P("Dokumen ini adalah simulasi untuk presentasi Carbon 2026. Seluruh data adalah data ilustrasi, bukan data nyata.", st_kecil),
    ]))

    def kaki(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B766F"))
        canvas.drawString(2 * cm, 1.2 * cm, "Balik Bumi - Tim Hore, Telkom University - Carbon 2026")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Halaman {doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.2 * cm, bottomMargin=1.7 * cm,
        title=f"Laporan Kepatuhan {nama} Agustus 2027", author="Balik Bumi",
    ).build(cerita, onFirstPage=kaki, onLaterPages=kaki)
    return buf.getvalue()


# ----------------------------------------------------------------------------
# Data simulasi operasional
# ----------------------------------------------------------------------------
RUTE_INFO = {
    "Rute 1": {"nama": "Dago - Dipatiukur - Riau", "mulai": (7, 30), "langkah": 15},
    "Rute 2": {"nama": "Braga - Asia Afrika - Pasirkaliki", "mulai": (8, 0), "langkah": 15},
    "Rute 3": {"nama": "Buahbatu - Setiabudi - Sukajadi", "mulai": (8, 30), "langkah": 20},
}

# Urutan titik jemput disusun mengikuti arah geografis rute. Lokasi dan koordinat adalah ilustrasi.
TITIK_JEMPUT = {
    "Rute 1": [
        "Kantin Dago Pakar", "Kedai Teras Dago Atas", "Kopi dan Roti Cisitu", "Roastery Simpang Dago",
        "Kopi Tuku-Tuku Dago", "Resto Dipatiukur 21", "Warung Kopi Dipatiukur Raya", "Kafe Riau Junction",
        "Bistro Riau Garden", "Rumah Makan Riau Sentosa",
    ],
    "Rute 2": [
        "Pasirkaliki Roast and Eat", "Warung Kopi Pasar Baru", "Kopi Braga Permai", "Bistro Braga Heritage",
        "Hotel Braga Lestari", "Kafe Naripan 12", "Kedai Asia Afrika 88", "Resto Alun-Alun Sentral",
        "Dapur Kota Lama",
    ],
    "Rute 3": [
        "Kedai Gegerkalong 5", "Hotel Setiabudi Permai", "Resto Setiabudi Garden", "Dapur Sukajadi Asri",
        "Sukajadi Cafe Rumahan", "Kafe Pasteur Rindang", "Hotel Cipaganti Asri", "Kopi Buahbatu Corner",
        "Bistro Buahbatu Hijau",
    ],
}

# Jumlah titik yang sudah selesai saat simulasi dimulai. Titik berikutnya tiap rute adalah mitra contoh dashboard.
SELESAI_AWAL = {"Rute 1": 4, "Rute 2": 3, "Rute 3": 6}

HUB = (-6.8905, 107.6157)  # Hub Balik Bumi, Dipatiukur (lokasi ilustrasi)

KOORDINAT = {
    "Kantin Dago Pakar": (-6.8628, 107.6322), "Kedai Teras Dago Atas": (-6.8702, 107.6205),
    "Kopi dan Roti Cisitu": (-6.8790, 107.6118), "Roastery Simpang Dago": (-6.8846, 107.6132),
    "Kopi Tuku-Tuku Dago": (-6.8870, 107.6138), "Resto Dipatiukur 21": (-6.8893, 107.6168),
    "Warung Kopi Dipatiukur Raya": (-6.8928, 107.6172), "Kafe Riau Junction": (-6.9068, 107.6182),
    "Bistro Riau Garden": (-6.9088, 107.6150), "Rumah Makan Riau Sentosa": (-6.9102, 107.6118),
    "Pasirkaliki Roast and Eat": (-6.9085, 107.5975), "Warung Kopi Pasar Baru": (-6.9150, 107.6035),
    "Kopi Braga Permai": (-6.9140, 107.6085), "Bistro Braga Heritage": (-6.9170, 107.6093),
    "Hotel Braga Lestari": (-6.9190, 107.6100), "Kafe Naripan 12": (-6.9195, 107.6128),
    "Kedai Asia Afrika 88": (-6.9212, 107.6105), "Resto Alun-Alun Sentral": (-6.9218, 107.6068),
    "Dapur Kota Lama": (-6.9235, 107.6042),
    "Kedai Gegerkalong 5": (-6.8615, 107.5915), "Hotel Setiabudi Permai": (-6.8685, 107.5965),
    "Resto Setiabudi Garden": (-6.8745, 107.5985), "Dapur Sukajadi Asri": (-6.8880, 107.5925),
    "Sukajadi Cafe Rumahan": (-6.8935, 107.5945), "Kafe Pasteur Rindang": (-6.8978, 107.5968),
    "Hotel Cipaganti Asri": (-6.9035, 107.5988), "Kopi Buahbatu Corner": (-6.9418, 107.6322),
    "Bistro Buahbatu Hijau": (-6.9498, 107.6352),
}


@st.cache_data(show_spinner=False)
def data_rute():
    rs = np.random.RandomState(5)
    baris = []
    for kode, info in RUTE_INFO.items():
        jam0, menit0 = info["mulai"]
        for i, nama in enumerate(TITIK_JEMPUT[kode]):
            total_menit = jam0 * 60 + menit0 + i * info["langkah"]
            jam, menit = divmod(total_menit, 60)
            if "Hotel" in nama:
                berat = int(rs.randint(120, 151))
            elif any(k in nama for k in ("Resto", "Bistro", "Rumah Makan", "Dapur")):
                berat = int(rs.randint(45, 81))
            else:
                berat = int(rs.randint(20, 46))
            lat, lon = KOORDINAT[nama]
            baris.append(
                {
                    "rute": kode,
                    "urut": i + 1,
                    "Nama Mitra": nama,
                    "Zona Rute": f"{kode}: {info['nama']}",
                    "Jadwal": f"{jam:02d}.{menit:02d} WIB",
                    "Estimasi Berat (kg)": berat,
                    "lat": lat,
                    "lon": lon,
                    "awal": i < SELESAI_AWAL[kode],
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


# ----------------------------------------------------------------------------
# Simulasi kurir, QR bin, dan peta rute (data hidup disimpan di st.session_state)
# ----------------------------------------------------------------------------
BIN_JENIS = [("Ampas kopi", "KOPI"), ("Sisa dapur", "DAPUR")]
HARI_SIMULASI = date(2027, 8, 30)  # Senin
HARI_SIMULASI_TEKS = "Senin, 30 Agustus 2027"
WARNA_RUTE = {"Rute 1": DAUN, "Rute 2": AMBER, "Rute 3": KOPI}
WARNA_STATUS = {"Selesai": HUTAN, "Dalam perjalanan": AMBER, "Menunggu": "#9CA3AF"}
WARNA_KURIR = "#2563EB"
TEMUAN = [
    "Tidak ada temuan", "Tercampur sedotan plastik", "Tulang besar dan cangkang",
    "Kantong plastik dan tisu", "Sisa busuk melebihi batas mutu", "Tercampur kemasan saus sachet",
]


def _susun_kode():
    kode = {n: v["kode"] for n, v in MITRA.items()}
    for rute, daftar in TITIK_JEMPUT.items():
        for i, n in enumerate(daftar):
            kode.setdefault(n, f"R{rute[-1]}{i + 1:02d}")
    return kode


KODE_MITRA = _susun_kode()
NAMA_DARI_KODE = {v: k for k, v in KODE_MITRA.items()}


def init_state():
    ss = st.session_state
    ss.setdefault("selesai_live", [])  # nama mitra yang sudah dijemput lewat simulasi kurir
    ss.setdefault("log_scan", [])  # satu baris per bin yang dipindai
    ss.setdefault("log_titik", [])  # satu baris per titik jemput selesai
    ss.setdefault("scan_ok", {})
    ss.setdefault("hasil_bin", {})
    ss.setdefault("kurir_stop", None)
    ss.setdefault("kam_hash", None)
    ss.setdefault("kam_pesan", None)
    ss.setdefault("notif_selesai", None)


def reset_sim():
    ss = st.session_state
    for k in list(ss.keys()):
        if k.startswith(("w_", "t_", "c_", "kam_")):
            del ss[k]
    ss["selesai_live"] = []
    ss["log_scan"] = []
    ss["log_titik"] = []
    ss["scan_ok"] = {}
    ss["hasil_bin"] = {}
    ss["kurir_stop"] = None
    ss["kam_hash"] = None
    ss["kam_pesan"] = None
    ss["notif_selesai"] = None


# ---- QR bin -----------------------------------------------------------------
def payload_bin(kode, kode_bin):
    return f"BB-BIN-{kode}-{kode_bin}-01"


def baca_payload(teks):
    bagian = (teks or "").strip().split("-")
    if len(bagian) == 5 and bagian[0] == "BB" and bagian[1] == "BIN":
        return bagian[2], bagian[3]
    return None


@st.cache_data(show_spinner=False)
def qr_uri(payload):
    return segno.make(payload, error="q").png_data_uri(scale=6, border=2, dark="#0B1F16", light="#FFFFFF")


@st.cache_data(show_spinner=False)
def qr_png(payload):
    buf = io.BytesIO()
    segno.make(payload, error="q").save(buf, kind="png", scale=14, border=3, dark="#0B1F16", light="#FFFFFF")
    return buf.getvalue()


def decode_qr(data):
    """Baca QR dari foto kamera. Mengembalikan (teks atau None, apakah pembaca tersedia)."""
    try:
        import cv2
    except Exception:
        return None, False
    gambar = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if gambar is None:
        return None, True
    teks, _, _ = cv2.QRCodeDetector().detectAndDecode(gambar)
    return (teks or None), True


# ---- Status rute hidup ---------------------------------------------------------
def rute_status():
    df = data_rute().copy()
    df["Status Penjemputan"] = "Menunggu"
    selesai = set(st.session_state["selesai_live"])
    for kode in RUTE_INFO:
        sudah = False
        for i in df.index[df["rute"] == kode]:
            if df.at[i, "awal"] or df.at[i, "Nama Mitra"] in selesai:
                status = "Selesai"
            elif not sudah:
                status = "Dalam perjalanan"
                sudah = True
            else:
                status = "Menunggu"
            df.at[i, "Status Penjemputan"] = status
    return df


def gabung_live(d, nama):
    """Gabungkan hasil scan kurir (sesi ini) ke data dashboard mitra."""
    baris_live = [r for r in st.session_state.get("log_titik", []) if r["mitra"] == nama]
    d2 = dict(d)
    d2["n_live"] = len(baris_live)
    if not baris_live:
        return d2
    df = d["df"].copy()
    tambahan = pd.DataFrame(
        [
            {
                "tanggal": HARI_SIMULASI,
                "minggu": int(df["minggu"].max()) + 1,
                "kopi": r["kopi"],
                "dapur": r["dapur"],
                "masuk": round(r["kopi"] + r["dapur"], 1),
                "ditolak": r["ditolak"],
                "status": r["status"],
                "catatan": r["catatan"],
            }
            for r in baris_live
        ]
    )
    df = pd.concat([df, tambahan], ignore_index=True)
    masuk_total = float(df["masuk"].sum())
    ditolak_total = float(df["ditolak"].sum())
    dialihkan = masuk_total - ditolak_total
    d2.update(
        df=df,
        kopi_total=float(df["kopi"].sum()),
        dapur_total=float(df["dapur"].sum()),
        masuk_total=masuk_total,
        ditolak_total=ditolak_total,
        dialihkan=dialihkan,
        persen_tolak=ditolak_total / masuk_total * 100,
        kotor=dialihkan * EF_TPA,
        bersih=dialihkan * EF_BERSIH,
        mingguan=df.groupby("minggu")[["kopi", "dapur"]].sum().reset_index(),
        berat_bulanan=[dialihkan * f for f in FAKTOR_BULANAN],
        co2_bulanan=[dialihkan * f * EF_BERSIH for f in FAKTOR_BULANAN],
    )
    return d2


def status_kualitas(tolak, masuk):
    rasio = tolak / masuk if masuk else 0.0
    if tolak == 0 or rasio <= BATAS_TOLAK / 100:
        return "Lolos"
    if rasio <= 0.06:
        return "Lolos dengan catatan"
    return "Perlu perbaikan pemilahan"


# ---- Peta rute ------------------------------------------------------------------
def _zoom(lats, lons, lebar, tinggi):
    span_lat = max(max(lats) - min(lats), 0.004)
    span_lon = max(max(lons) - min(lons), 0.004)
    z_lon = np.log2(360 * lebar / 512 / (span_lon * 1.35))
    z_lat = np.log2(360 * tinggi / 512 / (span_lat * 1.35))
    return float(np.clip(min(z_lon, z_lat), 10.0, 15.5))


def peta_rute(df, rute=None, sorot=None, tinggi=520, lebar=900):
    daftar = [rute] if rute else list(RUTE_INFO)
    ada_scattermap = hasattr(go, "Scattermap")
    SP = go.Scattermap if ada_scattermap else go.Scattermapbox
    kunci = "map" if ada_scattermap else "mapbox"
    fig = go.Figure()
    semua_lat, semua_lon = [HUB[0]], [HUB[1]]

    for kode in daftar:
        sub = df[df["rute"] == kode].sort_values("urut")
        titik = [HUB] + list(zip(sub["lat"], sub["lon"])) + [HUB]
        n_selesai = int((sub["Status Penjemputan"] == "Selesai").sum())
        lewat, sisa = titik[: n_selesai + 1], titik[n_selesai:]
        warna = WARNA_RUTE[kode]
        semua_lat += list(sub["lat"])
        semua_lon += list(sub["lon"])
        if len(lewat) > 1:
            fig.add_trace(
                SP(lat=[t[0] for t in lewat], lon=[t[1] for t in lewat], mode="lines",
                   line=dict(width=5, color=warna), legendgroup=kode, showlegend=False, hoverinfo="skip")
            )
        fig.add_trace(
            SP(lat=[t[0] for t in sisa], lon=[t[1] for t in sisa], mode="lines", opacity=0.5,
               line=dict(width=3, color=warna), legendgroup=kode, showlegend=(rute is None),
               name=f"{kode}: {RUTE_INFO[kode]['nama']}", hoverinfo="skip")
        )

    if sorot is not None:
        baris = df[df["Nama Mitra"] == sorot]
        fig.add_trace(
            SP(lat=baris["lat"], lon=baris["lon"], mode="markers", showlegend=False, hoverinfo="skip",
               marker=dict(size=46, color="rgba(217,119,6,0.30)"))
        )

    fig.add_trace(
        SP(lat=[HUB[0]], lon=[HUB[1]], mode="markers+text", text=["H"], textposition="middle center",
           textfont=dict(color="#FFFFFF", size=12), marker=dict(size=26, color="#3B2A20"),
           name="Hub Balik Bumi (Dipatiukur)", hovertext=["Hub Balik Bumi, Dipatiukur"], hoverinfo="text")
    )
    for status, warna in WARNA_STATUS.items():
        sub = df[(df["rute"].isin(daftar)) & (df["Status Penjemputan"] == status)]
        if sub.empty:
            continue
        hover = [
            f"<b>{r['Nama Mitra']}</b><br>Titik {r['urut']} · {r['rute']}<br>Jadwal {r['Jadwal']}<br>"
            f"Estimasi {r['Estimasi Berat (kg)']} kg<br>{r['Status Penjemputan']}"
            for _, r in sub.iterrows()
        ]
        fig.add_trace(
            SP(lat=sub["lat"], lon=sub["lon"], mode="markers+text", text=sub["urut"].astype(str),
               textposition="middle center", textfont=dict(color="#FFFFFF", size=11),
               marker=dict(size=30 if status == "Dalam perjalanan" else 22, color=warna),
               name=status, hovertext=hover, hoverinfo="text")
        )

    # posisi kurir: di antara titik terakhir yang selesai dan titik berikutnya
    kur_lat, kur_lon, kur_teks = [], [], []
    for kode in daftar:
        sub = df[df["rute"] == kode].sort_values("urut")
        n_selesai = int((sub["Status Penjemputan"] == "Selesai").sum())
        if n_selesai >= len(sub):
            continue
        asal = HUB if n_selesai == 0 else (sub.iloc[n_selesai - 1]["lat"], sub.iloc[n_selesai - 1]["lon"])
        tujuan = (sub.iloc[n_selesai]["lat"], sub.iloc[n_selesai]["lon"])
        kur_lat.append(asal[0] + 0.45 * (tujuan[0] - asal[0]))
        kur_lon.append(asal[1] + 0.45 * (tujuan[1] - asal[1]))
        kur_teks.append(f"Kurir {kode[-1]}")
    if kur_lat:
        fig.add_trace(
            SP(lat=kur_lat, lon=kur_lon, mode="markers+text", text=kur_teks, textposition="top center",
               textfont=dict(color=WARNA_KURIR, size=12), marker=dict(size=16, color=WARNA_KURIR),
               name="Kurir (simulasi)", hovertext=kur_teks, hoverinfo="text")
        )

    fig.update_layout(
        **{kunci: dict(style="open-street-map",
                       center=dict(lat=float(np.mean([min(semua_lat), max(semua_lat)])),
                                   lon=float(np.mean([min(semua_lon), max(semua_lon)]))),
                       zoom=_zoom(semua_lat, semua_lon, lebar, tinggi))},
        height=tinggi,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.88)", font=dict(size=11, family="Inter, sans-serif")),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(family="Inter, sans-serif", color=HUTAN)),
    )
    return fig


# ---- Aksi kurir (callback tombol) -------------------------------------------------
def pindai_bin(jenis, payload):
    ss = st.session_state
    ss["scan_ok"][jenis] = True
    ss["kam_pesan"] = ("ok", f"QR terbaca: {payload}")


def simpan_bin(jenis, nama, kode_rute, jadwal):
    ss = st.session_state
    berat = float(ss[f"w_{nama}_{jenis}"])
    tolak = min(float(ss[f"t_{nama}_{jenis}"]), berat)
    temuan = ss[f"c_{nama}_{jenis}"]
    kb = dict(BIN_JENIS)[jenis]
    ss["hasil_bin"][jenis] = {"berat": berat, "ditolak": tolak, "temuan": temuan}
    ss["kam_pesan"] = None
    ss["log_scan"].append(
        {
            "Jadwal": jadwal, "Mitra": nama, "Bin": jenis, "ID QR": payload_bin(KODE_MITRA[nama], kb),
            "Berat (kg)": berat, "Ditolak (kg)": tolak, "Rute": kode_rute,
        }
    )


def selesaikan_titik(nama, kode_rute, jadwal):
    ss = st.session_state
    kopi, dapur = ss["hasil_bin"]["Ampas kopi"], ss["hasil_bin"]["Sisa dapur"]
    masuk = kopi["berat"] + dapur["berat"]
    tolak = round(kopi["ditolak"] + dapur["ditolak"], 1)
    catatan = []
    for jenis, hasil in (("ampas kopi", kopi), ("sisa dapur", dapur)):
        if hasil["ditolak"] > 0:
            catatan.append(f"{hasil['temuan']} {angka(hasil['ditolak'], 1)} kg ({jenis})")
    ss["log_titik"].append(
        {
            "mitra": nama, "rute": kode_rute, "jadwal": jadwal, "kopi": round(kopi["berat"], 1),
            "dapur": round(dapur["berat"], 1), "ditolak": tolak,
            "status": status_kualitas(tolak, masuk),
            "catatan": "; ".join(catatan) if catatan else "Tidak ada temuan (dicatat via scan QR)",
        }
    )
    ss["selesai_live"].append(nama)
    ss["scan_ok"] = {}
    ss["hasil_bin"] = {}
    ss["kurir_stop"] = None
    ss["kam_pesan"] = None
    ss["kam_hash"] = None
    ss["notif_selesai"] = (
        f"{nama} selesai dijemput: {angka(masuk, 1)} kg tercatat lewat scan QR. "
        f"Data langsung masuk ke Dashboard Mitra dan peta rute di Dashboard Operasional."
    )


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
            Kota Bandung setiap Senin, Kamis, dan Sabtu. Setiap penjemputan ditimbang dan dipindai lewat kode QR, sehingga
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
        st.button("Coba Simulasi Kurir (Scan QR)", key="hero_kurir", on_click=pindah_halaman, args=(HAL_KURIR,))
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
        ("Dapur Lebih Bersih dan Higienis", "Penjemputan rutin 3x seminggu (Senin, Kamis, Sabtu) mencegah bau dan lindi menumpuk di area dapur."),
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
        ("02", "Jemput dan Timbang Digital", "Kurir menjemput Senin, Kamis, dan Sabtu, lalu mencatat berat per kategori dengan memindai kode QR."),
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
            <div class="bb-rumus-isi">W layak × (EF TPA − EF kompos)</div></div>
            <p style="color:#44504A;line-height:1.6;">W layak adalah berat bahan yang diterima dan diolah. EF TPA = {angka(EF_TPA, 4)} kg CO₂e per kg
            (proksi US EPA, 2024). EF kompos = {angka(EF_KOMPOS, 2)} kg CO₂e per kg (IPCC, 2006). Faktor EPA berasal dari kondisi TPA di
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
    h('<div class="bb-h2">Bayar per kilogram yang kami olah, makin besar volume makin murah.</div>')
    contoh_kafe = biaya_layanan(12 * HARI_PER_BULAN, True)
    hotel_kg = 500 * HARI_PER_BULAN
    hotel_efektif = biaya_layanan(hotel_kg, True) / hotel_kg
    p_kiri, p_kanan = st.columns(2, gap="medium")
    with p_kiri:
        h(
            f"""
            <div class="bb-gelap"><h4>Tarif berjenjang per kg</h4>
            <div class="bb-harga">Rp1.493<span style="font-size:1.2rem;font-weight:500;"> /kg</span></div>
            <p style="margin-top:8px;">Kontrak 3 tahun, 0 sampai 400 kg per bulan. Tarif dihitung per tingkat: Rp1.393 untuk
            401 sampai 1.500 kg dan Rp896 untuk di atas 1.500 kg. Tanpa kontrak (tarif promosi): Rp1.598, Rp1.491, dan Rp959.</p>
            <p style="margin-top:8px;">Contoh: kafe 12 kg per hari sekitar {rupiah(round(contoh_kafe, -3))} per bulan. Hotel 500 kg per hari
            efektif sekitar {rupiah(round(hotel_efektif))} per kg.</p>
            <p style="margin-top:8px;">Sudah termasuk bin berlabel QR, jemput terjadwal Senin, Kamis, Sabtu, penimbangan digital, dan laporan bulanan.</p></div>
            """
        )
    with p_kanan:
        h(
            f"""
            <div class="bb-card" style="border:2px solid {AMBER};"><span class="bb-badge bb-badge-amber">Promo Pilot</span>
            <h4 style="margin-top:12px;font-size:1.5rem;">Diskon 50% di 3 bulan pertama</h4>
            <p>Untuk 10 mitra pilot pertama di Bandung. Pilot menguji kesediaan membayar, volume per mitra, dan rendemen kompos
            sebelum perluasan ke 55 mitra pada bulan ke-24.</p>
            <p style="margin-top:8px;">Kontrak 3 tahun: tarif lebih murah, jadwal tetap, dan tong khusus anti bau.</p></div>
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
        proposal Carbon 2026 dan bukan data operasional nyata.</span>
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
        promo = c2.radio("Jalur Harga (diskon pilot 50% di 3 bulan pertama)", [JALUR_KONTRAK, JALUR_PROMO])
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
    biaya_normal = biaya_layanan(bulanan_kg, promo == JALUR_KONTRAK)
    biaya_pilot = biaya_normal * 3 * 0.5
    hemat = biaya_normal * 3 - biaya_pilot
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
                "Nama usaha", "Jenis usaha", "Penanggung jawab", "WhatsApp", "Lokasi", "Volume", "Jalur harga",
            ],
            "Isian": [
                nama_usaha.strip(), jenis, nama_pic.strip(), wa.strip(),
                f"{alamat.strip() + ', ' if alamat.strip() else ''}{kecamatan}, Bandung",
                f"{angka(volume, 0)} kg per hari", promo,
            ],
        }
    )
    tabel(ringkasan)
    s1, s2, s3 = st.columns(3)
    with s1:
        h(kartu_metrik("Biaya layanan normal per bulan", rupiah(biaya_normal), f"{angka(bulanan_kg, 0)} kg, efektif Rp{angka(biaya_normal / bulanan_kg, 0)}/kg (tarif berjenjang)"))
    with s2:
        h(kartu_metrik("Estimasi biaya 3 bulan pilot", rupiah(biaya_pilot), f"Diskon pilot 50%, hemat {rupiah(hemat)}", warna=AMBER))
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

    d = gabung_live(data_mitra(nama), nama)
    p = d["profil"]
    h(
        f"""
        <div style="margin:14px 0 10px 0;color:#44504A;font-size:0.95rem;">
        <b style="color:{HUTAN};">{nama}</b> · {p['jenis']} · {p['area']} · {p['rute']} · Periode Agustus 2027
        </div>
        """
    )

    tab_beranda, tab_jemput, tab_qr, tab_laporan = st.tabs(["Beranda", "Penjemputan", "Bin QR", "Laporan & CO₂e"])

    with tab_beranda:
        if d["n_live"]:
            st.success(
                f"Data terbaru dari scan QR kurir sudah masuk ke dashboard ini ({d['n_live']} penjemputan dari simulasi kurir)."
            )
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
                    x=[b.replace(" 20", " ") for b in d["bulan_label"]], y=np.round(kum_berat, 1), name="Akumulasi sampah dialihkan (kg)",
                    mode="lines+markers", line=dict(color=DAUN, width=3), marker=dict(size=8),
                    hovertemplate="%{x}<br>Dialihkan: %{y:,.1f} kg<extra></extra>",
                ),
                secondary_y=False,
            )
            fig2.add_trace(
                go.Scatter(
                    x=[b.replace(" 20", " ") for b in d["bulan_label"]], y=np.round(kum_co2, 1), name="Akumulasi CO₂e bersih (kg)",
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
            <p style="margin-top:4px;">PDF berisi ringkasan berat, bahan ditolak, estimasi CO₂e, faktor emisi, dan ID sertifikat QR. Excel berisi data tiap penjemputan.</p></div>
            """
        )
        u1, u2 = st.columns(2)
        with u1:
            try:
                st.download_button(
                    "Unduh Laporan Kepatuhan Bulanan (.pdf)", data=laporan_pdf(nama, d),
                    file_name=f"laporan_kepatuhan_{p['kode']}_2027-08.pdf", mime="application/pdf",
                    key=f"unduh_pdf_{p['kode']}", type="primary",
                )
            except Exception as e:
                st.caption(f"Laporan PDF belum tersedia ({type(e).__name__}). Pastikan reportlab ada di requirements.txt.")
        with u2:
            try:
                st.download_button(
                    "Unduh Data Penjemputan (.xlsx)", data=laporan_xlsx(nama, d),
                    file_name=f"data_penjemputan_{p['kode']}_2027-08.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"unduh_xlsx_{p['kode']}",
                )
            except Exception as e:
                st.caption(f"Data Excel belum tersedia ({type(e).__name__}). Pastikan openpyxl ada di requirements.txt.")

    with tab_jemput:
        j1, j2 = st.columns([1, 1.4], gap="medium")
        with j1:
            h(
                f"""
                <div class="bb-gelap"><div style="font-size:0.85rem;color:#CFE3D6;">Jadwal Penjemputan Berikutnya</div>
                <div style="font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.9rem;color:#FFFFFF;line-height:1.15;margin:6px 0;">{"Kamis, 2 September 2027" if d["n_live"] else "Senin, 30 Agustus 2027"}</div>
                <p>Pukul 08.00–10.00 WIB · {p['rute']}</p>
                <p style="margin-top:8px;">Jadwal tetap: Senin, Kamis, Sabtu. Siapkan dua bin berlabel QR: ampas kopi dan sisa dapur.</p></div>
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
        rdf = rute_status()
        kode_rute = p["rute"].split(" (")[0]
        sub_rute = rdf[rdf["rute"] == kode_rute].sort_values("urut")
        saya = sub_rute[sub_rute["Nama Mitra"] == nama].iloc[0]
        selesai_rute = int((sub_rute["Status Penjemputan"] == "Selesai").sum())
        if saya["Status Penjemputan"] == "Selesai":
            judul_lacak = "Penjemputan hari ini selesai"
            ket_lacak = "Berat tiap bin sudah tercatat lewat scan QR dan masuk ke laporan."
        else:
            sisa_titik = int(((sub_rute["urut"] < saya["urut"]) & (sub_rute["Status Penjemputan"] != "Selesai")).sum())
            judul_lacak = "Kurir menuju lokasimu" if sisa_titik == 0 else f"Kurir {sisa_titik} titik lagi dari lokasimu"
            ket_lacak = f"Perkiraan tiba sekitar {saya['Jadwal']}. Siapkan dua bin berlabel QR."
        l1, l2 = st.columns([1, 1.7], gap="medium")
        with l1:
            h(
                f"""
                <div class="bb-card"><div class="bb-metrik-label">Lacak kurir · simulasi {HARI_SIMULASI_TEKS}</div>
                <div class="bb-metrik-nilai" style="font-size:1.5rem;">{judul_lacak}</div>
                {bar_progres(selesai_rute / len(sub_rute) * 100)}
                <div class="bb-metrik-ket">{selesai_rute} dari {len(sub_rute)} titik di {kode_rute} sudah selesai</div>
                <p style="margin-top:10px;">{ket_lacak}</p></div>
                """
            )
            st.button("Buka Simulasi Kurir (Scan QR)", key="mitra_ke_kurir", on_click=pindah_halaman, args=(HAL_KURIR,))
        with l2:
            grafik(peta_rute(rdf, rute=kode_rute, sorot=nama, tinggi=360, lebar=620), f"mitra_peta_{p['kode']}", scroll=True)
        st.caption("Peta dan garis rute adalah ilustrasi (garis lurus antartitik), bukan rute jalan sebenarnya.")
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

    with tab_qr:
        h('<div style="font-weight:600;color:#1B4332;font-size:1.1rem;margin-bottom:4px;">Label QR pada bin kamu</div>')
        st.caption(
            "Setiap mitra memiliki dua bin berlabel QR. Kurir memindai label saat penjemputan, lalu berat dan hasil inspeksi "
            "tersimpan ke akun ini dan masuk ke laporan bulanan."
        )
        q1, q2 = st.columns(2, gap="medium")
        for kolom, (jenis, kb), warna in zip((q1, q2), BIN_JENIS, (KOPI, DAUN)):
            payload = payload_bin(p["kode"], kb)
            with kolom:
                h(
                    f"""
                    <div class="bb-qr-card" style="border-top:6px solid {warna};">
                    <div class="bb-metrik-label">Bin {jenis.lower()}</div>
                    <img src="{qr_uri(payload)}" width="190">
                    <div style="font-weight:600;color:{HUTAN};">{nama}</div>
                    <div class="bb-metrik-ket">ID label: {payload}</div></div>
                    """
                )
                st.download_button(
                    f"Unduh label QR bin {jenis.lower()} (.png)", data=qr_png(payload),
                    file_name=f"label_qr_{p['kode']}_{kb.lower()}.png", mime="image/png",
                    key=f"unduh_qr_{p['kode']}_{kb}",
                )
        st.write("")
        h(
            """
            <div class="bb-card"><h4>Alur scan</h4>
            <p>1. Pilah ke dua bin berlabel. 2. Kurir memindai QR bin saat jemput. 3. Berat dan inspeksi tersimpan ke akunmu.
            4. Angka masuk ke dashboard dan laporan kepatuhan bulanan.</p></div>
            """
        )
        st.write("")
        st.button("Coba scan di Simulasi Kurir", key="mitra_qr_ke_kurir", on_click=pindah_halaman, args=(HAL_KURIR,), type="primary")
        riwayat = []
        kode_rute_qr = p["rute"].split(" (")[0]
        for _, r in d["df"].sort_values("tanggal", ascending=False).head(6).iterrows():
            sumber = "Scan live (simulasi kurir)" if r["tanggal"] == HARI_SIMULASI else "Riwayat simulasi"
            for jenis, kb in BIN_JENIS:
                riwayat.append(
                    {
                        "Tanggal": tgl_pendek(r["tanggal"]),
                        "Bin": jenis,
                        "ID QR dipindai": payload_bin(p["kode"], kb),
                        "Berat (kg)": angka(r["kopi"] if kb == "KOPI" else r["dapur"], 1),
                        "Dicatat oleh": f"Kurir {kode_rute_qr}",
                        "Sumber": sumber,
                    }
                )
        h('<div style="font-weight:600;color:#1B4332;margin:14px 0 6px 0;">Riwayat scan terbaru</div>')
        tabel(pd.DataFrame(riwayat))

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
            h(kartu_metrik("Emisi transportasi jemput", f"{angka(transport, 1)} kg", f"Asumsi ilustrasi {angka(EF_TRANSPORT, 2)} kg CO₂e/kg", warna=AMBER))
        with c4:
            h(kartu_metrik("Emisi CO₂e bersih dihindari", f"{angka(bersih, 1)} kg", "W layak × (EF TPA − EF kompos)", warna=HUTAN, latar="#D8F3DC"))
        st.caption(
            f"Catatan: emisi bersih mengikuti rumus proposal. Jika emisi transportasi ilustrasi turut dikurangkan, "
            f"emisi bersih menjadi {angka(bersih - transport, 1)} kg CO₂e. Faktor EPA berasal dari kondisi TPA di Amerika Serikat, "
            f"dan angka ini adalah estimasi, bukan kredit karbon."
        )
        fig3 = go.Figure(
            go.Bar(
                x=["Emisi kotor (jika ke TPA)", "Emisi proses pengomposan", "Emisi transportasi (asumsi)", "Emisi CO₂e bersih dihindari"],
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
        h('<span class="bb-label-ilustrasi">Data ilustrasi operasional &amp; proyeksi finansial proposal</span>')
    with atas[1]:
        st.write("")
        st.button("Kembali ke Landing Page", key="ops_kembali", on_click=pindah_halaman, args=("Landing Page",))
    h(
        """
        <div style="margin:14px 0 10px 0;color:#44504A;font-size:0.95rem;">
        Tampilan internal tim Balik Bumi · Metrik bulanan: Februari 2028 (bulan ke-12 skenario dasar) · Tab Rute &amp; Jemput terhubung langsung dengan Simulasi Kurir
        </div>
        """
    )

    tab_beranda, tab_rute, tab_produksi, tab_keuangan, tab_tim = st.tabs(
        ["Beranda", "Rute & Jemput", "Produksi", "Keuangan", "🔒 Ruang Tim"]
    )

    with tab_beranda:
        armada = VOLUME_HARIAN_HUB / (2 * 800) * 100
        operator = VOLUME_HARIAN_HUB / (3 * 400) * 100
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
                <div class="bb-metrik-ket">Kapasitas terpasang: 2 sopir dan 3 operator</div></div>
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
        rute_df = rute_status()
        kolom_rute = st.columns(3, gap="medium")
        for kolom, (kode, info) in zip(kolom_rute, RUTE_INFO.items()):
            sub = rute_df[rute_df["rute"] == kode]
            selesai = int((sub["Status Penjemputan"] == "Selesai").sum())
            total = len(sub)
            posisi = f"kurir menuju titik ke-{selesai + 1}" if selesai < total else "semua titik selesai"
            with kolom:
                h(
                    f"""
                    <div class="bb-card"><div style="font-weight:600;color:{HUTAN};">{kode}: {info['nama']}</div>
                    <div class="bb-metrik-nilai" style="font-size:1.6rem;margin-top:6px;">{selesai} dari {total} titik</div>
                    {bar_progres(selesai / total * 100)}
                    <div class="bb-metrik-ket">{angka(selesai / total * 100, 0)}% selesai · {posisi}</div></div>
                    """
                )
        st.write("")
        pilihan = st.selectbox("Filter rute", ["Semua rute"] + [f"{k}: {v['nama']}" for k, v in RUTE_INFO.items()], key="filter_rute")
        kode_filter = None if pilihan == "Semua rute" else pilihan.split(":")[0]
        h(f'<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Peta titik jemput hari ini · simulasi {HARI_SIMULASI_TEKS}</div>')
        grafik(peta_rute(rute_df, rute=kode_filter, tinggi=540, lebar=1000), "ops_peta", scroll=True)
        st.caption(
            "Titik bernomor menunjukkan urutan jemput dan warnanya menunjukkan status. Lokasi mitra dan garis rute adalah ilustrasi "
            "(garis lurus antartitik, bukan rute jalan). Status berubah langsung saat kurir menyelesaikan titik di Simulasi Kurir."
        )
        tampil = rute_df if kode_filter is None else rute_df[rute_df["rute"] == kode_filter]
        total_berat = int(tampil["Estimasi Berat (kg)"].sum())
        tampil = tampil[["rute", "urut", "Nama Mitra", "Jadwal", "Estimasi Berat (kg)", "Status Penjemputan"]].copy()
        tampil.insert(0, "Zona Rute", tampil.pop("rute"))
        tampil = tampil.rename(columns={"urut": "Urutan"})
        tampil["Estimasi Berat (kg)"] = tampil["Estimasi Berat (kg)"].map(lambda x: angka(x, 0))
        h(f'<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Titik jemput hari ini ({HARI_SIMULASI_TEKS.split(",")[0]})</div>')
        tabel(tampil.reset_index(drop=True), tinggi=420)
        st.caption(
            f"Total estimasi berat pada tampilan ini {angka(total_berat, 0)} kg. Volume harian hub dihitung rata-rata 7 hari, "
            f"sehingga hari penjemputan (Senin, Kamis, Sabtu) lebih besar dari rata-rata harian."
        )
        h('<div style="font-weight:600;color:#1B4332;margin:14px 0 6px 0;">Aktivitas scan QR terbaru dari kurir</div>')
        if st.session_state["log_scan"]:
            log = pd.DataFrame(st.session_state["log_scan"]).iloc[::-1].reset_index(drop=True)
            log["Berat (kg)"] = log["Berat (kg)"].map(lambda x: angka(x, 1))
            log["Ditolak (kg)"] = log["Ditolak (kg)"].map(lambda x: angka(x, 1))
            tabel(log)
        else:
            st.info("Belum ada scan pada sesi ini. Buka Simulasi Kurir untuk memindai QR bin dan melihat peta serta tabel ini berubah.")
            st.button("Buka Simulasi Kurir (Scan QR)", key="ops_ke_kurir", on_click=pindah_halaman, args=(HAL_KURIR,), type="primary")

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
        k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
        with k1:
            h(kartu_metrik("Investasi awal", '<span class="bb-kecil">±Rp141 jt</span>', "Armada, mesin, area kompos, deposit", warna=KOPI))
        with k2:
            h(kartu_metrik("BEP operasional", '<span class="bb-kecil">Bulan 10</span>', "Skenario dasar", warna=HUTAN, latar="#D8F3DC"))
        with k3:
            h(kartu_metrik("Payback", '<span class="bb-kecil">Bulan 32</span>', "Kas kumulatif kembali positif", warna=HUTAN, latar="#D8F3DC"))
        with k4:
            h(kartu_metrik("Dana puncak", '<span class="bb-kecil">±Rp235 jt</span>', "Bulan 11, sudah memuat modal kerja Rp22,6 jt", warna=AMBER))
        with k5:
            h(kartu_metrik("ROI tahun ke-3", '<span class="bb-kecil">±57%</span>', "Laba tahun 3 Rp120,3 jt ÷ total dana Rp212,2 jt"))
        st.write("")
        tahun = ["Tahun 1", "Tahun 2", "Tahun 3"]
        pendapatan = [218.5, 577.6, 751.9]
        biaya_op = [236.9, 432.8, 589.3]
        ebitda = [-18.3, 144.8, 162.6]
        laba = [-37.6, 111.0, 120.3]
        kas = [-90.1, 135.7, 147.8]
        c_kiri, c_kanan = st.columns([1.3, 1], gap="medium")
        with c_kiri:
            fig = go.Figure()
            fig.add_bar(name="Pendapatan", x=tahun, y=pendapatan, marker_color=DAUN,
                        hovertemplate="%{x}<br>Pendapatan: Rp%{y:,.1f} juta<extra></extra>")
            fig.add_bar(name="Biaya operasional", x=tahun, y=biaya_op, marker_color=KOPI,
                        hovertemplate="%{x}<br>Biaya: Rp%{y:,.1f} juta<extra></extra>")
            fig.add_trace(go.Scatter(
                name="Laba bersih", x=tahun, y=laba, mode="lines+markers",
                line=dict(color=AMBER, width=3), marker=dict(size=9),
                hovertemplate="%{x}<br>Laba bersih: Rp%{y:,.1f} juta<extra></extra>"))
            fig.add_hline(y=0, line_dash="dash", line_color=BORDER)
            fig.update_layout(barmode="group", yaxis_title="Juta rupiah")
            grafik(gaya(fig, "Proyeksi keuangan skenario dasar (Rp juta per tahun)"), "ops_keu_tahun")
        with c_kanan:
            def fmt(v):
                return ("−" if v < 0 else "") + angka(abs(v), 1)
            tabel(pd.DataFrame({
                "Rp juta": ["Pendapatan", "Biaya operasional", "EBITDA", "Laba bersih", "Arus kas bersih"],
                "Tahun 1": [fmt(v[0]) for v in (pendapatan, biaya_op, ebitda, laba, kas)],
                "Tahun 2": [fmt(v[1]) for v in (pendapatan, biaya_op, ebitda, laba, kas)],
                "Tahun 3": [fmt(v[2]) for v in (pendapatan, biaya_op, ebitda, laba, kas)],
            }))
            st.caption("Akumulasi laba bersih 3 tahun Rp193,6 juta. Total gaji lapangan ±Rp526 juta selama 36 bulan sudah masuk biaya operasional.")

        h('<div class="bb-bagian" style="margin-top:26px;">Ketahanan terhadap risiko</div>')
        h('<div style="font-weight:600;color:#1B4332;margin:4px 0 6px 0;">Seberapa sensitif hasil terhadap tarif, volume, dan biaya?</div>')
        tabel(pd.DataFrame({
            "Skenario": [
                "Tarif kontrak turun 10%",
                "Batas bawah tarif kontrak kafe",
                "Volume resto dan hotel 30 kg/hari (asumsi 41)",
                "Biaya naik 5% per tahun, tarif terkunci 3 tahun",
                "Tanpa pelet (regulasi belum jelas)",
            ],
            "Dampak": [
                "Payback lewat 36 bulan",
                "±Rp1.426/kg. Turun lebih dari 4,5%, payback lewat 36 bulan",
                "Payback lewat 36 bulan",
                "Kas bulan 36 turun Rp21 juta",
                "Payback tetap ±bulan 32",
            ],
        }))
        st.caption(
            "Asumsi: tarif kontrak Rp1.493 / 1.393 / 896 per kg, diskon pilot 50% bulan 1–3, pengurus tanpa honor. "
            "Tarif final ditetapkan setelah wawancara kesediaan membayar dan pilot."
        )

    with tab_tim:
        ruang_tim()


def _kata_sandi_tim():
    try:
        return str(st.secrets["RUANG_TIM_SANDI"])
    except Exception:
        return "balikbumi2027"


def _kunci_tim():
    st.session_state["tim_terbuka"] = False


def ruang_tim():
    if not st.session_state.get("tim_terbuka"):
        h(
            f"""
            <div class="bb-card" style="max-width:560px;border-top:4px solid {KOPI};">
            <div style="font-size:2rem;">🔒</div>
            <h4 style="margin-top:6px;">Ruang Tim</h4>
            <p>Khusus tiga pendiri Balik Bumi: materi strategi, pasar, tarif, dan pendanaan. Masukkan kata sandi untuk membuka.</p></div>
            """
        )
        with st.form("form_tim"):
            sandi = st.text_input("Kata sandi", type="password")
            masuk = st.form_submit_button("Buka Ruang Tim", type="primary")
        if masuk:
            import hmac
            if hmac.compare_digest(sandi.encode("utf-8"), _kata_sandi_tim().encode("utf-8")):
                st.session_state["tim_terbuka"] = True
                st.rerun()
            else:
                st.error("Kata sandi salah.")
        return

    atas = st.columns([4, 1.2])
    with atas[0]:
        h('<span class="bb-badge bb-badge-amber">🔒 Internal: hanya pendiri</span>')
    with atas[1]:
        st.button("Kunci kembali", key="tim_kunci", on_click=_kunci_tim)
    st.write("")

    t_saing, t_pasar, t_tarif, t_dana = st.tabs(["Keunggulan vs pesaing", "Pasar", "Tarif berjenjang", "Struktur pendanaan"])

    # 1. Keunggulan vs pesaing
    with t_saing:
        h('<div class="bb-h2" style="font-size:1.6rem;">Pesaing dan respons Balik Bumi</div>')
        pesaing = [
            ("Waste4Change", "Langsung", "B2B di 19–21 kota; ada pusat pemulihan material di Bandung",
             "Fokus layanan organik lokal, rute padat, tarif berjenjang"),
            ("Pemkot Bandung (DLH, rumah maggot)", "Langsung / mitra", "Rumah maggot dan TPS Gedebage, tetapi pelaku usaha diminta mengelola mandiri",
             "Jadi mitra: tampung overflow dan beli produk"),
            ("Pegiat maggot (Magalarva, Biomagg, komunitas Bandung)", "Tidak langsung", "Berbasis Bogor dan Depok serta komunitas lokal; ada keluhan bau",
             "Fase 2 dengan SOP bau; kemitraan overflow"),
            ("Plastavfall, Rekosistem", "Tidak langsung", "Daur ulang anorganik; Plastavfall sudah punya jemput berlangganan untuk komersial",
             "Fokus organik; potensi kerja sama"),
            ("Kelola mandiri (hotel besar)", "Substitusi", "Mengolah sendiri", "Paket Resto &amp; Hotel dengan laporan"),
        ]
        baris = "".join(
            f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td style='color:#1B4332;font-weight:600;'>{d}</td></tr>"
            for a, b, c, d in pesaing
        )
        h(f"<table class='bb-tabel-saing'><tr><th>Pesaing</th><th>Jenis</th><th>Posisi mereka</th><th>Respons Balik Bumi</th></tr>{baris}</table>")
        st.caption("Referensi global: Reground, Compost RVA (diskon volume), Winnow, TreeDots.")
        h('<div class="bb-h2" style="font-size:1.6rem;margin-top:18px;">Cara kami unggul</div>')
        u1, u2, u3 = st.columns(3, gap="medium")
        keunggulan = [
            ("1", "Dua paket, tarif berjenjang", "Kafe kecil masuk dengan biaya ringan dan pilot. Resto dan hotel mendapat harga volume dan laporan."),
            ("2", "Layanan lokal yang andal", "Rute padat tiga kali per minggu, bin QR, timbang digital. Ampas kopi relatif homogen sehingga olahan konsisten."),
            ("3", "Kemitraan, bukan perang", "PHRI Jabar untuk akses hotel, DLH untuk legitimasi, rumah maggot untuk menampung overflow."),
        ]
        for kolom, (no, judul, isi) in zip((u1, u2, u3), keunggulan):
            with kolom:
                h(f'<div class="bb-card"><div class="bb-angka-langkah">KEUNGGULAN {no}</div><h4>{judul}</h4><p>{isi}</p></div>')
        st.caption("Laporan CO₂e adalah nilai tambah untuk mitra besar, bukan alasan utama kafe memilih Balik Bumi.")

    # 2. Pasar
    with t_pasar:
        h('<div class="bb-h2" style="font-size:1.6rem;">Pasar luas, target kami 55 mitra</div>')
        p1, p2, p3 = st.columns(3, gap="medium")
        with p1:
            h(kartu_metrik("TAM", "874 ton/hari", "Seluruh sampah organik kawasan komersial Bandung. Rp464 M per tahun secara teoretis", warna=KOPI))
        with p2:
            h(kartu_metrik("SAM", "131,1 ton/hari", "Horeka dalam jangkauan rute hub, ≥10 kg/hari, mau memilah. Rp70 M per tahun", warna=DAUN))
        with p3:
            h(kartu_metrik("SOM", "1,095 ton/hari", "Target realistis bulan 24: 55 mitra. Rp581 juta per tahun, 0,84% dari SAM", warna=HUTAN, latar="#D8F3DC"))
        st.write("")
        q1, q2, q3 = st.columns(3, gap="medium")
        with q1:
            h(f'<div class="bb-card"><span class="bb-badge bb-badge-hijau">Paket Kafe</span><h4 style="margin-top:10px;">40 kafe spesialti</h4><p>±12 kg per hari. Tarif Rp1.493/kg lewat kontrak, masuk dengan biaya ringan dan pilot.</p></div>')
        with q2:
            h(f'<div class="bb-card"><span class="bb-badge bb-badge-amber">Paket Resto &amp; Hotel</span><h4 style="margin-top:10px;">15 resto dan hotel</h4><p>Rata-rata ±41 kg per hari. Tarif turun per volume, hotel 500 kg/hari efektif ±Rp948/kg.</p></div>')
        with q3:
            h(f'<div class="bb-card"><span class="bb-badge bb-badge-abu">Pembeli produk</span><h4 style="margin-top:10px;">Petani, toko tanaman, Pemkot</h4><p>Kompos Rp2.000/kg. Pelet uji coba Rp4.000/kg.</p></div>')
        fig = go.Figure(go.Bar(
            x=["Bulan 3", "Bulan 6", "Bulan 12", "Bulan 18", "Bulan 24"], y=[10, 16, 29, 42, 55],
            marker_color=DAUN, text=[10, 16, 29, 42, 55], textposition="outside",
            hovertemplate="%{x}<br>%{y} mitra aktif<extra></extra>",
        ))
        fig.update_layout(yaxis_title="Mitra aktif", yaxis_range=[0, 65])
        grafik(gaya(fig, "Target mitra aktif: ±2 mitra baru per bulan (40 kafe + 15 resto/hotel)", tinggi=320), "tim_mitra")

    # 3. Tarif berjenjang
    with t_tarif:
        h('<div class="bb-h2" style="font-size:1.6rem;">Dua jalur harga, dihitung per tingkat (Rp per kg)</div>')
        tabel(pd.DataFrame({
            "Volume per bulan": ["0–400 kg", "401–1.500 kg", "Di atas 1.500 kg"],
            "Kontrak 3 tahun (terkunci)": [f"Rp{angka(t, 0)}" for t in TARIF_KONTRAK],
            "Tanpa kontrak (promosi)": [f"Rp{angka(t, 0)}" for t in TARIF_PROMO],
        }))
        st.caption("Pilot 10 mitra: diskon 50% di 3 bulan pertama. Kontrak 3 tahun: tarif lebih murah, jadwal tetap, tong khusus anti bau.")
        h('<div style="font-weight:600;color:#1B4332;margin:14px 0 6px 0;">Kalkulator tarif</div>')
        kg_hari = st.slider("Volume sisa pangan (kg per hari)", 5, 600, 12, 1, key="tim_kg_hari")
        kg_bulan = kg_hari * HARI_PER_BULAN
        b_kontrak = biaya_layanan(kg_bulan, True)
        b_promo = biaya_layanan(kg_bulan, False)
        r1, r2, r3 = st.columns(3, gap="medium")
        with r1:
            h(kartu_metrik("Kontrak 3 tahun", rupiah(round(b_kontrak, -3)) + "/bln", f"Efektif ±Rp{angka(b_kontrak / kg_bulan, 0)}/kg", warna=HUTAN, latar="#D8F3DC"))
        with r2:
            h(kartu_metrik("Tanpa kontrak", rupiah(round(b_promo, -3)) + "/bln", f"Efektif ±Rp{angka(b_promo / kg_bulan, 0)}/kg", warna=AMBER))
        with r3:
            h(kartu_metrik("Selisih per tahun", rupiah(round((b_promo - b_kontrak) * 12, -3)), "Penghematan jika kontrak 3 tahun", warna=KOPI))
        h(
            f"""
            <div class="bb-card" style="margin-top:14px;border-left:4px solid {AMBER};">
            <b>Batas bawah tarif ±Rp1.426/kg.</b> Tarif kontrak kafe turun lebih dari 4,5% membuat payback melewati 36 bulan.
            Tarif final menunggu wawancara kesediaan membayar (5–10 kafe dan resto) dan pilot.</div>
            """
        )

    # 4. Struktur pendanaan
    with t_dana:
        h('<div class="bb-h2" style="font-size:1.6rem;">Struktur pendanaan: mencari investor</div>')
        d1, d2, d3 = st.columns(3, gap="medium")
        with d1:
            h(kartu_metrik("Tahap 1: sebelum operasi", "±Rp141 jt", "Armada, mesin, area kompos, deposit", warna=KOPI))
        with d2:
            h(kartu_metrik("Tahap 2: bulan 4–11", "±Rp94 jt", "Pelet, Viar, deposit, dan modal kerja", warna=AMBER))
        with d3:
            h(kartu_metrik("Dana puncak (bulan 11)", "±Rp235 jt", "Tahap 1 + tahap 2; titik terendah kas", warna=HUTAN, latar="#D8F3DC"))
        fig = go.Figure()
        fig.add_bar(name="Tahap 1 (sebelum operasi)", y=["Kebutuhan dana"], x=[141], orientation="h", marker_color=KOPI,
                    text=["±Rp141 jt"], textposition="inside",
                    hovertemplate="Tahap 1: Rp141 juta<extra></extra>")
        fig.add_bar(name="Tahap 2 (bulan 4–11)", y=["Kebutuhan dana"], x=[94], orientation="h", marker_color=AMBER,
                    text=["±Rp94 jt"], textposition="inside",
                    hovertemplate="Tahap 2: Rp94 juta<extra></extra>")
        fig.update_layout(barmode="stack", xaxis_title="Juta rupiah", yaxis=dict(showticklabels=False))
        grafik(gaya(fig, "Dua tahap, total ±Rp235 juta", tinggi=240), "tim_dana")
        e1, e2 = st.columns(2, gap="medium")
        with e1:
            h(
                f"""
                <div class="bb-card"><h4>Yang didapat investor</h4>
                <p>BEP operasional bulan 10, modal kembali (payback) bulan 32, ROI tahun ke-3 ±57%, akumulasi laba bersih 3 tahun Rp193,6 juta.</p></div>
                """
            )
        with e2:
            h(
                f"""
                <div class="bb-card"><h4>Komitmen pendiri</h4>
                <p>Honor pengurus <b>Rp0 sampai modal investor kembali</b> (bulan 32). Setelah itu honor Rp2 juta per orang per bulan, dibayar sebelum pembagian laba.
                Gaji tenaga lapangan penuh (UMK + 10%) sudah masuk biaya operasional.</p></div>
                """
            )


# ----------------------------------------------------------------------------
# HALAMAN 4: Simulasi aplikasi kurir (scan QR bin)
# ----------------------------------------------------------------------------
def halaman_kurir():
    ss = st.session_state
    atas = st.columns([4, 1.3])
    with atas[0]:
        h('<h1 style="margin:0;font-size:2.2rem;">Simulasi Aplikasi Kurir</h1>')
        h('<span class="bb-label-ilustrasi">Alur scan QR bin · data ilustrasi</span>')
    with atas[1]:
        st.write("")
        st.button("Kembali ke Landing Page", key="kurir_kembali", on_click=pindah_halaman, args=("Landing Page",))
    h(
        f"""
        <div style="margin:14px 0 10px 0;color:#44504A;font-size:0.95rem;">
        Hari jemput simulasi: <b style="color:{HUTAN};">{HARI_SIMULASI_TEKS}</b>. Pilih rute, pindai QR kedua bin di titik jemput,
        isi berat hasil timbang, lalu selesaikan titik. Hasilnya langsung tampil di Dashboard Mitra dan peta di Dashboard Operasional.
        </div>
        """
    )
    if ss.get("notif_selesai"):
        st.success(ss["notif_selesai"])
        ss["notif_selesai"] = None

    rute_df = rute_status()
    pilih = st.selectbox("Rute kurir", [f"{k}: {v['nama']}" for k, v in RUTE_INFO.items()], key="rute_kurir")
    kode_rute = pilih.split(":")[0]
    sub = rute_df[rute_df["rute"] == kode_rute].sort_values("urut")
    belum = sub[sub["Status Penjemputan"] != "Selesai"]
    kiri, tengah, kanan = st.columns([1, 1.15, 1.35], gap="medium")

    if belum.empty:
        with tengah:
            st.success(f"Semua {len(sub)} titik di {kode_rute} sudah selesai dijemput. Pilih rute lain atau reset simulasi.")
            st.button("Lihat di Dashboard Operasional", key="kurir_ke_ops", on_click=pindah_halaman, args=("Dashboard Operasional",), type="primary")
        with kanan:
            grafik(peta_rute(rute_df, rute=kode_rute, tinggi=520, lebar=560), "kurir_peta_selesai", scroll=True)
        return

    titik = belum.iloc[0]
    nama = titik["Nama Mitra"]
    kode = KODE_MITRA[nama]
    jadwal = titik["Jadwal"]
    if ss["kurir_stop"] != nama:
        ss["kurir_stop"] = nama
        ss["scan_ok"] = {}
        ss["hasil_bin"] = {}
        ss["kam_pesan"] = None
        ss["kam_hash"] = None

    # ---- kiri: label QR bin di titik ini (untuk dipindai dari layar atau hasil cetak)
    with kiri:
        h('<div style="font-weight:600;color:#1B4332;margin-bottom:6px;">Label QR di titik ini</div>')
        for jenis, kb in BIN_JENIS:
            payload = payload_bin(kode, kb)
            h(
                f"""
                <div class="bb-qr-card" style="margin-bottom:10px;padding:12px;">
                <div class="bb-metrik-label">Bin {jenis.lower()} · {nama}</div>
                <img src="{qr_uri(payload)}" width="150">
                <div class="bb-metrik-ket">{payload}</div></div>
                """
            )
        st.caption("Arahkan kamera ke QR ini, atau tekan tombol Pindai di aplikasi kurir. QR dari mitra lain akan ditolak.")

    # ---- tengah: tampilan aplikasi kurir
    with tengah:
        with st.container(border=True):
            h(
                f"""
                <div class="bb-gelap" style="padding:18px 20px;">
                <div style="font-size:0.8rem;color:#CFE3D6;">Titik {int(titik['urut'])} dari {len(sub)} · {kode_rute}</div>
                <div class="bb-hp-judul">{nama}</div>
                <div class="bb-hp-ket">Jadwal {jadwal} · estimasi {angka(titik['Estimasi Berat (kg)'], 0)} kg</div></div>
                """
            )
            h(bar_progres((int(titik["urut"]) - 1) / len(sub) * 100))
            st.write("")

            with st.expander("Pindai dengan kamera (opsional)"):
                foto = st.camera_input("Arahkan kamera ke QR pada bin", key=f"kam_{nama}", label_visibility="collapsed")
                if foto is not None:
                    data = foto.getvalue()
                    sidik = hashlib.md5(data).hexdigest()
                    if ss["kam_hash"] != sidik:
                        ss["kam_hash"] = sidik
                        teks, tersedia = decode_qr(data)
                        if not tersedia:
                            ss["kam_pesan"] = ("info", "Pembaca kamera belum terpasang di server ini. Gunakan tombol Pindai.")
                        elif not teks:
                            ss["kam_pesan"] = ("warn", "QR belum terbaca. Dekatkan kamera dan pastikan QR terang dan tidak terpotong.")
                        else:
                            hasil = baca_payload(teks)
                            if not hasil:
                                ss["kam_pesan"] = ("error", f"Kode ini bukan label bin Balik Bumi: {teks}")
                            elif hasil[0] != kode:
                                pemilik = NAMA_DARI_KODE.get(hasil[0], "mitra lain")
                                ss["kam_pesan"] = ("error", f"QR ini milik {pemilik}, bukan titik ini ({nama}).")
                            else:
                                jenis_baca = "Ampas kopi" if hasil[1] == "KOPI" else "Sisa dapur"
                                ss["scan_ok"][jenis_baca] = True
                                ss["kam_pesan"] = ("ok", f"QR terbaca: {teks}. Bin {jenis_baca.lower()} milik {nama}.")
            if ss["kam_pesan"]:
                tipe, pesan = ss["kam_pesan"]
                {"ok": st.success, "error": st.error, "warn": st.warning, "info": st.info}[tipe](pesan)

            kopi_def, dapur_def = (
                (MITRA[nama]["kopi"], MITRA[nama]["dapur"]) if nama in MITRA
                else (round(titik["Estimasi Berat (kg)"] * 0.4, 1), round(titik["Estimasi Berat (kg)"] * 0.6, 1))
            )
            for jenis, kb in BIN_JENIS:
                payload = payload_bin(kode, kb)
                hasil = ss["hasil_bin"].get(jenis)
                st.markdown(f"**Bin {jenis.lower()}**")
                if hasil:
                    st.success(f"Tersimpan: {angka(hasil['berat'], 1)} kg ditimbang · {angka(hasil['ditolak'], 1)} kg ditolak")
                elif not ss["scan_ok"].get(jenis):
                    st.button(f"Pindai QR bin {jenis.lower()}", key=f"scan_{nama}_{kb}", on_click=pindai_bin, args=(jenis, payload))
                else:
                    st.caption(f"QR terbaca: {payload}")
                    c1, c2 = st.columns(2)
                    c1.number_input(
                        "Berat ditimbang (kg)", min_value=0.0, max_value=500.0, step=0.1, format="%.1f",
                        value=float(kopi_def if kb == "KOPI" else dapur_def), key=f"w_{nama}_{jenis}",
                    )
                    c2.number_input(
                        "Bahan ditolak (kg)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        value=0.0, key=f"t_{nama}_{jenis}",
                    )
                    st.selectbox("Temuan inspeksi", TEMUAN, key=f"c_{nama}_{jenis}")
                    st.button(
                        "Simpan penimbangan", key=f"simpan_{nama}_{kb}", type="primary",
                        on_click=simpan_bin, args=(jenis, nama, kode_rute, jadwal),
                    )

            if all(ss["hasil_bin"].get(j) for j, _ in BIN_JENIS):
                total = sum(v["berat"] for v in ss["hasil_bin"].values())
                tolak = sum(v["ditolak"] for v in ss["hasil_bin"].values())
                st.info(
                    f"Kedua bin tercatat: {angka(total, 1)} kg masuk, {angka(tolak, 1)} kg ditolak "
                    f"({angka(tolak / total * 100 if total else 0, 1)}%). Status kualitas: {status_kualitas(tolak, total)}."
                )
                st.button(
                    "Selesaikan titik dan lanjut", key="selesai_titik", type="primary",
                    on_click=selesaikan_titik, args=(nama, kode_rute, jadwal),
                )

    # ---- kanan: peta rute hidup
    with kanan:
        h('<div style="font-weight:600;color:#1B4332;margin-bottom:6px;">Peta rute · titik bersorot adalah tujuan kurir</div>')
        grafik(peta_rute(rute_df, rute=kode_rute, sorot=nama, tinggi=520, lebar=560), f"kurir_peta_{kode_rute}", scroll=True)
        st.caption("Lokasi dan garis rute adalah ilustrasi (garis lurus antartitik), bukan rute jalan sebenarnya.")


# ----------------------------------------------------------------------------
# Kendali utama
# ----------------------------------------------------------------------------
def main():
    if "nav_menu" not in st.session_state:
        st.session_state["nav_menu"] = HALAMAN[0]
    if "scroll_form" not in st.session_state:
        st.session_state["scroll_form"] = False
    init_state()
    render_sidebar()
    halaman = st.session_state["nav_menu"]
    st.session_state["halaman"] = halaman
    if halaman == HAL_KURIR:
        halaman_kurir()
    elif halaman == "Dashboard Mitra":
        halaman_mitra()
    elif halaman == "Dashboard Operasional":
        halaman_operasional()
    else:
        halaman_landing()


main()