import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

function Success() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const name = params.get("name");
    const email = params.get("email");
    const picture = params.get("picture");

    // ✅ Save user info to localStorage
    if (email) {
      localStorage.setItem("name", name);
      localStorage.setItem("email", email);
      localStorage.setItem("picture", picture);

      // ✅ Redirect to Playground
      navigate("/playground");
    }
  }, [params, navigate]);

  return <h2 style={{ textAlign: "center" }}>Logging in with Google...</h2>;
}

export default Success;
