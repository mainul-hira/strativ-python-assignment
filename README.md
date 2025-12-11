# Bangladesh Travel Weather API

A Django REST API that helps users find the best districts in Bangladesh for travel based on temperature and air quality data. The API fetches real-time weather forecasts and air quality metrics from Open-Meteo and provides intelligent travel recommendations.

## Features

- **JWT Authentication**: Secure user registration, login, and token-based authentication
- **Top 10 Districts**: Get the coolest and cleanest districts in Bangladesh based on 7-day average temperature and PM2.5 levels
- **District List**: Get all districts with their coordinates for easy reference
- **Travel Recommendations**: Compare your current location with a destination district to get personalized travel advice
- **Real-time Data**: Weather forecasts and air quality data updated periodically from Open-Meteo API
- **Fast Response**: Optimized for sub-500ms response times with database caching

## Technology Stack

- **Python**: 3.13
- **Django**: 5.2.9
- **Django REST Framework**: 3.16.1
- **JWT Authentication**: djangorestframework-simplejwt 5.5.1
- **PostgreSQL**: Database for storing district data and metrics
- **Open-Meteo API**: External API for weather and air quality data

## Prerequisites

Before running this project, ensure you have the following installed:

- Python 3.13 or higher
- PostgreSQL 15 or higher
- pip (Python package manager)
- virtualenv (recommended)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd strativ-python-assignment
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- Django==5.2.9
- djangorestframework==3.16.1
- djangorestframework-simplejwt==5.5.1
- django-cors-headers==4.9.0
- django-environ==0.12.0
- psycopg==3.3.2
- requests==2.32.5

### 4. Database Setup

#### Create PostgreSQL Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE travel_weather;

# Create user (optional, if not using existing user)
CREATE USER your_db_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE travel_weather TO your_db_user;

# Exit PostgreSQL
\q
```

### 5. Environment Configuration

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=travel_weather
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_LOG_LEVEL=ERROR
LOG_LEVEL=DEBUG
```

**Important**: You can generate secret key using:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Load District Data

Load the Bangladesh district data from the JSON file:

```bash
python manage.py load_districts
```

This command will populate the database with all 64 districts of Bangladesh including their coordinates.

### 8. Update District Metrics

Fetch weather and air quality data from Open-Meteo and calculate metrics:

```bash
python manage.py update_district_metrics
```

This command should be run periodically (e.g., via cron job) to keep the data fresh. The Open-Meteo API updates forecasts periodically, so running this command once or twice daily is recommended.

### 9. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication Endpoints

#### 1. Register

**Endpoint**: `POST /api/v1/auth/register`

**Authentication**: Not required

Create a new user account.

**Request Body**:

