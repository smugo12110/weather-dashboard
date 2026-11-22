# EA Escrow — Field-Level Encryption Integration Guide

## Overview

Your EA Escrow platform now includes **automatic field-level encryption** using AES-256-GCM. This guide walks through setup, usage, and best practices.

---

## What's Encrypted?

The following merchant data is automatically encrypted:

| Field | Example | Storage | Searchable |
|-------|---------|---------|-----------|
| **bankAccountNumber** | 9876543210 | AES-256-GCM ciphertext | Yes (via Hash) |
| **nationalId** | KE123456789 | AES-256-GCM ciphertext | Yes (via Hash) |
| **taxId** | P001234567 | AES-256-GCM ciphertext | Yes (via Hash) |

**In the database:**
- `bankAccountNumber` → `"ABC123:DEF456:GHI789..."`  (ciphertext)
- `bankAccountHash` → `"sha256hash..."` (blind index for searching)

**In your application code:**
- All decryption happens automatically
- You write and read plaintext values
- Encryption/decryption is transparent

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd escrow-mvp
npm install
```

This installs Prisma, the database client, and cryptography utilities.

### 2. Set Up Environment Variables

Create a `.env` file in the root:

```bash
# Database Connection
DATABASE_URL="postgresql://user:password@localhost:5432/escrow_db"

# Encryption Keys (CRITICAL: Keep these safe, never commit to git)
ENCRYPTION_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0"
HMAC_KEY="9z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2i1h0g9f8e7d6c5b4a3z2y1x0"

# API Configuration
PORT=5000
JWT_SECRET="your-jwt-secret-key"

# Flutterwave
FLW_SECRET_HASH="dev-only-change-me"

# Africa's Talking
AFRICAS_TALKING_API_KEY="replace-with-your-api-key"
AFRICAS_TALKING_USERNAME="replace-with-your-username"
AFRICAS_TALKING_SHORTCODE="12345"
```

**⚠️ IMPORTANT:** Never commit `.env` to git. Use strong, random keys for production.

**Generate new encryption keys:**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 3. Initialize the Database

```bash
# Create database and run migrations
npx prisma migrate dev --name init

# Generate Prisma client
npx prisma generate

# (Optional) Seed with test data
npm run db:seed
```

### 4. Start the Server

```bash
npm start

# Or for development with auto-reload
npm run dev
```

The server starts on `http://localhost:5000`

---

## Usage Examples

### Creating a Merchant (Encryption Automatic)

```typescript
import { prisma } from './src/db';

// Write plaintext, encryption happens automatically
const merchant = await prisma.merchant.create({
  data: {
    username: 'john_doe',
    email: 'john@example.com',
    businessName: 'John Trading Co',
    country: 'KE',
    phoneNumber: '+254700000000',
    
    // These are automatically encrypted before saving to database
    bankAccountNumber: '9876543210',
    nationalId: 'KE123456789',
    taxId: 'P001234567',
  },
});

console.log(merchant.bankAccountNumber); // "9876543210" (decrypted automatically!)
```

**In the database (PostgreSQL):**
```
bankAccountNumber: "ABC123:DEF456:GHI789..."  (encrypted)
bankAccountHash: "sha256hash..."              (for searching)
```

### Reading a Merchant (Decryption Automatic)

```typescript
// Read and decryption happens automatically
const merchant = await prisma.merchant.findUnique({
  where: { id: 'merchant-123' }
});

// All sensitive fields are automatically decrypted
console.log(merchant.bankAccountNumber); // "9876543210"
console.log(merchant.nationalId);        // "KE123456789"
console.log(merchant.taxId);             // "P001234567"
```

### Searching by Encrypted Field

```typescript
import { createBlindIndex } from './src/cryptoUtils';

// Find merchant by bank account (without knowing plaintext)
const accountNumber = '9876543210'; // User input

const merchant = await prisma.merchant.findUnique({
  where: {
    bankAccountHash: createBlindIndex(accountNumber)
  }
});

if (merchant) {
  console.log('Found merchant:', merchant.username);
  console.log('Account (decrypted):', merchant.bankAccountNumber); // "9876543210"
}
```

### Updating Encrypted Fields

```typescript
// Update plaintext, encryption happens automatically
const merchant = await prisma.merchant.update({
  where: { id: 'merchant-123' },
  data: {
    bankAccountNumber: '1234567890', // New account, re-encrypted automatically
    nationalId: 'KE987654321',
  },
});

console.log(merchant.bankAccountNumber); // "1234567890"
```

### Batch Operations

