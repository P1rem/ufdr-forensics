"""
parser.py — Extracts UFDR ZIP and parses XML into DataFrames.
Handles multiple XML structures including our generated format.
"""
import zipfile, io, xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

def parse_ufdr(file_bytes: bytes) -> dict:
    result = {"messages": pd.DataFrame(), "calls": pd.DataFrame(),
              "contacts": pd.DataFrame(), "metadata": {}, "errors": []}
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            names = zf.namelist()
            print("[Parser] ZIP contains:", names)
            msgs, calls, contacts = [], [], []
            for fname in names:
                if not fname.lower().endswith(".xml"):
                    continue
                data = zf.read(fname)
                fl   = fname.lower()
                if any(k in fl for k in ["message","sms","chat","whatsapp"]):
                    m = _parse_messages(data)
                    msgs.extend(m)
                    print(f"[Parser] {fname}: {len(m)} messages")
                elif any(k in fl for k in ["call","phone"]):
                    c = _parse_calls(data)
                    calls.extend(c)
                    print(f"[Parser] {fname}: {len(c)} calls")
                elif any(k in fl for k in ["contact","address"]):
                    contacts.extend(_parse_contacts(data))
                elif any(k in fl for k in ["meta","device"]):
                    result["metadata"] = _parse_meta(data)
                else:
                    # Try as messages anyway
                    m = _parse_messages(data)
                    if m:
                        msgs.extend(m)
                        print(f"[Parser] {fname} auto-detected: {len(m)} messages")
            if msgs:
                df = pd.DataFrame(msgs)
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df["hour"]      = df["timestamp"].dt.hour
                df["date"]      = df["timestamp"].dt.date
                result["messages"] = df
            else:
                result["errors"].append("No messages found in ZIP")
            if calls:
                df = pd.DataFrame(calls)
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                result["calls"] = df
            if contacts:
                result["contacts"] = pd.DataFrame(contacts)
    except zipfile.BadZipFile:
        result["errors"].append("Not a valid ZIP file.")
    except Exception as e:
        result["errors"].append(f"Error: {e}")
    return result

def _parse_messages(xml_bytes):
    rows = []
    try:
        root = ET.fromstring(xml_bytes)
        # Try <message>, <msg>, <sms> tags
        for tag in ["message","msg","sms","mms"]:
            for el in root.iter(tag):
                r = _msg_row(el)
                if r: rows.append(r)
            if rows: return rows
        # Generic: anything with timestamp+body
        for el in root.iter():
            has_ts   = any(el.find(t) is not None for t in ["timestamp","time","date","TimeStamp"])
            has_body = any(el.find(t) is not None for t in ["body","text","content","Body"])
            if has_ts and has_body:
                r = _msg_row(el)
                if r: rows.append(r)
    except ET.ParseError as e:
        print(f"[Parser] XML error: {e}")
    return rows

def _msg_row(el):
    ts_str = (_get(el,"timestamp") or _get(el,"time") or _get(el,"date")
              or _get(el,"TimeStamp") or el.get("date") or el.get("time"))
    ts = _parse_ts(ts_str)
    if not ts:
        return None
    contact = (_get(el,"contact_name") or _get(el,"contact") or _get(el,"name")
               or _get(el,"from") or _get(el,"sender") or _get(el,"party")
               or _get(el,"address") or el.get("address") or "Unknown")
    body    = (_get(el,"body") or _get(el,"text") or _get(el,"content") or "")
    dirn    = (_get(el,"direction") or _get(el,"type") or el.get("type") or "unknown").lower()
    if any(k in dirn for k in ["sent","out","1"]): dirn = "outgoing"
    elif any(k in dirn for k in ["recv","in","0"]): dirn = "incoming"
    return {"contact_name": contact, "timestamp": ts, "body": body,
            "direction": dirn, "type": _get(el,"type","SMS")}

def _parse_calls(xml_bytes):
    rows = []
    try:
        root = ET.fromstring(xml_bytes)
        for tag in ["call","phonecall","Call"]:
            for el in root.iter(tag):
                ts = _parse_ts(_get(el,"timestamp") or _get(el,"time") or _get(el,"date"))
                if not ts: continue
                contact = (_get(el,"contact_name") or _get(el,"contact")
                           or _get(el,"caller") or _get(el,"number") or "Unknown")
                try: dur = int(_get(el,"duration","0"))
                except: dur = 0
                rows.append({"contact_name": contact, "timestamp": ts,
                              "duration": dur, "type": _get(el,"type","unknown")})
            if rows: break
    except ET.ParseError: pass
    return rows

def _parse_contacts(xml_bytes):
    rows = []
    try:
        root = ET.fromstring(xml_bytes)
        for el in root.iter("contact"):
            rows.append({"name":  _get(el,"n") or _get(el,"name","?"),
                         "phone": _get(el,"phone") or _get(el,"number","")})
    except ET.ParseError: pass
    return rows

def _parse_meta(xml_bytes):
    meta = {}
    try:
        root = ET.fromstring(xml_bytes)
        for dev in root.iter("device"):
            for ch in dev: meta[ch.tag] = ch.text or ""
        for ch in root:
            if ch.text and ch.text.strip(): meta[ch.tag] = ch.text.strip()
    except ET.ParseError: pass
    return meta

def _parse_ts(s):
    if not s: return None
    fmts = ["%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S","%d/%m/%Y %H:%M:%S","%m/%d/%Y %H:%M:%S","%Y-%m-%d"]
    for f in fmts:
        try: return datetime.strptime(s.strip(), f)
        except: pass
    try:
        t = float(s.strip())
        if t > 1e9: return datetime.fromtimestamp(t)
    except: pass
    return None

def _get(el, tag, default=""):
    ch = el.find(tag)
    if ch is not None and ch.text: return ch.text.strip()
    v = el.get(tag)
    return v.strip() if v else default
