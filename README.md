# 🛡️ AI-Driven Threat Detection & Simulation Engine

> **Hack Malenadu '26 · Cybersecurity Track**  
> Real-time threat detection, multi-layer correlation, AI explainability, and attack simulation — built for Security Operations Center (SOC) analysts.

---

## 🧩 Overview

Traditional rule-based SIEM systems catch known patterns but miss novel attacks and overwhelm analysts with noise. This project replaces static rules with a **live ML detection pipeline** that ingests network, endpoint, and application logs, classifies threats with confidence scores, correlates signals across layers, and delivers actionable playbooks — all visualized on a real-time SOC dashboard.

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Attacker UI        │────▶│   FastAPI Backend │────▶│   Redis Streams     │
│  localhost:3001      │     │  localhost:8000   │     │  (Event Queue)      │
└─────────────────────┘     └──────────────────┘     └────────┬────────────┘
                                      │                        │
                              REST /ingest/*           Stream Consumer
                              REST /alerts/*              (Worker Process)
                              SSE  /alerts/live               │
                                      │                        ▼
┌─────────────────────┐               │              ┌─────────────────────┐
│   Defender SOC UI    │◀─────────────┘              │   ML Detection       │
│  localhost:3000      │  Server-Sent Events          │   Pipeline           │
│  (React Dashboard)   │  (Real-time alerts)          │                     │
└─────────────────────┘                              │  Feature Extraction  │
                                                     │  RandomForest ML     │
                                                     │  Cross-layer Corr.   │
                                                     │  Explainability      │
                                                     │  Playbook Engine     │
                                                     └──────────┬──────────┘
                                                                │
                                                     ┌──────────▼──────────┐
                                                     │     MongoDB          │
                                                     │  (Alert & Log Store) │
                                                     └─────────────────────┘
```

---

## ✨ Features

### 🔍 Multi-Layer Ingestion
- Ingests **Network**, **Endpoint**, and **Application** log layers simultaneously
- Normalizes heterogeneous log formats into a unified event schema
- High-throughput pipeline via **Redis Streams** — handles 500+ events/sec

### 🤖 AI-Powered Detection
- **RandomForest ML Classifier** (Scikit-Learn) trained on synthetic data
- Detects **4 distinct threat categories**:
  - 🔒 **Brute Force** / Credential Stuffing (MITRE T1110)
  - 🕸️ **Lateral Movement** — internal SMB pivoting (MITRE T1021)
  - 📤 **Data Exfiltration** — abnormal outbound transfers (MITRE T1041)
  - 📡 **Command & Control** beaconing — DNS/HTTP patterns (MITRE T1071)
- Smart **false positive detection** — authorized scanners (Nessus) correctly classified

### 🔗 Cross-Layer Correlation
- Sliding-window correlator (`±120s`) groups events by source IP
- If the same attacker triggers signals on **multiple layers simultaneously**, confidence is boosted automatically — turning separate low-severity signals into a high-confidence incident

### 💡 Explainability Engine
- Every alert includes a **plain-English explanation** generated from the actual event features (not template spam)
- E.g. *"Detected Data Exfiltration: 54.3 MB transferred to external IP from 10.0.3.21 — 15× above normal baseline, across 2 layer(s)."*

### 📋 Dynamic Playbooks
- Each alert type ships with a prioritized, **actionable mitigation checklist**
- Analysts can tick off steps in the UI with live progress tracking

### 📡 Real-Time SSE Dashboard
- Alerts stream to the browser **instantly** via Server-Sent Events over Redis Pub/Sub (cross-process safe — no polling needed)
- Live feed, severity stats, threat timeline chart, threat type pie chart

### 🎯 Red Team Simulator (Project Hacksaw)
- Dedicated **Attacker UI** (port 3001) with a dark terminal aesthetic
- Inject synthetic attack bursts: Brute Force, Lateral Movement, Data Exfil, C2, False Positive
- Adjustable intensity slider (10–500 events)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | FastAPI 0.115 + Uvicorn |
| **ML Engine** | Scikit-Learn (RandomForest), NumPy, Pandas |
| **Message Queue** | Redis 7 Streams + Pub/Sub |
| **Database** | MongoDB 7 (Motor async driver) |
| **Defender UI** | React + Tailwind CSS + Recharts |
| **Attacker UI** | React + Tailwind CSS (Red Team theme) |
| **Infrastructure** | Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (running)
- Python 3.11+
- Node.js 18+

### 1. Clone & Configure
```bash
git clone https://github.com/Mahanteshwali/ps3.git
cd ps3
```

Create a `.env` file in the root:
```env
# Redis (mapped to host port 16379 to avoid Windows Hyper-V conflicts)
REDIS_URL=redis://127.0.0.1:16379

# MongoDB
MONGO_URL=mongodb://127.0.0.1:27017/threatdb
MONGO_DB=threatdb

# Stream
REDIS_STREAM=threat-events
REDIS_CONSUMER_GROUP=threat-detector
REDIS_CONSUMER_NAME=worker-1

# ML Model
MODEL_PATH=models/saved/threat_classifier.pkl
FEATURE_PATH=models/saved/feature_scaler.pkl
```

### 2. Start Databases
```bash
cd docker
docker compose up -d redis mongo
```

### 3. Start Backend API
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000 --host 0.0.0.0
```

### 4. Start Stream Consumer (Worker)
```bash
# In a new terminal, inside backend/
python -m detection.stream_consumer
```

### 5. Start Defender Dashboard
```bash
cd frontend
npm install
npm run dev     # → http://localhost:3000
```

### 6. Start Attacker Interface
```bash
cd attacker-frontend
npm install
npm run dev     # → http://localhost:3001
```

---

## 🎬 Demo Flow

1. Open **Defender Dashboard** → `http://localhost:3000` (project on the screen for judges)
2. Open **Attacker Interface** → `http://localhost:3001` (on your laptop)
3. Select an attack type (e.g. **Data Exfiltration**), set intensity to 100, click **Initialize Attack**
4. Watch the SOC dashboard's **Alert Feed light up in real time** — no refresh needed
5. Click any alert to view the **AI Explanation**, **Confidence Score**, and **Mitigation Playbook**

### Reset for a clean demo
```bash
python scripts/clear_db.py
```

---

## 📁 Project Structure

```
ps3/
├── backend/
│   ├── api/           # FastAPI routers (ingest, alerts, simulate)
│   ├── db/            # MongoDB client + Pydantic models
│   ├── detection/     # Correlator, Detector, Explainer, Severity, Worker
│   ├── ingestion/     # Normalizer + Redis Stream producer
│   ├── models/        # Feature extractor + ML classifier
│   ├── playbooks/     # Mitigation playbook engine
│   └── requirements.txt
├── frontend/          # Defender SOC React App (port 3000)
├── attacker-frontend/ # Red Team Attack Console (port 3001)
├── docker/            # Docker Compose + Dockerfiles + NGINX config
├── scripts/
│   ├── generate_logs.py     # Load-test traffic generator
│   ├── clear_db.py          # Reset database for demo
│   └── test_sse_pubsub.py   # SSE pipeline verification
└── tests/
    └── test_false_positive.py
```

---

## 📊 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/network` | Ingest a network layer event |
| `POST` | `/ingest/endpoint` | Ingest an endpoint layer event |
| `POST` | `/ingest/application` | Ingest an application layer event |
| `GET`  | `/alerts/` | List alerts (paginated, filterable) |
| `GET`  | `/alerts/stats` | Severity + threat type counts |
| `GET`  | `/alerts/live` | SSE stream of real-time alerts |
| `GET`  | `/alerts/{id}` | Single alert with explanation + playbook |
| `POST` | `/simulate/attack` | Inject a synthetic attack scenario |

---

## 🏆 Hackathon Rubric Coverage

| Criteria | Status | Notes |
|----------|--------|-------|
| Multi-layer ingestion (2+ layers) | ✅ **Stretch** | All 3 layers: Network, Endpoint, Application |
| 4+ threat categories | ✅ **Stretch** | Brute Force, Lateral Movement, Data Exfil, C2 |
| Confidence score + severity | ✅ | Low / Medium / High / Critical |
| Cross-layer correlation | ✅ **Stretch** | Sliding-window, confidence boosting |
| Plain-English explainability | ✅ **Stretch** | Dynamic explanations per alert |
| Playbooks | ✅ | Dynamic, per-incident, interactive UI |
| Live SOC Dashboard | ✅ **Stretch** | Real-time SSE, timeline, charts |
| Threat Simulation Mode | ✅ **Bonus** | Dedicated Red Team UI |
| False positive detection | ✅ | Nessus scanner correctly classified |

---

## 🗺️ Roadmap & Future Enhancements

We have a clear path to integrate this engine with real-world production environments:

1. **MITRE ATT&CK Mapping:** Explicit technique and tactic IDs (e.g., T1110 for Brute Force) integrated directly into the ML classification output and UI badges.
2. **Threat Intelligence Enrichment:** Live integration with the AbuseIPDB API and VirusTotal to add real-time IP reputation scores to detected threats.
3. **Native Log Integration (Windows Events):** A `pywin32` endpoint agent to natively stream Windows Event Logs (Event IDs 4625, 4648, 4688) rather than synthetic Syslog data.

---

## 👥 Team

**Hack Malenadu '26 · Team Size: 2–4 students**

---

*Built with ❤️ for the Cybersecurity Track*
