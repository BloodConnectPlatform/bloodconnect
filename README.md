# Blood Connect

A donor discovery and connection platform designed to connect registered, verified blood donors with people seeking blood based on blood group and location.

> **Disclaimer**: Blood Connect is purely a connection platform and **NOT a blood bank**. It does not collect, store, test, transport, or handle blood. All medical checks, compatibility verification, and donation procedures must be carried out by authorized hospitals and medical professionals.

---

## 🚀 Quickstart (Backend)

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone <repo-url>
cd BloodConnect

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment
```bash
cp backend/.env.example backend/.env
```

### 5. Run Migrations & Seed Database (Locations & Sample Users)
```bash
cd backend
alembic upgrade head
python seed.py
```
*(Or from the project root: `python seed.py`)*


### 6. Run Automated Tests
```bash
pytest -v backend/tests
```

### 7. Start the FastAPI Development Server
```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- API Root: `http://127.0.0.1:8000/`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

## 🏛️ Architecture & Entity Model

See [ARCHITECTURE.md](ARCHITECTURE.md) for full ERD diagrams, schema definitions, indexes, and design decisions.

---

## 📊 Predefined Locations

Initial coverage includes:
- Coimbatore
- Sulur
- Tiruppur
- Pollachi
- Mettupalayam
- Avinashi
- Palladam
- Udumalpet
- Annur
- Madukkarai
- Perur

---

## 🔒 Privacy Guarantees
- Public search results conceal donor mobile numbers.
- Requester contact information is only revealed to the donor upon explicit request acceptance.
- OTPs are hashed and subject to expiry (5 mins) and attempt limiting (3 max).