```typescript
// Get all merchants with large transactions
const merchants = await prisma.merchant.findMany({
  where: {
    monthlyLimitCents: { gt: 10000000 }
  }
});

// All decryption happens automatically for each record
merchants.forEach(m => {
  console.log(`${m.username}: ${m.bankAccountNumber}`); // Decrypted
});
```

---

## Creating an Escrow (With Dashboard Integration)

```typescript
import { prisma } from './src/db';

// Create escrow
const escrow = await prisma.escrow.create({
  data: {
    txRef: 'TX-ESCROW-ABC123',
    buyerPhone: '+254700000001',
    sellerPhone: '+256700000002',
    itemDetails: 'Electronics shipment',
    sourceCurrency: 'KES',
    payoutCurrency: 'UGX',
    sourceAmountCents: 250000, // $2,500
    grossPayoutCents: 257500,
    platformFeeCents: 3750,
    netPayoutCents: 253750,
    riskLevel: 'low',
  },
  include: {
    buyer: true,  // Join with buyer merchant
    seller: true, // Join with seller merchant
  }
});

// Both buyer and seller data automatically decrypted
console.log(escrow.buyer?.bankAccountNumber); // Decrypted
```

---

## Dashboard & Analytics

### Get Merchant Dashboard (Merchant Authentication Required)

```typescript
// Endpoint: GET /api/dashboard
// Auth: JWT Bearer Token

async function getMerchantDashboard(merchantId: string) {
  const escrows = await prisma.escrow.findMany({
    where: {
      OR: [
        { buyerId: merchantId },
        { sellerId: merchantId }
      ]
    }
  });

  const stats = {
    totalTransactions: escrows.length,
    totalVolume: escrows.reduce((sum, e) => sum + e.sourceAmountCents, 0),
    completedCount: escrows.filter(e => e.status === 'released').length,
    successRate: (escrows.filter(e => e.status === 'released').length / escrows.length) * 100,
    totalFeesCollected: escrows.reduce((sum, e) => sum + e.platformFeeCents, 0),
  };

  return { merchantId, stats, recentTransactions: escrows.slice(-10) };
}
```

### Daily Analytics (Auto-Aggregated)

```typescript
// Query analytics dashboard
const analytics = await prisma.dailyAnalytic.findMany({
  where: { merchantId: 'merchant-123' },
  orderBy: { date: 'desc' },
  take: 30, // Last 30 days
});

analytics.forEach(day => {
  console.log(`${day.date}: ${day.transactionCount} txns, ${day.transactionVolumeCents} cents volume`);
});
```

---

## Disputes & Insurance

### File a Dispute

```typescript
const dispute = await prisma.dispute.create({
  data: {
    escrowId: 'escrow-123',
    filedBy: 'buyer',
    type: 'non-delivery',
    description: 'Seller did not deliver as agreed',
    evidenceDocs: [
      {
        url: 's3://escrow-bucket/evidence-1.jpg',
        type: 'photo',
        uploadedAt: new Date().toISOString()
      }
    ],
    status: 'pending',
  },
  include: {
    escrow: true,
  }
});

console.log(`Dispute filed: ${dispute.id}`);
```

### Resolve a Dispute (Admin Only)

```typescript
const resolved = await prisma.dispute.update({
  where: { id: 'dispute-123' },
  data: {
    status: 'adjudicated',
    resolution: 'refund_buyer', // or 'release_seller', 'partial_split'
    refundAmountCents: 250000,
    resolutionNotes: 'Buyer provided tracking proof of non-delivery',
  },
});

console.log(`Dispute resolved: refunding ${resolved.refundAmountCents} cents`);
```

### File Insurance Claim

```typescript
const claim = await prisma.insuranceClaim.create({
  data: {
    escrowId: 'escrow-123',
    type: 'buyer_protection',
    status: 'pending',
    claimAmountCents: 250000,
    evidence: {
      trackingNumber: 'FDX123456789',
      deliveryProof: 's3://bucket/delivery-photo.jpg'
    },
  },
});

console.log(`Insurance claim filed: ${claim.id}`);

// Auto-approve claims with clear evidence
if (claim.evidence?.trackingNumber) {
  await prisma.insuranceClaim.update({
    where: { id: claim.id },
    data: { status: 'approved' },
  });
}
```

---

## API Keys & Partner Integration

### Create an API Key for a Partner

