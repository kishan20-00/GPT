import { useState } from "react";
import "./App.css";
import { useNavigate } from "react-router-dom";

function App() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleMagicLink = async () => {
    if (!email) return;

    try {
      const res = await fetch("http://localhost:8000/request-magic-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();
      if (data.message) {
        setMsg("✅ Magic link has been sent to your email!");
      } else {
        setMsg("❌ Failed to send magic link.");
      }
    } catch (err) {
      setMsg("❌ Error connecting to backend.");
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:8000/login";
  };

  return (
    <div className="container">
      <div className="left-pane">
        <h1 className="logo">Unsungfields <span className="highlight">AI</span></h1>
        <p className="tagline">Powering Imagination ⚡ Elegantly</p>
      </div>

      <div className="right-pane">
        <div className="login-card">
          <h2>Create account or login</h2>
          <input
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button className="email-btn" onClick={handleMagicLink}>
            Login with Email
          </button>

          {msg && <p style={{ marginTop: "1rem", color: msg.includes("✅") ? "green" : "red" }}>{msg}</p>}

          <div className="divider">OR CONTINUE WITH</div>
          <button className="oauth github">Login with GitHub</button>
          <button className="oauth google" onClick={handleGoogleLogin}>
            Login with Google
          </button>

          <p className="terms">
            By continuing, I accept the <a href="#">Terms of Sale</a> and acknowledge that I have read the <a href="#">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
