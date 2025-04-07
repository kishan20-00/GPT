import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Playground() {
  const [userInput, setUserInput] = useState("");
  const [response, setResponse] = useState("");
  const [latency, setLatency] = useState(null);
  const [tokensPerSecond, setTokensPerSecond] = useState(null);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(100);
  const [model, setModel] = useState("tiny-gpt2");
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState("");
  const [rateLimitStatus, setRateLimitStatus] = useState(""); // available / exceeded
  const [rateLimitMessage, setRateLimitMessage] = useState(""); // human-friendly message
  const [tokenCount, setTokenCount] = useState(null); // number of tokens left
  const [waitTime, setWaitTime] = useState(0); // Time to wait if rate limit is exceeded
  const navigate = useNavigate();

  useEffect(() => {
    const savedName = localStorage.getItem("name");
    const savedPic = localStorage.getItem("picture");
    if (!savedName) navigate("/");
    setName(savedName);
    setAvatar(savedPic);
  }, [navigate]);

  // Check rate limit status
  const checkRateLimit = async () => {
    try {
      const res = await fetch("http://localhost:8000/rate-limit-status");
      const data = await res.json();
      setRateLimitStatus(data.status);
      setRateLimitMessage(data.message);
      setTokenCount(data.tokens); // Update token count
      if (data.status === "exceeded") {
        setWaitTime(data.tokens); // Set wait time if rate limit exceeded
        return false; // Block further requests if rate limit is exceeded
      }
      return true; // Allow the request if rate limit is available
    } catch (err) {
      console.error("Failed to check rate limit", err);
      return true; // Allow if the check fails
    }
  };

  const handleSubmit = async () => {
    const allowed = await checkRateLimit(); // Check if the request is allowed
    if (!allowed) return; // If rate limit exceeded, do not allow the request

    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: userInput,
        temperature,
        max_tokens: maxTokens,
      }),
    });

    const data = await res.json();
    setResponse(data.response || "Error");
    setLatency(data.latency);
    setTokensPerSecond(data.tokens_per_second); // Set tokens per second value
    setUserInput(""); // Clear the input field after submit
  };

  return (
    <div
      style={{
        fontFamily: "Arial, sans-serif",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "linear-gradient(to bottom, #c7a6ff, #f6a2f4)",
      }}
    >
      {/* Top Navigation Bar */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "1rem 2rem",
          borderBottom: "1px solid #ddd",
          backgroundColor: "#fff",
        }}
      >
        <h2 style={{ color: "#D000A9", margin: 0 }}>Unsungfields AI</h2>
        <div style={{ display: "flex", gap: "2rem" }}>
          <span style={{ fontWeight: "bold", color: "#ff5722" }}>Playground</span>
          <span onClick={() => navigate("/api-keys")} style={{ cursor: "pointer" }}>
            API Keys
          </span>
          <span>Dashboard</span>
          <span>Documentation</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span>{name}</span>
          <img src={avatar} alt="avatar" style={{ width: 40, height: 40, borderRadius: "50%" }} />
        </div>
      </header>

      {/* Rate Limit Status Bar */}
      {rateLimitStatus && (
        <div
          style={{
            backgroundColor: rateLimitStatus === "exceeded" ? "#ff4d4f" : "#52c41a",
            color: "white",
            padding: "0.75rem 2rem",
            fontWeight: "bold",
            textAlign: "center",
          }}
        >
          {rateLimitMessage}
          {tokenCount !== null && rateLimitStatus !== "exceeded" && (
            <div style={{ marginTop: "0.3rem", fontWeight: "normal" }}>
              🪙 Tokens remaining: <b>{tokenCount}</b>
            </div>
          )}
          {rateLimitStatus === "exceeded" && waitTime > 0 && (
            <div style={{ marginTop: "0.3rem", fontWeight: "normal", color: "#ffeb3b" }}>
              ⏳ Please wait {waitTime} seconds before retrying.
            </div>
          )}
        </div>
      )}

      {/* Controls */}
      <div style={{ display: "flex", padding: "1rem 2rem", alignItems: "center", gap: "1rem" }}>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          style={{ padding: "0.5rem" }}
        >
          <option value="tiny-gpt2">tiny-gpt2</option>
        </select>
        <button>{"</> View code"}</button>
      </div>

      {/* Optional System Prompt */}
      <div style={{ padding: "0.5rem 2rem", borderBottom: "1px solid #eee" }}>
        <input
          placeholder="SYSTEM — Enter system message (Optional)"
          style={{
            width: "100%",
            padding: "0.8rem",
            borderRadius: 8,
            border: "1px solid #ccc",
          }}
        />
      </div>

      {/* Chat Response */}
      <div style={{ flex: 1, padding: "2rem", overflowY: "auto" }}>
        {response && (
          <>
            <h3>🧠 Assistant</h3>
            <p>{response}</p>
            <div style={{ fontSize: "0.9rem", marginTop: "1rem", color: "#555" }}>
              Latency: <b>{latency} ms</b> ⚡ Tokens/s: <b>{tokensPerSecond}</b>
            </div>
          </>
        )}
      </div>

      {/* Input Field */}
      <div
        style={{
          padding: "1rem 2rem",
          display: "flex",
          alignItems: "center",
          borderTop: "1px solid #eee",
        }}
      >
        <input
          type="text"
          placeholder="User Message..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          style={{
            flex: 1,
            padding: "1rem",
            fontSize: "1rem",
            borderRadius: 8,
            border: "1px solid #ccc",
          }}
        />
        <button
          onClick={handleSubmit}
          style={{
            marginLeft: "1rem",
            backgroundColor: "#000",
            color: "#fff",
            padding: "1rem 2rem",
            fontSize: "1rem",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Submit
        </button>
      </div>

      {/* Parameter Panel */}
      <div
        style={{
          position: "fixed",
          top: 120,
          right: 0,
          width: 250,
          padding: "1rem",
          background: "#fff",
          borderLeft: "1px solid #eee",
          height: "calc(100vh - 120px)",
          maxHeight: "400px",
          overflowY: "auto",
        }}
      >
        <label>Temperature</label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={temperature}
          onChange={(e) => setTemperature(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <label style={{ display: "block", marginTop: "1rem" }}>Max Completion Tokens</label>
        <input
          type="number"
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          style={{ width: "100%", padding: "0.5rem" }}
        />
      </div>
    </div>
  );
}

export default Playground;
