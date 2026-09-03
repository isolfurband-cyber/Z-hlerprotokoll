if pdf.get_y() > 220:
            pdf.add_page()
            
        pdf.chapter_title("4. Unterschriften")
        pdf.ln(2)
        
        sig_y = pdf.get_y()
        
        # Vermieter Unterschrift verarbeiten
        if canvas_vermieter.json_data is not None and len(canvas_vermieter.json_data["objects"]) > 0:
            pil_img_v = canvas_vermieter.image_data
            if pil_img_v is not None:
                img_v = Image.fromarray(pil_img_v.astype("uint8"), mode="RGBA")
                # Weißer Hintergrund für das transparent gezeichnete Canvas
                bg_v = Image.new("RGB", img_v.size, (255, 255, 255))
                bg_v.paste(img_v, (0, 0), img_v)
                temp_sig_v = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                bg_v.save(temp_sig_v, "PNG")
                
                pdf.image(temp_sig_v, x=14, y=sig_y, w=85, h=35)
                
        # Mieter Unterschrift verarbeiten
        if canvas_mieter.json_data is not None and len(canvas_mieter.json_data["objects"]) > 0:
            pil_img_m = canvas_mieter.image_data
            if pil_img_m is not None:
                img_m = Image.fromarray(pil_img_m.astype("uint8"), mode="RGBA")
                bg_m = Image.new("RGB", img_m.size, (255, 255, 255))
                bg_m.paste(img_m, (0, 0), img_m)
                temp_sig_m = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                bg_m.save(temp_sig_m, "PNG")
                
                pdf.image(temp_sig_m, x=111, y=sig_y, w=85, h=35)

        # Unterschriftslinien und Beschriftungen unter den Bildern
        pdf.set_y(sig_y + 36)
        pdf.cell(95, 5, "___________________________________", 0, 0, "L")
        pdf.cell(0, 5, "___________________________________", 0, 1, "L")
        pdf.set_font("helvetica", size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(95, 5, "Vermieter (KARE-Immobilien)", 0, 0, "L")
        pdf.cell(0, 5, "Mieter", 0, 1, "L")
        pdf.ln(5)
