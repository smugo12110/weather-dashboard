# EA Escrow Platform — API Documentation

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: EA Escrow Platform API
  version: 2.0.0
  description: Cross-border B2B escrow platform for East Africa
  contact:
    email: api@eascrow.io
  license:
    name: Apache 2.0

servers:
  - url: https://api.eascrow.io
    description: Production
  - url: http://localhost:5000
    description: Development

paths:
  /api/health:
    get:
      summary: Health check
      tags:
        - System
      responses:
        200:
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
      security: []

  /api/signup:
    post:
      summary: Create merchant account
      tags:
        - Merchants
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SignupRequest'
      responses:
        201:
          description: Merchant created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'
        409:
          description: Username or email already exists
      security: []

  /api/dashboard:
    get:
      summary: Get merchant dashboard
      tags:
        - Dashboard
      responses:
        200:
          description: Dashboard data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DashboardResponse'
        401:
          description: Unauthorized
      security:
        - bearerAuth: []

  /api/analytics:
    get:
      summary: Get analytics data
      tags:
        - Analytics
      parameters:
        - name: days
          in: query
          schema:
            type: integer
            default: 30
      responses:
        200:
          description: Analytics data
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/DailyAnalytic'
      security:
        - bearerAuth: []

  /api/escrow/create:
    post:
      summary: Create escrow transaction
      tags:
        - Escrow
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateEscrowRequest'
      responses:
        201:
          description: Escrow created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EscrowResponse'
      security: []

  /api/escrow/{txRef}:
    get:
      summary: Get escrow status
      tags:
        - Escrow
      parameters:
        - name: txRef
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Escrow details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EscrowDetails'
        404:
          description: Escrow not found
      security: []

  /api/escrow/verify-otp:
    post:
      summary: Verify OTP code
      tags:
        - Escrow
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VerifyOTPRequest'
      responses:
        200:
          description: OTP verified
          content:
            application/json:
              schema:
                type: object
                properties:
                  verified: { type: boolean }
                  message: { type: string }
        400:
          description: Invalid or expired OTP
        423:
          description: Too many failed attempts
      security: []

  /api/escrow/release:
    post:
      summary: Release funds to seller
      tags:
        - Escrow
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                txRef:
                  type: string
      responses:
        200:
          description: Funds released
        400:
          description: Cannot release (wrong status)
      security: []

  /api/disputes:
    post:
      summary: File a dispute
      tags:
        - Disputes
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FileDisputeRequest'
      responses:
        201:
          description: Dispute filed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DisputeResponse'
      security: []

  /api/disputes/{id}:
    get:
      summary: Get dispute details
      tags:
        - Disputes
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Dispute details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DisputeDetails'
    put:
      summary: Resolve dispute (admin only)
      tags:
        - Disputes
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                resolution:
                  type: string
                  enum: [refund_buyer, release_seller, partial_split]
      responses:
        200:
          description: Dispute resolved
      security:
        - bearerAuth: []

  /api/claims:
    post:
      summary: File insurance claim
      tags:
        - Insurance
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FileClaimRequest'
      responses:
        201:
          description: Claim filed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ClaimResponse'
      security: []

  /api/keys:
    post:
      summary: Create API key
      tags:
        - Partner API
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                keyName:
                  type: string
      responses:
        201:
          description: API key created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiKeyResponse'
      security:
        - bearerAuth: []
    get:
      summary: List API keys
      tags:
        - Partner API
      responses:
        200:
          description: API keys
          content:
            application/json:
              schema:
                type: object
                properties:
                  keys:
                    type: array
                    items:
                      $ref: '#/components/schemas/ApiKeyInfo'
      security:
        - bearerAuth: []

