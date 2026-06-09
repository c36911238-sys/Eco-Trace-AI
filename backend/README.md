# ⚙️ EcoTrace AI+ Backend (FastAPI Core)

> **The high-performance API server and Machine Learning engine for EcoTrace AI+, built with FastAPI, SQLite, Scikit-Learn, and SHAP.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&style=flat-square)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&style=flat-square)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy--Asyncio-red?style=flat-square)](https://www.sqlalchemy.org)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E?logo=scikit-learn&style=flat-square)](https://scikit-learn.org)
[![SHAP](https://img.shields.io/badge/Explainable%20AI-SHAP-blue?style=flat-square)](https://github.com/shap/shap)

The EcoTrace AI+ backend serves as the core coordinator for database operations, authentication, ML classification, SHAP explanations, and scenario forecasting.

---

## ✨ Backend Features & Capabilities

- **TreeExplainer SHAP Calculator**: Uses a pre-trained Random Forest Regressor to compute Shapley Additive exPlanations for carbon consumption, outputting marginal CO₂ impacts for each log category.
- **Linear Regression Forecasting**: Provides a time-series predictor that forecasts base emissions and projects savings for custom lifestyle modification scenarios.
- **Asynchronous SQLite Engine**: Fully async endpoints leveraging SQLAlchemy and `aiosqlite` for database communication, preventing main-thread blocking during ML calculations.
- **Automated Database Initialization**: Uses FastAPI lifespan events to auto-generate DB tables on startup, ensuring zero manual database configuration.
- **Secure Authentication**: Implements JWT (JSON Web Tokens) with Bcrypt password hashing.

---

## 🛠️ Technology Stack

- **Web framework**: FastAPI
- **Server**: Uvicorn
- **ORM / Database**: SQLAlchemy (Asyncio runtime) + SQLite (`aiosqlite`)
- **Data Modelling**: Pydantic v2
- **ML & Explanations**: Scikit-Learn, SHAP, Pandas, NumPy
- **Auth**: Passlib (Bcrypt), Python-jose

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Virtualenv (`pip install virtualenv` if not installed)

### 1. Initialize Virtual Environment
```bash
python -m venv venv
```

Activate the environment:
* **Windows**: `.\venv\Scripts\activate`
* **macOS/Linux**: `source venv/bin/activate`

### 2. Install Packages
```bash
pip install -r requirements.txt
```

### 3. Run Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to interact with the OpenAPI/Swagger documentation.

---

## 📁 Key File Structure

```
backend/
├── app/
│   ├── api/                # Endpoint routers
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py      # User registration & token generation
│   │       │   └── carbon.py    # Log posting, SHAP insights, and Twin simulations
│   │       └── router.py        # Master v1 router
│   ├── core/
│   │   └── config.py            # Global project config & schema validation
│   ├── db/
│   │   ├── database.py          # Session engines
│   │   └── models.py            # SQLAlchemy tables (User, CarbonLog, etc.)
│   ├── schemas/
│   │   ├── auth.py              # Pydantic schemas for logins
│   │   └── carbon.py            # Pydantic schemas for logs & simulators
│   └── services/
│       ├── ai_explain.py        # Random Forest model + SHAP explanation runner
│       ├── twin_simulate.py     # Linear Regression forecasting simulator
│       └── ocr.py               # Document & receipt text classification mock
└── requirements.txt         # Core dependencies
```

---

*Developed with 💚 by the EcoTrace AI*
