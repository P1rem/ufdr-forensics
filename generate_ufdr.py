"""
Run once: python generate_ufdr.py
Creates sample_ufdr.zip for testing the app.
"""
import zipfile, random, os
from datetime import datetime, timedelta

CONTACTS = [
    {"name": "John Doe",       "phone": "+1-555-0001"},
    {"name": "Sarah Mitchell", "phone": "+1-555-0002"},
    {"name": "Unknown",        "phone": "+1-555-9999"},
    {"name": "Mike Torres",    "phone": "+1-555-0003"},
    {"name": "Lisa Park",      "phone": "+1-555-0004"},
]
START   = datetime(2024, 1, 1)
END     = datetime(2024, 2, 20)
SPIKE   = datetime(2024, 2, 12)
TOTAL   = 500

def rand_ts(date, night=False):
    if night and random.random() < 0.5:
        h = random.randint(0, 4)
    else:
        h = random.choice([8,9,10,11,12,13,14,15,16,17,18,19,20,21])
    return date.replace(hour=h, minute=random.randint(0,59), second=random.randint(0,59))

def messages_xml():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<messages>']
    days  = (END - START).days
    dates = []
    for i in range(days + 1):
        d = START + timedelta(days=i)
        if d.date() == SPIKE.date():
            n = 60
        elif i < 5:
            n = 0
        else:
            n = random.randint(3, 9)
        dates.extend([d] * n)
    random.shuffle(dates)
    dates = sorted(dates[:TOTAL])
    bodies = ["Ok","Sure","Call me","On my way","Got it","Yes confirmed",
              "Don't text me here","Delete this after","Where are you?",
              "Tomorrow same time","Not now","Need to talk"]
    for i, date in enumerate(dates, 1):
        w = [35, 20, 15, 15, 15]
        c = random.choices(CONTACTS, weights=w, k=1)[0]
        night = (c["phone"] == "+1-555-9999") or (date.date() == SPIKE.date())
        ts    = rand_ts(date, night)
        body  = random.choice(bodies)
        dirn  = random.choice(["incoming","outgoing"])
        lines.append(f"""  <message>
    <id>{i}</id>
    <contact_name>{c['name']}</contact_name>
    <sender>{'Subject' if dirn=='outgoing' else c['phone']}</sender>
    <recipient>{c['phone'] if dirn=='outgoing' else 'Subject'}</recipient>
    <timestamp>{ts.strftime('%Y-%m-%dT%H:%M:%S')}</timestamp>
    <body>{body}</body>
    <type>SMS</type>
    <direction>{dirn}</direction>
  </message>""")
    lines.append('</messages>')
    return '\n'.join(lines)

def calls_xml():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<calls>']
    days  = (END - START).days
    for i in range(1, 21):
        c    = random.choices(CONTACTS, weights=[40,20,10,15,15], k=1)[0]
        date = START + timedelta(days=random.randint(0, days))
        ts   = rand_ts(date)
        dirn = random.choice(["incoming","outgoing"])
        lines.append(f"""  <call>
    <id>{i}</id>
    <contact_name>{c['name']}</contact_name>
    <caller>{'Subject' if dirn=='outgoing' else c['phone']}</caller>
    <recipient>{c['phone'] if dirn=='outgoing' else 'Subject'}</recipient>
    <timestamp>{ts.strftime('%Y-%m-%dT%H:%M:%S')}</timestamp>
    <duration>{random.randint(30,600)}</duration>
    <type>{dirn}</type>
  </call>""")
    lines.append('</calls>')
    return '\n'.join(lines)

def contacts_xml():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<contacts>']
    for i, c in enumerate(CONTACTS, 1):
        lines.append(f"  <contact><id>{i}</id><name>{c['name']}</name><phone>{c['phone']}</phone></contact>")
    lines.append('</contacts>')
    return '\n'.join(lines)

def metadata_xml():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<metadata><device>
  <model>iPhone 13 Pro</model><os>iOS 16.2</os>
  <imei>354823110234567</imei>
  <extraction_date>2024-03-01</extraction_date>
  <case_id>CASE-2024-001</case_id>
</device></metadata>'''

with zipfile.ZipFile("sample_ufdr.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("messages.xml",  messages_xml())
    z.writestr("calls.xml",     calls_xml())
    z.writestr("contacts.xml",  contacts_xml())
    z.writestr("metadata.xml",  metadata_xml())

print(f"✅ Created sample_ufdr.zip ({os.path.getsize('sample_ufdr.zip')//1024} KB)")
print("Patterns: Feb 12 spike | Late-night Unknown contact | John Doe dominant | Jan 1-5 gap")