components:
  schemas:
    HealthResponse:
      type: object
      properties:
        status:
          type: string
          enum: [ok, error]
        version:
          type: string
        timestamp:
          type: string
          format: date-time
        features:
          type: array
          items:
            type: string

    SignupRequest:
      type: object
      required:
        - username
        - email
        - phoneNumber
        - country
      properties:
        username:
          type: string
        email:
          type: string
          format: email
        businessName:
          type: string
        country:
          type: string
        phoneNumber:
          type: string
        bankAccountNumber:
          type: string
        nationalId:
          type: string

    AuthResponse:
      type: object
      properties:
        merchant:
          type: object
          properties:
            id:
              type: string
            username:
              type: string
            email:
              type: string
            businessName:
              type: string
            country:
              type: string
            createdAt:
              type: string
              format: date-time
        token:
          type: string
          description: JWT token (valid 24 hours)
        message:
          type: string

    DashboardResponse:
      type: object
      properties:
        stats:
          type: object
          properties:
            totalTransactions:
              type: integer
            totalVolumeCents:
              type: integer
            completedCount:
              type: integer
            pendingCount:
              type: integer
            disputeCount:
              type: integer
            totalFeesCollectedCents:
              type: integer
            successRate:
              type: integer
        recentTransactions:
          type: array
          items:
            $ref: '#/components/schemas/EscrowSummary'

    CreateEscrowRequest:
      type: object
      required:
        - buyerPhone
        - sellerPhone
        - amount
        - sourceCurrency
        - payoutCurrency
      properties:
        buyerPhone:
          type: string
          pattern: '^\+?[0-9]{10,15}$'
        sellerPhone:
          type: string
          pattern: '^\+?[0-9]{10,15}$'
        amount:
          type: integer
          description: Amount in smallest currency unit (cents)
        sourceCurrency:
          type: string
          enum: [KES, UGX, RWF, TZS, BIF]
        payoutCurrency:
          type: string
          enum: [KES, UGX, RWF, TZS, BIF]
        itemDetails:
          type: string

    EscrowResponse:
      type: object
      properties:
        txRef:
          type: string
          description: Unique transaction reference
        status:
          type: string
          enum: [pending_funding, funded, released, disputed, cancelled]
        risk:
          type: object
          properties:
            score:
              type: integer
              minimum: 0
              maximum: 100
            level:
              type: string
              enum: [low, medium, high]
        message:
          type: string

    EscrowDetails:
      type: object
      properties:
        id:
          type: string
        txRef:
          type: string
        buyerPhone:
          type: string
        sellerPhone:
          type: string
        itemDetails:
          type: string
        sourceAmountCents:
          type: integer
        platformFeeCents:
          type: integer
        insuranceFeeCents:
          type: integer
        netPayoutCents:
          type: integer
        status:
          type: string
        riskScore:
          type: integer
        riskLevel:
          type: string
        buyerOtpVerified:
          type: boolean
        sellerOtpVerified:
          type: boolean
        fundedAt:
          type: string
          format: date-time
        releasedAt:
          type: string
          format: date-time
        createdAt:
          type: string
          format: date-time

    EscrowSummary:
      type: object
      properties:
        txRef:
          type: string
        sourceAmountCents:
          type: integer
        platformFeeCents:
          type: integer
        status:
          type: string
        riskLevel:
          type: string
        createdAt:
          type: string

    VerifyOTPRequest:
      type: object
      required:
        - txRef
        - role
        - code
      properties:
        txRef:
          type: string
        role:
          type: string
          enum: [buyer, seller]
        code:
          type: string
          pattern: '^[0-9]{6}$'

    FileDisputeRequest:
      type: object
      required:
        - escrowId
        - filedBy
        - type
        - description
      properties:
        escrowId:
          type: string
        filedBy:
          type: string
          enum: [buyer, seller]
        type:
          type: string
          enum: [non-delivery, partial-delivery, quality, other]
        description:
          type: string
        evidence:
          type: array
          items:
            type: string
            format: uri

    DisputeResponse:
      type: object
      properties:
        id:
          type: string
        escrowId:
          type: string
        filedBy:
          type: string
        type:
          type: string
        status:
          type: string
          enum: [pending, buyer_responded, seller_responded, adjudicated, appealed, final]
        createdAt:
          type: string

    DisputeDetails:
      type: object
      properties:
        id:
          type: string
        escrowId:
          type: string
        filedBy:
          type: string
        type:
          type: string
        description:
          type: string
        status:
          type: string
        evidenceDocs:
          type: array
          items:
            type: string
        resolution:
          type: string
        appealReason:
          type: string
        createdAt:
          type: string
        updatedAt:
          type: string

    FileClaimRequest:
      type: object
      required:
        - escrowId
        - claimType
        - amount
      properties:
        escrowId:
          type: string
        claimType:
          type: string
          enum: [buyer_protection, seller_protection]
        amount:
          type: integer
        evidence:
          type: object
          properties:
            trackingNumber:
              type: string

    ClaimResponse:
      type: object
      properties:
        id:
          type: string
        escrowId:
          type: string
        type:
          type: string
        status:
          type: string
          enum: [pending, approved, rejected, paid]
        claimAmountCents:
          type: integer
        createdAt:
          type: string

    ApiKeyResponse:
      type: object
      properties:
        id:
          type: string
        keyName:
          type: string
        apiKey:
          type: string
          description: "Only shown once at creation - save immediately"
        isActive:
          type: boolean
        createdAt:
          type: string

    ApiKeyInfo:
      type: object
      properties:
        id:
          type: string
        keyName:
          type: string
        isActive:
          type: boolean
        lastUsedAt:
          type: string
        createdAt:
          type: string
        expiresAt:
          type: string

    DailyAnalytic:
      type: object
      properties:
        date:
          type: string
          format: date
        transactionCount:
          type: integer
        transactionVolumeCents:
          type: integer
        feesCollectedCents:
          type: integer
        disputesFiled:
          type: integer

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## Common Use Cases

