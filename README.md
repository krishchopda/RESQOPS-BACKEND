# ResQOps — AI Emergency Response Operating System

> An AI-powered dispatch platform that helps emergency responders make faster, smarter, and more informed decisions in real time.

![ResQOps Dashboard](https://img.shields.io/badge/Status-Active-00ff88?style=flat-square) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square) ![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square) ![Claude AI](https://img.shields.io/badge/Claude-Sonnet-CC785C?style=flat-square)

---

## The Problem

Emergency dispatch is fragmented. Dispatchers must simultaneously track ambulance availability, hospital capacity, traffic conditions, and incident severity — under extreme time pressure — using outdated systems with no AI support.

**ResQOps changes that.** Instead of just showing information, it understands what's happening and recommends the best actions — with full reasoning.

---

## Live Demo

> https://resqops-frontend-lfwqglhuk-krishchopda-6940s-projects.vercel.app — Backend deployed on Railway · Frontend deployed on Vercel

---

## Key Features

### ⚡ Smart Dispatch Engine
The core of ResQOps. Uses a two-stage algorithm:

**Stage 1 — Hard Constraints** (eliminates candidates that can't physically handle the incident):
- Equipment matching: cardiac incidents require cardiac-equipped ambulances
- Trauma level matching: critical incidents route only to Level 1 trauma centers
- Capacity safety buffer: hospitals over 95% capacity are excluded

**Stage 2 — Soft Scoring** (ranks eligible candidates by weighted score):
```
score = travel_time_to_incident × 0.40
      + travel_time_to_hospital × 0.35
      + hospital_load           × 0.15
      - equipment_bonus         × 0.10
```

Every recommendation includes full reasoning, rejected candidates with reasons, confidence score, and number of combinations evaluated.

### 🗺️ Live Operations Map
Interactive map showing all ambulances, hospitals, and active incidents with real-time updates. Click anywhere to create a new incident — coordinates auto-fill.

### 🤖 AI Operations Assistant
Powered by Claude (Anthropic). Dispatchers ask natural language questions:
- *"Which hospital should we avoid right now?"*
- *"What is our biggest operational risk?"*
- *"Summarize current operations"*

The AI answers using live system data — not generic responses.

### 🚦 Real Road Routing
Travel times calculated using OSRM (Open Source Routing Machine) — actual road routes, not straight-line distance. Falls back to Haversine estimate if OSRM is unavailable.

### 📊 Prediction Engine
Rule-based alerts for:
- Hospital capacity warnings (75% → warning, 90% → critical)
- Ambulance shortage alerts
- Geographic incident clustering (possible mass casualty detection)

---

## Architecture

```
React Frontend (Vite)
        │
        │ HTTP / Axios
        ▼
FastAPI Backend (Python)
        │
    ┌───┴────────────────────────┐
    │                            │
    ▼                            ▼
PostgreSQL              External APIs
(SQLAlchemy ORM)     OSRM Routing · Anthropic Claude
```

### Folder Structure

```
Backend/
├── main.py                 # FastAPI app entry point
├── core/
│   └── database.py         # DB connection + session management
├── models/                 # SQLAlchemy table definitions
│   ├── ambulance.py
│   ├── hospital.py
│   └── incident.py
├── schemas/                # Pydantic request/response schemas
├── routes/                 # HTTP route handlers (thin layer)
│   ├── ambulances.py
│   ├── hospitals.py
│   ├── incidents.py
│   ├── dispatch.py
│   ├── predictions.py
│   └── ai.py
└── services/               # Business logic (all intelligence lives here)
    ├── dispatch_engine.py  # Core dispatch algorithm
    ├── prediction_service.py
    └── ai_assistant.py

frontend/
└── src/
    └── App.jsx             # React frontend
```

**Design principle:** Routes handle HTTP only. All business logic lives in services. Models describe data shape only. This separation means every layer is independently testable and replaceable.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI (Python) | Async-first, auto-generated docs, Pydantic validation |
| Database | PostgreSQL | Relational data with ACID guarantees |
| ORM | SQLAlchemy 2.0 | Type-safe queries, migration support |
| Frontend | React + Vite | Fast HMR, component model |
| Maps | Leaflet + OpenStreetMap | Open source, no API key required |
| Routing | OSRM | Real road travel time, free |
| AI | Anthropic Claude Sonnet | Best reasoning model for operational Q&A |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/health` | Health check |
| GET | `/ambulances/` | List all ambulances |
| POST | `/ambulances/` | Create ambulance |
| GET | `/hospitals/` | List all hospitals |
| POST | `/hospitals/` | Create hospital |
| GET | `/incidents/` | List all incidents |
| POST | `/incidents/` | Create incident |
| GET | `/dispatch/recommend/{id}` | Get dispatch recommendation |
| GET | `/predictions/` | Get system alerts and predictions |
| POST | `/ai/ask` | Ask AI operations assistant |

Full interactive docs available at `/docs` (Swagger UI).

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16

### Backend Setup

```bash
git clone https://github.com/krishchopda/RESQOPS-BACKEND
cd RESQOPS-BACKEND

pip install -r requirements.txt

# Create .env file
echo "DATABASE_URL=postgresql://username@localhost:5432/resqops" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Create database
psql postgres -c "CREATE DATABASE resqops;"

# Seed data
python3 seed.py

# Start server
python3 -m uvicorn main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
git clone https://github.com/krishchopda/RESQOPS-FRONTEND
cd RESQOPS-FRONTEND

npm install
npm run dev
# App available at http://localhost:5173
```

---

## Dispatch Algorithm — Design Decisions

**Why hard constraints before soft scoring?**

A naive weighted formula like `score = distance × 0.4 + hospital_distance × 0.3` would recommend a basic ambulance for a cardiac arrest if it's close enough. That's dangerous. Hard constraints eliminate physically ineligible candidates before any scoring runs — replicating how real EMS protocols work.

**Why travel time instead of distance?**

A hospital 3km away through Manhattan traffic may take 15 minutes. A hospital 5km away via highway may take 6 minutes. Haversine distance is meaningless for urban dispatch. OSRM provides actual road travel time.

**Why these scoring weights?**

Getting the ambulance to the scene fast matters most (0.40) — every minute of delay in cardiac response reduces survival by ~10%. Getting the patient to hospital fast is nearly as important (0.35). Hospital load affects care quality once the patient arrives (0.15). Equipment over-qualification is a small positive signal (0.10).

**Fallback for critical incidents with no qualified ambulance?**

Send whatever is available and flag it — never return an error when lives are at stake.

---

## Roadmap

- [x] Core dispatch engine with hard constraints
- [x] Real road routing via OSRM  
- [x] AI operations assistant
- [x] Prediction engine with hotspot detection
- [ ] WebSocket real-time updates
- [ ] Paramedic mobile app (React Native)
- [ ] GPS turn-by-turn navigation for ambulance crews
- [ ] Live hospital capacity API integration
- [ ] Authentication (dispatcher / supervisor / hospital staff roles)

---

## Author

**Krish Chopda**  
[GitHub](https://github.com/krishchopda)

---

*Built as a portfolio project targeting operations-focused engineering roles. Architecture designed for production scalability — stateless FastAPI instances, PostgreSQL with indexing, service layer separation.*
