"""
ai_summary.py — Gemini AI summary with template fallback.
Works even without an API key.
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

def generate_summary(metrics: dict) -> str:
    key = os.getenv("GEMINI_API_KEY","")
    if key and key != "paste_your_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            top = metrics.get("top_contact",{})
            contacts_text = "\n".join(
                f"  #{c['rank']} {c['contact_name']}: {c['messages']} msgs, {c['calls']} calls ({c['msg_pct']}%)"
                for c in metrics.get("top_contacts",[])[:5]
            )
            prompt = f"""You are a forensic intelligence analyst. Write a professional executive summary in exactly 3 short paragraphs based on these metrics from a phone forensic extraction:

Total messages: {metrics.get('total_messages')}
Total calls: {metrics.get('total_calls')}
Date range: {metrics.get('date_range')}
Days active: {metrics.get('days_active')}
Unique contacts: {metrics.get('unique_contacts')}
Dominant contact: {top.get('contact_name','Unknown')} — {top.get('messages',0)} messages ({top.get('msg_pct',0)}%)
Late-night activity (12AM-4AM): {metrics.get('night_activity_pct')}%
Activity spike: {metrics.get('spike_count')} messages on {metrics.get('spike_date')} ({metrics.get('spike_increase_pct')}% above average)
Longest silence gap: {metrics.get('max_gap_days')} days

Top contacts:
{contacts_text}

Rules: Paragraph 1 = most critical finding. Paragraph 2 = patterns and timeline. Paragraph 3 = risk indicators. Objective tone, plain language, 2-3 sentences each."""
            for model_name in ["gemini-2.0-flash-lite","gemini-1.5-flash","gemini-pro"]:
                try:
                    model = genai.GenerativeModel(model_name)
                    return model.generate_content(prompt).text.strip()
                except: continue
        except Exception as e:
            print(f"[AI] Gemini failed: {e}")
    return _fallback(metrics)

def _fallback(m):
    top   = m.get("top_contact",{})
    name  = top.get("contact_name","an unidentified contact")
    pct   = top.get("msg_pct",0)
    night = m.get("night_activity_pct",0)
    spike = m.get("spike_increase_pct",0)
    gap   = m.get("max_gap_days",0)
    p1 = (f"Analysis of {m.get('total_messages',0)} messages over {m.get('days_active',0)} days "
          f"reveals concentrated communication with {name}, who accounts for {pct}% of all messaging activity — "
          f"a dominant relationship warranting investigative priority.")
    p2 = (f"Peak activity occurs at {m.get('peak_hour_label','unknown hours')}, with {night}% of messages "
          f"sent between 12AM and 4AM. A significant spike of {spike}% above the daily baseline was recorded "
          f"on {m.get('spike_date','an unknown date')}, potentially corresponding to a critical event.")
    p3 = (f"Key risk indicators include {'elevated late-night activity, ' if night > 15 else ''}"
          f"{'a ' + str(gap) + '-day communication gap, ' if gap > 3 else ''}"
          f"and contact concentration suggesting a primary covert relationship. "
          f"Immediate investigative focus is recommended on the spike date and dominant contact.")
    return f"{p1}\n\n{p2}\n\n{p3}"
