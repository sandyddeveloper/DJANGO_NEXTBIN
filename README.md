"""
README - Nextbin Django Project
A production-ready Django REST API with Swagger/OpenAPI documentation.

## Project Structure

### Apps
- **core**: Central utilities, API logging, system settings
- **user**: User management, profiles, sessions, and activities
- **admin**: Admin dashboard and administrative features
- **ai**: AI/ML model management and predictions
- **automations**: Workflow automation and task management
- **management**: System management, backups, and monitoring

### Configuration
- **config/**: Django project configuration
  - settings.py: Production-ready settings
  - urls.py: API routing with Swagger docs
  - wsgi.py: WSGI application
  - celery.py: Celery task queue configuration

### Utilities
- **utils/**: Helper functions and utilities
  - helpers.py: Common utility functions
  - exceptions.py: Custom exception classes
  - middleware.py: Custom middleware
  - validators.py: Custom validators
  - permissions.py: Custom permission classes

## Setup Instructions

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 2. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# or use the custom command:
python manage.py create_superuser
```

### 3. Run Development Server
```bash
python manage.py runserver
```

### 4. Access the API
- API Documentation (Swagger): http://localhost:8000/api/docs/
- API Documentation (ReDoc): http://localhost:8000/api/redoc/
- Admin Panel: http://localhost:8000/admin/
- Health Check: http://localhost:8000/health/

## Docker Setup

### Using Docker Compose
```bash
# Start all services
docker-compose up

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

Services:
- Django Web: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Celery Worker: Background tasks
- Celery Beat: Scheduled tasks

## API Endpoints

### Core API
- `GET /api/v1/core/health/` - Health check
- `GET /api/v1/core/logs/` - API logs
- `GET /api/v1/core/settings/` - System settings

### Users API
- `POST /api/v1/users/register/` - Register new user
- `GET /api/v1/users/me/` - Get current user
- `GET /api/v1/users/{id}/` - Get user details
- `POST /api/v1/users/{id}/set_password/` - Change password
- `GET /api/v1/users/profiles/` - User profiles
- `GET /api/v1/users/sessions/` - User sessions
- `GET /api/v1/users/activities/` - User activities

### Admin API
- `GET /api/v1/admin-panel/dashboards/` - Admin dashboards
- `GET /api/v1/admin-panel/logs/` - Admin logs
- `GET /api/v1/admin-panel/dashboards/statistics/` - Dashboard statistics

### AI API
- `GET /api/v1/ai/models/` - List AI models
- `POST /api/v1/ai/models/` - Create AI model
- `GET /api/v1/ai/predictions/` - AI predictions
- `GET /api/v1/ai/training-jobs/` - Training jobs

### Automations API
- `GET /api/v1/automations/` - List automations
- `POST /api/v1/automations/` - Create automation
- `GET /api/v1/automations/executions/` - Execution history
- `GET /api/v1/automations/tasks/` - Tasks

### Management API
- `GET /api/v1/management/backups/` - Backup jobs
- `POST /api/v1/management/backups/trigger_backup/` - Trigger backup
- `GET /api/v1/management/maintenance/` - Maintenance windows
- `GET /api/v1/management/alerts/` - System alerts
- `GET /api/v1/management/metrics/` - Performance metrics

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps

# Run specific app tests
pytest apps/user/tests/
```

### Test Coverage
```bash
pytest --cov=apps --cov-report=html
# Open htmlcov/index.html
```

## Production Deployment

### Environment Variables
Update `.env` with production values:
- DEBUG=False
- SECRET_KEY=your-production-secret-key
- ALLOWED_HOSTS=yourdomain.com
- DB_HOST=your-db-host
- CELERY_BROKER_URL=redis://your-redis-host

### Run Migrations
```bash
python manage.py migrate
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Run with Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## Security Best Practices

1. Change SECRET_KEY in production
2. Set DEBUG=False in production
3. Use environment variables for sensitive data
4. Enable HTTPS
5. Configure SECURE_SSL_REDIRECT
6. Use database backups
7. Implement rate limiting
8. Enable CORS carefully
9. Validate all inputs
10. Keep dependencies updated

## Useful Commands

```bash
# Create app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Collect static files
python manage.py collectstatic

# Shell access
python manage.py shell

# Check project status
python manage.py check

# Database shell
python manage.py dbshell

# Export data
python manage.py dumpdata > data.json

# Import data
python manage.py loaddata data.json
```

## Troubleshooting

### Database Connection Issues
- Check DB_HOST, DB_USER, DB_PASSWORD in .env
- Ensure PostgreSQL is running
- Check database exists: `createdb nextbin_db`

### Static Files Not Loading
- Run: `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings

### Redis Connection Issues
- Ensure Redis is running
- Check CELERY_BROKER_URL in .env
- Check Redis connectivity: `redis-cli ping`

### Migration Issues
- Check migration files for syntax errors
- Rollback: `python manage.py migrate app_name 0001_initial`
- Create new migration: `python manage.py makemigrations`

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- drf-spectacular (Swagger): https://drf-spectacular.readthedocs.io/
- Celery: https://docs.celeryproject.io/
- PostgreSQL: https://www.postgresql.org/docs/

## License

This project is provided as-is for educational and commercial use.

## Support

For issues and questions, please check the documentation or create an issue in the project repository.
