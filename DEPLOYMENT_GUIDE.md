# EA Escrow Platform — Complete Deployment Guide

## Overview

Your EA Escrow platform is now **production-ready** with:
- ✅ Field-level AES-256-GCM encryption (automatic)
- ✅ Merchant dashboard & analytics
- ✅ Dispute resolution system
- ✅ Insurance & fraud protection
- ✅ Partner API with rate limiting
- ✅ PostgreSQL database with indexes
- ✅ Audit logging for compliance
- ✅ JWT authentication
- ✅ OTP verification

---

## 📋 Pre-Deployment Checklist

- [ ] Node.js 18+ installed
- [ ] PostgreSQL 13+ running locally or in cloud
- [ ] Git initialized
- [ ] `.env` file created with all keys
- [ ] Database migrations run successfully
- [ ] All tests passing
- [ ] API endpoints tested with Postman/curl

---

## 🚀 Local Development Setup (5 minutes)

### 1. Install Dependencies

```bash
cd escrow-mvp
npm install
npx prisma generate
```

### 2. Create `.env` File

Copy the example and add your secrets:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Database (Local PostgreSQL)
DATABASE_URL="postgresql://postgres:password@localhost:5432/escrow_dev"

# Encryption Keys (Generate these!)
ENCRYPTION_KEY="your-32-byte-hex-key-here"
HMAC_KEY="your-32-byte-hex-key-here"

# API
PORT=5000
JWT_SECRET="dev-secret-change-in-production"

# Flutterwave
FLW_SECRET_HASH="dev-only-change-me"

# Africa's Talking
AFRICAS_TALKING_API_KEY="your-api-key"
AFRICAS_TALKING_USERNAME="your-username"
AFRICAS_TALKING_SHORTCODE="12345"

# Environment
NODE_ENV="development"
```

### 3. Generate Encryption Keys

```bash
# Generate ENCRYPTION_KEY
node -e "console.log('ENCRYPTION_KEY=' + require('crypto').randomBytes(32).toString('hex'))"

# Generate HMAC_KEY
node -e "console.log('HMAC_KEY=' + require('crypto').randomBytes(32).toString('hex'))"
```

### 4. Initialize Database

```bash
# Create database (if not exists)
createdb escrow_dev

# Run migrations
npx prisma migrate dev --name init

# View database
npx prisma studio  # Opens http://localhost:5555
```

### 5. Start Development Server

```bash
npm run dev

# Server runs on http://localhost:5000
# Frontend on http://localhost:5000/index.html
```

### 6. Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Create merchant
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "phoneNumber": "+254700000000",
    "businessName": "John Trading",
    "country": "KE",
    "bankAccountNumber": "9876543210",
    "nationalId": "KE123456789"
  }'
```

---

## 🐳 Docker Deployment (Production)

### 1. Create `Dockerfile`

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm install --production
RUN npx prisma generate

# Copy application
COPY server ./server
COPY public ./public

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Start server
CMD ["npm", "start"]
```

### 2. Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: escrow_db
    environment:
      POSTGRES_DB: escrow_prod
      POSTGRES_USER: escrow_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U escrow_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # EA Escrow App
  escrow-app:
    build: .
    container_name: escrow_app
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://escrow_user:${DB_PASSWORD}@postgres:5432/escrow_prod
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      HMAC_KEY: ${HMAC_KEY}
      JWT_SECRET: ${JWT_SECRET}
      PORT: 5000
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. Deploy with Docker Compose

```bash
# Create .env with production values
cp .env.production .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f escrow-app

# Stop services
docker-compose down
```

---

## ☁️ Cloud Deployment (AWS/GCP/Azure)

### AWS EC2 + RDS Deployment

#### 1. Create RDS PostgreSQL Instance

```bash
# AWS CLI
aws rds create-db-instance \
  --db-instance-identifier escrow-prod \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username escrow_admin \
  --master-user-password ${DB_PASSWORD} \
  --allocated-storage 20 \
  --publicly-accessible false \
  --db-name escrow_db
```

#### 2. Launch EC2 Instance

```bash
# Ubuntu 22.04, t3.small, 30GB SSD
# Security group: allow 5000 (app), 22 (SSH)
```

#### 3. Deploy Application

```bash
# SSH into EC2
ssh -i key.pem ubuntu@public-ip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs git

# Clone repo
git clone https://github.com/your-org/escrow-mvp.git
cd escrow-mvp

# Install dependencies
npm install
npx prisma generate

# Create .env with RDS connection
cat > .env << EOF
DATABASE_URL="postgresql://escrow_admin:${DB_PASSWORD}@escrow-prod.xxxxx.us-east-1.rds.amazonaws.com:5432/escrow_db"
ENCRYPTION_KEY="${ENCRYPTION_KEY}"
HMAC_KEY="${HMAC_KEY}"
JWT_SECRET="${JWT_SECRET}"
PORT=5000
NODE_ENV=production
EOF

# Run migrations
npx prisma migrate deploy

