import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function AuthCallback() {
  const navigate = useNavigate();
  const processed = useRef(false);  // 🛡️ prevent double-processing

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const query = window.location.search;
    console.log("🔍 query string:", query);
    
    const params = new URLSearchParams(query);
    const token = params.get("token");

    console.log("🧪 extracted token:", token);

    if (token) {
      localStorage.setItem("jwt", token);
      navigate("/"); // ✅ redirect to home
    } else {
      console.error("❌ No token found in URL params.");
      navigate("/login");
    }
  }, [navigate]);

  return <p>Logging in...</p>;
}

export default AuthCallback;
