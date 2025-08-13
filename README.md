# E-Book Processing Backend

A secure backend for an e-book processing web application with authentication, file upload, text/image/formula/font/layout extraction, XML validation, format conversion, dashboard stats, and premium pricing.

## Features

- **Authentication**: JWT-based authentication with access & refresh tokens
- **Role-based Access Control**: Free, Premium, Admin user roles
- **E-Book Upload & Processing**:
  - Support for PDF, DOCX, EPUB formats
  - Extraction of text, images, formulas, fonts, layout
  - XML generation with validation rules
  - Conversion to HTML, EPUB, MOBI
- **Dashboard**:
  - User statistics: books uploaded, completed, in-progress, failed
  - Admin dashboard for all users' uploads with filtering
  - Detailed per-upload information
- **Pricing / Premium Features**:
  - Free tier with limits on file size and daily conversions
  - Premium tier with higher limits and priority processing
  - Admin-configurable pricing plans

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with passlib for password hashing
- **File Processing**: PyPDF2, python-docx, ebooklib, Pillow, pytesseract
- **Background Tasks**: FastAPI BackgroundTasks (Celery optional)

## Project Structure

```
/app
    main.py               # FastAPI application entry point
    /api                  # API endpoints versioning
        /api_v1           # API v1 endpoints
    /core                 # Core configuration
        config.py         # Environment variables and settings
    /db                   # Database
        base_class.py     # SQLAlchemy base class
        session.py        # Database session
    /models               # SQLAlchemy models
        user.py           # User model
        upload.py         # Upload model
        pricing.py        # Pricing plans model
    /schemas              # Pydantic schemas for API
        user.py           # User schemas
        upload.py         # Upload schemas
        pricing.py        # Pricing plan schemas
    /routes               # API route handlers
        auth.py           # Authentication routes
        upload.py         # Upload routes
        dashboard.py      # Dashboard routes
        pricing.py        # Pricing plan routes
        downloads.py      # File download routes
    /services             # Business logic services
        extraction.py     # E-book content extraction
        xml_validation.py # XML validation
        conversion.py     # Format conversion
    /utils                # Utility functions
        jwt_handler.py    # JWT token handling
        file_utils.py     # File utilities
        dependencies.py   # FastAPI dependencies
migrations/               # Database migrations with Alembic
requirements.txt          # Python dependencies
.env.example              # Example environment variables
Dockerfile                # Docker configuration
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Redis (optional, for Celery background tasks)
- Tesseract OCR (for formula detection)

### Environment Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your database and JWT settings

### Database Setup

1. Create a PostgreSQL database:
   ```bash
   createdb ebook_app
   ```

2. Run database migrations:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

### Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. The API will be available at http://localhost:8000
3. API documentation is available at http://localhost:8000/api/v1/docs

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t ebook-backend .
   ```

2. Run the container:
   ```bash
   docker run -d -p 8000:8000 --env-file .env ebook-backend
   ```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register`: Register a new user
- `POST /api/v1/auth/login`: Login and get access token
- `POST /api/v1/auth/refresh`: Refresh access token
- `POST /api/v1/auth/logout`: Logout (optional token blacklisting)
- `GET /api/v1/auth/me`: Get current user information

### Uploads

- `POST /api/v1/uploads`: Upload a new e-book
- `GET /api/v1/uploads`: List all uploads for current user
- `GET /api/v1/uploads/{upload_id}`: Get details for a specific upload
- `DELETE /api/v1/uploads/{upload_id}`: Delete an upload

### Dashboard

- `GET /api/v1/dashboard/statistics`: Get current user's upload statistics
- `GET /api/v1/dashboard/admin`: (Admin only) Get all uploads with filtering
- `GET /api/v1/dashboard/admin/statistics`: (Admin only) Get system-wide statistics

### Pricing

- `GET /api/v1/pricing`: List all pricing plans
- `POST /api/v1/pricing`: (Admin only) Create a new pricing plan
- `PUT /api/v1/pricing/{plan_id}`: (Admin only) Update a pricing plan
- `DELETE /api/v1/pricing/{plan_id}`: (Admin only) Delete a pricing plan

### Downloads

- `GET /api/v1/downloads/{user_id}/{filename}`: Download a processed file

## Initial Setup

Create initial admin user and pricing plans:

```python
# Create admin user
from app.models.user import User, UserRole
from app.utils.jwt_handler import get_password_hash
from app.db.session import SessionLocal

db = SessionLocal()
admin = User(
    email="admin@example.com",
    hashed_password=get_password_hash("adminpassword"),
    first_name="Admin",
    last_name="User",
    role=UserRole.ADMIN
)
db.add(admin)
db.commit()

# Create pricing plans
from app.models.pricing import PricingPlan

free_plan = PricingPlan(
    name="Free",
    description="Basic e-book processing",
    price_monthly=0,
    price_yearly=0,
    max_file_size=10485760,  # 10MB
    daily_conversions_limit=3,
    is_active=True
)

premium_plan = PricingPlan(
    name="Premium",
    description="Advanced e-book processing with higher limits",
    price_monthly=9.99,
    price_yearly=99.99,
    max_file_size=104857600,  # 100MB
    daily_conversions_limit=20,
    is_active=True
)

db.add(free_plan)
db.add(premium_plan)
db.commit()
db.close()
```

## Testing

Run the tests using pytest:

```bash
pytest
```

## License

[MIT License](LICENSE)