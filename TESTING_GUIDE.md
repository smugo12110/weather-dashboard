# EA Cross-Border Escrow — Complete Testing Guide

This guide walks through testing the entire escrow system with OTP authentication via SMS and voice calls using Africa's Talking.

---

## Part 1: Setup

### 1.1 Get Africa's Talking Credentials

1. Go to **https://africastalking.com**
2. Sign up for a free account (sandbox mode)
3. Navigate to **Settings > API Keys** and copy your:
   - **API Key** (long alphanumeric string)
   - **Username** (your account username)
4. Find your **Short Code** in **Settings > Messaging** (or use the default `12345` for testing)

### 1.2 Configure the Backend

```bash
cd escrow-mvp/server

# Copy the environment template
cp .env.example .env

# Edit .env and fill in your Africa's Talking credentials
# FLW_SECRET_HASH=dev-only-change-me  (keep this for testing)
# AFRICAS_TALKING_API_KEY=your-api-key-here
# AFRICAS_TALKING_USERNAME=your-username-here
# AFRICAS_TALKING_SHORTCODE=12345  (or your short code)
```

### 1.3 Start the Backend

```bash
cd escrow-mvp/server
node index.js
```

You should see:
```
╔══════════════════════════════════════════════════════════╗
║  EA Escrow backend listening on http://localhost:5000   ║
║  Supported currencies: KES, UGX, RWF, TZS, BIF, USD      ║
║  Africa's Talking: CONNECTED                            ║
╚══════════════════════════════════════════════════════════╝
```

(If Africa's Talking credentials aren't set, it will say `STUBBED` instead of `CONNECTED`, and OTP codes will be logged to the console for testing.)

### 1.4 Open the Website

Open `escrow-mvp/public/index.html` in your browser (double-click it or drag it into a browser tab).

---

## Part 2: Full End-to-End Test Flow

### Step 1: **Lock Funds in Escrow (Section 01)**

**What to fill in:**
- **Buyer Phone**: `256770000001` (Uganda, 10 digits + country code)
- **Seller Phone**: `254712345678` (Kenya, 10 digits + country code)
- **Amount**: `100000`
- **Buyer Pays In**: UGX
- **Seller Receives In**: KES
- **Item Details**: `Test cargo shipment`
- **Buyer Email**: `buyer@test.com`

**Click:** "Generate Escrow Payment Contract"

**Expected results:**
1. Terminal (right panel) shows:
   - ✅ `CONTRACT INITIATED: TX-ESCROW-XXXXXXXX` (your unique reference)
   - ✅ Pricing breakdown (exchange rate, gross payout, platform fee, net payout)
   - ✅ `AI Risk Assessment: LOW (score 0/100)` 
   - ✅ `OTP codes sent via SMS to buyer and seller. Valid for 10 minutes.`

2. **AI Risk Badge** appears below the form (green = low risk)

3. **Buyer Authentication** section appears:
   - "A 6-digit OTP code has been sent to the buyer's phone via SMS"
   - Two buttons: **Verify** and **📞 Call** (voice call fallback)

4. **Seller Authentication** section appears (in Section 03):
   - Same two buttons for seller

---

### Step 2: **Buyer Verifies OTP (Section 01)**

**If SMS is connected:**
- The buyer receives a real SMS: `Your EA Escrow OTP: 123456. Valid for 10 minutes. Do not share this code.`
- Enter the 6-digit code in the "Buyer Authentication" field
- Click **Verify**

**If SMS is NOT connected (stubbed mode):**
- Check the terminal on the right — it logs: `[SMS STUB] To +256770000001: Your EA Escrow OTP: 123456...`
- Use that code for testing

**Expected result:**
- ✅ Status changes to `✅ Buyer authenticated`
- ✅ Terminal logs: `Buyer authentication successful.`

**If code is wrong:**
- ❌ Error: `Incorrect code` with attempt count (max 5 attempts, then locked)

**For voice call fallback:**
- Click the **📞 Call** button instead
- Africa's Talking initiates a voice call that reads out the OTP code
- Terminal shows: `Requesting voice call for buyer...` → `Voice call initiated to +256770000001 with OTP`

---

### Step 3: **Simulate Payment Confirmation (Section 02)**

