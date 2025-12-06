# DOCKER DEPLOYMENT & QUICK START GUIDE

## File 1: docker-compose.yml (Full Stack)

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: face-emotion-postgres
    environment:
      POSTGRES_USER: faceuser
      POSTGRES_PASSWORD: securepassword123
      POSTGRES_DB: face_emotion
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U faceuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend FastAPI Service
  backend:
    build:
      context: ./backend
      dockerfile: docker/Dockerfile
    container_name: face-emotion-backend
    environment:
      DATABASE_URL: postgresql://faceuser:securepassword123@postgres:5432/face_emotion
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_S3_BUCKET: ${AWS_S3_BUCKET}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./models:/app/models
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend React Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: face-emotion-frontend
    environment:
      REACT_APP_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend/src:/app/src
    command: npm run dev

  # Redis for caching (optional)
  redis:
    image: redis:7-alpine
    container_name: face-emotion-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: face-emotion-network
```

---

## File 2: backend/docker/Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## File 3: frontend/Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev"]
```

---

## File 4: frontend/.env.example

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=300000
```

---

## QUICK START GUIDE

### Option 1: Docker Compose (Recommended)

#### Prerequisites:
- Docker (20.10+)
- Docker Compose (2.0+)
- 8GB RAM minimum
- 10GB disk space

#### Steps:

```bash
# 1. Clone repository
git clone <repository-url>
cd face-emotion-system

# 2. Create environment file
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Edit .env with your AWS credentials (optional for local dev)
# Leave blank to use local storage in dev

# 4. Start all services
docker-compose up -d

# 5. Wait for services to start (2-3 minutes)
docker-compose logs -f

# 6. Access services:
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Database:  localhost:5432

# 7. Stop services
docker-compose down

# 8. Remove all data
docker-compose down -v
```

---

### Option 2: Local Development (Without Docker)

#### Prerequisites:
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- CUDA 11.8+ (for GPU, optional)

#### Backend Setup:

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup database
# Create PostgreSQL database named face_emotion

# 5. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 6. Run migrations (if using Alembic)
# alembic upgrade head

# 7. Start backend
python -m app.main

# Backend runs on http://localhost:8000
```

#### Frontend Setup:

```bash
# 1. Navigate to frontend (in new terminal)
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env if backend is on different host

# 4. Start development server
npm run dev

# Frontend runs on http://localhost:3000
```

---

### Option 3: Production Deployment (AWS)

#### Infrastructure:
- **Compute:** AWS ECS / EKS / EC2
- **Database:** RDS PostgreSQL
- **Storage:** S3 for images
- **Cache:** ElastiCache Redis
- **CDN:** CloudFront
- **Monitoring:** CloudWatch

#### Deployment Steps:

```bash
# 1. Build Docker images
docker build -f backend/docker/Dockerfile -t face-emotion-backend:latest ./backend
docker build -f frontend/Dockerfile -t face-emotion-frontend:latest ./frontend

# 2. Tag images for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag face-emotion-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-emotion-backend:latest
docker tag face-emotion-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-emotion-frontend:latest

# 3. Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-emotion-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/face-emotion-frontend:latest

# 4. Update ECS task definitions
# (See DEPLOYMENT.md for detailed steps)

# 5. Deploy to ECS/EKS
aws ecs update-service --cluster face-emotion-prod --service backend --force-new-deployment
```

---

## DATABASE SETUP

### PostgreSQL Schema

```sql
-- Create database
CREATE DATABASE face_emotion;

-- Connect to database
\c face_emotion

-- Create tables (auto-created by SQLAlchemy on first run)
-- Tables:
-- - session_user (session management)
-- - emotion_log (emotion analysis records)
-- - session_aggregated_emotion (aggregated results)

-- Or run migrations
-- alembic upgrade head
```

### Initialize Database from Docker:

```bash
# Connect to PostgreSQL container
docker-compose exec postgres psql -U faceuser -d face_emotion

# Run SQL commands
\dt  # List tables
SELECT * FROM session_user;
```

---

## COMMON COMMANDS

### Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose stop

# Restart services
docker-compose restart backend

# Remove containers
docker-compose down

# Remove all data
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker-compose exec backend python -m app.main
```

### Database:

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U faceuser -d face_emotion

# Create database backup
docker-compose exec postgres pg_dump -U faceuser face_emotion > backup.sql

# Restore database
docker-compose exec -T postgres psql -U faceuser face_emotion < backup.sql
```

### Testing:

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test API
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "user_name": "Test User",
    "captured_image": "base64-encoded-image",
    "privacy_policy_agreed": true,
    "timestamp": "2025-12-06T10:00:00Z"
  }'

# View API documentation
# Open http://localhost:8000/docs
```

---

## TROUBLESHOOTING

### Issue: "Connection refused" to backend

**Solution:**
```bash
# Check if backend container is running
docker-compose ps

# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check port availability
lsof -i :8000
```

### Issue: PostgreSQL connection error

**Solution:**
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Issue: Frontend can't reach backend

**Solution:**
```bash
# In frontend .env, set API URL
REACT_APP_API_URL=http://localhost:8000

# Ensure CORS is configured in backend
# Check backend/app/main.py CORS settings

# Restart frontend
docker-compose restart frontend
```

### Issue: Out of memory

**Solution:**
```bash
# Increase Docker memory
# Docker Desktop: Settings → Resources → Memory (increase to 8GB+)

# Or use environment variable
export COMPOSE_MEMORY=8g
docker-compose up
```

---

## MONITORING & LOGS

### View Real-time Logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Follow from specific timestamp
docker-compose logs --since 5m -f
```

### Health Checks:

```bash
# Backend health
curl http://localhost:8000/api/health

# Database health
docker-compose exec postgres pg_isready -U faceuser

# Check running processes
docker-compose ps
```

---

## PERFORMANCE TUNING

### Database:

```bash
# Optimize PostgreSQL for performance
docker-compose exec postgres psql -U faceuser -d face_emotion << EOF
-- Index creation for faster queries
CREATE INDEX idx_session_id ON session_user(session_id);
CREATE INDEX idx_emotion_session ON emotion_log(session_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM session_user WHERE session_id = 'test-id';
EOF
```

### Backend:

```bash
# Increase worker count in docker-compose.yml
# Change command to:
# command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Or use environment variable
export WORKERS=4
```

### Frontend:

```bash
# Build optimized production bundle
npm run build

# This creates optimized bundle in dist/
# Can be served by nginx or any static server
```

---

## NEXT STEPS

1. **API Testing:** Use http://localhost:8000/docs (Swagger UI)
2. **Integration Testing:** See TESTING.md
3. **Production Setup:** See DEPLOYMENT.md
4. **Monitoring:** Setup CloudWatch/Prometheus
5. **CI/CD:** Configure GitHub Actions or GitLab CI

---

**You're ready to run the system!** 🚀

Start with: `docker-compose up -d`

