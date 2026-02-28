"""
aggregator.py — Calculates all metrics from parsed DataFrames.
All contact references use column 'contact_name' consistently.
"""
import pandas as pd

def aggregate(messages: pd.DataFrame, calls: pd.DataFrame, metadata: dict) -> dict:
    m = {}
    m["metadata"]       = metadata
    m["total_messages"] = len(messages)
    m["total_calls"]    = len(calls)

    if messages.empty:
        return m

    messages = messages.copy()
    messages["timestamp"] = pd.to_datetime(messages["timestamp"], errors="coerce")
    messages = messages.dropna(subset=["timestamp"])

    # Date range
    mn, mx = messages["timestamp"].min(), messages["timestamp"].max()
    m["date_range"]       = f"{mn.strftime('%b %d, %Y')} to {mx.strftime('%b %d, %Y')}"
    m["days_active"]      = max((mx - mn).days + 1, 1)
    m["avg_daily_messages"] = round(m["total_messages"] / m["days_active"], 1)

    # Unique contacts (excluding Subject)
    all_c = messages["contact_name"].dropna()
    if not calls.empty:
        all_c = pd.concat([all_c, calls["contact_name"].dropna()])
    unique = [c for c in all_c.unique() if str(c).lower() not in ("subject","","nan")]
    m["unique_contacts"] = len(unique)

    # Top contacts
    msg_cnt  = messages.groupby("contact_name").size().reset_index(name="messages")
    msg_cnt  = msg_cnt[~msg_cnt["contact_name"].str.lower().isin(["subject",""])]

    if not calls.empty:
        call_cnt = calls.groupby("contact_name").size().reset_index(name="calls")
    else:
        call_cnt = pd.DataFrame(columns=["contact_name","calls"])

    top = msg_cnt.merge(call_cnt, on="contact_name", how="left").fillna(0)
    top["calls"]    = top["calls"].astype(int)
    top["msg_pct"]  = (top["messages"] / max(m["total_messages"],1) * 100).round(1)
    top             = top.sort_values("messages", ascending=False).reset_index(drop=True)
    top["rank"]     = range(1, len(top)+1)
    top["priority"] = top["rank"].apply(lambda r: "HIGH" if r==1 else ("MEDIUM" if r<=3 else "STANDARD"))
    m["top_contacts"] = top.head(10).to_dict("records")
    m["top_contact"]  = top.iloc[0].to_dict() if not top.empty else {}

    # Night activity
    messages["hour"] = messages["timestamp"].dt.hour
    night = messages[messages["hour"].between(0,4)]
    m["night_activity_pct"]  = round(len(night) / max(m["total_messages"],1) * 100, 1)
    m["night_message_count"] = len(night)

    # Hourly distribution
    hourly = messages.groupby("hour").size().reindex(range(24), fill_value=0)
    m["hourly_distribution"] = hourly.to_dict()
    m["peak_hour"]            = int(hourly.idxmax())
    m["peak_hour_label"]      = f"{m['peak_hour']:02d}:00–{m['peak_hour']+1:02d}:00"

    # Daily volume + spike
    messages["date"] = messages["timestamp"].dt.date
    daily = messages.groupby("date").size()
    m["daily_volume"]       = {str(k): int(v) for k, v in daily.items()}
    m["avg_daily_messages"] = round(daily.mean(), 1)
    spike_date  = daily.idxmax()
    spike_count = int(daily.max())
    spike_pct   = int((spike_count / max(daily.mean(),1) - 1) * 100)
    m["spike_date"]         = str(spike_date)
    m["spike_count"]        = spike_count
    m["spike_increase_pct"] = spike_pct

    # Max gap
    sorted_dates = sorted(daily.index)
    max_gap, gap_start, gap_end = 0, None, None
    for i in range(1, len(sorted_dates)):
        gap = (sorted_dates[i] - sorted_dates[i-1]).days
        if gap > max_gap:
            max_gap   = gap
            gap_start = str(sorted_dates[i-1])
            gap_end   = str(sorted_dates[i])
    m["max_gap_days"] = max_gap
    m["gap_start"]    = gap_start
    m["gap_end"]      = gap_end

    # Network edges
    m["network_edges"] = [
        {"source":"Subject","target":r["contact_name"],"weight":int(r["messages"])}
        for r in top.head(10).to_dict("records")
    ]
    return m
