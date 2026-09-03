# -*- coding: utf-8 -*-
"""
KARE-Immobilien Wohnungsabnahmeprotokoll Generator
Vollständiger Quellcode für die Tkinter-basierte Desktop-Anwendung.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class WohnungsabnahmeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KARE-Immobilien - Wohnungsabnahmeprotokoll")
        self.root.geometry("850x750")
        self.root.config(bg="#f4f6f9")

        # Header Frame
        header_frame = tk.Frame(root, bg="#1e293b", pady=15)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame, 
            text="KARE-Immobilien — Wohnungsabnahmeprotokoll", 
            font=("Arial", 16, "bold"), 
            fg="white", 
            bg="#1e293b"
        )
        title_label.pack()

        sub_label = tk.Label(
            header_frame, 
            text="Talstr. 32, 07545 Gera | Tel.: 0365 / 800 49 37 | E-Mail: Info@KARE-Immobilien.de", 
            font=("Arial", 9), 
            fg="#94a3b8", 
            bg="#1e293b"
        )
        sub_label.pack(pady=2)

        # Main Scrollable / Form Area using Canvas
        container = tk.Frame(root, bg="#f4f6f9")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        canvas = tk.Canvas(container, bg="#f4f6f9", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#f4f6f9")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill=tk.Y)

        self.create_form_fields()

        # Footer Button Frame
        btn_frame = tk.Frame(root, bg="#f4f6f9", pady=10)
        btn_frame.pack(fill=tk.X, padx=20)

        generate_btn = tk.Button(
            btn_frame, 
            text="Protokoll als PDF erstellen", 
            font=("Arial", 11, "bold"), 
            bg="#0284c7", 
            fg="white", 
            padx=15, 
            pady=8,
            command=self.generate_pdf
        )
        generate_btn.pack(side=tk.RIGHT)

        exit_btn = tk.Button(
            btn_frame, 
            text="Schließen", 
            font=("Arial", 11), 
            bg="#64748b", 
            fg="white", 
            padx=15, 
            pady=8,
            command=root.quit
        )
        exit_btn.pack(side=tk.LEFT)

    def create_form_fields(self):
        # 1. Objektdaten & Parteien
        self.add_section_header("1. Objektdaten & Vertragsparteien")
        
        self.entries = {}
        
        fields_part1 = [
            ("Anschrift des Objekts:", "objekt_anschrift", "Musterstraße 1, 07545 Gera"),
            ("Vermieter / Vertreter:", "vermieter", "KARE-Immobilien (Talstr. 32, Gera)"),
            ("Mieter (neu):", "mieter_neu", ""),
            ("Mieter (ausziehend / alt):", "mieter_alt", ""),
            ("Datum der Abnahme:", "datum", datetime.date.today().strftime("%d.%m.%Y"))
        ]

        for label_text, key, default in fields_part1:
            row = tk.Frame(self.scrollable_frame, bg="#f4f6f9")
            row.pack(fill=tk.X, pady=4)
            lbl = tk.Label(row, text=label_text, width=25, anchor="w", font=("Arial", 10), bg="#f4f6f9")
            lbl.pack(side=tk.LEFT)
            ent = tk.Entry(row, font=("Arial", 10), width=45)
            ent.insert(0, default)
            ent.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.entries[key] = ent

        # 2. Zählerstände
        self.add_section_header("2. Zählerstände")
        
        self.meter_entries = {}
        meters = [
            ("Kaltwasserzähler", "Zählerstand (m³)"),
            ("Warmwasserzähler", "Zählerstand (m³)"),
            ("Heizungszähler - Wohnzimmer", "Zählerstand / Ablesewert"),
            ("Heizungszähler - Kinderzimmer", "Zählerstand / Ablesewert"),
            ("Heizungszähler - Flur", "Zählerstand / Ablesewert"),
            ("Heizungszähler - Bad", "Zählerstand / Ablesewert"),
            ("Heizungszähler - Küche", "Zählerstand / Ablesewert")
        ]

        for meter_name, unit_label in meters:
            row = tk.Frame(self.scrollable_frame, bg="#f4f6f9")
            row.pack(fill=tk.X, pady=3)
            lbl = tk.Label(row, text=meter_name, width=28, anchor="w", font=("Arial", 10), bg="#f4f6f9")
            lbl.pack(side=tk.LEFT)
            
            ent_nr = tk.Entry(row, font=("Arial", 10), width=15)
            ent_nr.insert(0, "Zählernr.")
            ent_nr.pack(side=tk.LEFT, padx=5)

            ent_val = tk.Entry(row, font=("Arial", 10), width=20)
            ent_val.insert(0, "0.0")
            ent_val.pack(side=tk.LEFT, padx=5)
            
            self.meter_entries[meter_name] = (ent_nr, ent_val)

        # 3. Schlüsselübergabe
        self.add_section_header("3. Schlüsselübergabe")
        self.key_entries = {}
        key_types = ["Haustürschlüssel", "Wohnungsschlüssel", "Kellerschlüssel", "Briefkastenschlüssel", "Garagenschlüssel"]
        
        for kt in key_types:
            row = tk.Frame(self.scrollable_frame, bg="#f4f6f9")
            row.pack(fill=tk.X, pady=3)
            lbl = tk.Label(row, text=kt, width=28, anchor="w", font=("Arial", 10), bg="#f4f6f9")
            lbl.pack(side=tk.LEFT)
            
            ent_count = tk.Entry(row, font=("Arial", 10), width=10)
            ent_count.insert(0, "0")
            ent_count.pack(side=tk.LEFT, padx=5)
            tk.Label(row, text="Stück", font=("Arial", 10), bg="#f4f6f9").pack(side=tk.LEFT)

            self.key_entries[kt] = ent_count

        # 4. Mängel / Bemerkungen
        self.add_section_header("4. Mängel, Zustand & Bemerkungen")
        
        row = tk.Frame(self.scrollable_frame, bg="#f4f6f9")
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, text="Erfasste Mängel / Vereinbarungen:", font=("Arial", 10), bg="#f4f6f9", anchor="w").pack(anchor="w")
        
        self.text_maengel = tk.Text(self.scrollable_frame, font=("Arial", 10), height=6, width=70)
        self.text_maengel.pack(fill=tk.X, pady=5)
        self.text_maengel.insert(tk.END, "Keine gravierenden Mängel festgestellt. Zustand ordnungsgemäß.")

    def add_section_header(self, title):
        lbl = tk.Label(
            self.scrollable_frame, 
            text=title, 
            font=("Arial", 11, "bold"), 
            fg="#0f172a", 
            bg="#e2e8f0",
            anchor="w",
            padx=8,
            pady=4
        )
        lbl.pack(fill=tk.X, pady=(15, 5))

    def generate_pdf(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "Fehler", 
                "Die ReportLab-Bibliothek ist nicht installiert.\nBitte installieren Sie diese via 'pip install reportlab'."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dateien", "*.pdf")],
            initialfile="Wohnungsabnahmeprotokoll.pdf"
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor("#1e293b"),
                spaceAfter=6
            )

            subtitle_style = ParagraphStyle(
                'SubTitleStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor("#64748b"),
                spaceAfter=15
            )

            h2_style = ParagraphStyle(
                'H2Style',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor("#0f172a"),
                spaceBefore=10,
                spaceAfter=6
            )

            body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14)

            story.append(Paragraph("KARE-Immobilien — Wohnungsabnahmeprotokoll", title_style))
            story.append(Paragraph("Talstr. 32, 07545 Gera | Tel.: 0365 / 800 49 37 | E-Mail: Info@KARE-Immobilien.de", subtitle_style))
            story.append(Spacer(1, 10))

            # Part 1 Data
            story.append(Paragraph("1. Objektdaten & Vertragsparteien", h2_style))
            data_part1 = [
                [Paragraph(f"<b>{k}:</b>", body_style), Paragraph(v.get(), body_style)] 
                for k, v in [
                    ("Objektanschrift", self.entries["objekt_anschrift"]),
                    ("Vermieter", self.entries["vermieter"]),
                    ("Neuer Mieter", self.entries["mieter_neu"]),
                    ("Ausziehender Mieter", self.entries["mieter_alt"]),
                    ("Datum der Abnahme", self.entries["datum"])
                ]
            ]
            t1 = Table(data_part1, colWidths=[150, 380])
            t1.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t1)
            story.append(Spacer(1, 10))

            # Part 2 Meters
            story.append(Paragraph("2. Zählerstände", h2_style))
            meter_data = [["Zählerart", "Zählernummer", "Zählerstand"]]
            for m_name, (ent_nr, ent_val) in self.meter_entries.items():
                meter_data.append([m_name, ent_nr.get(), ent_val.get()])

            t2 = Table(meter_data, colWidths=[200, 150, 180])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ]))
            story.append(t2)
            story.append(Spacer(1, 10))

            # Part 3 Keys
            story.append(Paragraph("3. Schlüsselübergabe", h2_style))
            key_data = [["Schlüsselart", "Anzahl"]]
            for k_name, ent_cnt in self.key_entries.items():
                key_data.append([k_name, ent_cnt.get()])

            t3 = Table(key_data, colWidths=[330, 200])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ]))
            story.append(t3)
            story.append(Spacer(1, 10))

            # Part 4 Maengel
            story.append(Paragraph("4. Mängel, Zustand & Bemerkungen", h2_style))
            maengel_text = self.text_maengel.get("1.0", tk.END).strip()
            t4 = Table([[Paragraph(maengel_text, body_style)]], colWidths=[530])
            t4.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t4)
            story.append(Spacer(1, 30))

            # Signatures
            sig_data = [
                ["___________________________________", "___________________________________"],
                ["Unterschrift Vermietung / KARE", "Unterschrift Mieter"]
            ]
            t_sig = Table(sig_data, colWidths=[265, 265])
            t_sig.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_sig)

            doc.build(story)
            messagebox.showinfo("Erfolg", f"Protokoll erfolgreich gespeichert unter:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen der PDF:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WohnungsabnahmeApp(root)
    root.mainloop()
