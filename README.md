# TrustChain: Blockchain-Based Event Detection & Trust Verification

[![Python](https://img.shields.io/badge/Python-3.7.0-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-2.1.15-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.11-363636?style=flat-square&logo=solidity&logoColor=white)](https://soliditylang.org/)
[![Truffle](https://img.shields.io/badge/Truffle-5.4.29-5E464D?style=flat-square&logo=truffle&logoColor=white)](https://trufflesuite.com/)
[![Web3.py](https://img.shields.io/badge/Web3.py-4.7.2-F16822?style=flat-square)](https://web3py.readthedocs.io/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-1.14.0-FF6F00?style=flat-square&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Keras](https://img.shields.io/badge/Keras-2.3.1-D00000?style=flat-square&logo=keras&logoColor=white)](https://keras.io/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20%26%20Storage-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> **Decentralized, Deep Learning-Powered Crisis Intelligence Platform**  
> Combines Natural Language Processing (2D Convolutional Neural Networks), Ethereum Smart Contracts, and Cloud Hybrid Persistence (Supabase PostgreSQL + Storage) to detect disaster events from social feeds, anchor tamper-proof cryptographic proofs on-chain, and calculate explainable trust scores (0–100).

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. System Architecture](#2-system-architecture)
- [3. Key Innovations & Technical Highlights](#3-key-innovations--technical-highlights)
  - [3.1 Deep Learning Classification Pipeline](#31-deep-learning-classification-pipeline)
  - [3.2 Deterministic SHA-256 Data Integrity](#32-deterministic-sha-256-data-integrity)
  - [3.3 Explainable Trust & Reliability Score](#33-explainable-trust--reliability-score)
  - [3.4 Ethereum Smart Contract Registry](#34-ethereum-smart-contract-registry)
  - [3.5 Supabase Cloud Persistence & Storage](#35-supabase-cloud-persistence--storage)
  - [3.6 Academic Demonstration: Tamper & Restoration](#36-academic-demonstration-tamper--restoration)
  - [3.7 Modern Glassmorphic UI with 3D WebGL Engine](#37-modern-glassmorphic-ui-with-3d-webgl-engine)
- [4. Project Structure](#4-project-structure)
- [5. Prerequisites & Environment Setup](#5-prerequisites--environment-setup)
- [6. Installation & Configuration Guide](#6-installation--configuration-guide)
  - [Step 1: Clone & Navigate](#step-1-clone--navigate)
  - [Step 2: Environment Configuration (.env)](#step-2-environment-configuration-env)
  - [Step 3: Python Environment & Dependencies](#step-3-python-environment--dependencies)
  - [Step 4: Launch Local Ethereum Blockchain (Truffle)](#step-4-launch-local-ethereum-blockchain-truffle)
  - [Step 5: Supabase Cloud Database & Storage Setup](#step-5-supabase-cloud-database--storage-setup)
  - [Step 6: Launch Django Web Application](#step-6-launch-django-web-application)
- [7. Core User Workflows](#7-core-user-workflows)
- [8. Smart Contract Reference (`Event.sol`)](#8-smart-contract-reference-eventsol)
- [9. Database & Storage Schema](#9-database--storage-schema)
- [10. Automated Test Suites & Quality Verification](#10-automated-test-suites--quality-verification)
- [11. Troubleshooting & FAQs](#11-troubleshooting--faqs)
- [12. Academic Citation & License](#12-academic-citation--license)

---

## 1. Executive Summary

During critical natural disasters and public emergencies (earthquakes, floods, wildfires, industrial accidents), social media channels become saturated with contradictory eyewitness reports, rumors, and coordinated disinformation. Emergency responders and civil protection agencies lack automated tools to verify the veracity of incoming incident alerts and guarantee that reported event data cannot be retroactively manipulated.

**TrustChain** resolves this crisis intelligence challenge by unifying:
1. **Deep Learning Natural Language Processing (NLP):** Automatically filters, cleans, tokenizes, and categorizes unstructured text reports into `Disaster Event Detected` vs. `Normal Event Detected`, outputting exact Softmax confidence percentages.
2. **Decentralized Cryptographic Anchoring:** Computes a canonical SHA-256 cryptographic digest of the event payload and commits it to an Ethereum smart contract.
3. **Explainable Composite Trust Scoring:** Computes an explainable 0–100 score balancing cryptographic integrity (50 pts), classification confidence (40 pts), and crisis context (10 pts). A hard-gate cryptographic rule forfeits the score to strictly `0 / 100` if the on-chain hash does not match.
4. **Hybrid Storage with Decoupled Media Assets:** Stores complete event records in Supabase PostgreSQL and photographic attachments in Supabase Storage (`event-images`), while keeping heavy assets off-chain to maintain high transaction throughput.

---

## 2. System Architecture

```
                                  +-----------------------------------------------+
                                  |              User Web Browser                 |
                                  |   (Modern Glassmorphic UI + 3D WebGL Mesh)   |
                                  +-----------------------+-----------------------+
                                                          |
                                           HTTP POST / Multipart Form Data
                                           (Event Text + Optional Image)
                                                          |
                                                          v
                                  +-----------------------------------------------+
                                  |          Django 2.1.15 Backend Engine         |
                                  |   (EventApp/views.py & Event/settings.py)    |
                                  +---+-------------------+-------------------+---+
                                      |                   |                   |
                        Clean & Vectorize Text      Direct Upload         Web3 RPC
                                      |             (Service Role)            |
                                      v                   |                   v
                +-----------------------------+           |     +-----------------------------+
                |   Deep Learning 2D CNN      |           |     |    Ethereum Smart Contract  |
                |   (Conv2D + MaxPool2D)      |           |     |     (Truffle Devnet :9545)  |
                |                             |           |     |                             |
                |  Class: Disaster / Normal   |           |     |  Contract: 0x701c696E...    |
                |  Confidence: Softmax Probs  |           |     |  Methods: recordEvent()     |
                +--------------+--------------+           |     |           getEvent()        |
                               |                          |     |           verifyEventHash() |
                    Compute SHA-256 Digest                |     |           simulateTamper()  |
                     & Explainable Trust                  |     |           restoreEvent()    |
                               |                          |     +--------------+--------------+
                               v                          |                    ^
                +-----------------------------+           |                    |
                |  Canonical Post Hash Bytes  |           |         Anchors Hash & Score
                |  (username$text$date$class) |           |                    |
                +--------------+--------------+           |                    |
                               |                          |                    |
                               +--------------------+     |                    |
                                                    |     |                    |
                                                    v     v                    |
                                  +---------------------------------------+    |
                                  |        Supabase Cloud Platform        |    |
                                  |                                       |    |
                                  |  1. Storage Bucket: 'event-images'    |    |
                                  |     (Secure backend upload,           |    |
                                  |      public read CDN URL)             |    |
                                  |                                       |    |
                                  |  2. PostgreSQL Table: 'public.events' |----+
                                  |     (Metadata, Hash, Trust Score,     |
                                  |      image_url, blockchain_tx_hash)   |
                                  +---------------------------------------+
```

---

## 3. Key Innovations & Technical Highlights

### 3.1 Deep Learning Classification Pipeline
- **Text Normalization:** Lowercasing, punctuation stripping, tokenization, stopword removal (NLTK English corpus), Porter stemming, and WordNet lemmatization.
- **Vector Space Representation:** `TfidfVectorizer(max_features=300)` extracts the 300 most salient term frequencies, standardized via `StandardScaler`.
- **2D Tensor Transformation:** Reshapes the 300-dimension vector into a `(1, 10, 10, 3)` pseudo-image tensor suitable for 2D convolutional feature extraction.
- **Convolutional Neural Network Architecture:**
  - `Conv2D(32, (3, 3), activation='relu')`
  - `MaxPooling2D(pool_size=(2, 2))`
  - `Conv2D(32, (3, 3), activation='relu')`
  - `MaxPooling2D(pool_size=(2, 2))`
  - `Flatten()` -> `Dense(256, activation='relu')` -> `Dense(2, activation='softmax')`
- **Trained Weights:** Pre-trained on 5,080 disaster/normal tweets ([Dataset/DisasterTweets.csv](Blockchain--4--main/Blockchain/BlockchainEventDetection/Dataset/DisasterTweets.csv)), stored in [model/dl_weights.hdf5](Blockchain--4--main/Blockchain/BlockchainEventDetection/model/dl_weights.hdf5).
- **Benchmarking Suite:** Side-by-side performance evaluation across 8 algorithms: Naive Bayes, KNN, SVM, Logistic Regression, Decision Tree, Random Forest, XGBoost, and 2D CNN (Deep Learning).

### 3.2 Deterministic SHA-256 Data Integrity
- Computes a canonical cryptographic fingerprint:
  ```python
  post_str = f"{username}${tweet}${event_date}${classification}\n"
  sha256_digest = hashlib.sha256(post_str.encode('utf-8')).hexdigest()
  ```
- **Asset Decoupling:** Image binaries and Supabase URLs are intentionally excluded from the cryptographic hash. This guarantees that image storage upgrades or URL redirects never invalidate existing on-chain cryptographic proofs.

### 3.3 Explainable Trust & Reliability Score
A transparent, explainable reliability score between **0 and 100** computed in [EventApp/views.py](Blockchain--4--main/Blockchain/BlockchainEventDetection/EventApp/views.py):
1. **Cryptographic Integrity (50 Points Max):**
   - Verified (Supabase SHA-256 matches Ethereum on-chain `dataHash`): **50 points**.
   - Tampered / Mismatched: **0 points** (Hard-Gate: entire score drops to 0).
2. **Deep Learning Softmax Confidence (40 Points Max):**
   - Derived directly from CNN output: `round((confidence / 100.0) * 40.0)`.
3. **Event Context Corroboration (10 Points Max):**
   - Disaster Event detected: **10 points**.
   - Normal Event detected: **8 points**.

$$\text{Trust Score} = \begin{cases} 0, & \text{if integrity verification fails} \\ \min(100, 50 + \text{round}(0.40 \times \text{Conf}) + \text{Context}), & \text{if verified} \end{cases}$$

### 3.4 Ethereum Smart Contract Registry
- Implemented in Solidity `0.8.11` ([hello-eth/contracts/Event.sol](Blockchain--4--main/Blockchain/hello-eth/contracts/Event.sol)) and compiled with Truffle.
- Stores immutable event anchors in an EVM `mapping(uint256 => EventRecord) public events`.
- Emits indexed EVM log events: `EventRecorded`, `EventTampered`, and `EventRestored`.
- Protected by `onlyOwner` access control modifiers.

### 3.5 Supabase Cloud Persistence & Storage
- **PostgreSQL Database:** Hosts `public.events` containing structured event records, classifications, confidence values, SHA-256 digests, and Ethereum transaction hashes.
- **Storage Bucket (`event-images`):** Hosts uploaded disaster scene photos. Uploads are strictly controlled server-side via `SUPABASE_SERVICE_ROLE_KEY`; no public upload policy is permitted, preventing unauthorized asset injection.
- **Validation Gating:** Max 5 MB per image, whitelisted formats (`.jpg`, `.jpeg`, `.png`, `.webp`), and randomized UUID naming (`evt_<12hex>_<filename>`) to prevent directory traversal.

### 3.6 Academic Demonstration: Tamper & Restoration
- Built-in simulation lab accessible directly via the web UI (`/VerifyIntegrity`):
  - **Simulate Blockchain Tampering:** Invokes `simulateEventTampering()` on Ethereum, mutating the on-chain hash to `0xdeadbeef...`. The verification engine immediately flags the event as `TAMPERED / UNVERIFIED` and drops the trust score to `0 / 100`.
  - **Restore Event:** Invokes `restoreEvent()` to rewrite the authentic pre-tamper hash and trust score back to Ethereum, restoring the record to `VERIFIED`.

### 3.7 Modern Glassmorphic UI with 3D WebGL Engine
- Custom dark glassmorphism theme using HSL tailored gradients, cyan accenting, and responsive layout cards.
- Fullscreen animated 3D particle ledger mesh powered by Three.js.
- Headless matplotlib integration generating crisp base64-encoded comparison charts without X11/GUI display server dependencies.

---

## 4. Project Structure

```
c:/FYP/Blockchain/
├── README.md                              # Root Documentation
├── Blockchain--4--main/Blockchain/        # Active Repository Root
│   ├── BlockchainEventDetection/          # Django Web Application Root
│   │   ├── .env                           # Environment secrets (Supabase credentials)
│   │   ├── Dataset/                       # Training corpus (5,080 labeled tweets)
│   │   ├── Event/                         # Django Project Settings
│   │   ├── Event.json                     # Compiled Smart Contract ABI
│   │   ├── EventApp/                      # Views, models, static, templates
│   │   ├── model/                         # CNN weights & serialized features
│   │   ├── test_*.py                      # Automated test suites
│   │   └── venv/                          # Python 3.7 virtual environment
│   ├── hello-eth/                         # Truffle Ethereum Project
│   │   ├── contracts/Event.sol            # Solidity Smart Contract
│   │   └── truffle-config.js              # Network settings (Port 9545)
│   ├── doc/                               # Academic thesis documentation
│   └── requirements.txt                   # Pinned dependency manifest
```

---

## 5. Prerequisites & Environment Setup

| Component | Required Version | Verification Command |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 x64, Linux, or macOS | `systeminfo` / `uname -a` |
| **Python** | Python 3.7.0 (64-bit) | `python --version` |
| **Node.js** | Node.js v12.13.1 (or v12–v16) | `node --version` |
| **Truffle** | v5.4.29 | `npx truffle version` |
| **Solidity** | 0.8.11 | Embedded in Truffle |

---

## 6. Installation & Configuration Guide

### Step 1: Environment Configuration (.env)
Create or verify `.env` inside `Blockchain--4--main/Blockchain/BlockchainEventDetection/`:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-publishable-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-secret-service-role-key
```

### Step 2: Python Environment & Dependencies
```powershell
cd Blockchain--4--main/Blockchain/BlockchainEventDetection
py -3.7 -m venv venv
.\venv\Scripts\activate
pip install -r ../requirements.txt
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"
```

### Step 3: Launch Local Ethereum Blockchain (Truffle)
In a separate terminal window:
```powershell
cd Blockchain--4--main/Blockchain/hello-eth
npm install
npx truffle develop
```
Inside the `truffle(develop)>` prompt:
```text
compile
migrate --reset
```

### Step 4: Launch Django Web Application
```powershell
cd Blockchain--4--main/Blockchain/BlockchainEventDetection
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py runserver 8000
```
Open your browser at: `http://127.0.0.1:8000/index.html`

---

## 7. Automated Test Suites & Quality Verification

```powershell
cd Blockchain--4--main/Blockchain/BlockchainEventDetection

# 1. Django Backend Health Check
.\venv\Scripts\python.exe manage.py check

# 2. Phase 10 Image Support & Gating Suite (12/12 PASS)
.\venv\Scripts\python.exe test_phase10_image_support.py

# 3. Phase 9 End-to-End Regression Validation Suite (16/16 PASS)
.\venv\Scripts\python.exe test_phase9_full_validation.py

# 4. Supabase Cloud Connection Test
.\venv\Scripts\python.exe test_supabase_connection.py
```

---

## 8. License & Academic Citation

Developed as a Final Year Project (FYP) in Computer Science & Engineering.  
Licensed under the [MIT License](LICENSE) — free for educational, academic, and non-commercial research use.
