from datetime import datetime
import json
import os
import tempfile
from fpdf import FPDF
from PIL import Image, ImageDraw
import streamlit as st
from streamlit_drawable_canvas import st_canvas

# 1. Seitenkonfiguration
st.set_page_config(
    page_title="Zählerprotokoll KARE",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 2. Modernes CSS Styling einfügen (lässt den Header normal sichtbar, damit der Standard-Pfeil wieder da ist)
st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
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


# --- DATENBANK & ARCHIV VERWALTUNG (PERSISTENT ÜBER JSON) ---
ARCHIV_DIR = "archiv_protokolle"
DB_FILE = "archiv_datenbank.json"
STRASSEN_FILE = "strassen_datenbank.json"

if not os.path.exists(ARCHIV_DIR):
    os.makedirs(ARCHIV_DIR)


def lade_json(datei, standard_wert):
    if os.path.exists(datei):
        try:
            with open(datei, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return standard_wert
    return standard_wert


def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)


# Session State initialisieren
if "archiv_historie" not in st.session_state:
    st.session_state.archiv_historie = lade_json(DB_FILE, [])

if "strassen_liste" not in st.session_state:
    standard_strassen = ["Talstraße 32"]
    geladene_strassen = lade_json(STRASSEN_FILE, standard_strassen)
    if "Talstraße 32" not in geladene_strassen:
        geladene_strassen.insert(0, "Talstraße 32")
    st.session_state.strassen_liste = geladene_strassen

if "delete_target" not in st.session_state:
    st.session_state.delete_target = None


# --- SEITENLEISTE (HIERARCHIE: Jahr > Straße > Etage) ---
with st.sidebar:
    st.image(
        "kare_logo.png" if os.path.exists("kare_logo.png") else "", width=150
    )
    st.title("📂 Archiv-Browser")
    st.write("Struktur: **Jahr ➔ Straße ➔ Etage**")
    st.divider()

    if not st.session_state.archiv_historie:
        st.info("Noch keine Protokolle im Archiv vorhanden.")
    else:
        # 1. Nach Jahren gruppieren
        jahre_dict = {}
        for item in st.session_state.archiv_historie:
            zeit_str = item.get("zeit", "")
            jahr = (
                zeit_str.split(".")[2][:4]
                if len(zeit_str) >= 10
                else str(datetime.now().year)
            )
            if jahr not in jahre_dict:
                jahre_dict[jahr] = []
            jahre_dict[jahr].append(item)

        for jahr in sorted(jahre_dict.keys(), reverse=True):
            with st.expander(f"📅 Jahr {jahr} ({len(jahre_dict[jahr])})"):
                # 2. Nach Straßen gruppieren
                strassen_dict = {}
                for item in jahre_dict[jahr]:
                    strasse = item.get("strasse", "Unbekannte Straße")
                    if strasse not in strassen_dict:
                        strassen_dict[strasse] = []
                    strassen_dict[strasse].append(item)

                for strasse, eintraege_strasse in strassen_dict.items():
                    st.markdown(f"📍 **{strasse}**")

                    # 3. Nach Etagen gruppieren
                    etagen_dict = {}
                    for item in eintraege_strasse:
                        etage = (
                            item.get("etage", "Keine Etage angegeben")
                            if item.get("etage")
                            else "Keine Etage angegeben"
                        )
                        if etage not in etagen_dict:
                            etagen_dict[etage] = []
                        etagen_dict[etage].append(item)

                    for etage, eintraege_etage in etagen_dict.items():
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏢 *{etage}*")
                        for item in eintraege_etage:
                            real_index = st.session_state.archiv_historie.index(
                                item
                            )
                            st.caption(
                                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;👤 {item['mieter']} ({item.get('zeit', '')})"
                            )

                            if os.path.exists(item["pfad"]):
                                col_dl, col_del = st.columns([1, 1])
                                with col_dl:
                                    with open(item["pfad"], "rb") as pdf_file:
                                        st.download_button(
                                            label="📥",
                                            data=pdf_file,
                                            file_name=item["name"],
                                            mime="application/pdf",
                                            key=f"dl_{real_index}_{item['name']}",
                                            help="PDF herunterladen",
                                        )
                                with col_del:
                                    if st.button(
                                        "🗑️",
                                        key=f"btn_del_{real_index}_{item['name']}",
                                        help="Protokoll löschen",
                                    ):
                                        st.session_state.delete_target = (
                                            item["name"]
                                        )

                                if (
                                    st.session_state.delete_target == item["name"]
                                ):
                                    st.warning("Wirklich löschen?")
                                    col_y, col_n = st.columns(2)
                                    with col_y:
                                        if st.button(
                                            "Ja",
                                            key=f"yes_{real_index}_{item['name']}",
                                        ):
                                            if os.path.exists(item["pfad"]):
                                                os.remove(item["pfad"])
                                            st.session_state.archiv_historie.pop(
                                                real_index
                                            )
                                            speichere_json(
                                                DB_FILE,
                                                st.session_state.archiv_historie,
                                            )
                                            st.session_state.delete_target = (
                                                None
                                            )
                                            st.success("Gelöscht!")
                                            st.rerun()
                                    with col_n:
                                        if st.button(
                                            "Nein",
                                            key=f"no_{real_index}_{item['name']}",
                                        ):
                                            st.session_state.delete_target = (
                                                None
                                            )
                                            st.rerun()
                            else:
                                st.error("Datei nicht gefunden.")
                    st.markdown("---")

    # --- STRASSEN VERWALTEN (VORSCHLÄGE LÖSCHEN) ---
    st.divider()
    with st.expander("⚙️ Straßen verwalten"):
        st.write(
            "Hier kannst du gespeicherte Straßen-Vorschläge aus der Liste"
            " entfernen:"
        )
        if not st.session_state.strassen_liste:
            st.info("Keine Straßen gespeichert.")
        else:
            for s_idx, s_name in enumerate(
                list(st.session_state.strassen_liste)
            ):
                col_s1, col_s2 = st.columns([3, 1])
                with col_s1:
                    st.text(s_name)
                with col_s2:
                    if st.button(
                        "❌",
                        key=f"del_str_{s_idx}",
                        help=f"Straße '{s_name}' aus Vorschlägen löschen",
                    ):
                        if s_name == "Talstraße 32":
                            st.warning(
                                "Hauptadresse kann nicht entfernt werden."
                            )
                        else:
                            st.session_state.strassen_liste.remove(s_name)
                            speichere_json(
                                STRASSEN_FILE, st.session_state.strassen_liste
                            )
                            st.success(f"'{s_name}' entfernt!")
                            st.rerun()


# --- HEADER BEREICH IN DER HÄUPTSEITE ---
logo_path = "kare_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=400)
else:
    st.warning("⚠️ Hinweis: Die Datei 'kare_logo.png' wurde nicht gefunden.")
    st.markdown(
        "<h1 style='text-align: center;'>⚡ KARE-Immobilien"
        " Zählerprotokoll</h1>",
        unsafe_allow_html=True,
    )

st.write("")

# --- ABSCHNITT 1: STAMMDATEN & STRASSEN-RUBRIK ---
with st.container(border=True):
    st.subheader("👤 1. Stammdaten & Straßen-Rubrik")

    dropdown_strassen = list(st.session_state.strassen_liste) + [
        "➕ Neue Straße hinzufügen..."
    ]

    col_str1, col_str2 = st.columns(2)
    with col_str1:
        strassen_auswahl = st.selectbox(
            "Straße (Rubrik-Auswahl)", dropdown_strassen
        )
        if strassen_auswahl == "➕ Neue Straße hinzufügen...":
            neue_strasse_input = st.text_input(
                "Geben Sie den Namen der neuen Straße ein:"
            )
            strasse = neue_strasse_input.strip()
            if (
                strasse
                and strasse not in st.session_state.strassen_liste
                and strasse != "➕ Neue Straße hinzufügen..."
            ):
                st.session_state.strassen_liste.append(strasse)
                speichere_json(STRASSEN_FILE, st.session_state.strassen_liste)
        else:
            strasse = strassen_auswahl

    with col_str2:
        ort = st.text_input("Ort, PLZ", value="07545 Gera")

    col1, col2 = st.columns(2)
    with col1:
        wohnung = st.text_input(
            "Genaue Adresse / Wohnung (z.B. Hausnr. 32, Whg 2)"
        )
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
    "📄 Protokoll generieren & permanent speichern",
    type="primary",
    use_container_width=True,
):
    if not wohnung or not mieter or not strasse:
        st.error(
            "Bitte fülle mindestens die Straße, die Objektadresse und den Namen"
            " des Mieters aus!"
        )
    else:
        pdf = ModernPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)

        pdf.set_font("helvetica", "B", 15)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "ZÄHLERPROTOKOLL", 0, 1, "C")
        pdf.ln(5)

        pdf.chapter_title("1. Stammdaten")
        pdf.set_font("helvetica", size=10)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(45, 6, "Straße / Rubrik:", 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(
            0,
            6,
            strasse.encode("latin-1", "replace").decode("latin-1"),
            0,
            1,
        )

        pdf.set_font("helvetica", size=10)
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

        if uploaded_files:
            pdf.chapter_title("3. Fotodokumentation")
            pdf.set_font("helvetica", size=9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(
                0, 5, "Übersicht der beigefügten Zählerfotos:", 0, 1, "L"
            )
            pdf.ln(2)

            x_start = 14
            y_start = pdf.get_y()            img_width = 56
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

        sauberer_mieter = "".join(
            c for c in mieter if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        filename = f"Zaehlerprotokoll_{sauberer_mieter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(ARCHIV_DIR, filename)

        pdf.output(file_path)

        neuer_eintrag = {
            "name": filename,
            "pfad": file_path,
            "strasse": strasse,
            "etage": etage if etage else "Keine Etage",
            "mieter": mieter,
            "zeit": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        st.session_state.archiv_historie.insert(0, neuer_eintrag)
        speichere_json(DB_FILE, st.session_state.archiv_historie)

        st.success(
            "Protokoll wurde erstellt und permanent im Archiv gespeichert!"
        )
        st.balloons()
        st.rerun()
