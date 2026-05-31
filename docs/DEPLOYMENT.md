# Production Deployment Guide

## Prerequisites
- Ubuntu 20.04 LTS or later
- PostgreSQL 12+
- Redis 6.0+
- Python 3.9+
- Nginx
- Systemd

## Installation Steps

### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git

# Create app user
sudo useradd -m -s /bin/bash nextbin
sudo usermod -aG sudo nextbin
```

### 2. Application Setup
```bash
# Switch to nextbin user
sudo su - nextbin

# Clone repository (or upload files)
git clone <your-repo> nextbin
cd nextbin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE nextbin_db;
CREATE USER nextbin_user WITH PASSWORD 'your_secure_password';
ALTER ROLE nextbin_user SET client_encoding TO 'utf8';
ALTER ROLE nextbin_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE nextbin_user SET default_transaction_deferrable TO on;
ALTER ROLE nextbin_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nextbin_db TO nextbin_user;
\q

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Nginx Setup
```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/nextbin

# Enable site
sudo ln -s /etc/nginx/sites-available/nextbin /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 5. SSL Setup (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
# Update paths in nginx.conf
sudo systemctl restart nginx
```

### 6. Systemd Services
```bash
# Copy service files
sudo cp nextbin.service /etc/systemd/system/
sudo cp nextbin-celery.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable nextbin nextbin-celery
sudo systemctl start nextbin nextbin-celery

# Check status
sudo systemctl status nextbin
sudo systemctl status nextbin-celery
```

### 7. Environment Configuration
```bash
# Create .env file
nano .env
# Add production settings:
# DEBUG=False
# SECRET_KEY=your-production-key
# ALLOWED_HOSTS=yourdomain.com
# DB_HOST=localhost
# DB_USER=nextbin_user
# DB_PASSWORD=your_secure_password
```

### 8. Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/nextbin
```

Add:
```
/var/log/nextbin/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload nextbin > /dev/null 2>&1 || true
    endscript
}
```

### 9. Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor Django
sudo journalctl -u nextbin -f

# Monitor Celery
sudo journalctl -u nextbin-celery -f
```

## Backup Strategy

```bash
# Database backup
sudo -u postgres pg_dump nextbin_db | gzip > nextbin_db_$(date +%Y%m%d).sql.gz

# Media files backup
tar -czf nextbin_media_$(date +%Y%m%d).tar.gz /var/www/nextbin/media/

# Automated backup (cron)
0 2 * * * /usr/local/bin/backup_nextbin.sh
```

## Troubleshooting

### Check Service Status
```bash
systemctl status nextbin
systemctl status nextbin-celery
systemctl status redis-server
systemctl status postgresql
```

### View Logs
```bash
journalctl -u nextbin -n 100 -f
journalctl -u nextbin-celery -n 100 -f
tail -f /var/log/nginx/nextbin_error.log
```

### Database Issues
```bash
# Check database connection
psql -h localhost -U nextbin_user -d nextbin_db

# Restore backup
gunzip < nextbin_db_backup.sql.gz | psql -U postgres nextbin_db
```

### Restart Services
```bash
sudo systemctl restart nextbin
sudo systemctl restart nextbin-celery
sudo systemctl restart nginx
```

## Performance Optimization

1. **Enable Caching**
   - Configure Redis for caching
   - Add cache headers in nginx

2. **Database Optimization**
   - Add indexes to frequently queried fields
   - Use database query optimization

3. **Static Files**
   - Use CDN for static files
   - Enable gzip compression in nginx

4. **Monitoring**
   - Set up New Relic or DataDog
   - Configure error tracking (Sentry)

5. **Load Balancing**
   - Use load balancer for multiple app servers
   - Configure sticky sessions if needed

## Security Hardening

1. Firewall rules
2. SSH key-based authentication
3. Regular security updates
4. Database encryption
5. HTTPS enforcement
6. Rate limiting
7. Web Application Firewall (WAF)
8. DDoS protection
