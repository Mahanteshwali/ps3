# 🛡️ ThreatAI — AI-Driven Threat Detection & Simulation Engine

A full-stack, real-time cybersecurity platform that uses Machine Learning to detect, classify, and explain cyber threats across **network**, **endpoint**, and **application** layers.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔄 Multi-layer log ingestion | REST endpoints for network, endpoint, application logs |
| ⚡ Real-time processing | Redis Streams consumer at 500+ events/sec |
| 🧠 ML Threat Detection | RandomForest detecting 4 threat types + false positives |
| 🔗 Cross-layer correlation | Sliding-window event grouping with confidence boosting |
| 🧾 Explainability | Human-readable explanation per alert |
| 🛡️ Playbook engine | Ordered mitigation steps per threat type |
| 📊 SOC Dashboard | Live alert feed, timeline chart, severity stats |
| 🧪 Attack Simulation | Inject synthetic attacks through the full pipeline |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for frontend dev)
- Python 3.11+ (for backend dev)

### 1. Clone & Configure

```bash
cp .env.example .env
```

### 2. Train the ML model (first time only)

```bash
cd backend
pip install -r requirements.txt
python -m models.threat_classifier
```

### 3. Start all services

```bash
cd docker
docker compose up --build
```

Services:
| Service | URL |
|---|---|
| API (FastAPI) | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Dashboard (React) | http://localhost:3000 |
| Full stack (NGINX) | http://localhost:80 |

---

## 🧪 Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt

# Terminal 1 — API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Worker
python -m detection.stream_consumer
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000
```

---

## 🔬 Running Tests

```bash
cd backend
pip install pytest
pytest ../tests/test_false_positive.py -v
```

---

## 📡 API Reference

### Ingestion
```
POST /ingest/network       — Ingest network layer log
POST /ingest/endpoint      — Ingest endpoint layer log
POST /ingest/application   — Ingest application layer log
```

### Alerts
```
GET  /alerts/              — Paginated alert list
GET  /alerts/stats         — Severity & type counts
GET  /alerts/live          — SSE real-time stream
GET  /alerts/{id}          — Single alert detail
```

### Simulation
```
POST /simulate/attack      — Inject synthetic attack
```

---

## 🎯 Threat Types Detected

| Threat | Key Signals |
|---|---|
| **Brute Force** | High failed login count in short window |
| **Lateral Movement** | Unusual internal IP-to-IP connections |
| **Data Exfiltration** | Large outbound data transfers |
| **Command & Control** | DNS beaconing, regular interval callbacks |
| **False Positive** | Scanner-like traffic (Nessus, etc.) |

---

## 🧱 Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **ML**: Scikit-learn (RandomForest + StandardScaler)
- **Stream**: Redis 7 Streams
- **Database**: MongoDB 7
- **Frontend**: React 18 + Vite + Tailwind CSS + Recharts
- **DevOps**: Docker Compose + NGINX

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── api/           FastAPI app + routers
│   ├── ingestion/     Normalizer + Redis producer
│   ├── detection/     Stream consumer, detector, correlator, explainer
│   ├── models/        Feature extractor + ML classifier
│   ├── playbooks/     Mitigation playbook engine
│   └── db/            MongoDB client + Pydantic models
├── frontend/
│   └── src/
│       ├── components/ AlertCard, ThreatTimeline
│       └── pages/      Dashboard, AlertDetail, Simulate
├── tests/             Pytest test suite (incl. false positive)
├── scripts/           Log generator (500+ eps load test)
└── docker/            Docker Compose + NGINX + Dockerfiles
```