### 1. Create Escrow and Verify OTP

```bash
# Step 1: Create escrow
curl -X POST https://api.eascrow.io/api/escrow/create \
  -H "Content-Type: application/json" \
  -d '{
    "buyerPhone": "+254700000000",
    "sellerPhone": "+256700000000",
    "amount": 250000,
    "sourceCurrency": "KES",
    "payoutCurrency": "UGX",
    "itemDetails": "Electronics shipment"
  }'

# Response:
# {
#   "txRef": "TX-ESCROW-ABC123",
#   "status": "pending_funding",
#   "risk": {"score": 25, "level": "low"}
# }

# Step 2: User receives OTP via SMS, then verify
curl -X POST https://api.eascrow.io/api/escrow/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "txRef": "TX-ESCROW-ABC123",
    "role": "buyer",
    "code": "123456"
  }'

# Response:
# {"verified": true, "message": "OTP verified successfully"}

# Step 3: Fund escrow (via Flutterwave webhook)
# Step 4: Release funds when seller confirms delivery
curl -X POST https://api.eascrow.io/api/escrow/release \
  -H "Content-Type: application/json" \
  -d '{"txRef": "TX-ESCROW-ABC123"}'
```

### 2. File Dispute

```bash
curl -X POST https://api.eascrow.io/api/disputes \
  -H "Content-Type: application/json" \
  -d '{
    "escrowId": "escrow-123",
    "filedBy": "buyer",
    "type": "non-delivery",
    "description": "Items not received after 7 days",
    "evidence": [
      "https://example.com/proof1.jpg",
      "https://example.com/proof2.jpg"
    ]
  }'

# Response:
# {
#   "id": "dispute-456",
#   "escrowId": "escrow-123",
#   "status": "pending",
#   "createdAt": "2024-01-15T10:30:00Z"
# }
```

### 3. File Insurance Claim

```bash
curl -X POST https://api.eascrow.io/api/claims \
  -H "Content-Type: application/json" \
  -d '{
    "escrowId": "escrow-123",
    "claimType": "buyer_protection",
    "amount": 250000,
    "evidence": {
      "trackingNumber": "FDX123456789"
    }
  }'

# Response:
# {
#   "id": "claim-789",
#   "status": "approved",
#   "claimAmountCents": 250000
# }
# Note: auto-approved because tracking number provided
```

