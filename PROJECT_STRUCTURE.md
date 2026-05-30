# Project Structure

## Directory Layout

```
Django-Nextbin/
├── apps/                          # Django applications
│   ├── __init__.py
│   │
│   └── core/                      # Core utilities, system settings & logs
│       ├── __init__.py
│       ├── models.py             # BaseModel, APILog, SystemSettings
│       ├── serializers.py        # REST serializers
│       ├── views.py              # ViewSets
│       ├── urls.py               # URL routing
│       ├── admin.py              # Django admin config
│       ├── apps.py               # App configuration
│       └── management/
│           ├── __init__.py
│           └── commands/
│               ├── __init__.py
│               └── create_superuser.py
│
├── config/                        # Django configuration
│   ├── __init__.py
│   ├── settings.py               # Main Django settings (production-ready)
│   ├── urls.py                   # URL routing & Swagger docs
│   ├── wsgi.py                   # WSGI application
│   └── celery.py                 # Celery configuration
│
├── media/                         # User uploaded files
│
├── static/                        # Static files (CSS, JS)
│   ├── css/
│   └── js/
│
├── templates/                     # HTML templates (if needed)
│
├── utils/                         # Utility modules
│   ├── __init__.py
│   ├── helpers.py                # Helper functions
│   ├── exceptions.py             # Custom exceptions
│   ├── middleware.py             # Custom middleware
│   ├── validators.py             # Custom validators
│   └── permissions.py            # Custom permissions
│
├── logs/                          # Application logs
│   └── .gitkeep
│
├── .github/                       # GitHub configuration
│   └── workflows/
│       └── tests.yml             # CI/CD pipeline
│
├── .env                          # Environment variables (local)
│   └── .env.example              # Environment template
├── .gitignore                    # Git ignore rules
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
├── DEPLOYMENT.md                 # Deployment instructions
├── API_DOCS.md                   # API documentation
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker compose setup
├── nginx.conf                    # Nginx configuration
├── nextbin.service               # Systemd service file
├── nextbin-celery.service        # Celery systemd service
├── pytest.ini                    # Pytest configuration
└── conftest.py                   # Pytest fixtures
```

## File Descriptions

### Django Configuration (config/)

- **settings.py**: Production-ready settings with:
  - Database configuration
  - REST Framework setup
  - Swagger/OpenAPI integration
  - Celery configuration
  - Security settings
  - Logging configuration
  - Cache configuration

- **urls.py**: Main URL router with:
  - API versioning (v1)
  - Swagger endpoints
  - Health check endpoint
  - Core app URLs

- **wsgi.py**: WSGI application entry point
- **celery.py**: Asynchronous task queue setup

### Applications (apps/)

Each app follows Django best practices:

1. **models.py** - Database models
2. **serializers.py** - DRF serializers
3. **views.py** - ViewSets and views
4. **urls.py** - URL routing
5. **admin.py** - Django admin configuration
6. **apps.py** - App configuration

### Core App Features

- **BaseModel**: Abstract model with common fields
- **APILog**: Track API requests/responses
- **SystemSettings**: Global system settings
- **Management Commands**: Custom Django commands

### Utilities (utils/)

- **helpers.py**: Reusable helper functions
- **exceptions.py**: Custom API exceptions
- **middleware.py**: Custom middleware classes
- **validators.py**: Custom validators
- **permissions.py**: Custom permission classes

### Infrastructure Files

- **Dockerfile**: Container image definition
- **docker-compose.yml**: Multi-container setup
- **nginx.conf**: Web server configuration
- **nextbin.service**: Systemd service
- **nextbin-celery.service**: Celery service
- **pytest.ini**: Testing configuration

### Documentation

- **README.md**: Complete project documentation
- **QUICKSTART.md**: Get started quickly
- **DEPLOYMENT.md**: Production deployment guide
- **API_DOCS.md**: API endpoint documentation

## Data Models

### Core Models
- `BaseModel`: Abstract base with timestamps
- `APILog`: API request/response logging
- `SystemSettings`: Global configuration

## API Structure

### URL Pattern
```
/api/v1/{app}/{resource}/
/api/v1/{app}/{resource}/{id}/
```

### Versioning
- Current version: v1
- Easy to add v2, v3, etc.

### Authentication
- JWT tokens

### Documentation
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- Schema: `/api/schema/`

## Configuration Files

### Environment Variables (.env)
```
DEBUG=True/False
SECRET_KEY=your-key
ALLOWED_HOSTS=hosts
DB_ENGINE=database-engine
DB_NAME=database-name
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://url
CELERY_RESULT_BACKEND=redis://url
REDIS_URL=redis://url
EMAIL_BACKEND=email-backend
```

### Dependencies (requirements.txt)
- Django 4.2.11
- Django REST Framework 3.14
- drf-spectacular 0.27 (Swagger)
- PostgreSQL driver
- Redis client
- Celery
- Testing tools
- Code quality tools

## Security Features

1. **CORS Configuration**: Configurable cross-origin access
2. **CSRF Protection**: Built-in Django protection
3. **SSL/TLS**: HTTPS enforced in production
4. **Password Hashing**: Django's security system
5. **Permission Classes**: Fine-grained access control
6. **Rate Limiting**: API request throttling
7. **Security Headers**: X-Frame-Options, CSP, etc.
8. **SQL Injection**: ORM prevents SQL injection
9. **XSS Protection**: Template escaping
10. **Authentication**: JWT + Session auth

## Performance Features

1. **Database Indexes**: Optimized queries
2. **Caching**: Redis integration
3. **Pagination**: Efficient data loading
4. **Query Optimization**: Select/prefetch related
5. **Static File Compression**: WhiteNoise
6. **Celery Tasks**: Async processing
7. **Connection Pooling**: Database connections
8. **API Throttling**: Rate limiting

## Scalability Features

1. **Horizontal Scaling**: Stateless design
2. **Load Balancing**: Nginx ready
3. **Database Replication**: PostgreSQL support
4. **Cache Layer**: Redis caching
5. **Task Queue**: Celery distributed tasks
6. **Multiple Workers**: Gunicorn workers
7. **CDN Ready**: Static file serving

## Monitoring & Logging

1. **API Logging**: Request/response tracking
2. **System Settings**: Global configuration
3. **Error Handling**: Comprehensive exception handling
4. **Debug Logging**: Detailed debug logs
5. **Log Rotation**: Rotating file handlers
