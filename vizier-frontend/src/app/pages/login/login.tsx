// src/pages/login/Login.tsx
import './login.css';

function Login() {
  const GOOGLE_CLIENT_ID = '626032096110-ujnpegq48sk2pfeclevtqdm2umcq779g.apps.googleusercontent.com';
  const REDIRECT_URI = 'http://localhost:8000/auth/callback'; // backend callback

  const googleLoginUrl =
    `https://accounts.google.com/o/oauth2/v2/auth?` +
    `response_type=code&client_id=${GOOGLE_CLIENT_ID}` +
    `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
    `&scope=email%20profile&access_type=offline&prompt=consent`;

    return (
        <div className="login-page">
          <div className="login-card">
            <h1 className="login-title">Welcome to <span className="highlight">Vizier</span></h1>
            <p className="login-subtitle">Your research co-pilot</p>
            <a className="login-btn" href={googleLoginUrl}>
              Sign in with Google
            </a>
          </div>
        </div>
    );
}

export default Login;
