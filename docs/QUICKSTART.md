# Nextbin Django Project

A comprehensive, production-ready Django REST API framework with integrated Swagger/OpenAPI documentation.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Initialize Database
```bash
python manage.py migrate
python manage.py create_superuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Access the API at: http://localhost:8000

### 5. View API Documentation
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Docker Compose

```bash
docker-compose up
# Access at http://localhost:8000
```

## Project Apps

1. **Core** - Central utilities, health checks, logging
2. **User** - Authentication, profiles, sessions
3. **Admin** - Administrative dashboard
4. **AI** - Machine learning model management
5. **Automations** - Workflow automation
6. **Management** - System management, backups, monitoring

## Key Features

✅ Production-ready Django setup
✅ RESTful API with DRF
✅ Swagger/OpenAPI documentation integrated
✅ JWT authentication
✅ Comprehensive error handling
✅ Database logging and monitoring
✅ Celery task queue support
✅ Docker & Docker Compose ready
✅ Multi-app modular architecture
✅ Admin interface
✅ User management system
✅ AI/ML model management
✅ Workflow automation
✅ System monitoring

## Default Admin Credentials

- Username: admin
- Password: admin

Change these immediately in production!