```typescript
import { generateApiKey, hashApiKey } from './src/cryptoUtils';

const apiKey = generateApiKey('sk');
const keyHash = hashApiKey(apiKey);

const key = await prisma.apiKey.create({
  data: {
    merchantId: 'merchant-123',
    keyName: 'Integration with Kobo360',
    keyHash: keyHash, // Store hash, never the actual key
    isActive: true,
    rateLimit: 1000, // 1000 requests/minute
    expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000), // 1 year
  },
});

// Return actual key to partner (only once!)
console.log(`Generated API key: ${apiKey}`);
console.log('Store this securely. It will not be shown again.');
```

### Validate API Key

```typescript
import { hashApiKey } from './src/cryptoUtils';

function validateApiKey(req: Request) {
  const authHeader = req.headers['authorization'];
  if (!authHeader?.startsWith('Bearer ')) return null;
  
  const apiKey = authHeader.slice(7);
  const keyHash = hashApiKey(apiKey);
  
  const key = await prisma.apiKey.findUnique({
    where: { keyHash: keyHash }
  });
  
  if (!key || !key.isActive) return null;
  
  // Update last used
  await prisma.apiKey.update({
    where: { id: key.id },
    data: { lastUsedAt: new Date() }
  });
  
  return key.merchantId;
}
```

### Register a Webhook

```typescript
const webhook = await prisma.webhook.create({
  data: {
    merchantId: 'merchant-123',
    eventType: 'escrow.released', // escrow.created, escrow.funded, escrow.released, dispute.filed
    webhookUrl: 'https://partner.example.com/webhooks/escrow',
    isActive: true,
  },
});

console.log(`Webhook registered: ${webhook.id}`);
```

---

## Audit Logging (Compliance)

### Log an Action

```typescript
await prisma.auditLog.create({
  data: {
    merchantId: 'merchant-123',
    action: 'create_escrow',
    resourceType: 'escrow',
    resourceId: 'escrow-123',
    details: {
      txRef: 'TX-ESCROW-ABC123',
      amount: 250000,
      currency: 'KES',
    },
    ipAddress: '192.168.1.1',
  },
});
```

### Query Audit Trail

```typescript
// Get all actions by a merchant
const logs = await prisma.auditLog.findMany({
  where: { merchantId: 'merchant-123' },
  orderBy: { createdAt: 'desc' },
  take: 100,
});

logs.forEach(log => {
  console.log(`[${log.createdAt}] ${log.action} on ${log.resourceType}`);
});
```

---

## Security Best Practices

### 1. Environment Variables
- **NEVER** commit `.env` to git
- Use `.env.example` with placeholder values
- Rotate encryption keys annually
- Store keys in secure vault (AWS Secrets Manager, HashiCorp Vault)

### 2. Encryption Keys
- Keys must be 32 bytes (256 bits) for AES-256
- Use `crypto.randomBytes(32)` to generate
- Keep keys separate from code
- Different keys for dev/staging/production

### 3. Database Access
- Use database connection pooling
- Restrict database access to application server only
- Enable SSL/TLS for database connections
- Regular backups with encryption

### 4. Searching Encrypted Fields
- Always use blind index hashing (`createBlindIndex()`)
- Never try to search by plaintext encrypted fields
- Blind indices are one-way: cannot recover plaintext from hash

### 5. API Keys
- Store hashes, never actual keys
- Rotate keys quarterly
- Implement rate limiting per key
- Revoke keys immediately if compromised

### 6. Audit Logging
- Log all sensitive operations
- Retain logs for compliance (7 years recommended)
- Encrypt audit logs at rest
- Monitor for suspicious patterns

---

## Common Issues & Troubleshooting

### Issue: "Decryption failed: Invalid encrypted format"

**Cause:** Field contains unencrypted data (legacy data)  
**Solution:** Graceful degradation is built-in. Logs warning and leaves as-is.

```typescript
// To migrate legacy data:
const merchants = await prisma.merchant.findMany();
for (const m of merchants) {
  if (m.bankAccountNumber && !m.bankAccountNumber.includes(':')) {
    // Unencrypted data, re-encrypt
    await prisma.merchant.update({
      where: { id: m.id },
      data: { bankAccountNumber: m.bankAccountNumber } // Will be re-encrypted
    });
  }
}
```

### Issue: "ENCRYPTION_KEY not set"

**Cause:** Environment variables not loaded  
**Solution:** Ensure `.env` file exists and is properly formatted

```bash
# Verify .env is loaded
node -e "require('dotenv').config(); console.log(process.env.ENCRYPTION_KEY)"
```

### Issue: Decryption timing out for large queries

**Cause:** Decrypting thousands of records is CPU-intensive  
**Solution:** Batch decrypt or use projections to exclude encrypted fields

