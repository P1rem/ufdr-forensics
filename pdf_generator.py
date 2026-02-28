"""pdf_generator.py — Generates professional forensic PDF report."""
import io, base64
from datetime import datetime

def generate_pdf(metrics: dict, summary: str, risks: list, graph_b64: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable, Image as RLImage, PageBreak)

        NAVY  = colors.HexColor("#0a0e27")
        PANEL = colors.HexColor("#111936")
        CYAN  = colors.HexColor("#00d9ff")
        RED   = colors.HexColor("#ff4757")
        AMBER = colors.HexColor("#ffa502")
        GREEN = colors.HexColor("#2ed573")
        MUTED = colors.HexColor("#8892b0")
        WHITE = colors.white
        W, H  = A4

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
              topMargin=18*mm, bottomMargin=15*mm,
              leftMargin=15*mm, rightMargin=15*mm)

        def S(name, **kw): return ParagraphStyle(name, **kw)
        title_s  = S("T", fontSize=18, textColor=CYAN,  alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4)
        sub_s    = S("S", fontSize=9,  textColor=MUTED, alignment=TA_CENTER, spaceAfter=2)
        h2_s     = S("H", fontSize=12, textColor=CYAN,  fontName="Helvetica-Bold", spaceAfter=4)
        body_s   = S("B", fontSize=8,  textColor=WHITE, leading=13, spaceAfter=3)
        muted_s  = S("M", fontSize=7,  textColor=MUTED, leading=10)

        def bg(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(NAVY);  canvas.rect(0,0,W,H,fill=1,stroke=0)
            canvas.setFillColor(PANEL); canvas.rect(0,H-12*mm,W,12*mm,fill=1,stroke=0)
            canvas.setFillColor(CYAN);  canvas.setFont("Helvetica-Bold",8)
            canvas.drawString(15*mm, H-8*mm, "⚠ CONFIDENTIAL — RESTRICTED FORENSIC DOCUMENT")
            canvas.setFillColor(MUTED); canvas.setFont("Helvetica",7)
            canvas.drawRightString(W-15*mm,H-8*mm,f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            canvas.setFillColor(PANEL); canvas.rect(0,0,W,10*mm,fill=1,stroke=0)
            canvas.setFillColor(MUTED); canvas.setFont("Helvetica",7)
            canvas.drawString(15*mm,3.5*mm,"UFDRINSIGHT Forensic Intelligence Platform | Authorized Use Only")
            canvas.drawRightString(W-15*mm,3.5*mm,f"Page {doc.page}")
            canvas.restoreState()

        def hr(): return HRFlowable(width="100%",thickness=0.5,color=CYAN,spaceAfter=5,spaceBefore=5)
        def section(t): return [hr(), Paragraph(t, h2_s), Spacer(1,2*mm)]

        story = [Spacer(1,6*mm)]
        story.append(Paragraph("UFDRINSIGHT FORENSIC INTELLIGENCE REPORT", title_s))
        story.append(Paragraph("AI-Powered Communication Analysis", sub_s))
        story.append(Spacer(1,4*mm))

        meta = metrics.get("metadata",{})
        meta_data = [
            ["Case ID", meta.get("case_id","CASE-001"), "Device", meta.get("model","Unknown")],
            ["Date Range", metrics.get("date_range","—"), "Extraction", meta.get("extraction_date","—")],
            ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M"), "Platform", "UFDRINSIGHT"],
        ]
        mt = Table(meta_data, colWidths=[35*mm,60*mm,35*mm,50*mm])
        mt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),PANEL),
            ("TEXTCOLOR",(0,0),(0,-1),CYAN),("TEXTCOLOR",(2,0),(2,-1),CYAN),
            ("TEXTCOLOR",(1,0),(1,-1),WHITE),("TEXTCOLOR",(3,0),(3,-1),WHITE),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.3,CYAN),("PADDING",(0,0),(-1,-1),5),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[PANEL,colors.HexColor("#151c40")]),
        ]))
        story.append(mt); story.append(Spacer(1,4*mm))

        # KPIs
        story.extend(section("KEY METRICS"))
        kpi_vals = ["Total Messages","Total Calls","Unique Contacts","Days Active","Night Activity %","Daily Average"]
        kpi_data_v = [str(metrics.get("total_messages",0)), str(metrics.get("total_calls",0)),
                      str(metrics.get("unique_contacts",0)), str(metrics.get("days_active",0)),
                      f"{metrics.get('night_activity_pct',0)}%", str(metrics.get("avg_daily_messages",0))]
        kpi_tbl = Table([kpi_vals, kpi_data_v], colWidths=[30*mm]*6)
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),PANEL),("BACKGROUND",(0,1),(-1,1),colors.HexColor("#151c40")),
            ("TEXTCOLOR",(0,0),(-1,0),CYAN),("TEXTCOLOR",(0,1),(-1,1),WHITE),
            ("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),7),
            ("FONTSIZE",(0,1),(-1,1),13),("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("GRID",(0,0),(-1,-1),0.5,CYAN),("ROWHEIGHT",(0,0),(-1,-1),8*mm),
        ]))
        story.append(kpi_tbl); story.append(Spacer(1,4*mm))

        # Summary
        story.extend(section("EXECUTIVE SUMMARY"))
        for para in summary.split("\n\n"):
            if para.strip(): story.append(Paragraph(para.strip(), body_s)); story.append(Spacer(1,2*mm))

        # Contacts
        story.extend(section("KEY INDIVIDUALS"))
        contacts = metrics.get("top_contacts",[])[:8]
        hdr = ["Rank","Contact","Messages","Calls","Share %","Priority"]
        rows = [hdr] + [[f"#{c['rank']}",c["contact_name"],str(c["messages"]),
                          str(c["calls"]),f"{c['msg_pct']}%",c["priority"]] for c in contacts]
        ct = Table(rows, colWidths=[15*mm,60*mm,25*mm,20*mm,25*mm,35*mm])
        pc = {"HIGH":RED,"MEDIUM":AMBER,"STANDARD":GREEN}
        ts_list = [("BACKGROUND",(0,0),(-1,0),CYAN),("TEXTCOLOR",(0,0),(-1,0),NAVY),
                   ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
                   ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(1,0),(1,-1),"LEFT"),
                   ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#1a2040")),
                   ("ROWBACKGROUNDS",(0,1),(-1,-1),[PANEL,colors.HexColor("#151c40")]),
                   ("TEXTCOLOR",(0,1),(-1,-1),WHITE),("ROWHEIGHT",(0,0),(-1,-1),7*mm)]
        for i, c in enumerate(contacts,1):
            ts_list.append(("TEXTCOLOR",(5,i),(5,i),pc.get(c["priority"],GREEN)))
            ts_list.append(("FONTNAME",(5,i),(5,i),"Helvetica-Bold"))
        ct.setStyle(TableStyle(ts_list)); story.append(ct)

        # Risks
        story.append(PageBreak())
        story.extend(section("RISK SIGNALS"))
        sc = {"HIGH":RED,"MEDIUM":AMBER,"INFO":CYAN}
        for risk in risks:
            col = sc.get(risk["severity"],CYAN)
            row_data = [[
                Paragraph(f"<b>{risk['icon']} {risk['flag']}  [{risk['severity']}]</b>",
                          S("rh",fontSize=9,textColor=col,fontName="Helvetica-Bold")),
                Paragraph(risk["detail"], body_s),
            ]]
            t = Table(row_data, colWidths=[55*mm,115*mm])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),
                                   ("GRID",(0,0),(-1,-1),0.5,col),
                                   ("PADDING",(0,0),(-1,-1),5),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(t); story.append(Spacer(1,2*mm))

        # Graph
        if graph_b64:
            story.extend(section("COMMUNICATION NETWORK"))
            try:
                img = RLImage(io.BytesIO(base64.b64decode(graph_b64)), width=160*mm, height=120*mm)
                story.append(img)
            except: pass

        # Disclaimer
        story.append(Spacer(1,6*mm)); story.append(hr())
        story.append(Paragraph(
            "DISCLAIMER: Generated by AI-assisted forensic analysis for investigative support only. "
            "Not court-admissible without qualified forensic examiner review. Unauthorized distribution prohibited.",
            muted_s))

        doc.build(story, onFirstPage=bg, onLaterPages=bg)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"[PDF] Error: {e}")
        return b""
