# Automated IT Ticket Classification & Lifecycle Management System

An intelligent, AI-powered IT Helpdesk and Service Management backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Scikit-learn**, and **NLP (TF-IDF + Calibrated Classifiers)**.

The system automatically understands raw IT ticket inquiries, predicts **Category**, **Subcategory**, and **Priority**, calculates **SLA deadlines**, auto-routes to departments, performs **workload-balanced agent assignment**, captures **human feedback**, and provides real-time **analytics** and an interactive **Dashboard UI**.

---

## Architecture Overview

```
                                  +-----------------------+
                                  |     Web Dashboard /   |
                                  |     REST API Client   |
                                  +-----------+-----------+
                                              |
                                              v
                                   FastAPI Application
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
           Authentication & RBAC                              Ticket Service Layer
        (JWT, Passlib, Roles:                                          |
     Admin, Manager, Agent, User)                                      v
                                                          ML Inference & NLP Engine
                                                                       |
                                                +----------------------+----------------------+
                                                |                      |                      |
                                                v                      v                      v
                                         Category Model        Subcategory Model       Priority Model
                                      (Logistic Regression)   (Logistic Regression)  (Logistic Regression)
                                                |                      |                      |
                                                +----------------------+----------------------+
                                                                       |
                                                                       v
                                                        Confidence & SLA Calculator
                                                                       |
                                                        +--------------+--------------+
                                                        |                             |
                                                        v                             v
                                             Auto-Department Routing        Load-Balanced Agent
                                                                                Assignment
                                                                       |
                                                                       v
                                                            Database (PostgreSQL / SQLite)
```

---

## Key Features

- **Automated Multi-Target ML Classification**: Uses NLP text cleaning, negation preservation, TF-IDF vectorization with n-grams, and 3 dedicated calibrated classification models.
- **Dynamic Confidence Scoring & Human-In-The-Loop**: Calculates real-time prediction confidence. Classifications below threshold (`0.80`) are flagged `needs_review = true` and routed to the technician review queue.
- **Continuous Learning & Feedback Loop**: When technicians correct or confirm a classification, the data is automatically appended to the training dataset and available for background retraining.
- **Load-Balanced Agent Auto-Assignment**: Evaluates technician workloads across departments and automatically assigns new tickets to the least-burdened available technician.
- **SLA Tracking & Breach Detection**: Assigns SLA resolution deadlines based on ticket priority (Critical: 2h, High: 4h, Medium: 24h, Low: 72h) and actively monitors breach status.
- **Role-Based Access Control (RBAC)**: Secure access tailored for Employees, Agents, Managers, and System Administrators.
- **Interactive Single-Page Dashboard (`/dashboard`)**: Visual dashboard with live AI sandbox, ticket queue, lifecycle actions, comments thread, analytics charts, and model retraining panel.
- **FastAPI Swagger UI (`/docs`) & ReDoc (`/redoc`)**: Interactive OpenAPI specification with token authorization.

---

## Project Structure

```
helpdesk/
├── app/
│   ├── main.py                     # FastAPI application factory & lifespan
│   ├── core/                       # Config, security, logging, exceptions
│   ├── database/                   # SQLAlchemy engine, session maker, Base models
│   ├── models/                     # User, Role, Department, Category, Ticket, MLModel, AuditLog
│   ├── schemas/                    # Pydantic validation schemas
│   ├── api/v1/                     # REST API routers (Auth, Tickets, ML, Analytics, etc.)
│   ├── services/                   # Service layer business logic
│   ├── ml/                         # Preprocessing, training, inference, model manager
│   │   └── artifacts/              # Serialized models and vectorizer (.joblib)
│   └── static/                     # Interactive Helpdesk Dashboard UI (HTML, CSS, JS)
├── data/
│   ├── training/tickets.csv        # Comprehensive dataset (760+ realistic IT tickets)
│   └── uploads/                    # Ticket attachments directory
├── scripts/
│   ├── seed_database.py            # Initial seed script (Roles, Departments, Users, Tickets)
│   ├── train_model.py              # ML model training CLI
│   └── generate_dataset.py         # Synthetic dataset generator
├── tests/                          # Pytest test suite (Auth, Tickets, ML, Analytics)
├── Dockerfile                      # Production container image
├── docker-compose.yml              # Multi-container Postgres + API setup
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Environment variable template
└── README.md
```

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### 2. Installation
```bash
# Clone or navigate to the repository
cd helpdesk

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Data & Train ML Models
```bash
# Generate training dataset
python scripts/generate_dataset.py

