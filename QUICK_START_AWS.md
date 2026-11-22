# 🚀 Quick Start: Deploy to AWS in 30 Minutes

## Overview

This guide deploys your EA Escrow platform to AWS in **30 minutes** using:
- **RDS PostgreSQL** - Managed database ($10-15/month)
- **EC2** - Application server ($5-15/month)
- **Nginx** - Reverse proxy (free)
- **Let's Encrypt** - SSL/TLS (free)

**Total cost**: ~$20/month (free tier eligible for 1 year)

---

## Prerequisites

Before starting, you need:
- ✅ AWS account (free tier works)
- ✅ Domain name (e.g., `api.eascrow.io`)
- ✅ Git repository with code
- ✅ SSH key pair for EC2

---

## Step 1: Set Up RDS Database (5 minutes)

### 1.1 Create RDS Instance

1. Open **AWS RDS Console**
2. Click **Create database**
3. Choose **PostgreSQL**
4. Select **Free tier** template
5. **DB Instance Identifier**: `escrow-prod-db`
6. **Master username**: `escrow_admin`
7. **Master password**: Generate strong password, save it!
8. **Database name**: `escrow_prod`
9. **Publicly accessible**: No
10. Click **Create database**

⏳ Wait 5 minutes for creation

### 1.2 Get Connection Details

1. Click your database in RDS console
2. Copy **Endpoint** (e.g., `escrow-prod-db.xxxxx.us-east-1.rds.amazonaws.com`)
3. Save this - you'll need it in Step 2

---

## Step 2: Create EC2 Instance (5 minutes)

### 2.1 Launch Instance

1. Open **AWS EC2 Console**
2. Click **Launch instance**
3. **Name**: `escrow-api-prod`
4. **AMI**: Ubuntu 22.04 LTS
5. **Instance type**: `t3.small` (or `t2.micro` free tier)
6. **Key pair**: Create new or select existing
7. **Inbound rules**:
   - SSH (22) - Your IP
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0
8. **Storage**: 30 GB
9. Click **Launch**

### 2.2 Connect to Instance

Wait 2 minutes, then:

```bash
# From your laptop
ssh -i your-key.pem ubuntu@<PUBLIC_IP>

# Replace <PUBLIC_IP> with EC2 public IP from AWS console
```

---

## Step 3: Automated Deployment (15 minutes)

### 3.1 Download Deploy Script

Once connected to EC2:

```bash
# Download deployment script
cd ~
wget https://your-repo/deploy.sh
chmod +x deploy.sh
```

Or manually create the script from `deploy.sh` in outputs folder.

### 3.2 Run Deployment

```bash
# Run automated deployment
sudo bash deploy.sh

# Answer prompts:
# - RDS Endpoint: escrow-prod-db.xxxxx.us-east-1.rds.amazonaws.com
# - RDS Password: (your password from Step 1)
# - Domain: api.eascrow.io
# - Email: your@email.com
```

The script will:
- ✅ Install Node.js, PostgreSQL, Nginx
- ✅ Clone your repository
- ✅ Setup database migrations
- ✅ Start application with PM2
- ✅ Configure Nginx reverse proxy
- ✅ Install SSL certificate (Let's Encrypt)
- ✅ Enable firewall
- ✅ Setup auto-updates

⏳ Wait for completion (~10 minutes)

---

## Step 4: Verify Deployment (2 minutes)

### 4.1 Check Application

```bash
# From EC2 instance
curl http://localhost:5000/api/health

# Should return:
# {"status":"ok","version":"2.0",...}
```

### 4.2 Check HTTPS

```bash
# From your laptop
curl https://api.eascrow.io/api/health

# Should return same response
# If DNS not ready, add to hosts file:
# <EC2_PUBLIC_IP>  api.eascrow.io
```

### 4.3 View Logs

```bash
# From EC2 instance
pm2 logs escrow-api
pm2 monit

# Check Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## Step 5: Configure Payment Providers (5 minutes)

### 5.1 Update Environment Variables

```bash
# On EC2 instance
nano .env

# Update:
AFRICAS_TALKING_API_KEY="your-api-key"
AFRICAS_TALKING_USERNAME="your-username"
FLW_SECRET_HASH="your-flutterwave-key"

# Save and restart
pm2 restart escrow-api
```

### 5.2 Test SMS Integration

```bash
# Should send test OTP via SMS
curl -X POST https://api.eascrow.io/api/escrow/create \
  -H "Content-Type: application/json" \
  -d '{
    "buyerPhone": "+254700000000",
    "sellerPhone": "+256700000000",
    "amount": 250000,
    "sourceCurrency": "KES",
    "payoutCurrency": "UGX",
    "itemDetails": "Test transaction"
  }'
```

---

## Step 6: Point Domain to EC2 (5 minutes)

### 6.1 Update DNS

In your domain registrar (GoDaddy, Namecheap, etc.):

1. Add **A record**:
   - **Name**: `api` (or subdomain)
   - **Value**: EC2 public IP
   - **TTL**: 300 (or automatic)

2. Wait for DNS propagation (~5-15 minutes)

### 6.2 Verify DNS

```bash
# From your laptop
nslookup api.eascrow.io
# Should return EC2 public IP

