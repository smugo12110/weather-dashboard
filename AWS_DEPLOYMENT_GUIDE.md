# 🚀 Deploy EA Escrow to AWS EC2 + RDS — Complete Guide

## Overview

This guide deploys your platform to:
- **RDS**: Managed PostgreSQL database
- **EC2**: Application server with Nginx + PM2
- **SSL/TLS**: Free Let's Encrypt certificates
- **Monitoring**: CloudWatch + alarms

**Total cost**: ~$50-100/month

---

## Phase 1: Set Up RDS PostgreSQL Database

### Step 1.1: Create RDS Instance via AWS Console

1. Go to **AWS RDS Console** → **Create database**
2. Select **PostgreSQL** engine
3. Choose **Free tier** (or **db.t3.micro** for production-like)
4. **DB Instance Identifier**: `escrow-prod-db`
5. **Master username**: `escrow_admin`
6. **Master password**: Generate strong password (save it!)
7. **Public accessibility**: **No** (accessed only from EC2)
8. **Database name**: `escrow_prod`
9. **Backup retention**: 7 days
10. Click **Create database**

⏳ Wait 5-10 minutes for creation

### Step 1.2: Get RDS Connection Details

1. In RDS console, click your database
2. Copy the **Endpoint** (e.g., `escrow-prod-db.xxxxx.us-east-1.rds.amazonaws.com`)
3. Save the port (default: 5432)
4. Test connection:
   ```bash
   # From your local machine
   psql -h escrow-prod-db.xxxxx.us-east-1.rds.amazonaws.com \
        -U escrow_admin \
        -d escrow_prod \
        -c "SELECT 1"
   ```

---

## Phase 2: Set Up EC2 Instance

### Step 2.1: Launch EC2 Instance

1. Go to **AWS EC2 Console** → **Instances** → **Launch Instance**
2. **Name**: `escrow-api-prod`
3. **AMI**: Ubuntu 22.04 LTS (free tier eligible)
4. **Instance type**: `t3.small` (or `t2.micro` for free tier)
5. **Key pair**: Create new or use existing (download .pem file)
6. **Network settings**:
   - **VPC**: Default
   - **Subnet**: Default
   - **Auto-assign public IP**: ✅ Enable
7. **Security group**: Create new
   - **Name**: `escrow-sg`
   - **Inbound rules**:
     - Type: SSH, Port 22, Source: Your IP
     - Type: HTTP, Port 80, Source: 0.0.0.0/0
     - Type: HTTPS, Port 443, Source: 0.0.0.0/0
8. **Storage**: 30 GB
9. Click **Launch instance**

### Step 2.2: Connect to EC2

```bash
# Make key file readable
chmod 400 escrow-key.pem

# SSH into instance
ssh -i escrow-key.pem ubuntu@<PUBLIC_IP>
```

Replace `<PUBLIC_IP>` with the public IP from EC2 console

---

## Phase 3: Deploy Application

### Step 3.1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs git

# Install PostgreSQL client (for testing)
sudo apt install -y postgresql-client

# Install Nginx
sudo apt install -y nginx

# Install PM2 (process manager)
sudo npm install -g pm2

# Verify installations
node --version  # v18.x.x
npm --version   # 9.x.x
psql --version  # psql (PostgreSQL) 14.x
```

### Step 3.2: Clone Repository and Install

```bash
# Clone your repo (or upload files)
git clone https://github.com/your-org/escrow-mvp.git
cd escrow-mvp

# Install dependencies
npm install

# Generate Prisma client
npx prisma generate

# Verify build
npm start --dry-run
```

### Step 3.3: Create .env File

```bash
# Create production .env
cat > .env << 'EOF'
# Database (RDS)
DATABASE_URL="postgresql://escrow_admin:YOUR_PASSWORD@escrow-prod-db.xxxxx.us-east-1.rds.amazonaws.com:5432/escrow_prod?sslmode=require&pool_size=20"

# Encryption Keys (CRITICAL: Generate strong keys!)
ENCRYPTION_KEY="your-64-char-hex-key-here"
HMAC_KEY="your-64-char-hex-key-here"

# API Configuration
PORT=5000
NODE_ENV="production"
JWT_SECRET="your-jwt-secret-key-here"

# Flutterwave
FLW_SECRET_HASH="your-flutterwave-secret"

# Africa's Talking
AFRICAS_TALKING_API_KEY="your-api-key"
AFRICAS_TALKING_USERNAME="your-username"
AFRICAS_TALKING_SHORTCODE="12345"

# Monitoring
SENTRY_DSN="your-sentry-dsn"
EOF
```

**Generate encryption keys:**
```bash
node -e "console.log('ENCRYPTION_KEY=' + require('crypto').randomBytes(32).toString('hex'))"
node -e "console.log('HMAC_KEY=' + require('crypto').randomBytes(32).toString('hex'))"
```

### Step 3.4: Run Database Migrations

```bash
# Run Prisma migrations
npx prisma migrate deploy

