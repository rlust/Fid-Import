# Docker Deployment Guide

Run Fidelity Portfolio Tracker in Docker containers for consistent, isolated deployment.

## Quick Start

### Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- `.env` file with your credentials

### 1. Build the Image

```bash
docker build -t fidelity-portfolio-tracker:latest .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Docker Services

The `docker-compose.yml` defines multiple services:

### 1. **portfolio-tracker** (Main Service)
Runs one-time sync operations

```bash
docker-compose up portfolio-tracker
```

### 2. **dashboard** (Web UI)
Runs the Streamlit dashboard on port 8501

```bash
docker-compose up dashboard
# Access at: http://localhost:8501
```

### 3. **api** (REST API)
Runs the FastAPI server on port 8000

```bash
docker-compose up api
# API docs at: http://localhost:8000/docs
```

### 4. **scheduler** (Automated Syncs)
Runs scheduled syncs based on config

```bash
docker-compose up scheduler
```

## Running Commands

### One-Time Sync

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  fidelity-portfolio-tracker:latest \
  portfolio-tracker sync
```

### Interactive Shell

```bash
docker run --rm -it \
  --env-file .env \
  -v $(pwd)/config:/app/config:ro \
  fidelity-portfolio-tracker:latest \
  /bin/bash
```

### View Status

```bash
docker run --rm \
  -v $(pwd)/fidelity_portfolio.db:/app/fidelity_portfolio.db:ro \
  fidelity-portfolio-tracker:latest \
  portfolio-tracker status --detailed
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
FIDELITY_USERNAME=your_username
FIDELITY_PASSWORD=your_password
FIDELITY_MFA_SECRET=your_totp_secret
```

### Volume Mounts

Important directories to mount:

- `./config:/app/config` - Configuration files (read-only recommended)
- `./data:/app/data` - Data files (JSON, CSV)
- `./logs:/app/logs` - Log files
- `./fidelity_portfolio.db:/app/fidelity_portfolio.db` - SQLite database

## Production Deployment

### 1. Build Production Image

```bash
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t fidelity-portfolio-tracker:v2.0.0 \
  -t fidelity-portfolio-tracker:latest \
  .
```

### 2. Use Docker Secrets (Recommended)

Instead of `.env` file, use Docker secrets for credentials:

```bash
echo "your_username" | docker secret create fidelity_username -
echo "your_password" | docker secret create fidelity_password -
echo "your_totp_secret" | docker secret create fidelity_mfa_secret -
```

Update `docker-compose.yml`:

```yaml
services:
  portfolio-tracker:
    secrets:
      - fidelity_username
      - fidelity_password
      - fidelity_mfa_secret

secrets:
  fidelity_username:
    external: true
  fidelity_password:
    external: true
  fidelity_mfa_secret:
    external: true
```

### 3. Resource Limits

Add resource constraints:

```yaml
services:
  portfolio-tracker:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. Automated Restarts

```yaml
services:
  portfolio-tracker:
    restart: unless-stopped
```

## Scheduled Syncs with Cron

Run syncs on schedule using cron in container:

```bash
# Add to crontab in container
0 18 * * * /app/portfolio-tracker sync >> /app/logs/cron.log 2>&1
```

Or use the scheduler service:

```bash
docker-compose up -d scheduler
```

## Multi-Architecture Builds

Build for multiple platforms (ARM64, AMD64):

```bash
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t fidelity-portfolio-tracker:latest \
  --push \
  .
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs portfolio-tracker

# Check container status
docker-compose ps

# Inspect container
docker inspect fidelity-portfolio-tracker
```

### Permission Issues

```bash
# Fix file permissions
chmod -R 755 data/ logs/
chown -R $(id -u):$(id -g) data/ logs/
```

### Database Locked

```bash
# Stop all containers accessing the database
docker-compose down

# Check for stale lock files
rm -f fidelity_portfolio.db-journal

# Restart
docker-compose up -d
```

### Memory Issues

```bash
# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 4GB+

# Or add to docker-compose.yml
services:
  portfolio-tracker:
    mem_limit: 2g
    memswap_limit: 2g
```

## Health Checks

The image includes a health check:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' fidelity-portfolio-tracker

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' fidelity-portfolio-tracker
```

## Best Practices

1. **Use volumes for data persistence**
   - Mount `./data`, `./logs`, and database file

2. **Keep credentials secure**
   - Use Docker secrets or encrypted .env
   - Never commit credentials to Git

3. **Regular backups**
   ```bash
   docker run --rm \
     -v $(pwd):/backup \
     fidelity-portfolio-tracker:latest \
     tar czf /backup/portfolio-backup-$(date +%Y%m%d).tar.gz /app/data /app/fidelity_portfolio.db
   ```

4. **Monitor logs**
   ```bash
   docker-compose logs -f --tail=100
   ```

5. **Update regularly**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Docker Hub

To publish to Docker Hub:

```bash
docker login
docker tag fidelity-portfolio-tracker:latest yourusername/fidelity-portfolio-tracker:v2.0.0
docker push yourusername/fidelity-portfolio-tracker:v2.0.0
```

## Example: Complete Production Setup

```bash
# 1. Clone repository
git clone https://github.com/rlust/Fid-Import.git
cd Fid-Import

# 2. Create production .env
cp .env.example .env
nano .env  # Add your credentials

# 3. Build image
docker-compose build

# 4. Initialize database
docker-compose run --rm portfolio-tracker portfolio-tracker setup

# 5. Run first sync
docker-compose run --rm portfolio-tracker portfolio-tracker sync

# 6. Start all services
docker-compose up -d

# 7. Check everything is running
docker-compose ps
docker-compose logs -f

# 8. Access dashboard
open http://localhost:8501

# 9. Access API
open http://localhost:8000/docs
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t fidelity-portfolio-tracker:${{ github.sha }} .
      - name: Test image
        run: |
          docker run --rm fidelity-portfolio-tracker:${{ github.sha }} portfolio-tracker --version
      - name: Push to registry
        if: success()
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag fidelity-portfolio-tracker:${{ github.sha }} yourusername/fidelity-portfolio-tracker:latest
          docker push yourusername/fidelity-portfolio-tracker:latest
```
