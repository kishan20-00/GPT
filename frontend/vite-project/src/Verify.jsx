import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

function Verify() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const token = params.get("token");

  useEffect(() => {
    const verifyToken = async () => {
      try {
        const res = await fetch(`http://localhost:8000/verify-magic-link?token=${token}`);
        const data = await res.json();

        if (data.email) {
          // ✅ Store dummy profile
          localStorage.setItem("email", data.email);
          localStorage.setItem("name", data.email.split("@")[0]); // just username
          localStorage.setItem("picture", `https://api.dicebear.com/7.x/thumbs/svg?seed=${data.email}`);

          // ✅ Redirect
          navigate("/playground");
        } else {
          setError(data.error || "Invalid token");
        }
      } catch {
        setError("Backend error");
      }
    };

    if (token) verifyToken();
  }, [token, navigate]);

  if (error) return <h2 style={{ color: "red", textAlign: "center" }}>{error}</h2>;

  return <h2 style={{ textAlign: "center" }}>Verifying magic link...</h2>;
}

export default Verify;
