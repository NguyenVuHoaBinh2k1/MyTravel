# MyTravel Deployment Guide

This guide covers deployment of the MyTravel application to production.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (recommended: Let's Encrypt)
- Minimum 2GB RAM, 2 CPU cores
- 20GB disk space

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/MyTravel.git
cd MyTravel

# Copy and configure environment variables
cp .env.production.example .env.production
nano .env.production  # Edit with your values
```

### 2. Configure Required API Keys

You need to obtain the following API keys:

- **Gemini API**: https://makersuite.google.com/app/apikey
- **OpenAI API** (optional): https://platform.openai.com/api-keys
- **Google Maps API**: https://console.cloud.google.com/
- **Booking.com API** (via RapidAPI): https://rapidapi.com/

### 3. Database Setup

```bash
# Start database first
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### 4. Deploy Application

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Verify Deployment

```bash
# Check service health
curl http://localhost/health

# Check backend API
curl http://localhost/api/v1/

# Check frontend
curl http://localhost/
```

## SSL/HTTPS Setup

### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certificates will be saved to /etc/letsencrypt/live/yourdomain.com/

# Update nginx.conf to use SSL (uncomment HTTPS server block)
# Update SSL certificate paths in docker-compose.prod.yml
```

### Certificate Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Auto-renewal is configured by default via cron
```

## Environment Variables

### Critical Variables

- `SECRET_KEY`: Use a strong random key (min 32 characters)
- `DB_PASSWORD`: Secure database password
- `REDIS_PASSWORD`: Secure Redis password
- `GEMINI_API_KEY`: Your Gemini API key

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate passwords
openssl rand -base64 32
```

## Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres mytravel > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20240101.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres mytravel
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run new migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Scale Services

```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Check running instances
docker-compose -f docker-compose.prod.yml ps
```

## Security Checklist

- [ ] Strong passwords for DB and Redis
- [ ] SECRET_KEY is random and secure
- [ ] SSL/HTTPS configured
- [ ] Firewall configured (only 80, 443 open)
- [ ] Regular backups scheduled
- [ ] API keys stored securely (never in git)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Logs monitored regularly

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# 1. Database not ready - wait and retry
# 2. Missing environment variables - check .env.production
# 3. Migration errors - check database state
```

### Database Connection Errors

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d mytravel

# Check database health
docker-compose -f docker-compose.prod.yml exec db pg_isready
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit resources in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

## Performance Optimization

### Database Indexing

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_conversations_trip_id ON conversations(trip_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

### Redis Caching

Redis is used for:
- Session storage
- API response caching
- Rate limiting

Configure cache TTL in backend settings.

### CDN Configuration

For better performance, serve static assets via CDN:

1. Upload Next.js static files to CDN
2. Configure `NEXT_PUBLIC_CDN_URL`
3. Update nginx to proxy static requests to CDN

## Disaster Recovery

### Backup Strategy

1. **Database**: Daily automated backups
2. **User uploads**: Sync to S3/cloud storage
3. **Configuration**: Store .env files securely
4. **Code**: Use git tags for releases

### Recovery Steps

1. Restore database from backup
2. Restore configuration files
3. Redeploy application
4. Run migrations
5. Verify data integrity

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/MyTravel/issues
- Documentation: https://docs.yourdomain.com
- Email: support@yourdomain.com
