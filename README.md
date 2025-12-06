# Cyprus Dam Water Levels API

Real-time dam water levels and predictive insights for Cyprus.

---

## Quickstart

### Prerequisites

- Python 3.10+

### Setup

```bash
# Clone and navigate to project
cd smart-pafos-360-hackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn main:app --reload
# or 
fastapi dev main.py
```

The API will be available at **http://localhost:8000**

### Verify

- Open http://localhost:8000 — API info
- Open http://localhost:8000/health — Health check
- Open http://localhost:8000/docs — Interactive Swagger docs

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/summary` | Overview of all dams |
| `GET /api/dams` | List all dams with current levels |
| `GET /api/dam?name={name}` | Single dam details |
| `GET /api/trend` | Historical trend data |
| `GET /api/forecast` | Predictive capacity forecast |
| `GET /api/narrative` | AI-generated narrative insights |

---

## Configuration

Environment defaults in `app/config.py`:

- **Database:** SQLite (`cyprus_dams.db`)
- **External API:** https://cyprus-water.appspot.com
- **Cache TTL:** 1 hour

