# ✅ Daily Operations Quick Reference

**Print this and keep it handy for daily operations.**

---

## 🌅 MORNING CHECKLIST (5 minutes)

Run at 8:00 AM before market opens:

```bash
# Copy and paste this entire block
/opt/escrow/morning-checklist.sh
```

### Expected Results:
- [ ] ✅ API responds with status: "ok"
- [ ] ✅ Database shows escrow count
- [ ] ✅ Application status: "online"
- [ ] ✅ Disk usage < 70%
- [ ] ✅ Memory usage < 70%
- [ ] ✅ No ALARM state in CloudWatch

**If anything fails:** → See "TROUBLESHOOTING" section below

---

## 📊 DURING TRADING DAY (Continuous)

### Every Hour:
1. Check CloudWatch Alarms: https://console.aws.amazon.com/cloudwatch/home#alarmsV2:
   - Any RED alarms? → Investigate immediately
   - Any YELLOW alarms? → Monitor closely

2. Spot check API health:
   ```bash
   curl -s https://api.eascrow.io/api/health | jq .
   ```

### Every 4 Hours:
1. Check transaction volume:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM escrows WHERE DATE(created_at) = CURRENT_DATE"
   ```

2. Check for any disputes filed:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM disputes WHERE DATE(created_at) = CURRENT_DATE"
   ```

---

## 🌙 EVENING CHECKLIST (5 minutes)

Run at 5:00 PM after market closes:

```bash
# Daily reconciliation report
echo "=== Daily Reconciliation Report ==="
echo "Date: $(date)"
echo ""

# Total transactions
echo "Daily Transactions:"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM escrows WHERE DATE(created_at) = CURRENT_DATE"

# Daily volume
echo ""
echo "Daily Volume (cents):"
psql $DATABASE_URL -c "SELECT COALESCE(SUM(source_amount_cents), 0) FROM escrows WHERE DATE(created_at) = CURRENT_DATE"

# Daily revenue
echo ""
echo "Daily Revenue (cents):"
psql $DATABASE_URL -c "SELECT COALESCE(SUM(platform_fee_cents), 0) FROM escrows WHERE DATE(created_at) = CURRENT_DATE"

# Success rate
echo ""
echo "Success Rate:"
psql $DATABASE_URL -c "
SELECT 
  (COUNT(CASE WHEN status = 'released' THEN 1 END)::float / COUNT(*) * 100)::int as success_rate_percent
FROM escrows 
WHERE DATE(created_at) = CURRENT_DATE"

# Check backups
echo ""
echo "Latest Backup:"
aws rds describe-db-snapshots \
  --db-instance-identifier escrow-prod-db \
  --query 'DBSnapshots[0].[DBSnapshotIdentifier, SnapshotCreateTime]' \
  --output text
```

### Expected Evening Results:
- [ ] Total transactions recorded
- [ ] Volume calculated correctly
- [ ] Revenue calculated
- [ ] Success rate > 80%
- [ ] Backup completed in last 24 hours

---

## 🚨 TROUBLESHOOTING QUICK GUIDE

### Problem: API Health Check Fails

```bash
# Step 1: Check if server is running
pm2 status
# Expected: escrow-api = online

# Step 2: If not running, restart
pm2 restart escrow-api

# Step 3: Check logs for errors
pm2 logs escrow-api --err | head -50

# Step 4: Check database connectivity
psql $DATABASE_URL -c "SELECT 1"
# Expected: (1 row)

# Step 5: Check disk space
df -h | grep "/$"
# Expected: < 70% used

# Step 6: Check memory
free -h
# Expected: < 70% used
```

**Still failing?** → Escalate to L2 engineer

---

### Problem: Database Connection Fails

```bash
# Step 1: Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier escrow-prod-db \
  --query 'DBInstances[0].DBInstanceStatus'
# Expected: available

# Step 2: If "rebooting", wait 5 minutes and retry

# Step 3: If "failed", trigger reboot
aws rds reboot-db-instance \
  --db-instance-identifier escrow-prod-db

# Step 4: Wait for "available" status
aws rds wait db-instance-available \
  --db-instance-identifier escrow-prod-db

# Step 5: Restart application
pm2 restart escrow-api
```

**Still failing?** → Escalate to L2 engineer (possible data corruption)

---

### Problem: High CPU Usage (> 80%)

```bash
# Step 1: Identify process
top -bn1 | head -20

# Step 2: Check if it's the Node.js app
pm2 monit

# Step 3: Check for memory leaks
node --check ./server/index.ts

# Step 4: Restart application
pm2 restart escrow-api

# Step 5: Monitor for 10 minutes
pm2 monit
```

**Still high after restart?** → Check for query abuse or traffic spike

---

### Problem: High Memory Usage (> 80%)

```bash
# Step 1: Check details
free -h

# Step 2: Check PM2 memory
pm2 monit | grep memory

# Step 3: Restart application
pm2 kill escrow-api
pm2 start npm --name "escrow-api" -- start

# Step 4: Check if memory drops
watch -n 5 'free -h'
```

**Keeps growing?** → Memory leak, escalate to L2 engineer

---

### Problem: Disk Space Critical (> 85%)

```bash
# Step 1: Check disk usage
df -h

# Step 2: Find large directories
du -sh /* | sort -rh

# Step 3: Clean old logs
rm -f ~/.pm2/logs/*-error.log.* 2>/dev/null
rm -f ~/.pm2/logs/*-out.log.* 2>/dev/null

# Step 4: Clean old database dumps
rm -f ~/backups/*.sql.gz

# Step 5: Check again
df -h
```

