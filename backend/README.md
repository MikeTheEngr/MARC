# MARC — Money on Arc

MARC is an AI-powered onchain finance companion built on the Arc Network — 
a Layer-1 blockchain where USDC is the native gas token and programmable 
money is the foundation.

Talk to MARC like a friend. Check your wallet balance, send USDC, estimate 
gas fees, look up transactions, and get clear answers to any Web3 or DeFi 
question — all in natural conversation.

## Features
- AI chat powered by Groq (Llama 3.3 70B)
- Onchain actions: balance, send, fees, transactions
- User auth via email or MetaMask wallet
- Persistent memory across sessions (Upstash Redis)
- Personalized by name, language, and experience level

## Stack
- Frontend: React + Vite (Vercel)
- Backend: FastAPI (Render)
- AI: Groq — Llama 3.3 70B
- Blockchain: Arc Testnet (EVM, USDC gas)
- Auth + DB: Supabase
- Memory: Upstash Redis

## Network
Arc Testnet · Chain ID 5042002 · Gas token: USDC