# Train baseline ML models and save artifacts
python scripts/train_model.py

# Seed database with initial roles, departments, users, and sample tickets
python scripts/seed_database.py
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload --port 8000
```

Access the application:
- **Interactive Web Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Pre-Configured Seed Users

| Email | Role | Department | Password |
| :--- | :--- | :--- | :--- |
| `admin@example.com` | ADMIN | - | `AdminPass123!` |
| `manager@example.com` | MANAGER | IT Helpdesk | `ManagerPass123!` |
| `network.agent@example.com` | AGENT | Network Support | `AgentPass123!` |
| `hardware.agent@example.com` | AGENT | Hardware Support | `AgentPass123!` |
| `security.agent@example.com` | AGENT | Security | `AgentPass123!` |
| `rajan@example.com` | EMPLOYEE | - | `UserPass123!` |
| `alice@example.com` | EMPLOYEE | - | `UserPass123!` |

---

## API Map

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` - Register a new user account
- `POST /api/v1/auth/login` - Authenticate and receive JWT bearer token
- `GET /api/v1/auth/me` - Fetch profile of currently authenticated user

### Tickets (`/api/v1/tickets`)
- `POST /api/v1/tickets` - Submit new ticket (Triggers ML classification, SLA calculation, and agent assignment)
- `GET /api/v1/tickets` - List tickets with filtering (`status`, `priority`, `category`, `assigned_to`, `needs_review`) and pagination
- `GET /api/v1/tickets/search?q={query}` - Search tickets across titles, numbers, categories, and descriptions
- `GET /api/v1/tickets/{id}` - Retrieve detailed ticket record
- `PATCH /api/v1/tickets/{id}` - Update ticket fields
- `POST /api/v1/tickets/{id}/assign` - Reassign ticket to specific technician
- `POST /api/v1/tickets/{id}/resolve` - Mark ticket as resolved with resolution details
- `POST /api/v1/tickets/{id}/close` - Close resolved ticket
- `POST /api/v1/tickets/{id}/reopen` - Reopen ticket for further investigation

### Classification & Machine Learning (`/api/v1/classification`, `/api/v1/models`)
- `POST /api/v1/classification/predict` - Standalone ML prediction endpoint (returns Category, Priority, Department, Confidence)
- `POST /api/v1/classification/batch` - Batch classification for high-volume inputs
- `POST /api/v1/feedback` - Human-in-the-loop correction endpoint (updates record and feeds retraining)
- `GET /api/v1/models` - List registered model versions and validation metrics
- `POST /api/v1/models/train` - Trigger background/synchronous model retraining
- `POST /api/v1/models/{id}/activate` - Switch active serving model version

### Analytics & SLA (`/api/v1/analytics`)
- `GET /api/v1/analytics/tickets` - Overall status breakdown (Open, In Progress, Resolved, Closed, Review)
- `GET /api/v1/analytics/categories` - Volume distribution by category
- `GET /api/v1/analytics/priorities` - Volume distribution by priority
- `GET /api/v1/analytics/sla` - Average resolution time, breach counts, compliance rate
- `GET /api/v1/analytics/agents` - Workload distribution across agents

---

## Running with Docker Compose

To deploy with PostgreSQL in a multi-container architecture:

```bash
docker-compose up --build -d
```

This starts:
1. `helpdesk_postgres`: PostgreSQL 16 on port `5432` with health checks and persistent volume
2. `helpdesk_api`: FastAPI application on port `8000` connected to PostgreSQL

---

## Running Automated Tests

Run the complete test suite:
```bash
python -m pytest -v
```