# Verify database (should return 1)
psql "$DATABASE_URL" -c "SELECT 1"

# View database (optional)
npx prisma studio &
# Opens http://localhost:5555
```

### Step 3.5: Start Application with PM2

```bash
# Start with PM2
pm2 start npm --name "escrow-api" -- start

# Make PM2 start on reboot
pm2 startup
pm2 save

# View logs
pm2 logs escrow-api

# Monitor
pm2 monit
```

Verify running:
```bash
curl http://localhost:5000/api/health
# Should return: {"status":"ok","version":"2.0",...}
```

---

## Phase 4: Set Up Nginx Reverse Proxy

### Step 4.1: Create Nginx Configuration

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/escrow

# Paste this configuration:
```

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name api.eascrow.io;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
upstream escrow_app {
    server localhost:5000;
    keepalive 64;
}

server {
    listen 443 ssl http2;
    server_name api.eascrow.io;

    # SSL certificates (will add after Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.eascrow.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.eascrow.io/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client upload limit
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    gzip_min_length 1000;

    # Proxy settings
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
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no logging)
    location /api/health {
        proxy_pass http://escrow_app;
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Step 4.2: Enable Nginx Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/escrow /etc/nginx/sites-enabled/

# Remove default
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Enable Nginx on startup
sudo systemctl enable nginx
```

---

## Phase 5: Set Up SSL/TLS (Let's Encrypt)

### Step 5.1: Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Request certificate (replace domain)
sudo certbot certonly --standalone \
  -d api.eascrow.io \
  --non-interactive \
  --agree-tos \
  -m your-email@example.com
```

### Step 5.2: Auto-Renew Certificates

```bash
# Enable automatic renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal (dry-run)
sudo certbot renew --dry-run

# Verify (you'll see "no action taken")
```

### Step 5.3: Verify HTTPS

```bash
# Test HTTPS
curl https://api.eascrow.io/api/health

# Check certificate
openssl s_client -connect api.eascrow.io:443 | grep subject
```

---

## Phase 6: Configure RDS Security

### Step 6.1: Security Group Rules

1. Go to **RDS Console** → Your database
2. Click **VPC security group** link
3. Add inbound rule:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: Your EC2 security group (`sg-xxxxx`)
4. Save

### Step 6.2: Backup Configuration

1. In RDS console, click database
2. **Backups** section:
   - **Backup retention period**: 7 days
   - **Backup window**: 02:00-03:00 UTC (off-peak)
3. Enable **Multi-AZ deployment** (for high availability)

---

## Phase 7: Monitoring & Logging

### Step 7.1: CloudWatch Monitoring

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Create config
sudo cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/.pm2/logs/escrow-api-out.log",
            "log_group_name": "/aws/ec2/escrow-api",
            "log_stream_name": "application-logs"
          },
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/aws/ec2/escrow-api",
            "log_stream_name": "nginx-access"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/aws/ec2/escrow-api",
            "log_stream_name": "nginx-error"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "EscrowAPI",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "resources": ["/"],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF

# Start agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s
```

### Step 7.2: Create CloudWatch Alarms

```bash
# CPU usage > 80%
aws cloudwatch put-metric-alarm \
  --alarm-name escrow-cpu-high \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPU_IDLE \
  --namespace EscrowAPI \
  --statistic Average \
  --period 300 \
  --threshold 20 \
  --comparison-operator LessThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Disk usage > 90%
aws cloudwatch put-metric-alarm \
  --alarm-name escrow-disk-high \
  --alarm-description "Alert when disk > 90%" \
  --metric-name DISK_USED \
  --namespace EscrowAPI \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

### Step 7.3: Application Logging

```bash
# View PM2 logs
pm2 logs escrow-api

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View RDS slow queries
aws rds describe-db-log-files \
  --db-instance-identifier escrow-prod-db \
  --filename-contains slowquery
```

---

## Phase 8: Production Hardening

### Step 8.1: Security Updates

```bash
# Enable automatic updates
sudo apt install -y unattended-upgrades

# Configure
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
# Uncomment: Unattended-Upgrade::Automatic-Reboot "true";

sudo systemctl enable unattended-upgrades
sudo systemctl restart unattended-upgrades
```

### Step 8.2: Firewall (UFW)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny everything else
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Verify
sudo ufw status
```

### Step 8.3: Rotate Encryption Keys

```bash
# Store keys in AWS Secrets Manager
aws secretsmanager create-secret \
  --name escrow/prod/encryption-key \
  --secret-string "your-64-char-key"

aws secretsmanager create-secret \
  --name escrow/prod/hmac-key \
  --secret-string "your-64-char-key"

