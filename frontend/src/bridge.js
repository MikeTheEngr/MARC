import { BridgeKit } from "@circle-fin/bridge-kit";
import { createAdapterFromProvider } from "@circle-fin/adapter-viem-v2";

const ARC_CHAIN_HEX = "0x4CE152";

export const BRIDGE_SOURCES = {
  sepolia: { name: "Ethereum Sepolia", chainId: 11155111 },
  baseSepolia: { name: "Base Sepolia", chainId: 84532 },
};

export async function bridgeToArc({ fromChainId = 11155111, amount, onStatus }) {
  if (!window.ethereum) throw new Error("No EVM wallet found. Please install MetaMask.");

  onStatus?.("Connecting wallet...");

  // Switch MetaMask to source chain first
  await window.ethereum.request({
    method: "wallet_switchEthereumChain",
    params: [{ chainId: "0x" + fromChainId.toString(16) }],
  }).catch(() => {});

  const sourceAdapter = await createAdapterFromProvider(window.ethereum);

  onStatus?.("Setting up destination chain...");

  // Switch to Arc Testnet for destination adapter
  try {
    await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: ARC_CHAIN_HEX }] });
  } catch (e) {
    if (e.code === 4902) {
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [{ chainId: ARC_CHAIN_HEX, chainName: "Arc Testnet", nativeCurrency: { name: "USDC", symbol: "USDC", decimals: 18 }, rpcUrls: ["https://rpc.testnet.arc.network"], blockExplorerUrls: ["https://testnet.arcscan.app"] }],
      });
    }
  }

  const destAdapter = await createAdapterFromProvider(window.ethereum);

  // Switch back to source chain for the actual bridge
  await window.ethereum.request({
    method: "wallet_switchEthereumChain",
    params: [{ chainId: "0x" + fromChainId.toString(16) }],
  }).catch(() => {});

  const kit = new BridgeKit();
  const fromChainName = Object.values(BRIDGE_SOURCES).find(s => s.chainId === fromChainId)?.name || "Ethereum Sepolia";

  onStatus?.("Approve USDC in MetaMask (step 1 of 2)...");

  const result = await kit.bridge({
    from: { adapter: sourceAdapter, chain: fromChainName },
    to: {
      adapter: destAdapter,
      chain: "Arc Testnet",
      useForwarder: true,
    },
    amount: amount.toString(),
    onStatusChange: (status) => {
      if (status === "pending_approval") onStatus?.("Approve USDC in MetaMask (step 1 of 2)...");
      if (status === "pending_burn") onStatus?.("Confirm bridge transaction in MetaMask (step 2 of 2)...");
      if (status === "pending_attestation") onStatus?.("Waiting for Circle attestation (~20s)...");
      if (status === "pending_mint") onStatus?.("Minting USDC on Arc Testnet...");
      if (status === "complete") onStatus?.("Bridge complete!");
    },
  });

  return {
    success: true,
    sourceTxHash: result.sourceTxHash,
    destTxHash: result.destinationTxHash,
    amount,
    fromChain: fromChainName,
    toChain: "Arc Testnet",
    explorerUrl: result.destinationTxHash ? `https://testnet.arcscan.app/tx/${result.destinationTxHash}` : "https://testnet.arcscan.app",
  };
}

export function detectBridgeRequest(text) {
  const lower = text.toLowerCase();
  const hasBridge = lower.includes("bridge") || lower.includes("transfer from another chain");
  const hasUsdc = lower.includes("usdc");
  const hasConfirm = lower.includes("confirm") || lower.includes("go ahead") || lower.includes("say yes") || lower.includes("shall i") || lower.includes("ready");
  return hasBridge && hasUsdc && hasConfirm;
}

export function extractBridgeDetails(text) {
  const amountMatch = text.match(/(\d+(?:\.\d+)?)\s*usdc/i);
  const isBaseSepolia = text.toLowerCase().includes("base");
  return {
    amount: amountMatch ? parseFloat(amountMatch[1]) : null,
    fromChainId: isBaseSepolia ? 84532 : 11155111,
    fromChainName: isBaseSepolia ? "Base Sepolia" : "Ethereum Sepolia",
  };
}