import { useState, useRef, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

const API_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);

const timeStr = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const store = (k, v) => localStorage.setItem(k, JSON.stringify(v));
const load = (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } };

const LANGUAGES = ["English", "French", "Spanish", "Portuguese", "Arabic", "Yoruba", "Hausa", "Igbo"];
const SUGGESTIONS = ["What can you do?", "Check my balance", "What is Arc Network?", "How do I send USDC?", "Explain DeFi to me"];

function MarcAvatar({ size = 36 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%", flexShrink: 0,
      background: "linear-gradient(135deg, #00E5BE 0%, #0066FF 100%)",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Sora', sans-serif", fontWeight: "800",
      fontSize: size * 0.38, color: "#020B18",
      boxShadow: "0 0 0 2px rgba(0,229,190,0.25)",
    }}>M</div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "5px", padding: "10px 14px" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{ width: "7px", height: "7px", borderRadius: "50%", background: "linear-gradient(135deg, #00E5BE, #0066FF)", animation: "bounce 1.2s infinite", animationDelay: `${i * 0.18}s` }} />
      ))}
    </div>
  );
}

function MessageBubble({ msg, isLatest }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: "16px", gap: "8px", alignItems: "flex-end", animation: isLatest ? "fadeUp 0.3s ease" : "none" }}>
      {!isUser && <MarcAvatar size={28} />}
      <div style={{ maxWidth: "78%", display: "flex", flexDirection: "column", gap: "3px" }}>
        {!isUser && <span style={{ fontSize: "10px", color: "rgba(0,229,190,0.6)", fontWeight: "700", marginLeft: "3px", letterSpacing: "0.08em" }}>MARC</span>}
        <div style={{ padding: "10px 14px", borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px", background: isUser ? "linear-gradient(135deg, #0055DD, #0033AA)" : "rgba(255,255,255,0.06)", border: isUser ? "none" : "1px solid rgba(255,255,255,0.08)", color: "#EEF2FF", fontSize: "14px", lineHeight: "1.6", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {msg.content}
        </div>
        <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.2)", alignSelf: isUser ? "flex-end" : "flex-start", margin: isUser ? "0 3px 0 0" : "0 0 0 3px" }}>{msg.time}</span>
      </div>
      {isUser && <div style={{ width: "28px", height: "28px", borderRadius: "50%", flexShrink: 0, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px" }}>👤</div>}
    </div>
  );
}

// ── Auth Screen ───────────────────────────────────────────────
function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("signin");
  const [form, setForm] = useState({ email: "", password: "", username: "", language: "English", risk_appetite: "beginner" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    setLoading(true); setError("");
    try {
      if (mode === "signup") {
        const res = await fetch(`${API_URL}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: form.email, password: form.password, username: form.username, language: form.language, risk_appetite: form.risk_appetite }) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Signup failed");
        store("marc_user", { user_id: data.user_id, profile: data.profile });
        onAuth({ user_id: data.user_id, profile: data.profile });
      } else {
        const res = await fetch(`${API_URL}/auth/signin`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: form.email, password: form.password }) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Sign in failed");
        store("marc_user", { user_id: data.user_id, profile: data.profile });
        onAuth({ user_id: data.user_id, profile: data.profile });
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const connectWallet = async () => {
    if (!window.ethereum) return setError("MetaMask not found. Please install it.");
    setLoading(true); setError("");
    try {
      const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
      const res = await fetch(`${API_URL}/auth/wallet`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ wallet_address: accounts[0], language: form.language, risk_appetite: form.risk_appetite }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Wallet login failed");
      store("marc_user", { user_id: data.user_id, profile: data.profile });
      onAuth({ user_id: data.user_id, profile: data.profile });
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const inp = (placeholder, key, type = "text") => (
    <input type={type} placeholder={placeholder} value={form[key]} onChange={e => set(key, e.target.value)}
      onKeyDown={e => e.key === "Enter" && handleSubmit()}
      style={{ width: "100%", padding: "13px 16px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", color: "#EEF2FF", fontSize: "15px", fontFamily: "'IBM Plex Mono', monospace", outline: "none", marginBottom: "10px", transition: "border-color 0.2s" }}
      onFocus={e => e.target.style.borderColor = "rgba(0,229,190,0.4)"}
      onBlur={e => e.target.style.borderColor = "rgba(255,255,255,0.1)"}
    />
  );

  return (
    <div style={{ minHeight: "100vh", minHeight: "100dvh", background: "#020B18", display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
      {/* Background glow */}
      <div style={{ position: "fixed", top: "20%", left: "50%", transform: "translateX(-50%)", width: "400px", height: "400px", background: "radial-gradient(circle, rgba(0,229,190,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ width: "100%", maxWidth: "400px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "24px", padding: "clamp(24px, 5vw, 40px) clamp(20px, 5vw, 36px)" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <MarcAvatar size={52} />
          <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: "800", fontSize: "clamp(22px, 5vw, 28px)", color: "#F0F6FF", marginTop: "10px", letterSpacing: "0.04em" }}>MARC</div>
          <div style={{ fontSize: "11px", color: "rgba(0,229,190,0.5)", letterSpacing: "0.14em", marginTop: "2px" }}>MONEY ON ARC</div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "6px", marginBottom: "20px", background: "rgba(255,255,255,0.04)", borderRadius: "12px", padding: "4px" }}>
          {[["signin", "Sign In"], ["signup", "Sign Up"]].map(([m, label]) => (
            <button key={m} onClick={() => { setMode(m); setError(""); }} style={{ flex: 1, padding: "9px", borderRadius: "9px", border: "none", cursor: "pointer", background: mode === m ? "rgba(0,229,190,0.12)" : "transparent", color: mode === m ? "#00E5BE" : "rgba(255,255,255,0.4)", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", fontWeight: "600", transition: "all 0.2s" }}>{label}</button>
          ))}
        </div>

        {mode === "signup" && inp("Username", "username")}
        {inp("Email address", "email", "email")}
        {inp("Password", "password", "password")}

        {mode === "signup" && (
          <>
            <select value={form.language} onChange={e => set("language", e.target.value)} style={{ width: "100%", padding: "13px 16px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", color: "#EEF2FF", fontSize: "14px", fontFamily: "'IBM Plex Mono', monospace", outline: "none", marginBottom: "10px", cursor: "pointer" }}>
              {LANGUAGES.map(l => <option key={l} value={l} style={{ background: "#020B18" }}>{l}</option>)}
            </select>
            <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
              {["beginner", "experienced"].map(r => (
                <button key={r} onClick={() => set("risk_appetite", r)} style={{ flex: 1, padding: "10px", borderRadius: "10px", cursor: "pointer", background: form.risk_appetite === r ? "rgba(0,229,190,0.12)" : "rgba(255,255,255,0.04)", color: form.risk_appetite === r ? "#00E5BE" : "rgba(255,255,255,0.4)", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", border: `1px solid ${form.risk_appetite === r ? "rgba(0,229,190,0.3)" : "rgba(255,255,255,0.08)"}`, transition: "all 0.2s", textTransform: "capitalize" }}>{r}</button>
              ))}
            </div>
          </>
        )}

        {error && <div style={{ color: "#FF6B6B", fontSize: "12px", marginBottom: "10px", textAlign: "center", padding: "8px", background: "rgba(255,107,107,0.08)", borderRadius: "8px" }}>{error}</div>}

        <button onClick={handleSubmit} disabled={loading} style={{ width: "100%", padding: "14px", borderRadius: "14px", border: "none", background: "linear-gradient(135deg, #00E5BE, #0066FF)", color: "#020B18", fontSize: "15px", fontWeight: "700", fontFamily: "'Sora', sans-serif", cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1, marginBottom: "10px", transition: "opacity 0.2s, transform 0.1s" }}
          onMouseDown={e => !loading && (e.currentTarget.style.transform = "scale(0.98)")}
          onMouseUp={e => e.currentTarget.style.transform = "scale(1)"}
        >{loading ? "Please wait..." : mode === "signup" ? "Create Account" : "Sign In"}</button>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", margin: "14px 0" }}>
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.07)" }} />
          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.07)" }} />
        </div>

        <button onClick={connectWallet} disabled={loading} style={{ width: "100%", padding: "13px", borderRadius: "14px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", color: "#EEF2FF", fontSize: "14px", fontWeight: "600", fontFamily: "'IBM Plex Mono', monospace", cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", transition: "all 0.2s" }}
          onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(0,229,190,0.3)"}
          onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"}
        ><span style={{ fontSize: "18px" }}>🦊</span> Connect MetaMask</button>
      </div>
    </div>
  );
}

// ── Chat Screen ───────────────────────────────────────────────
function ChatScreen({ user, onSignOut }) {
  const profile = user.profile || {};
  const name = profile.username || "there";
  const [messages, setMessages] = useState([{ role: "assistant", content: `Hey ${name}! I'm MARC — your onchain finance companion on Arc. What's on your mind?`, time: timeStr() }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const sendMessage = async (text) => {
    const content = (text || input).trim();
    if (!content || loading) return;
    setShowSuggestions(false);
    setSidebarOpen(false);
    const userMsg = { role: "user", content, time: timeStr() };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: content, user_id: user.user_id }) });
      const data = await res.json();
      setMessages([...updated, { role: "assistant", content: data.reply, time: timeStr() }]);
    } catch {
      setMessages([...updated, { role: "assistant", content: "Something went wrong — make sure the backend is running!", time: timeStr() }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKey = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  const clearChat = async () => {
    if (user.user_id) await fetch(`${API_URL}/chat/history/${user.user_id}`, { method: "DELETE" });
    setMessages([{ role: "assistant", content: `Fresh start! What do you want to talk about, ${name}?`, time: timeStr() }]);
    setShowSuggestions(true);
    setSidebarOpen(false);
  };

  const SidebarContent = () => (
    <>
      {/* Brand */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <MarcAvatar size={38} />
          <div>
            <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: "800", fontSize: "20px", color: "#F0F6FF", letterSpacing: "0.04em" }}>MARC</div>
            <div style={{ fontSize: "9px", color: "rgba(0,229,190,0.5)", letterSpacing: "0.14em" }}>MONEY ON ARC</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#00E5BE", animation: "pulse 2s infinite" }} />
          <span style={{ fontSize: "10px", color: "rgba(0,229,190,0.8)", fontWeight: "600" }}>Online</span>
        </div>
      </div>

      {/* User card */}
      <div style={{ background: "linear-gradient(135deg, rgba(0,229,190,0.06), rgba(0,102,255,0.06))", border: "1px solid rgba(0,229,190,0.12)", borderRadius: "12px", padding: "12px", marginBottom: "16px" }}>
        <div style={{ fontSize: "9px", color: "rgba(0,229,190,0.5)", letterSpacing: "0.12em", marginBottom: "6px" }}>LOGGED IN AS</div>
        <div style={{ fontSize: "14px", color: "#F0F6FF", fontWeight: "700", marginBottom: "3px" }}>{name}</div>
        <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.35)" }}>{profile.risk_appetite === "beginner" ? "🌱 Beginner" : "⚡ Experienced"} · {profile.language || "English"}</div>
        {profile.wallet_address && <div style={{ fontSize: "10px", color: "rgba(0,229,190,0.5)", marginTop: "5px", wordBreak: "break-all" }}>{profile.wallet_address.slice(0, 6)}...{profile.wallet_address.slice(-4)}</div>}
      </div>

      {/* Network */}
      <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "12px", marginBottom: "16px" }}>
        <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.3)", letterSpacing: "0.12em", marginBottom: "6px" }}>NETWORK</div>
        <div style={{ fontSize: "13px", color: "#00E5BE", fontWeight: "700", marginBottom: "4px" }}>Arc Testnet</div>
        <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)", lineHeight: "1.7" }}>Chain ID: 5042002<br />Gas: USDC</div>
      </div>

      {/* Quick prompts */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.25)", letterSpacing: "0.12em", marginBottom: "8px" }}>TRY ASKING</div>
        {SUGGESTIONS.map(s => (
          <button key={s} onClick={() => sendMessage(s)} style={{ display: "block", width: "100%", textAlign: "left", background: "transparent", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "8px", padding: "7px 10px", color: "rgba(255,255,255,0.4)", fontSize: "11px", cursor: "pointer", marginBottom: "5px", fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.2s" }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,229,190,0.05)"; e.currentTarget.style.color = "#00E5BE"; e.currentTarget.style.borderColor = "rgba(0,229,190,0.2)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.4)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.05)"; }}
          >{s}</button>
        ))}
      </div>

      {/* Footer */}
      <div style={{ paddingTop: "14px", borderTop: "1px solid rgba(255,255,255,0.04)", display: "flex", flexDirection: "column", gap: "2px" }}>
        {[["🚰 Get Testnet USDC", "https://faucet.circle.com"], ["🔍 Explorer", "https://testnet.arcscan.app"], ["📄 Arc Docs", "https://docs.arc.io"]].map(([label, url]) => (
          <a key={url} href={url} target="_blank" rel="noreferrer" style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)", textDecoration: "none", padding: "4px 0", transition: "color 0.2s" }}
            onMouseEnter={e => e.target.style.color = "#00E5BE"} onMouseLeave={e => e.target.style.color = "rgba(255,255,255,0.3)"}>{label}</a>
        ))}
        <button onClick={clearChat} style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.25)", fontSize: "11px", cursor: "pointer", textAlign: "left", padding: "4px 0", fontFamily: "'IBM Plex Mono', monospace" }}
          onMouseEnter={e => e.target.style.color = "#FF6B6B"} onMouseLeave={e => e.target.style.color = "rgba(255,255,255,0.25)"}>🗑 Clear chat</button>
        <button onClick={onSignOut} style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.25)", fontSize: "11px", cursor: "pointer", textAlign: "left", padding: "4px 0", fontFamily: "'IBM Plex Mono', monospace" }}
          onMouseEnter={e => e.target.style.color = "#FF6B6B"} onMouseLeave={e => e.target.style.color = "rgba(255,255,255,0.25)"}> Sign out</button>
      </div>
    </>
  );

  return (
    <div style={{ display: "flex", height: "100vh", height: "100dvh", background: "#020B18", overflow: "hidden", position: "relative" }}>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div onClick={() => setSidebarOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40, display: "none" }} className="mobile-overlay" />
      )}

      {/* Sidebar — desktop always visible, mobile drawer */}
      <div style={{
        width: "240px", flexShrink: 0,
        background: "rgba(255,255,255,0.02)",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        display: "flex", flexDirection: "column",
        padding: "20px 14px",
        transition: "transform 0.3s ease",
        zIndex: 50,
      }} className="sidebar">
        <SidebarContent />
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden" }}>

        {/* Header */}
        <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(255,255,255,0.04)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(255,255,255,0.01)", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {/* Hamburger for mobile */}
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="hamburger" style={{ display: "none", background: "transparent", border: "none", cursor: "pointer", padding: "4px", flexDirection: "column", gap: "4px" }}>
              {[0,1,2].map(i => <div key={i} style={{ width: "20px", height: "2px", background: "#00E5BE", borderRadius: "2px" }} />)}
            </button>
            <MarcAvatar size={32} />
            <div>
              <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: "700", fontSize: "15px", color: "#F0F6FF" }}>MARC</div>
              <div style={{ fontSize: "10px", color: "rgba(255,255,255,0.35)" }}>Your onchain finance companion</div>
            </div>
          </div>
          <div style={{ fontSize: "10px", color: "rgba(0,229,190,0.7)", background: "rgba(0,229,190,0.07)", border: "1px solid rgba(0,229,190,0.15)", borderRadius: "20px", padding: "4px 10px", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>⚡ TESTNET</div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px", WebkitOverflowScrolling: "touch" }}>
          <div style={{ maxWidth: "700px", width: "100%", margin: "0 auto" }}>
            {messages.map((msg, i) => <MessageBubble key={i} msg={msg} isLatest={i === messages.length - 1} />)}
            {loading && (
              <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", marginBottom: "16px", animation: "fadeUp 0.3s ease" }}>
                <MarcAvatar size={28} />
                <div style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "18px 18px 18px 4px" }}><TypingIndicator /></div>
              </div>
            )}
            {showSuggestions && messages.length === 1 && (
              <div style={{ marginTop: "8px", display: "flex", flexWrap: "wrap", gap: "6px", animation: "fadeUp 0.4s ease 0.2s both" }}>
                {["What can you do?", "Check my balance", "What is Arc?"].map(s => (
                  <button key={s} onClick={() => sendMessage(s)} style={{ background: "rgba(0,229,190,0.06)", border: "1px solid rgba(0,229,190,0.2)", borderRadius: "20px", padding: "7px 14px", color: "#00E5BE", fontSize: "12px", cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.2s", whiteSpace: "nowrap" }}
                    onMouseEnter={e => e.currentTarget.style.background = "rgba(0,229,190,0.12)"}
                    onMouseLeave={e => e.currentTarget.style.background = "rgba(0,229,190,0.06)"}>{s}</button>
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{ padding: "12px 16px 16px", background: "rgba(255,255,255,0.01)", borderTop: "1px solid rgba(255,255,255,0.04)", flexShrink: 0 }}>
          <div style={{ maxWidth: "700px", margin: "0 auto" }}>
            <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", background: "rgba(255,255,255,0.04)", border: `1px solid ${input ? "rgba(0,229,190,0.25)" : "rgba(255,255,255,0.08)"}`, borderRadius: "16px", padding: "10px 12px", transition: "border-color 0.2s" }}>
              <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                placeholder="Talk to MARC..." rows={1}
                style={{ flex: 1, background: "transparent", border: "none", color: "#EEF2FF", fontSize: "14px", fontFamily: "'IBM Plex Mono', monospace", lineHeight: "1.5", maxHeight: "100px", overflowY: "auto", resize: "none" }}
                onInput={e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 100) + "px"; }}
              />
              <button onClick={() => sendMessage()} disabled={loading || !input.trim()} style={{ width: "34px", height: "34px", borderRadius: "10px", flexShrink: 0, background: loading || !input.trim() ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, #00E5BE, #0066FF)", border: "none", cursor: loading || !input.trim() ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke={loading || !input.trim() ? "rgba(255,255,255,0.2)" : "#020B18"} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            </div>
            <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.12)", textAlign: "center", marginTop: "6px" }}>Enter to send · Shift+Enter for new line</p>
          </div>
        </div>
      </div>

      {/* Mobile sidebar drawer */}
      {sidebarOpen && (
        <>
          <div onClick={() => setSidebarOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40 }} />
          <div style={{ position: "fixed", left: 0, top: 0, bottom: 0, width: "260px", background: "#0A1628", borderRight: "1px solid rgba(255,255,255,0.08)", display: "flex", flexDirection: "column", padding: "20px 14px", zIndex: 50, animation: "slideInLeft 0.25s ease" }}>
            <button onClick={() => setSidebarOpen(false)} style={{ alignSelf: "flex-end", background: "transparent", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "18px", marginBottom: "12px" }}>✕</button>
            <SidebarContent />
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() => load("marc_user"));
  const handleAuth = (data) => { store("marc_user", data); setUser(data); };
  const handleSignOut = () => { localStorage.removeItem("marc_user"); setUser(null); };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Sora:wght@400;600;700;800&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { -webkit-text-size-adjust: 100%; }
        body { background: #020B18; font-family: 'IBM Plex Mono', monospace; overflow: hidden; }
        @keyframes bounce { 0%,80%,100%{transform:translateY(0);opacity:.5} 40%{transform:translateY(-6px);opacity:1} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
        @keyframes slideInLeft { from{transform:translateX(-100%)} to{transform:translateX(0)} }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: rgba(0,229,190,.15); border-radius: 4px; }
        textarea { resize: none; }
        textarea:focus, input:focus { outline: none; }
        textarea::placeholder, input::placeholder { color: rgba(255,255,255,.25); }
        select { outline: none; }
        button { -webkit-tap-highlight-color: transparent; }

        /* Mobile styles */
        @media (max-width: 640px) {
          .sidebar { display: none !important; }
          .hamburger { display: flex !important; }
        }

        /* Tablet styles */
        @media (min-width: 641px) and (max-width: 900px) {
          .sidebar { width: 200px !important; padding: 16px 12px !important; }
        }
      `}</style>
      {user ? <ChatScreen user={user} onSignOut={handleSignOut} /> : <AuthScreen onAuth={handleAuth} />}
    </>
  );
}