# Start server with PM2
sudo npm install -g pm2
pm2 start npm --name "escrow-api" -- start
pm2 startup
pm2 save
```

#### 4. Set Up Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/escrow

upstream escrow_app {
  server localhost:5000;
  keepalive 64;
}

server {
  listen 80;
  server_name api.eascrow.io;

  # Redirect HTTP to HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name api.eascrow.io;

  ssl_certificate /etc/letsencrypt/live/eascrow.io/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/eascrow.io/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;

  client_max_body_size 50M;

  # Gzip compression
  gzip on;
  gzip_types text/plain application/json application/javascript;

  location / {
    proxy_pass http://escrow_app;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
  }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/escrow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL with Let's Encrypt
sudo certbot certonly --nginx -d api.eascrow.io
```

---

## 🔐 Security Hardening

### 1. Database Security

```bash
# Restrict access to application server only
# In RDS security group: allow 5432 from EC2 instance security group only
```

### 2. Environment Variables

Never commit `.env` to git:

```bash
# .gitignore
.env
.env.local
.env.*.local
```

Use a secrets manager:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name escrow/prod/encryption-key \
  --secret-string "${ENCRYPTION_KEY}"
```

### 3. Rotate Encryption Keys (Annual)

```typescript
// scripts/rotate-keys.ts
import { prisma } from '../src/db';
import { encryptField, decryptField } from '../src/cryptoUtils';

async function rotateKeys(oldKey: string, newKey: string) {
  const merchants = await prisma.merchant.findMany();
  
  for (const merchant of merchants) {
    // Decrypt with old key
    const oldDecrypted = decryptField(merchant.bankAccountNumber);
    
    // Re-encrypt with new key
    process.env.ENCRYPTION_KEY = newKey;
    const newEncrypted = encryptField(oldDecrypted);
    
    await prisma.merchant.update({
      where: { id: merchant.id },
      data: { bankAccountNumber: newEncrypted }
    });
  }
}
```

### 4. API Rate Limiting

```typescript
// middleware/rate-limit.ts
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 60 * 1000,         // 1 minute
  max: 100,                     // 100 requests per window
  message: 'Too many requests',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', apiLimiter);
```

### 5. CORS & HTTPS Only

```typescript
// In server initialization
app.use(cors({
  origin: ['https://eascrow.io', 'https://app.eascrow.io'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
}));

// Force HTTPS
app.use((req, res, next) => {
  if (req.header('x-forwarded-proto') !== 'https') {
    return res.redirect(301, `https://${req.header('host')}${req.url}`);
  }
  next();
});
```

---

## 📊 Monitoring & Logging

### 1. Application Logging

```typescript
// utils/logger.ts
import winston from 'winston';

export const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Usage
logger.info('Escrow created', { txRef, amount });
logger.error('Webhook failed', { error, escrowId });
```

### 2. Prometheus Metrics

```typescript
// middleware/metrics.ts
import promClient from 'prom-client';

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
});

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration.labels(req.method, req.route?.path, res.statusCode).observe(duration);
  });
  next();
});
```

### 3. Sentry Error Tracking

```bash
npm install @sentry/node
```

```typescript
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
});

app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler());
```

---

## 🧪 Testing & QA

### Unit Tests

```bash
npm install --save-dev jest @types/jest

# Run tests
npm test

# Coverage
npm test -- --coverage
```

### Integration Tests

```bash
# Test database operations
npm run test:integration

# Load testing
npm install -g artillery
artillery run load-test.yml
```

---

## 📈 Performance Tuning

### Database Connection Pooling

```env
# .env
DATABASE_URL="postgresql://...?sslmode=require&pool_size=20&statement_cache_size=0"
```

### Redis Caching (Optional)

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

// Cache merchant data
async function getMerchantCached(id: string) {
  const cached = await redis.get(`merchant:${id}`);
  if (cached) return JSON.parse(cached);
  
  const merchant = await prisma.merchant.findUnique({ where: { id } });
  await redis.setex(`merchant:${id}`, 3600, JSON.stringify(merchant));
  return merchant;
}
```

### CDN for Static Assets

```nginx
# Serve static files from CloudFront
location /static {
  add_header Cache-Control "public, max-age=31536000";
  alias /app/public/static;
}
```

---

## 🚨 Incident Response

### Database Connection Lost

```typescript
// Automatic reconnection
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
    }
  }
}
```

### API Rate Limit Hit

```typescript
// Graceful degradation
if (res.status === 429) {
  logger.warn('Rate limit exceeded', { clientIp: req.ip });
  return res.status(429).json({ error: 'Too many requests, retry later' });
}
```

---

## 📅 Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Database backups | Daily (automated) | DevOps |
| Encryption key rotation | Annually | Security |
| Security patches | As released | DevOps |
| Audit log review | Weekly | Compliance |
| Performance monitoring | Daily | Engineering |
| Disaster recovery test | Quarterly | DevOps |

---

## 🎯 Launch Checklist

- [ ] All tests passing (100% coverage for critical paths)
- [ ] Security audit completed
- [ ] Database backed up
- [ ] Monitoring configured (Sentry, Datadog, etc.)
- [ ] Alerts configured (critical errors, high latency)
- [ ] SSL certificates installed
- [ ] DNS pointed to load balancer
- [ ] API documentation published
- [ ] Rate limits configured
- [ ] Audit logging enabled
- [ ] Incident response plan documented
- [ ] On-call rotation established

---

## 📞 Deployment Support

For questions:
- Prisma docs: https://www.prisma.io/docs
- Node.js best practices: https://nodejs.org/en/docs/
- Docker deployment: https://docs.docker.com/

**You're ready to launch! 🚀**

