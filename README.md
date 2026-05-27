# Smart Mobility Insights System

A smart city mobility platform integrating 11 government open datasets with an interactive route planner, FASTag volume-based toll estimation, traffic-aware routing, weather-aware ETA, road condition reporting. Built with Django 5.2 + SQLite — no PostGIS required (geometries stored as JSONField, haversine for proximity).

---

## Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                         Web Browser                                │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
 │  │         Route Planner (Leaflet map + overlays)                │  │
 │  └──────────────────────────┬───────────────────────────────────┘  │
 └─────────────────────────────┼──────────────────────────────────────┘
                               │
     ┌─────────────────────────┴──────────────────────────────────────┐
    │                     Django (WSGI)                                │
    │  ┌──────────────────────────────────────────────────────────┐   │
    │  │                   URL Router (urls.py)                   │   │
    │  │   /  /admin/  /api/*                                   │   │
    │  └──────────┬───────────────────────────────────────────────┘   │
    │             │                                                    │
    │  ┌──────────┴───────────────────────────────────────────────┐   │
    │  │                    Views (views.py)                      │   │
    │  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │   │
    │  │  │ MapView │ │ 13 API   │ │ Endpoints│ │             │  │   │
    │  │  │(planner)│ │(user)    │ │(staff)   │ │ Endpoints    │  │   │
    │  │  └────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘  │   │
    │  └───────┼───────────┼────────────┼───────────────┼─────────┘   │
    │          │           │            │               │              │
    │  ┌───────┴───────────┴────────────┴───────────────┴─────────┐   │
    │  │                    Service Layer                          │   │
    │  │  routing.py  │  toll_calc.py  │  traffic.py  │  weather  │   │
    │  │  (OSRM+Nom)  │  (FASTag vol)  │  (time/area) │  (OWM)    │   │
    │  └──────────────────────────────────────────────────────────┘   │
    │             │                                                    │
    │  ┌──────────┴───────────────────────────────────────────────┐   │
    │  │                       Models (15)                        │   │
    │  │  Trip │ TollCollection │ CongestionLog │ RoadCondition   │   │
    │  │  TollPlaza │ FASTagTransaction │ NationalHighway         │   │
    │  │  RoadAccident │ RoadAccidentByCollision                  │   │
    │  │  RoadAccidentByRoadUser │ RoadStatistic                  │   │
    │  │  NETCProcessingRate │ NETCUptime │ NETCDispute           │   │
    │  │  EconomicSurvey                                          │   │
    │  └──────────┬───────────────────────────────────────────────┘   │
    │             │                                                    │
    │  ┌──────────┴───────────────────────────────────────────────┐   │
    │  │              SQLite Database (db.sqlite3)                │   │
    │  │              ~210,000 records across 15 tables            │   │
    │  └──────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Features

### Route Planning with Intelligence
- Real-time geocoding (Nominatim) and routing (OSRM)
- **FASTag volume-based toll estimation** — toll calculated from historical transaction data at plazas along your route, with per-plaza breakdown
- Configurable fallback toll calculation (slab-based or dynamic per km)
- Traffic-aware ETA adjustments based on time of day and area congestion
- Road condition factors (potholes, accidents, flooding, closures) affect route delay
- Weather integration (rain, fog, thunderstorms) further adjusts ETA
- Route comparison with distance, ETA, toll, traffic level, and weather
- Toll plaza overlay — 3,453 real toll plazas mapped as interactive markers
- National Highway overlay — 62,030 highway segments rendered as orange GeoJSON (1,004 merged groups)
- NH filter dropdown — search any highway by number, rendered as colored routes

### Road Condition Reporting
- Users report conditions (pothole, poor surface, accident, flooding, closed, etc.)
- Auto-flagging at 3+ reports near the same location
- Color-coded condition markers on the map
- Conditions affect route ETA calculations
- Admin resolve workflow with severity tracking

---

## 11 Integrated Government Datasets

The system pulls data from 7 management commands, each loading real open government data:

| # | Dataset | Source | Records | Command |
|---|---------|--------|--------:|:-------:|
| 1 | **FASTag Transactions** | IHMCL (via OGD India) | 34,530 | `seed_fastag` |
| 2 | **Toll Plazas** | IHMCL (via OGD India) | 3,453 | `seed_fastag` |
| 3 | **National Highway Geospatial** | MORTH (GitHub) | 62,030 features (1,004 groups) | `seed_nh_highways` |
| 4 | **Road Accidents (Violations)** | MORTH (via OGD) | 24 | `seed_road_accidents` |
| 5 | **Road Accidents (Collision Type)** | MORTH (via OGD) | 15 | `seed_road_accidents` |
| 6 | **Road Accidents (Road User)** | MORTH (via OGD) | 18 | `seed_road_accidents` |
| 7 | **Road Statistics** | MORTH (via OGD) | 36 (3 yrs x 6 categories x 2 props) | `seed_road_statistics` |
| 8 | **NETC Processing Rate** | NPCI (via OGD) | 15 | `seed_netc` |
| 9 | **NETC Uptime** | NPCI (via OGD) | 12 | `seed_netc` |
| 10 | **NETC Disputes** | NPCI (via OGD) | 10 | `seed_netc` |
| 11 | **Economic Survey Tables** | MoSPI (historical) | 11 (1961–2024) | `seed_economic_survey` |
| — | **Congestion / Conditions** | User-generated | Dynamic | `seed_data` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.2 |
| Database | SQLite (geometries as JSONField + Python haversine for proximity) |
| Frontend | Bootstrap 5, Leaflet.js, Chart.js |
| External APIs | OSRM (routing), Nominatim (geocoding), OpenWeather (weather) |
| Data Sources | IHMCL, MORTH, NPCI, MoSPI, Open Government Data India |

---

## API Endpoints

### Page Routes

| Page | URL | Auth |
|------|:---:|:----:|
| Route Planner (Map) | `/` | Login |
| Login | `/login/` | Anonymous |
| Register | `/register/` | Anonymous |
| Django Admin | `/admin/` | Staff |

### REST API Endpoints

All require authentication unless noted.

| Endpoint | Method | Auth | Description |
|----------|--------|:----:|-------------|
| `/api/geocode/` | GET | Login | Forward geocode via Nominatim (`?q=`) |
| `/api/reverse-geocode/` | GET | Login | Reverse geocode (`?lat=&lng=`) |
| `/api/route/` | POST | Login | Full route: OSRM routing + FASTag toll + traffic + weather + conditions |
| `/api/trips/` | GET | Login | Current user's trip history (paginated, 100/page) |
| `/api/road-conditions/` | GET | Login | Road conditions with optional lat/lng/radius filter |
| `/api/road-conditions/report/` | POST | Login | Report a road condition (JSON body) |
| `/api/road-conditions/<id>/resolve/` | POST | Staff | Resolve/verify a condition |
| `/api/road-conditions/stats/` | GET | No Auth | Condition type/severity breakdown |
| `/api/fastag/stats/` | GET | Login | FASTag transaction volume & amount by state |
| `/api/toll-plazas/` | GET | Login | All toll plazas with lat/lng for map overlay |
| `/api/national-highways/` | GET | Login | All NH features merged by number, simplified GeoJSON |
| `/api/road-accidents/stats/` | GET | Login | Accident totals by state and violation type |
| `/api/road-statistics/` | GET | Login | Road length by year (total vs surfaced) + by category |
| `/api/netc/stats/` | GET | Login | NETC processing rates, uptime, dispute totals |
| `/api/economic-survey/` | GET | Login | Road network growth across planning eras |
| `/api/road-collisions/stats/` | GET | Login | Collisions by type with totals (accidents, killed, injured) |
| `/api/road-users/stats/` | GET | Login | Road user type breakdown |
| `/api/netc/disputes/` | GET | Login | NETC dispute records by bank/category |
| `/api/admin/stats/` | GET | Staff | Revenue analytics + vehicle breakdown |
| `/health/` | GET | No Auth | Health check — returns `{"status": "ok"}` |

---

## Map Overlays

On the route planner page (`/`), toggle buttons control:

| Overlay | Button | What it shows |
|---------|--------|:-------------|
| Toll Plazas | `Show Toll Plazas` | Purple markers for 3,453 seeded plazas with name/state/type popups |
| National Highways | `Show Highways` | Orange lines for 62,030 highway segments merged into 1,004 NH groups |
| Road Conditions | `Show Road Conditions` | Letter-coded markers (P=pothole, A=accident, C=construction...) |
| Traffic | `Show Traffic` | Circles sized by severity (green→yellow→orange→red) |
| NH Filter | Dropdown | Select a specific NH number → highway highlights on map |

---

## Project Structure

```
smart-mobility-insights/
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── data/
│   └── config.json                # Toll slabs, multipliers, traffic config
├── mobility/                      # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── insights/                      # Django app
│   ├── models.py                  # 15 models
│   ├── views.py                   # All views + 20 API endpoints
│   ├── urls.py                    # URL routing (31 paths)
│   ├── admin.py                   # Django admin registrations
│   ├── forms.py                   # Login/Register forms
│   ├── routing.py                 # Geocoding (Nominatim) + OSRM routing
│   ├── toll_calc.py               # FASTag volume-based + config-based toll
│   ├── traffic.py                 # Traffic factor by time/area
│   ├── road_conditions.py         # Auto-flagging + route impact
│   ├── weather.py                 # OpenWeather integration
│   ├── utils.py                   # Shared utility functions
│   ├── datasets/                  # Dataset ingestion modules
│   │   ├── __init__.py
│   │   ├── fastag.py              # FASTag + TollPlaza parser
│   │   ├── nh_geospatial.py       # National Highway GeoJSON parser
│   │   ├── road_accidents.py      # Road accident records parser
│   │   ├── road_statistics.py     # Road length stats parser
│   │   ├── netc_performance.py    # NETC rate/uptime/dispute parser
│   │   ├── economic_survey.py     # Economic survey tables parser
│   │   └── ogd_client.py          # Open Government Data API client
│   ├── management/commands/
│   │   ├── seed_data.py           # Base demo data (trips, conditions, users)
│   │   ├── seed_fastag.py         # FASTag transactions + TollPlazas
│   │   ├── seed_nh_highways.py    # National Highway geospatial
│   │   ├── seed_road_accidents.py # Road accident records
│   │   ├── seed_road_statistics.py# Road length statistics
│   │   ├── seed_netc.py           # NETC processing/uptime/disputes
│   │   └── seed_economic_survey.py# Economic survey tables
│   ├── templates/
│   │   ├── base.html              # Base layout with nav + dark map
│   │   ├── index.html             # Route planner with map + overlays
 │   │   └── registration/
│   │       ├── login.html
│   │       └── register.html
│   ├── static/vendor/
│   │   ├── bootstrap/5.3.3
│   │   ├── leaflet/1.9.4
│   │   └── chartjs/4.4.8
│   └── migrations/
├── staticfiles/                   # Collected static files
└── db.sqlite3                     # SQLite database
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- pip

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` as needed. Defaults work for local development. The only optional key is `OPENWEATHER_API_KEY` (weather features work without it, but with reduced data).

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Seed All Data

```bash
# Base demo data (users, trips, conditions)
python manage.py seed_data

# Government open datasets
python manage.py seed_fastag                      # 34,530 FASTag transactions + 3,453 toll plazas
python manage.py seed_nh_highways                 # 62,030 national highway features (50MB GeoJSON)
python manage.py seed_road_accidents              # 24 violations + 15 collisions + 18 road users
python manage.py seed_road_statistics             # 36 road length records (3 years x 6 categories)
python manage.py seed_netc                        # 15 rates + 12 uptimes + 10 disputes
python manage.py seed_economic_survey             # 11 historical records (1961-2024)
```

### 6. Start Server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. Log in with:
- **Demo user**: username `user`, password `user1234`
- **Admin user**: username `admin`, password `admin123`

### Quick Access Links

| Page | URL |
|------|:---:|
| Route Planner (Map) | `http://127.0.0.1:8000/` |
| Login | `http://127.0.0.1:8000/login/` |
| Register | `http://127.0.0.1:8000/register/` |
| Django Admin | `http://127.0.0.1:8000/admin/` |
| Health Check | `http://127.0.0.1:8000/health/` |

---

## Toll Calculation

### Primary Method — FASTag Volume-Based

When a route is planned, the system:

1. **Extracts coordinates** from the OSRM route geometry
2. **Searches for nearby toll plazas** within 5 km of the route path
3. **Computes average toll** at each plaza from seeded FASTag transaction data (`amount_collected / vehicle_count`)
4. **Applies vehicle multiplier** (`bike: 0.5x`, `car: 1.0x`, `bus: 1.5x`, `truck: 2.0x`, `ambulance: free`)
5. **Sums all plaza tolls** → total route toll
6. **Shows per-plaza breakdown** on the route card with plaza name, state, and individual toll

If no plazas are found near the route, it falls back to the config-based formula.

### Fallback Method — Config-Based

| Distance | Model | Base Rate |
|:--------:|:-----:|:---------:|
| ≤ 5 km | Slab | ₹10 |
| 5–10 km | Slab | ₹20 |
| 10–15 km | Slab | ₹30 |
| 15–20 km | Slab | ₹40 |
| > 20 km | Slab | ₹60 |
| > 10 km | Dynamic | ₹2.00/km |

### Method Comparison

| Aspect | Config-Based | FASTag Volume-Based |
|--------|:------------:|:-------------------:|
| **Data Source** | Static `config.json` values | Seeded FASTag transactions from 3,453 real plazas |
| **Route Awareness** | None — flat per-km regardless of route | Route-aware — identifies plazas along actual path |
| **State Variation** | Same rate nationwide | State-specific — each plaza has its own historical average |
| **Vehicle Handling** | Config multiplier applied to flat base | Multiplier applied to each plaza's actual average toll |
| **Accuracy** | Approximate formula | Statistical average from real transaction data |
| **Per-Plaza Breakdown** | Not shown | Displayed on route card — name, state, and per-plaza toll |
| **Fallback** | N/A (primary method) | Falls back to config-based when no plazas near route |
| **Pricing Model Label** | `slab` or `dynamic` | `fastag` with blue badge on route card |
| **Frontend Display** | Single total on route card | Per-plaza list + total with names and states |

---

## Configuration

Toll pricing, vehicle multipliers, peak hours, congestion thresholds, and weather factors are in `data/config.json`. Edit this file to adjust system behavior without code changes.

```json
{
  "toll": {
    "slabs": [
      { "max_km": 5, "rate": 10 },
      { "max_km": 10, "rate": 20 },
      { "max_km": 15, "rate": 30 },
      { "max_km": 20, "rate": 40 },
      { "rate": 60 }
    ],
    "dynamic_rate_per_km": 2.0,
    "decision_threshold_km": 10,
    "vehicle_multipliers": {
      "bike": 0.5, "car": 1.0, "bus": 1.5, "truck": 2.0, "ambulance": 0
    }
  },
  "traffic": {
    "peak_hours": {
      "morning": { "start": 8, "end": 10 },
      "evening": { "start": 17, "end": 19 }
    },
    "congestion_factors": {
      "low": 1.0, "moderate": 1.3, "high": 1.5, "severe": 1.8
    }
  }
}
```

---

## Running Tests

```bash
python manage.py test
```

Tests cover haversine distance, toll calculation (2 methods), trip model, toll collection, National Highway model, API views, routing, and road condition reporting.

---

## Security Notes

- `DEBUG = True` in `.env` for development; set `False` for production
- Update `SECRET_KEY` in `.env` for production — never commit the real key
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `.env` for deployment
- Most API endpoints require login (`@login_required` or `@staff_member_required`)
- Password validators enforce minimum 8 chars, no common/numeric-only passwords
- Rate limiting on login (10 attempts per 60 seconds per IP)
- No API keys or secrets are hardcoded in the codebase