# Test HTTPS
curl https://api.eascrow.io/api/health
# Should return 200 OK with green lock icon
```

---

## 🎉 You're Live!

Your platform is now running at **https://api.eascrow.io** ✅

### Dashboard Access
- **Frontend**: https://api.eascrow.io
- **API**: https://api.eascrow.io/api/*
- **Health**: https://api.eascrow.io/api/health

---

## Common Issues & Fixes

### "Cannot connect to database"
```bash
# Check RDS security group allows EC2
# 1. Go to RDS console
# 2. Click your database
# 3. Security group -> Inbound rules
# 4. Add rule: PostgreSQL (5432) from EC2 security group
```

### "Certificate not valid"
```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check Nginx is using cert
sudo nginx -t
```

### "Application not responding"
```bash
# Check PM2 status
pm2 status

# Restart
pm2 restart escrow-api

# View logs
pm2 logs escrow-api

# Check database connection
psql $DATABASE_URL -c "SELECT 1"
```

### "Disk space full"
```bash
# Check disk usage
df -h

# Clean logs
sudo journalctl --vacuum=50M
pm2 flush

# Prune old database logs
aws rds describe-db-log-files --db-instance-identifier escrow-prod-db
```

---

## Useful Commands

### Application Management
```bash
# View logs
pm2 logs escrow-api

# Monitor CPU/memory
pm2 monit

# Restart application
pm2 restart escrow-api

# Stop application
pm2 stop escrow-api

# Start application
pm2 start escrow-api
```

### Database Management
```bash
# Connect to database
psql $DATABASE_URL

# View tables
\dt

# Check database size
SELECT pg_size_pretty(pg_database_size(current_database()));

# Create backup
aws rds create-db-snapshot \
  --db-instance-identifier escrow-prod-db \
  --db-snapshot-identifier escrow-backup-$(date +%Y%m%d)
```

### Nginx/SSL
```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# View Nginx errors
sudo tail -f /var/log/nginx/error.log

# Check SSL certificate
sudo certbot certificates
```

### System Health
```bash
# CPU/Memory usage
htop

# Disk usage
df -h

# Network traffic
iftop

# Log in to system
sudo -i
```

---

## Security Checklist

- [ ] SSL certificate valid (green padlock)
- [ ] Firewall enabled (UFW)
- [ ] Security groups configured (EC2 + RDS)
- [ ] SSH key secured (don't share .pem file)
- [ ] Encryption keys in .env (not in code)
- [ ] Backups enabled (RDS automatic)
- [ ] Auto-updates enabled
- [ ] Monitoring configured (CloudWatch)

---

## Scaling Tips

### When you reach 100K requests/month:

1. **Add read replica** (for database reads)
   ```bash
   aws rds create-db-instance-read-replica \
     --db-instance-identifier escrow-prod-db-replica \
     --source-db-instance-identifier escrow-prod-db
   ```

2. **Enable caching** (Redis)
   ```bash
   # Add to .env:
   REDIS_URL="redis://localhost:6379"
   ```

3. **Monitor with CloudWatch**
   - CPU utilization
   - Database connections
   - API response time

### When you reach 1M+ requests/month:

1. **Add load balancer** (AWS ELB)
2. **Auto-scaling group** (multiple EC2 instances)
3. **Multi-AZ RDS** (high availability)
4. **CloudFront CDN** (static files)

---

## Support

If you get stuck:

1. **Check logs**: `pm2 logs escrow-api`
2. **Check AWS console**: Look for error messages
3. **Verify DNS**: `nslookup api.eascrow.io`
4. **Test connectivity**: `curl http://localhost:5000/api/health`
5. **Review deployment guide**: `AWS_DEPLOYMENT_GUIDE.md`

---

## Next Steps

### Immediate (Today)
- [ ] Run deployment script
- [ ] Verify API responds
- [ ] Point domain to EC2
- [ ] Test SMS/payments

### This Week
- [ ] Set up monitoring (CloudWatch)
- [ ] Enable database backups
- [ ] Create pilot merchant accounts
- [ ] Test end-to-end transactions

### This Month
- [ ] Launch with 50 merchants
- [ ] Collect feedback
- [ ] Iterate on UX
- [ ] Plan Series A fundraise

---

## Cost Summary

| Item | Cost | Notes |
|------|------|-------|
| EC2 t3.small | $15/mo | Reduces to $5 with free tier |
| RDS db.t3.micro | $15/mo | Free tier available |
| Domain | $12/year | Use existing or register |
| Data transfer | $5/mo | Minimal for startup volume |
| SSL (Let's Encrypt) | Free | Auto-renews |
| **Total** | **~$40/mo** | **~$15/mo with free tier** |

---

**🎉 Your platform is production-ready and live!**

**Next: Raise capital using the INVESTOR_ROADMAP.md**
