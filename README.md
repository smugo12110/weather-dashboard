# East African Cross-Border Escrow Middleware Core MVP

This repository contains the backend codebase package for a lean, production-ready **Cross-Border Digital Escrow MVP** designed to mitigate financial exclusion friction points between merchants in Kenya, Uganda, and Rwanda.

## 🚀 Architectural Design Architecture
The software layer is built entirely on top of high-availability payment aggregates (**Flutterwave**) and cloud telecom infrastructure gateways (**Africa's Talking**) to bypass complex infrastructure licensing constraints on day one.

## 📁 Repository Blueprint Component Structure
* `/src/index.js` - Main application pipeline routing layer containing Inbound Payment Generation, Secure Idempotent Release Engines, Webhook Catch Nodes, and native USSD string state flow controllers.
* `package.json` - Node dependencies block configured with low-footprint framework runtimes.
* `.env.example` - Explicit structural reference parameter mapping setup schemas.

## 🛠️ Step-by-Step Initial Setup Manual

1. **Unzip & Extract Contents**
   Extract the archive to your workspace environment.

2. **Install Runtime Node Modules**
   Navigate to the directory in your terminal run:
   ```bash
   npm install
   ```

3. **Configure Local Environment Profiles**
   Duplicate `.env.example`, rename it to `.env`, and insert your developer keys from your developer portal platforms.
   ```bash
   cp .env.example .env
   ```

4. **Launch Local Cluster Development Node Instance**
   ```bash
   npm run start
   ```

## 🔌 API Route Map Overview

### A. Create a New Escrow Hold
* **Endpoint:** `POST /api/escrow/initiate`
* **JSON Request Body Payload JSON Payload Example:**
  ```json
  {
    "buyerPhone": "+256700000000",
    "sellerPhone": "+254700000000",
    "amountUGX": "290000",
    "itemDetails": "Balewares Freight"
  }
  ```

### B. Receive Inbound Payment Notification Triggers
* **Endpoint:** `POST /api/webhooks/flutterwave`
* **Purpose:** Process inbound collection confirmations using asynchronous webhook payloads. Ensure headers contain verification configuration verification strings (`verif-hash`).

### C. Execute Payout Allocation Separations
* **Endpoint:** `POST /api/escrow/release`
* **JSON Request Body Payload JSON Payload Example:**
  ```json
  {
    "txRef": "TX-ESCROW-XXXXXX"
  }
  ```

### D. Interoperable USSD Core Controller Node Route
* **Endpoint:** `POST /api/ussd`
* **Format:** Expects `Content-Type: application/x-www-form-urlencoded` payloads directly generated from Africa's Talking API interfaces.