```typescript
// ✅ Good: Only select needed fields
const merchants = await prisma.merchant.findMany({
  select: {
    id: true,
    username: true,
    email: true,
    // Exclude: bankAccountNumber, nationalId, taxId
  }
});

// ✅ Good: Batch process with pagination
const merchants = await prisma.merchant.findMany({
  take: 100,
  skip: 0,
});
```

### Issue: Search by hash returns null

**Cause:** Hash field not updated when plaintext changed  
**Solution:** Hash is auto-updated on write, but verify with findUnique

```typescript
// ✅ Correct: Uses blind index for search
const merchant = await prisma.merchant.findUnique({
  where: {
    bankAccountHash: createBlindIndex(accountNumber)
  }
});

// ❌ Wrong: Cannot search by encrypted ciphertext
// const merchant = await prisma.merchant.findUnique({
//   where: { bankAccountNumber: "ABC123:DEF456:..." }
// });
```

---

## Performance Optimization

### Indexes
Database includes indexes on:
- `merchantId` (for lookups)
- `escrowId` (for joins)
- `status` (for filtering)
- `createdAt` (for time-range queries)

### Caching
For read-heavy operations, cache decrypted data:

```typescript
import NodeCache from 'node-cache';

const cache = new NodeCache({ stdTTL: 300 }); // 5 min TTL

async function getMerchantCached(id: string) {
  const cached = cache.get(`merchant:${id}`);
  if (cached) return cached;
  
  const merchant = await prisma.merchant.findUnique({ where: { id } });
  cache.set(`merchant:${id}`, merchant);
  return merchant;
}
```

### Connection Pooling
Configure in `DATABASE_URL`:

```
postgresql://user:pass@host:5432/db?schema=public&poolingMode=transaction&pool_size=20
```

---

## Migration from Unencrypted Database

To encrypt existing data:

```bash
# 1. Create migration
npx prisma migrate dev --name encrypt_sensitive_fields

# 2. Run encryption script
node scripts/encrypt-migration.js
```

Script example:
```typescript
import { prisma } from './src/db';
import { encryptField, createBlindIndex } from './src/cryptoUtils';

async function migrateMerchantEncryption() {
  const merchants = await prisma.merchant.findMany();
  
  for (const merchant of merchants) {
    if (merchant.bankAccountNumber && !merchant.bankAccountNumber.includes(':')) {
      console.log(`Encrypting merchant ${merchant.id}...`);
      
      await prisma.merchant.update({
        where: { id: merchant.id },
        data: {
          bankAccountNumber: merchant.bankAccountNumber, // Re-encrypted via middleware
          bankAccountHash: createBlindIndex(merchant.bankAccountNumber),
        },
      });
    }
  }
  
  console.log('Migration complete!');
}

migrateMerchantEncryption().catch(console.error).finally(() => process.exit());
```

---

## Regulatory Compliance

### Data Protection (GDPR, CCPA, Kenya DPA)
- ✅ Field-level encryption protects personal data
- ✅ Audit logs track data access
- ✅ Data retention policies configurable
- ✅ Right-to-be-forgotten: delete merchant cascades all related records

```typescript
// Delete merchant (cascades to escrows, disputes, etc.)
await prisma.merchant.delete({
  where: { id: 'merchant-123' }
});
```

### KYC/AML Compliance
- Store encrypted KYC documents
- Separate compliance flags (`kycStatus`, `amlStatus`)
- Audit trail of all KYC checks

```typescript
await prisma.merchant.update({
  where: { id: 'merchant-123' },
  data: {
    kycStatus: 'verified',
    kycVerifiedAt: new Date(),
    amlStatus: 'clear',
  },
});
```

### PCI-DSS Compliance (for payment info)
- Never store full credit card numbers
- Store only tokenized references (from Flutterwave)
- Encrypted bank account numbers satisfy tokenization requirement

---

## Next Steps

1. **Install & Initialize**
   ```bash
   npm install
   npm run db:migrate
   npm start
   ```

2. **Test the Dashboard**
   - Open `http://localhost:5000/dashboard`
   - Create a merchant account
   - View encrypted data in real-time

3. **Deploy to Production**
   - Use strong encryption keys (rotate from `.env`)
   - Set up PostgreSQL (managed database)
   - Enable SSL/TLS
   - Regular backups

4. **Monitor**
   - Check audit logs daily
   - Monitor API key usage
   - Alert on suspicious patterns

---

## Support

For questions or issues:
- Check Prisma docs: https://www.prisma.io/docs/
- View schema: `npx prisma studio`
- Contact: support@eascrow.io

**Your platform is now production-ready with enterprise-grade encryption! 🎉**