**Still above 85%?** → May need to upgrade disk, escalate to L2

---

## 🔄 WEEKLY TASKS (Monday Morning)

```bash
# Generate weekly report
cat > /tmp/weekly-report.sh << 'EOF'
#!/bin/bash

echo "=== WEEKLY REPORT ==="
echo "Week Ending: $(date)"
echo ""

# Weekly transactions
echo "Weekly Transactions:"
psql $DATABASE_URL -c "
SELECT DATE(created_at), COUNT(*) as txn_count
FROM escrows
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC"

# Weekly revenue
echo ""
echo "Weekly Revenue (cents):"
psql $DATABASE_URL -c "
SELECT COALESCE(SUM(platform_fee_cents), 0)
FROM escrows
WHERE created_at > NOW() - INTERVAL '7 days'"

# Weekly disputes
echo ""
echo "Weekly Disputes:"
psql $DATABASE_URL -c "
SELECT COUNT(*) FROM disputes
WHERE created_at > NOW() - INTERVAL '7 days'"

# Security audit
echo ""
echo "Security Check:"
sudo ufw status

echo ""
echo "Certificate Expiration:"
sudo certbot certificates

# Resource trends
echo ""
echo "Resource Trends:"
aws cloudwatch get-metric-statistics \
  --namespace EscrowAPI \
  --metric-name CPU_IDLE \
  --statistics Average \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 | jq '.Datapoints | sort_by(.Timestamp) | .[] | {Time: .Timestamp, CPUUsage: (100 - .Average)}'

EOF

chmod +x /tmp/weekly-report.sh
/tmp/weekly-report.sh
```

---

## 📋 MONTHLY TASKS (First Day of Month)

```bash
# Database maintenance
psql $DATABASE_URL -c "VACUUM ANALYZE"

# Update system
sudo apt update && sudo apt upgrade -y

# Update Node dependencies
npm audit fix
npm update

# Review slow queries
psql $DATABASE_URL -c "
SELECT 
  query,
  calls,
  mean_time,
  max_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10"

# Generate financial report
psql $DATABASE_URL -c "
SELECT 
  DATE_TRUNC('month', created_at)::date as month,
  COUNT(*) as total_transactions,
  SUM(source_amount_cents) as total_volume,
  SUM(platform_fee_cents) as total_fees,
  COUNT(CASE WHEN status = 'released' THEN 1 END) as completed,
  COUNT(CASE WHEN status = 'disputed' THEN 1 END) as disputed
FROM escrows
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC
LIMIT 3"
```

---

## 📞 ESCALATION CONTACTS

| Severity | Condition | Action | Contact |
|----------|-----------|--------|---------|
| 🔴 CRITICAL | API down | Page on-call immediately | +254 700 000 000 |
| 🔴 CRITICAL | Database down | Page on-call immediately | +254 700 000 000 |
| 🟠 HIGH | Error rate > 1% | Email ops team within 15 min | ops@eascrow.io |
| 🟠 HIGH | CPU/Memory > 85% | Email ops team within 15 min | ops@eascrow.io |
| 🟡 MEDIUM | Response time > 200ms | Log issue, monitor trend | #alerts-channel |
| 🟡 MEDIUM | Disk space > 80% | Plan cleanup, monitor | #alerts-channel |
| 🟢 LOW | Certificate expiring | Renew (auto-renewal active) | #alerts-channel |

---

## 🔗 QUICK LINKS

| Resource | URL |
|----------|-----|
| CloudWatch Alarms | https://console.aws.amazon.com/cloudwatch/home#alarmsV2: |
| API Health | https://api.eascrow.io/api/health |
| RDS Dashboard | https://console.aws.amazon.com/rds/home |
| EC2 Instances | https://console.aws.amazon.com/ec2/v2/home#Instances: |
| CloudWatch Logs | https://console.aws.amazon.com/logs/home |
| CloudWatch Dashboard | https://console.aws.amazon.com/cloudwatch/home#dashboards:name=EscrowAPIDashboard |

---

## ✅ SIGN-OFF CHECKLIST

At end of day, verify:

- [ ] Morning checklist passed
- [ ] No ALARM state in CloudWatch
- [ ] Evening checklist completed
- [ ] All transactions accounted for
- [ ] No critical errors in logs
- [ ] Backup completed successfully
- [ ] Team notified of any issues

---

## 💡 TIPS FOR SUCCESS

1. **Set phone reminders** for 8:00 AM (morning) and 5:00 PM (evening) checklist
2. **Bookmark all URLs** above in browser
3. **Keep terminal window open** with `tail -f ~/.pm2/logs/escrow-api-out.log`
4. **Watch the dashboard** throughout the day
5. **Test your escalation process** monthly
6. **Keep this guide printed** at your desk

---

## 📞 Emergency Contact Procedure

If something breaks:

1. **Keep calm** - You have runbooks
2. **Take action** - Follow troubleshooting steps above
3. **Document** - Note time, error, action taken
4. **Escalate** - Contact next level if > 15 min without resolution
5. **Notify** - Send status update to team
6. **Post-mortem** - Review what happened once resolved

---

**Print this page and keep it on your desk!** 📌

🚀 You've got this! The platform is in good hands.
