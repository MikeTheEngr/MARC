# MARC

## Money on Arc — AI-Powered Onchain Finance Companion

![Network](https://img.shields.io/badge/Network-Arc%20Testnet-00E5BE?style=flat-square)
![AI](https://img.shields.io/badge/AI-Groq%20%7C%20Gemini-0066FF?style=flat-square)
![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?style=flat-square&logo=react)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python-009688?style=flat-square)
![Database](https://img.shields.io/badge/Database-Supabase%20%7C%20Redis-3ECF8E?style=flat-square)
![Deploy](https://img.shields.io/badge/Deploy-Vercel%20%7C%20Render-black?style=flat-square)
![Status](https://img.shields.io/badge/status-live-brightgreen?style=flat-square)

-----

## Why MARC?

Crypto is powerful but inaccessible. Most users can’t bridge funds, track balances, interpret transactions, or navigate DeFi — without opening five different apps, reading documentation, and hoping they don’t make a costly mistake.

MARC changes that. Talk to MARC the way you’d talk to a brilliant friend who happens to be a financial expert. He checks your wallet, sends USDC, bridges assets cross-chain, fetches live market data, explains DeFi concepts, and executes onchain transactions — all through natural conversation.

MARC is both an AI financial advisor and an autonomous onchain agent. He doesn’t just answer questions. He acts.

-----

## Core Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│         (Vercel — marc-livid-phi.vercel.app)         │
│                                                      │
│  Auth (Supabase)  │  Chat UI  │  Wallet (ethers.js)  │
│  MetaMask signing │  Bridge   │  Conversation memory │
└──────────────────────────┬──────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────┐
│                  FastAPI Backend                     │
│              (Render — marc-00n3.onrender.com)       │
│                                                      │
│   MARC Agent (Groq + Gemini dual provider)          │
│   Tool execution  │  Auth routes  │  Memory (Redis)  │
└──────┬───────────────────┬───────────────────────────┘
       │                   │
┌──────▼──────┐    ┌───────▼────────────────────────┐
│  Arc Testnet │    │         External APIs           │
│  Chain 5042002│   │  CoinGecko · DeFi Llama        │
│  USDC gas    │    │  DuckDuckGo · Circle CCTP       │
└─────────────┘    └────────────────────────────────┘
```

-----

## What MARC Can Do

### Onchain Actions

- **Check Balance** — reads USDC balance from connected wallet on Arc Testnet
- **Send USDC** — user signs via MetaMask, MARC broadcasts to Arc Testnet
- **Transaction History** — fetches and interprets last N transactions in plain English
- **Token Transfers** — tracks USDC sent and received
- **Gas Estimation** — real-time fee estimates on Arc Testnet
- **Cross-Chain Bridge** — bridges USDC to Arc via Circle CCTP v2 (2 signatures, rest is automatic)

### Intelligence

- **Live Crypto Prices** — BTC, ETH, USDC via CoinGecko (no key needed)
- **DeFi Market Stats** — total TVL, top protocols via DeFi Llama
- **Real-Time Web Search** — DuckDuckGo for current news and events
- **Network Status** — Arc Testnet RPC health and latest block

### Personalization

- **Adaptive Tone** — beginner mode uses analogies and check-ins; experienced mode is peer-level and technical
- **Persistent Memory** — Redis stores conversation history per user across sessions
- **User Profiles** — name, language preference, risk appetite stored in Supabase
- **Wallet Integration** — any EVM wallet (MetaMask, Coinbase Wallet, Rainbow, etc.)

-----

## Stack

|Layer        |Technology                          |
|-------------|------------------------------------|
|Frontend     |React 18, Vite, ethers.js           |
|Backend      |FastAPI, Python 3.12                |
|AI — Primary |Groq (llama-3.3-70b-versatile)      |
|AI — Fallback|Gemini 2.0 Flash                    |
|Blockchain   |Arc Testnet, Web3.py, Circle CCTP v2|
|Auth         |Supabase Auth                       |
|Database     |Supabase (PostgreSQL)               |
|Memory       |Upstash Redis                       |
|Deployment   |Vercel (frontend), Render (backend) |

-----

## Agent Tools

|Tool                     |Trigger                        |Description                   |
|-------------------------|-------------------------------|------------------------------|
|`check_balance`          |“wallet”, “balance”            |USDC balance on Arc Testnet   |
|`send_usdc`              |“send”, “transfer”             |Sign + broadcast USDC transfer|
|`get_transaction_history`|“transactions”, “history”      |Last N txns from Arc explorer |
|`get_token_transfers`    |“transfers”, “sent”, “received”|USDC in/out                   |
|`estimate_gas_fee`       |“fees”, “gas”                  |Current fee estimates         |
|`get_transaction_info`   |tx hash                        |Full tx details               |
|`get_network_status`     |“network”, “Arc status”        |RPC health + latest block     |
|`get_bridge_info`        |“bridge”, “cross-chain”        |Circle CCTP bridging guide    |
|`get_crypto_prices`      |“price”, “BTC”, “ETH”          |Live market prices            |
|`get_defi_stats`         |“DeFi”, “TVL”                  |Market overview               |
|`web_search`             |“news”, “latest”, “today”      |Real-time web results         |

-----

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.12+
- MetaMask (or any EVM wallet)
- Supabase account
- Upstash Redis account
- Groq API key (free at console.groq.com)
- Gemini API key (free at aistudio.google.com)

### 1. Clone

```bash
git clone https://github.com/MikeTheEngr/MARC.git
cd MARC
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your keys in .env
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_BACKEND_URL
npm run dev
```

### 4. Database

Run in Supabase SQL Editor:

```sql
create table public.profiles (
  id uuid references auth.users on delete cascade primary key,
  username text unique,
  wallet_address text,
  language text default 'English',
  risk_appetite text default 'beginner',
  created_at timestamp with time zone default timezone('utc', now())
);
alter table public.profiles enable row level security;
create policy "Service role full access" on public.profiles for all using (true) with check (true);
```

### 5. Add Arc Testnet to MetaMask

|Field          |Value                            |
|---------------|---------------------------------|
|Network Name   |Arc Testnet                      |
|RPC URL        |<https://rpc.testnet.arc.network>|
|Chain ID       |5042002                          |
|Currency Symbol|USDC                             |
|Block Explorer |<https://testnet.arcscan.app>    |

### 6. Get Testnet USDC

Visit [faucet.circle.com](https://faucet.circle.com) and request testnet USDC to your wallet.

-----

## Environment Variables

### Backend (`backend/.env`)

```
GROQ_API_KEY=
GEMINI_API_KEY=
ARC_RPC_URL=https://rpc.testnet.arc.network
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

### Frontend (`frontend/.env`)

```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_BACKEND_URL=https://marc-00n3.onrender.com
```

-----

## Roadmap

- [x] Phase 1 — Browser wallet signing (MetaMask, no server key)
- [x] Phase 2 — Cross-chain bridge via Circle CCTP v2
- [ ] Phase 3 — FX swaps + P2P payment links
- [ ] Phase 4 — Proactive alerts, portfolio tracking, tx explanations
- [ ] Phase 5 — Agentic multi-step flows, scheduled payments, webhooks
- [ ] Mobile — React Native / PWA

-----

## Live Demo

**Frontend:** [marc-livid-phi.vercel.app](https://marc-livid-phi.vercel.app)
**Backend:** [marc-00n3.onrender.com](https://marc-00n3.onrender.com)

-----

## Built On

[![Arc Network](https://img.shields.io/badge/Built%20on-Arc%20Network-00E5BE?style=flat-square)](https://arc.io)

Arc is an EVM-compatible Layer-1 blockchain built for programmable money. USDC is the native gas token, enabling stablecoin-native DeFi without ETH volatility.

-----

*MARC is currently on Arc Testnet — no real funds at risk.*