### 4. Get Merchant Dashboard

```bash
curl -X GET https://api.eascrow.io/api/dashboard \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Response:
# {
#   "stats": {
#     "totalTransactions": 125,
#     "totalVolumeCents": 31250000,
#     "completedCount": 110,
#     "successRate": 88,
#     ...
#   },
#   "recentTransactions": [...]
# }
```

### 5. Create & Manage API Keys

```bash
# Create API key
curl -X POST https://api.eascrow.io/api/keys \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"keyName": "Integration-Q1"}'

# Response:
# {
#   "id": "key-123",
#   "keyName": "Integration-Q1",
#   "apiKey": "sk_live_abc123def456...",
#   "isActive": true
# }

# List API keys
curl -X GET https://api.eascrow.io/api/keys \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Use API key for programmatic access
curl -X POST https://api.eascrow.io/api/escrow/create \
  -H "Authorization: Bearer sk_live_abc123def456..." \
  -H "Content-Type: application/json" \
  -d '{...escrow data...}'
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Description of what went wrong"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 423 | Locked - Too many failed attempts |
| 500 | Server Error - Internal server error |

---

## Rate Limiting

- **Anonymous endpoints**: 100 requests/minute
- **Authenticated endpoints**: 1000 requests/minute
- **Partner API keys**: 5000 requests/minute (configurable)

Response headers include:
- `X-RateLimit-Limit`: Rate limit quota
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Webhooks

Your application can receive real-time events:

```bash
# Event: Escrow created
POST /your-webhook-url
{
  "event": "escrow.created",
  "data": {
    "txRef": "TX-ESCROW-ABC123",
    "buyerPhone": "+254700000000",
    "amount": 250000
  },
  "timestamp": "2024-01-15T10:30:00Z"
}

# Event: Escrow funded
POST /your-webhook-url
{
  "event": "escrow.funded",
  "data": {
    "txRef": "TX-ESCROW-ABC123",
    "fundedAt": "2024-01-15T10:35:00Z"
  }
}

# Event: Dispute filed
POST /your-webhook-url
{
  "event": "dispute.filed",
  "data": {
    "disputeId": "dispute-456",
    "escrowId": "escrow-123",
    "filedBy": "buyer"
  }
}
```

---

## SDKs & Libraries

### JavaScript/Node.js
```bash
npm install @eascrow/sdk
```

```javascript
const EscrowClient = require('@eascrow/sdk');

const client = new EscrowClient({
  apiKey: 'sk_live_...'
});

// Create escrow
const escrow = await client.escrow.create({
  buyerPhone: '+254700000000',
  sellerPhone: '+256700000000',
  amount: 250000,
  sourceCurrency: 'KES'
});

// Get dashboard
const dashboard = await client.dashboard.get();

// File dispute
const dispute = await client.disputes.file({
  escrowId: escrow.id,
  filedBy: 'buyer',
  type: 'non-delivery'
});
```

### Python
```bash
pip install eascrow-sdk
```

```python
from eascrow import EscrowClient

client = EscrowClient(api_key='sk_live_...')

# Create escrow
escrow = client.escrow.create(
    buyer_phone='+254700000000',
    seller_phone='+256700000000',
    amount=250000,
    source_currency='KES'
)

# Get status
status = client.escrow.get_status(escrow.tx_ref)
```

---

## Testing

### Postman Collection

Import this collection: `escrow-api.postman_collection.json`

Includes all endpoints with examples and environment variables.

### Test Credentials

```
Test Buyer Phone: +254700000000
Test Seller Phone: +256700000000
Test Amount: 250000 cents
Test OTP: 123456 (always succeeds in dev)
```

---

**API Documentation Version 2.0**  
**Last Updated: January 2024**  
**Status: Production Ready ✅**
