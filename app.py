import streamlit as st
import datetime
import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="KARE-Immobilien Wohnungsabnahmeprotokoll", page_icon="🏠", layout="centered")

st.markdown("<h2 style='text-align: center; color: #1e293b;'>KARE-Immobilien — Wohnungsabnahmeprotokoll</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b;'>Talstr. 32, 07545 Gera | Tel.: 0365 / 800 49 37 | E-Mail: Info@KARE-Immobilien.de</p>", unsafe_allow_html=True)
st.markdown("---")

st.subheader("1. Objektdaten & Vertragsparteien")
col1, col2 = st.columns(2)
with col1:
    objekt_anschrift = st.text_input("Anschrift des Objekts", "Musterstraße 1, 07545 Gera")
    vermieter = st.text_input("Vermieter / Vertreter", "KARE-Immobilien (Talstr. 32, Gera)")
    datum = st.date_input("Datum der Abnahme", datetime.date.today())
with col2:
    mieter_neu = st.text_input("Neuer Mieter", "")
    mieter_alt = st.text_input("Ausziehender Mieter", "")

st.subheader("2. Zählerstände")
meters = [
    "Kaltwasserzähler",
    "Warmwasserzähler",
    "Heizungszähler - Wohnzimmer",
    "Heizungszähler - Kinderzimmer",
    "Heizungszähler - Flur",
    "Heizungszähler - Bad",
    "Heizungszähler - Küche"
]

meter_data = []
for m in meters:
    cols = st.columns([2, 1, 1.5])
    with cols[0]:
        st.write(f"**{m}**")
    with cols[1]:
        nr = st.text_input("Zählernr.", key=f"nr_{m}", label_visibility="collapsed")
    with cols[2]:
        val = st.text_input("Stand", "0.0", key=f"val_{m}", label_visibility="collapsed")
    meter_data.append((m, nr, val))

st.subheader("3. Schlüsselübergabe")
keys = ["Haustürschlüssel", "Wohnungsschlüssel", "Kellerschlüssel", "Briefkastenschlüssel", "Garagenschlüssel"]
key_data = []
for k in keys:
    cols = st.columns([3, 1])
    with cols[0]:
        st.write(k)
    with cols[1]:
        count = st.number_input("Stück", min_value=0, value=0, key=f"key_{k}", label_visibility="collapsed")
    key_data.append((k, count))

st.subheader("4. Mängel, Zustand & Bemerkungen")
maengel = st.text_area("Erfasste Mängel / Vereinbarungen", "Keine gravierenden Mängel festgestellt. Zustand ordnungsgemäß.")

st.markdown("---")

if st.button("Protokoll als PDF generieren", type="primary", use_container_width=True):
    if not REPORTLAB_AVAILABLE:
        st.error("ReportLab ist in der Umgebung nicht installiert.")
    else:
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1e293b"), spaceAfter=6)
            subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=15)
            h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=6)
            body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14)

            story.append(Paragraph("KARE-Immobilien — Wohnungsabnahmeprotokoll", title_style))
            story.append(Paragraph("Talstr. 32, 07545 Gera | Tel.: 0365 / 800 49 37 | E-Mail: Info@KARE-Immobilien.de", subtitle_style))
            story.append(Spacer(1, 10))

            # 1. Objektdaten
            story.append(Paragraph("1. Objektdaten & Vertragsparteien", h2_style))
            data_p1 = [
                [Paragraph("<b>Objektanschrift:</b>", body_style), Paragraph(objekt_anschrift, body_style)],
                [Paragraph("<b>Vermieter:</b>", body_style), Paragraph(vermieter, body_style)],
                [Paragraph("<b>Neuer Mieter:</b>", body_style), Paragraph(mieter_neu, body_style)],
                [Paragraph("<b>Ausziehender Mieter:</b>", body_style), Paragraph(mieter_alt, body_style)],
                [Paragraph("<b>Datum:</b>", body_style), Paragraph(datum.strftime("%d.%m.%Y"), body_style)],
            ]
            t1 = Table(data_p1, colWidths=[150, 380])
            t1.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t1)
            story.append(Spacer(1, 10))

            # 2. Zählerstände
            story.append(Paragraph("2. Zählerstände", h2_style))
            t2_data = [["Zählerart", "Zählernummer", "Zählerstand"]] + [[m, nr, val] for m, nr, val in meter_data]
            t2 = Table(t2_data, colWidths=[200, 150, 180])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ]))
            story.append(t2)
            story.append(Spacer(1, 10))

            # 3. Schlüssel
            story.append(Paragraph("3. Schlüsselübergabe", h2_style))
            t3_data = [["Schlüsselart", "Anzahl"]] + [[k, str(c)] for k, c in key_data]
            t3 = Table(t3_data, colWidths=[330, 200])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ]))
            story.append(t3)
            story.append(Spacer(1, 10))

            # 4. Mängel
            story.append(Paragraph("4. Mängel, Zustand & Bemerkungen", h2_style))
            t4 = Table([[Paragraph(maengel, body_style)]], colWidths=[530])
            t4.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t4)
            story.append(Spacer(1, 30))

            # Unterschriften
            sig_data = [
                ["___________________________________", "___________________________________"],
                ["Unterschrift Vermietung / KARE", "Unterschrift Mieter"]
            ]
            t_sig = Table(sig_data, colWidths=[265, 265])
            t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('TOPPADDING', (0,0), (-1,-1), 4)]))
            story.append(t_sig)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            
            st.success("PDF erfolgreich erstellt!")
            st.download_button(
                label="📥 PDF herunterladen",
                data=pdf_bytes,
                file_name="Wohnungsabnahmeprotokoll.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Fehler bei der PDF-Generierung: {e}")