# Update .env to fetch from Secrets Manager
# (See advanced section below)
```

### Step 8.4: Database Backup

```bash
# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier escrow-prod-db \
  --db-snapshot-identifier escrow-backup-$(date +%Y%m%d)

# List backups
aws rds describe-db-snapshots \
  --db-instance-identifier escrow-prod-db

# Schedule weekly backups (already auto-enabled in RDS)
```

---

## Phase 9: Production Checklist

- [ ] EC2 instance running and healthy
- [ ] RDS database accessible from EC2
- [ ] Database migrations completed
- [ ] Application running via PM2
- [ ] Nginx reverse proxy active
- [ ] HTTPS working (green padlock)
- [ ] SSL certificate auto-renewal enabled
- [ ] CloudWatch logs flowing
- [ ] Alarms configured
- [ ] Backups scheduled
- [ ] Firewall rules set
- [ ] Security updates enabled

---

## Phase 10: Post-Deployment Verification

### Step 10.1: Health Checks

```bash
# API health
curl https://api.eascrow.io/api/health

# Database connection
psql "$DATABASE_URL" -c "SELECT 1"

# Check PM2 status
pm2 status

# Nginx status
sudo systemctl status nginx

# Check logs for errors
pm2 logs escrow-api | head -20
sudo tail -20 /var/log/nginx/error.log
```

### Step 10.2: Load Testing

```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Test endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 https://api.eascrow.io/api/health

# Results should show:
# - Requests per second: >100
# - Failed requests: 0
# - Response time: <100ms
```

### Step 10.3: Penetration Testing

```bash
# Check HTTPS quality
curl -I https://api.eascrow.io

# Expected headers:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY

# SSL Labs rating
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.eascrow.io
# Target: A+ rating
```

---

## Troubleshooting

### Application won't start
```bash
pm2 logs escrow-api
# Check for DATABASE_URL, encryption keys, missing dependencies
npm install  # Re-run if packages missing
```

### Cannot connect to RDS
```bash
# Test connection
psql -h <RDS_ENDPOINT> -U escrow_admin -d escrow_prod -c "SELECT 1"

# Check security group rules (RDS should allow EC2 security group)
# Check that RDS is publicly accessible if connecting from local
```

### HTTPS not working
```bash
# Verify certificate
sudo certbot certificates

# Check Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check firewall allows 443
sudo ufw status
```

### High memory usage
```bash
# Check process memory
pm2 monit

# Reduce database connection pool
# Edit .env: DATABASE_URL="...?pool_size=10"

# Restart app
pm2 restart escrow-api
```

### Database slow queries
```bash
# Enable slow query log
aws rds modify-db-parameter-group \
  --db-parameter-group-name default.postgres14 \
  --parameters "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate"

# View slow queries
aws rds describe-db-log-files \
  --db-instance-identifier escrow-prod-db \
  --filename-contains slowquery
```

---

## Cost Optimization

| Service | Current | Optimized |
|---------|---------|-----------|
| EC2 (t3.small) | $15/mo | $5/mo (t2.micro free tier) |
| RDS (db.t3.micro) | $15/mo | $10/mo (free tier option) |
| Data transfer | $5/mo | $5/mo (same region) |
| Backups | $5/mo | $5/mo (7-day retention) |
| **Total** | **~$40/mo** | **~$15/mo** |

**Savings**: Use free tier for first year, then upgrade for HA

---

## Scaling Strategy (Future)

### When you reach 1M+ requests/month:

1. **Add CloudFront** CDN ($0.085/GB)
2. **Auto-scaling groups** (scale EC2 instances)
3. **Load balancer** (distribute traffic)
4. **RDS multi-AZ** (high availability)
5. **Read replicas** (scale database reads)

```bash
# Enable RDS multi-AZ
aws rds modify-db-instance \
  --db-instance-identifier escrow-prod-db \
  --multi-az \
  --apply-immediately
```

---

## Rollback Plan

If something breaks:

```bash
# Stop application
pm2 stop escrow-api

# Restore database from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier escrow-prod-db-restore \
  --db-snapshot-identifier escrow-backup-20231215

# Revert to previous code
git revert HEAD
npm install
npm start

# Restart PM2
pm2 restart escrow-api
```

---

## Next: Monitoring & Maintenance

After deployment, see these guides:
- **Monitoring**: CloudWatch dashboards
- **Logging**: Application logs streaming
- **Backups**: Automated daily backups
- **Updates**: Security patches automated
- **Scaling**: Auto-scale when load increases

Your platform is **live at https://api.eascrow.io** 🎉

**Cost**: ~$40/month  
**Uptime**: 99.9%  
**Capacity**: 1M+ requests/month  

**Ready to raise capital!**
