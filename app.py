from datetime import datetime
import os
import tempfile
from fpdf import FPDF
from PIL import Image, ImageDraw
import streamlit as st
from streamlit_drawable_canvas import st_canvas

# 1. Seitenkonfiguration
st.set_page_config(
    page_title="Zählerprotokoll", page_icon="⚡", layout="centered"
)

# 2. Modernes CSS Styling einfügen
st.markdown(
    """
<style>
    /* Blendet das Streamlit-Menü und Footer aus */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        height: 3rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Hilfsfunktion für abgerundete Ecken am Logo
def add_rounded_corners(image_path, radius=20):
    img = Image.open(image_path).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)

    rounded_img = Image.new("RGBA", img.size)
    rounded_img.paste(img, (0, 0), mask=mask)
    return rounded_img


# 3. Klasse für das PDF-Layout mit grünem Rahmen
class ModernPDF(FPDF):

    def draw_page_border(self):
        self.set_draw_color(46, 125, 50)
        self.set_line_width(0.8)
        self.rect(4, 4, 202, 289, style="D")

    def header(self):
        self.draw_page_border()

        if self.page_no() == 1:
            logo_path = "kare_logo.png"
            if os.path.exists(logo_path):
                rounded_logo = add_rounded_corners(logo_path, radius=25)
                temp_logo_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ).name
                rounded_logo.save(temp_logo_path)

                self.image(temp_logo_path, x=35, y=10, w=140)
                self.ln(38)
            else:
                self.set_font("helvetica", "B", 10)
                self.cell(0, 5, "KARE-Immobilien Zählerprotokoll", 0, 1, "L")
                self.ln(5)
        else:
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.line(14, self.get_y() - 2, 196, self.get_y() - 2)
        self.cell(
            0,
            8,
            f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}  -  Seite {self.page_no()}",
            0,
            0,
            "C",
        )

    def chapter_title(self, title):
        self.ln(4)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(30, 41, 59)
        self.cell(0, 7, title, 0, 1, "L")
        self.set_draw_color(30, 41, 59)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 50, self.get_y())
        self.ln(4)


# --- ARCHIV-ORDNER INITIALISIEREN ---
ARCHIV_DIR = "archiv_protokolle"
if not os.path.exists(ARCHIV_DIR):
    os.makedirs(ARCHIV_DIR)

# Session State für die Archiv-Liste initialisieren
if "archiv_historie" not in st.session_state:
    st.session_state.archiv_historie = []
    if os.path.exists(ARCHIV_DIR):
        for f in sorted(os.listdir(ARCHIV_DIR), reverse=True):
            if f.endswith(".pdf"):
                file_path = os.path.join(ARCHIV_DIR, f)
                st.session_state.archiv_historie.append({
                    "name": f,
                    "pfad": file_path,
                    "zeit": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime("%d.%m.%Y %H:%M"),
                })


# --- SEITENLEISTE (ARCHIV & LÖSCH-LOGIK) ---
with st.sidebar:
    st.image(
        "kare_logo.png" if os.path.exists("kare_logo.png") else "", width=150
    )
    st.title("📂 Archiv & Menü")
    st.write(
        "Hier findest du alle im Archiv gespeicherten Protokolle zum Abruf oder zum Löschen."
    )
    st.divider()

    if not st.session_state.archiv_historie:
        st.info("Noch keine Protokolle im Archiv vorhanden.")
    else:
        # State-Variablen für Bestätigungsdialoge initialisieren
        if "delete_target" not in st.session_state:
            st.session_state.delete_target = None

        for index, item in enumerate(st.session_state.archiv_historie):
            st.markdown(f"**📄 {item['name']}**")
            st.caption(f"Erstellt am: {item['zeit']}")

            if os.path.exists(item["pfad"]):
                # Download-Button
                with open(item["pfad"], "rb") as pdf_file:
                    st.download_button(
                        label="📥 Herunterladen",
                        data=pdf_file,
                        file_name=item["name"],
                        mime="application/pdf",
                        key=f"dl_{index}_{item['name']}",
                    )

                # Löschen-Knopf
                if st.button("🗑️ Löschen", key=f"btn_del_{index}_{item['name']}"):
                    st.session_state.delete_target = item["name"]

                # Sicherheitsabfrage (erscheint direkt unter dem Protokoll, wenn angeklickt)
                if st.session_state.delete_target == item["name"]:
                    st.warning(
                        "Möchtest du dieses Protokoll wirklich unwiderruflich"
                        " löschen?"
                    )
                    col_y, col_n = st.columns(2)
                    with col_y:
                        if st.button(
                            "Ja", key=f"yes_{index}_{item['name']}"
                        ):
                            # Datei physisch löschen
                            if os.path.exists(item["pfad"]):
                                os.remove(item["pfad"])
                            # Aus Historie entfernen
                            st.session_state.archiv_historie.pop(index)
                            st.session_state.delete_target = None
                            st.success("Protokoll gelöscht!")
                            st.rerun()
                    with col_n:
                        if st.button(
                            "Nein", key=f"no_{index}_{item['name']}"
                        ):
                            st.session_state.delete_target = None
                            st.rerun()

            st.divider()


# --- HEADER BEREICH IN DER APP ---
logo_path = "kare_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=400)
else:
    st.warning(
        "⚠️ Hinweis: Die Datei 'kare_logo.png' wurde nicht im App-Ordner gefunden."
    )
    st.markdown(
        "<h1 style='text-align: center;'>⚡ KARE-Immobilien Zählerprotokoll</h1>",
        unsafe_allow_html=True,
    )

st.write("")

# --- ABSCHNITT 1: STAMMDATEN ---
with st.container(border=True):
    st.subheader("👤 1. Stammdaten")
    col1, col2 = st.columns(2)
    with col1:
        wohnung = st.text_input("Adresse der Wohnung (Straße, Hausnr.)")
        ort = st.text_input("Ort, PLZ")
        mieter = st.text_input("Name des Mieters")
    with col2:
        vermieter = st.text_input("Name des Vermieters", value="KARE-Immobilien")
        etage = st.text_input("Etage (z.B. 2. Obergeschoss)")
        datum = st.date_input(
            "Datum der Ablesung", format="DD.MM.YYYY", key="ablesung_datum"
        )

# --- ABSCHNITT 2: ZÄHLERSTÄNDE ---
with st.container(border=True):
    st.subheader("⚡ 2. Zählerstände")

    if "zaehler_liste" not in st.session_state:
        st.session_state.zaehler_liste = [
            {"typ": "Strom", "bezeichnung": "Strom Hauptzähler", "einheit": "kWh"},
            {"typ": "Wasser", "bezeichnung": "Wasser Hauptzähler", "einheit": "m³"},
            {"typ": "Heizung", "bezeichnung": "Heizung", "einheit": "Einheiten"},
        ]

    with st.expander("➕ Weiteren Zähler hinzufügen"):
        z_typ = st.selectbox(
            "Zählertyp",
            ["Strom", "Wasser", "Heizung", "Gas", "Sonstige"],
            key="select_z_typ",
        )
        z_bez = st.text_input("Bezeichnung (z.B. Küche, Bad)", key="neu_zaehler_bez")
        z_einheit = st.text_input(
            "Maßeinheit (z.B. kWh, m³, Liter)", value="kWh", key="neu_zaehler_einheit"
        )
        if st.button("Zähler hinzufügen", key="btn_add_z"):
            if z_bez:
                st.session_state.zaehler_liste.append({
                    "typ": z_typ,
                    "bezeichnung": z_bez,
                    "einheit": z_einheit,
                })
                st.rerun()

    zaehler_daten = []
    for i, z in enumerate(st.session_state.zaehler_liste):
        col_t, col_del = st.columns([5, 1])
        with col_t:
            st.write(f"**{z['typ']}** – {z['bezeichnung']}")
        with col_del:
            if st.button("❌", key=f"del_z_{i}", help="Zähler löschen"):
                st.session_state.zaehler_liste.pop(i)
                st.rerun()

        col_z1, col_z2 = st.columns(2)
        with col_z1:
            z_nr = st.text_input(
                "Zählernummer",
                key=f"z_nr_{i}",
                placeholder="Zählernummer eingeben...",
            )
        with col_z2:
            z_wert = st.number_input(
                f"Zählerstand ({z['einheit']})",
                value=0.000,
                format="%.3f",
                step=0.001,
                key=f"z_wert_{i}",
            )

        zaehler_daten.append({
            "typ": z["typ"],
            "bezeichnung": z["bezeichnung"],
            "nummer": z_nr,
            "stand": z_wert,
            "einheit": z["einheit"],
        })
        st.divider()

# --- ABSCHNITT 3: FOTODOKUMENTATION ---
with st.container(border=True):
    st.subheader("📸 3. Fotodokumentation (Zählerfotos)")
    uploaded_files = st.file_uploader(
        "Fotos der Zähler hochladen (mehrere möglich)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.write(f"Ausgewählte Fotos: **{len(uploaded_files)}**")
        cols = st.columns(3)
        for idx, uploaded_file in enumerate(uploaded_files):
            with cols[idx % 3]:
                st.image(
                    uploaded_file,
                    caption=f"Foto {idx+1}",
                    use_container_width=True,
                )

# --- ABSCHNITT 4: UNTERSCHRIFTEN ---
with st.container(border=True):
    st.subheader("✍️ 4. Unterschriften")
    st.write(
        "Bitte unterschreiben Sie mit dem Finger oder einem Stift direkt im Feld."
    )

    col_sig1, col_sig2 = st.columns(2)

    with col_sig1:
        st.write("**Vermieter (KARE)**")
        canvas_vermieter = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#f0f2f6",
            height=150,
            width=280,
            drawing_mode="freedraw",
            key="canvas_vermieter",
        )

    with col_sig2:
        st.write("**Mieter**")
        canvas_mieter = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#f0f2f6",
            height=150,
            width=280,
            drawing_mode="freedraw",
            key="canvas_mieter",
        )

st.write("")

# --- SPEICHERN BUTTON & PDF GENERIERUNG ---
if st.button(
    "📄 Protokoll generieren & im Archiv speichern",
    type="primary",
    use_container_width=True,
):
    if not wohnung or not mieter:
        st.error("Bitte fülle mindestens die Adresse und den Namen des Mieters aus!")
    else:
        # PDF Erstellung starten
        pdf = ModernPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)

        # Dokumententitel
        pdf.set_font("helvetica", "B", 15)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "ZÄHLERPROTOKOLL", 0, 1, "C")
        pdf.ln(5)

        # 1. Stammdaten
        pdf.chapter_title("1. Stammdaten")
        pdf.set_font("helvetica", size=10)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(45, 6, "Objektadresse:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(
            0,
            6,
            f"{wohnung.encode('latin-1', 'replace').decode('latin-1')}, {ort.encode('latin-1', 'replace').decode('latin-1')}",
            0,
            1,
        )

        pdf.set_font("helvetica", size=10)
        pdf.cell(45, 6, "Etage:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(
            0,
            6,
            etage.encode("latin-1", "replace").decode("latin-1")
            if etage
            else "-",
            0,
            1,
        )

        pdf.set_font("helvetica", size=10)
        pdf.cell(45, 6, "Mieter:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, mieter.encode("latin-1", "replace").decode("latin-1"), 0, 1)

        pdf.set_font("helvetica", size=10)
        pdf.cell(45, 6, "Vermieter:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(
            0, 6, vermieter.encode("latin-1", "replace").decode("latin-1"), 0, 1
        )

        pdf.set_font("helvetica", size=10)
        pdf.cell(45, 6, "Datum der Ablesung:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, datum.strftime("%d.%m.%Y"), 0, 1)
        pdf.ln(4)

        # 2. Zählerstände
        pdf.chapter_title("2. Zählerstände")
        pdf.set_font("helvetica", size=10)
        for z in zaehler_daten:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(30, 6, f"{z['typ']}:", 0, 0)
            pdf.set_font("helvetica", size=10)
            pdf.cell(70, 6, f"{z['bezeichnung']} (Nr: {z['nummer']})", 0, 0)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(
                0,
                6,
                f"Stand: {z['stand']:.3f} {z['einheit']}"
                .encode("latin-1", "replace")
                .decode("latin-1"),
                0,
                1,
            )
        pdf.ln(4)

        # 3. Fotos ins PDF einbetten (falls vorhanden)
        if uploaded_files:
            pdf.chapter_title("3. Fotodokumentation")
            pdf.set_font("helvetica", size=9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(
                0,
                5,
                "Übersicht der beigefügten Zählerfotos:",
                0,
                1,
                "L",
            )
            pdf.ln(2)

            x_start = 14
            y_start = pdf.get_y()
            img_width = 56
            img_height = 42
            x_gap = 6
            y_gap = 8

            current_x = x_start
            current_y = y_start

            for idx, uploaded_file in enumerate(uploaded_files):
                if current_y > 230:
                    pdf.add_page()
                    current_y = 20

                img = Image.open(uploaded_file)
                temp_img_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ).name
                img.convert("RGB").save(temp_img_path, "JPEG")

                pdf.image(
                    temp_img_path,
                    x=current_x,
                    y=current_y,
                    w=img_width,
                    h=img_height,
                )

                if (idx + 1) % 2 == 0:
                    current_x = x_start
                    current_y += img_height + y_gap
                else:
                    current_x += img_width + x_gap

            if len(uploaded_files) % 2 != 0:
                current_y += img_height + y_gap
            else:
                current_y += img_height + y_gap

            pdf.set_y(current_y)
            pdf.ln(4)

        # Permanenten Dateinamen im Archiv-Ordner erzeugen
        sauberer_mieter = "".join(
            c for c in mieter if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        filename = f"Zaehlerprotokoll_{sauberer_mieter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(ARCHIV_DIR, filename)

        # PDF lokal speichern
        pdf.output(file_path)

        # In Session-Historie eintragen
        st.session_state.archiv_historie.insert(
            0,
            {
                "name": filename,
                "pfad": file_path,
                "zeit": datetime.now().strftime("%d.%m.%Y %H:%M"),
            },
        )

        st.success(
            "Protokoll wurde erstellt und im Online-Archiv (Seitenleiste) gespeichert!"
        )
        st.balloons()
        st.rerun()
