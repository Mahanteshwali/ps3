 Plan Summary
Phase 1 — MITRE ATT&CK Mapping (~1–2 hrs)

Add a _MITRE_MAP lookup to playbooks/engine.py
Attach mitre_tactic + mitre_technique_id to every AlertDocument
Show a clickable T1110 · Credential Access badge on the Alert Detail page
Phase 2 — AbuseIPDB Threat Intelligence (~2–3 hrs)

New backend/enrichment/abuseipdb.py module with caching
Enrich every alert with abuse_confidence, country, isp, is_tor
Display IP reputation panel on Alert Detail
⚠️ Needs a free API key from https://www.abuseipdb.com/register
Phase 3 — Windows Event Log Reader (~3–4 hrs)

New backend/ingestion/winevent_reader.py using pywin32
Watches Event IDs 4625 (failed login), 4648, 4688 in real time
Feeds real local Windows logs directly into the Redis Stream
⚠️ Must run as Administrator
Do you have an AbuseIPDB API key? If yes, share it (or put it in your .env)