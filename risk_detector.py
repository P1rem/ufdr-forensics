"""risk_detector.py — Rule-based forensic risk flags."""

def detect_risks(metrics: dict) -> list:
    flags = []
    top      = metrics.get("top_contact", {})
    contacts = metrics.get("top_contacts", [])

    # 1. Dominant contact
    pct = top.get("msg_pct", 0)
    if pct >= 25:
        flags.append({"flag":"Dominant Contact Relationship","severity":"HIGH","icon":"🔴",
            "detail":f"{top.get('contact_name','Unknown')} accounts for {pct}% of all messages "
                     f"({top.get('messages',0)} messages). High concentration indicates a primary relationship."})

    # 2. Activity spike
    spike = metrics.get("spike_increase_pct", 0)
    if spike >= 200:
        sev = "HIGH" if spike >= 300 else "MEDIUM"
        flags.append({"flag":"Abnormal Activity Spike","severity":sev,
            "icon":"🔴" if sev=="HIGH" else "🟡",
            "detail":f"Message volume on {metrics.get('spike_date')} was {spike}% above the daily average "
                     f"({metrics.get('spike_count')} messages vs avg {metrics.get('avg_daily_messages')}/day). "
                     f"This spike may correspond to a critical event."})

    # 3. Late-night activity
    night = metrics.get("night_activity_pct", 0)
    if night >= 15:
        sev = "HIGH" if night >= 30 else "MEDIUM"
        flags.append({"flag":"Elevated Late-Night Communication","severity":sev,
            "icon":"🔴" if sev=="HIGH" else "🟡",
            "detail":f"{night}% of messages ({metrics.get('night_message_count',0)} total) sent 12AM–4AM. "
                     f"Pattern may indicate urgency, secrecy, or coordination outside normal hours."})

    # 4. Unknown contact in top 5
    unknowns = [c for c in contacts[:5]
                if "unknown" in str(c.get("contact_name","")).lower()
                or str(c.get("contact_name","")).startswith("+")]
    if unknowns:
        u = unknowns[0]
        flags.append({"flag":"Unidentified High-Frequency Contact","severity":"HIGH","icon":"🔴",
            "detail":f"Unidentified contact in top contacts with {u.get('messages',0)} messages. "
                     f"Unidentified numbers in primary communication roles are a key investigative priority."})

    # 5. Communication gap
    gap = metrics.get("max_gap_days", 0)
    if gap >= 5:
        flags.append({"flag":"Suspicious Communication Gap","severity":"MEDIUM","icon":"🟡",
            "detail":f"No communication detected for {gap} days "
                     f"({metrics.get('gap_start','')} to {metrics.get('gap_end','')}). "
                     f"Possible alternative device, deliberate blackout, or device seizure."})

    if not flags:
        flags.append({"flag":"No High-Priority Signals Detected","severity":"INFO","icon":"🔵",
            "detail":"Communication patterns appear within normal parameters."})
    return flags