```json
{
  "username": "mainul_hira",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Response Example**:

```json
{
  "id": 1,
  "username": "mainul_hira"
}
```

#### 2. Login

**Endpoint**: `POST /api/v1/auth/login`

**Authentication**: Not required

Obtain JWT access and refresh tokens.

**Request Body**:

```json
{
  "username": "mainul_hira",
  "password": "SecurePass123!"
}
```

**Response Example**:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token Lifetimes**:
- Access Token: 30 minutes
- Refresh Token: 7 days

#### 3. Token Refresh

**Endpoint**: `POST /api/v1/auth/token-refresh`

**Authentication**: Not required

Refresh an expired access token using a valid refresh token.

**Request Body**:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response Example**:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 4. Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Authentication**: Required (Bearer Token)

Blacklist the refresh token to prevent further use.

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**: `204 No Content`

---

### Travel & Weather Endpoints

**Note**: All endpoints below require authentication. Include the JWT access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

#### 5. District List

**Endpoint**: `GET /api/v1/districts`

**Authentication**: Required

Get a list of all 64 districts in Bangladesh with their coordinates.

**Response Example**:

```json
[
  {
    "id": 1,
    "name": "Dhaka",
    "latitude": 23.8103,
    "longitude": 90.4125
  },
  {
    "id": 2,
    "name": "Chittagong",
    "latitude": 22.3569,
    "longitude": 91.7832
  }
  // ... 62 more districts
]
```

#### 6. Top 10 Districts

**Endpoint**: `GET /api/v1/top-districts`

**Authentication**: Required

Returns the top 10 best districts for travel based on coolest temperature and best air quality.

**Response Example**:

```json
[
  {
    "rank": 1,
    "district_id": 42,
    "district_name": "Rangamati",
    "avg_temp_2pm_7day": 28.5,
    "avg_pm25_7day": 15.2,
    "last_updated": "2024-12-11T12:30:00+06:00"
  },
  {
    "rank": 2,
    "district_id": 15,
    "district_name": "Sylhet",
    "avg_temp_2pm_7day": 29.1,
    "avg_pm25_7day": 18.7,
    "last_updated": "2024-12-11T12:30:00+06:00"
  }
  // ... 8 more districts
]
```

**Ranking Logic**:
- Primary sort: Average temperature at 2 PM (ascending - cooler first)
- Secondary sort: Average PM2.5 levels (ascending - cleaner air first if same temperature)

#### 7. Travel Recommendation

**Endpoint**: `POST /api/v1/travel-recommendation`

**Authentication**: Required

Compare your current location with a destination district and get a travel recommendation.

**Request Body**:

```json
{
  "current_lat": 23.8103,
  "current_lon": 90.4125,
  "destination_district_id": 14,
  "travel_date": "2024-12-14"
}
```

**Request Parameters**:
- `current_lat` (float): Your current latitude
- `current_lon` (float): Your current longitude
- `destination_district_id` (integer): ID of the destination district
- `travel_date` (string): Travel date in YYYY-MM-DD format (must be within next 5 days)

**Response Example (Recommended)**:

```json
{
  "status": "Recommended",
  "reason": "Your destination (Rangamati) is 3.2°C cooler and has significantly better air quality than your current location. Enjoy your trip!",
  "travel_date": "2024-12-15",
  "current": {
    "temperature_2pm": 31.5,
    "pm25_2pm": 45.3
  },
  "destination": {
    "district": "Rangamati",
    "temperature_2pm": 28.3,
    "pm25_2pm": 18.7
  }
}
```

**Response Example (Not Recommended)**:

```json
{
  "status": "Not Recommended",
  "reason": "Your destination (Dhaka) is hotter and has worse air quality than your current location. It's better to stay where you are.",
  "travel_date": "2024-12-15",
  "current": {
    "temperature_2pm": 28.5,
    "pm25_2pm": 25.3
  },
  "destination": {
    "district": "Dhaka",
    "temperature_2pm": 32.1,
    "pm25_2pm": 65.8
  }
}
```

**Recommendation Logic**:
- **Recommended**: Destination is both cooler AND has better air quality
- **Not Recommended**: Destination is hotter OR has worse air quality (or both)

## Project Structure

```
strativ-python-assignment/
├── data/
│   └── bd-districts.json          # Bangladesh district data
├── travel/                         # Travel & weather app
│   ├── api/
│   │   ├── serializers.py         # Request/response serializers
│   │   ├── urls.py                # API URL routing
│   │   └── views.py               # API view classes
│   ├── management/
│   │   └── commands/
│   │       ├── load_districts.py           # Load district data
│   │       └── update_district_metrics.py  # Update weather metrics
│   ├── models.py                  # District and DistrictMetrics models
│   └── services.py                # Business logic and Open-Meteo client
├── users/                          # Authentication app
│   └── api/
│       ├── serializers.py         # User auth serializers
│       ├── urls.py                # Auth URL routing
│       └── views.py               # Auth view classes
├── travel_weather/                # Django project settings
│   ├── settings.py                # Project settings with JWT config
│   └── urls.py                    # Root URL configuration
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
└── manage.py                      # Django management script
```

## Management Commands

### Load Districts

```bash
python manage.py load_districts
```

Loads district data from `data/bd-districts.json` into the database. This command:
- Creates or updates all 64 districts
- Uses bulk operations for efficiency on first load
- Can be run multiple times safely (idempotent)

### Update District Metrics

```bash
python manage.py update_district_metrics
```

Fetches weather and air quality data from Open-Meteo API and updates metrics. This command:
- Fetches 7-day forecasts for all districts
- Calculates average temperature at 2 PM
- Calculates average PM2.5 levels at 2 PM
- Updates or creates metrics records
- Should be scheduled to run periodically



## Development Notes

### Time Considerations
    •	All times are in Asia/Dhaka timezone (UTC+6)
    •	Temperature and PM2.5 are measured at 2 PM (14:00) local time
    •	Travel date must be within the next 5 days (Open-Meteo forecast limitation)

### Why use a management command instead of Celery or cron?

The assignment asked to “take super simple approaches”.
A management command:
	•	Is easy to run manually
	•	Avoids extra complexity (Celery, Redis, worker processes)
	•	Fits within the assignment time constraints
	•	Keeps the API extremely fast by precomputing metrics
	•	Is idiomatic in Django for batch jobs

If needed, this same command can later be run on a cron schedule without code changes.


### Why precompute 7-day averages?
	•	Open-Meteo API calls are relatively slow (700–900ms each).
	•	Precomputing avoids calling external APIs inside request-response cycle.
	•	Makes /top-districts respond under 500ms as required.


### Why use a service layer?
	•	Keeps view code thin and clean
	•	Makes business logic reusable (API + commands share the same services)
	•	Easier to test and modify
	•	Prevents duplication of Open-Meteo logic

### Why travel-recommendation api travel_date restrict to 5days?
    The Open-Meteo Air Quality API's 7-day forecast often returns null data for the last two days. To ensure reliable air quality data, the `travel_date` is restricted to 5 days, which aligns with the API's more consistent 5-day forecast.
	


## Data Sources

- **District Data**: [Bangladesh Districts JSON](https://raw.githubusercontent.com/strativ-dev/technical-screening-test/main/bd-districts.json)
- **Weather Data**: [Open-Meteo Weather API](https://open-meteo.com/en/docs)
- **Air Quality Data**: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api)