Once buyer is verified, simulate the Flutterwave webhook (in a real system, this happens when the buyer's payment clears):

**What's pre-filled:**
- **Escrow Reference**: Auto-filled from Step 1 (e.g., `TX-ESCROW-XXXXXXXX`)

**Click:** "Simulate Funding"

**Expected result:**
- ✅ Terminal logs: `FUNDING CONFIRMED: Escrow marked as funded`
- ✅ The escrow is now `funded` and waiting for seller verification + release

**Without buyer OTP (if you skip Step 2):**
- ❌ Error: `Buyer has not completed OTP authentication — funds cannot be marked as received.`

---

### Step 4: **Seller Verifies OTP (Section 03)**

**Escrow Reference** is auto-filled. Now scroll to the **Seller Authentication** section.

**If SMS is connected:**
- Seller receives SMS: `Your EA Escrow OTP: 654321. Valid for 10 minutes. Do not share this code.`
- Enter the code in the seller field
- Click **Verify**

**If SMS is stubbed:**
- Terminal shows: `[SMS STUB] To +254712345678: Your EA Escrow OTP: 654321...`
- Use that code

**Expected result:**
- ✅ Status changes to `✅ Seller authenticated`
- ✅ The **"Authorize Payout"** button changes from grey (disabled) to green (enabled)
- ✅ Terminal logs: `Seller authentication successful.`

**For voice call:**
- Click **📞 Call** and receive a voice call with the OTP code

---

### Step 5: **Authorize Payout (Section 03)**

Once seller is verified, the "Authorize Payout" button is now **enabled** (green).

**Click:** "Authorize Payout"

**Expected result:**
- ✅ Terminal logs:
  - `Authorizing escrow release for: TX-ESCROW-XXXXXXXX...`
  - `LIQUIDATION CONFIRMED: Payout disbursed to seller`
  - `Disbursed: XXX.XX KES` (the net amount, after platform fee)

- ✅ The escrow status changes from `funded` to `released`

**Without seller OTP:**
- ❌ Error: `Seller has not completed OTP authentication — payout cannot be released.`

---

### Step 6: **Check Final Status (Section 04)**

Verify the entire transaction is complete.

**Escrow Reference**: Auto-filled (e.g., `TX-ESCROW-XXXXXXXX`)

**Click:** "Lookup"

**Expected result:**
- ✅ Terminal logs:
  - `Status: released`
  - `Amount: 100000 UGX -> KES`
  - `Buyer verified: true | Seller verified: true`
  - `AI Risk: LOW (0/100)`

---

## Part 3: Test Error Scenarios

### Scenario A: Wrong OTP Code

1. In Step 2 (Buyer OTP), enter `000000` instead of the real code
2. **Expected**: Error message with "Attempts remaining: 4"
3. After 5 wrong attempts: `Too many failed attempts. This OTP is locked.`

### Scenario B: OTP Expired

1. Lock funds (Step 1)
2. Wait 10+ minutes (the OTP TTL)
3. Try to verify OTP
4. **Expected**: Error: `OTP has expired. Re-initiate the escrow to get a new code.`

### Scenario C: Identical Buyer/Seller Phones (High Risk)

1. In Step 1, use the same phone for both buyer and seller: `256770000001`
2. **Expected**:
   - AI Risk Badge shows **HIGH** (red) with score 70+
   - Reason listed: `Buyer and seller phone numbers are identical`

### Scenario D: Large Transaction (>$5,000)

1. Set amount to a very large number (e.g., `2000000000` UGX, roughly $8,500)
2. **Expected**: AI Risk shows **MEDIUM** or **HIGH** with reason: `Transaction value is unusually large (>$5,000 equivalent)`

### Scenario E: Missing Item Details

1. Leave "Item Details" blank
2. **Expected**: AI Risk increases by 5 points, reason: `No item/order description provided`

### Scenario F: Release Without Buyer Verification

1. Lock funds (Step 1)
2. Skip buyer OTP (Step 2)
3. Click "Simulate Funding" (Step 3)
4. **Expected**: Error: `Buyer has not completed OTP authentication — funds cannot be marked as received.`

### Scenario G: Release Without Seller Verification

1. Complete Steps 1-4
2. Skip seller OTP verification
3. Click "Authorize Payout" (it will be disabled, but if you somehow enable it)
4. **Expected**: Error: `Seller has not completed OTP authentication — payout cannot be released.`

---

## Part 4: Testing with Different Currencies

The system supports: **KES, UGX, RWF, TZS, BIF, USD**

**Test a Kenya → Rwanda cross-border transaction:**
- Buyer Pays In: **KES** (Kenya Shilling)
- Seller Receives In: **RWF** (Rwandan Franc)
- Amount: `50000` KES
- **Expected**: Pricing shows the exchange rate and converted payout amount

---

## Part 5: Troubleshooting

### OTP codes appear in terminal but not arriving via SMS

**Status**: Africa's Talking credentials not configured
- Check `.env` file has `AFRICAS_TALKING_API_KEY` and `AFRICAS_TALKING_USERNAME` filled in
- Restart the server: `node index.js`
- Check the startup message says `Africa's Talking: CONNECTED` (not `STUBBED`)

### "Network Connect Fault" in terminal

**Status**: Backend is not running or URL is wrong
- Verify: `curl http://localhost:5000/api/health` returns `{"status":"ok"}`
- Check `BACKEND_URL` at the top of the HTML file matches your server

### Voice call doesn't work

**Status**: Africa's Talking account may not have voice permissions
- Free Africa's Talking sandbox accounts sometimes need approval for voice
- Check: https://africastalking.com > Settings > Capabilities
- Fall back to SMS testing while you wait for approval

### "Too many failed attempts" but I haven't entered 5 codes

**Status**: The OTP counter is per phone/role, shared across browser sessions
- Solution: Initiate a new escrow (new txRef) to get new OTP codes

---

## Part 6: What's Happening Behind the Scenes

1. **Initiate** → Backend generates OTP codes, sends SMS via Africa's Talking
2. **Buyer/Seller verify OTP** → Backend compares entered code to stored code, marks role as verified
3. **Webhook (Funding)** → Backend checks buyer verified before marking `funded`
4. **Release** → Backend checks seller verified before releasing payout
5. **Status** → Backend returns transaction state (never exposes actual OTP codes, only verified flags)

---

## Part 7: Security Notes

- ✅ OTP codes are **never** shown in API responses (only on-screen for dev testing)
- ✅ OTP codes are **never** exposed in status lookups
- ✅ Codes expire after 10 minutes
- ✅ Lockout after 5 failed attempts
- ✅ Webhooks are signature-verified (FLW_SECRET_HASH header)
- ⚠️ In production, remove dev OTP from responses and send via real SMS/voice only

---

## Part 8: Next Steps

After this testing:
1. **Integrate a real payment provider** (Flutterwave, M-Pesa, DPO)
2. **Wire up a database** (replace in-memory Map with Postgres/MySQL)
3. **Add merchant onboarding** (KYC, bank account verification)
4. **Implement dispute resolution** (buyer/seller claims)
5. **Set up compliance** (regulatory approvals per country)

---

**Questions?** Check the terminal logs on the right panel—every API call and result is logged there.

Good luck with your testing!
