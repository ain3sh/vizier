import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css'
import App from './App.tsx';
import OnBoarding from './pages/onboarding/onboarding.tsx';
import Login from './pages/login/login.tsx'
import AuthCallback from './pages/login/AuthCallback.tsx';
import AgentFlowGraph from './pages/graph/graphpage.tsx';

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/login/success" element={<AuthCallback />} />
                <Route path="/*" element={<App />} />
                <Route path="/graph" element={<AgentFlowGraph />} />
                {/* <Route path="/" element={<OnBoarding/>}/> */}
            </Routes>
        </BrowserRouter>
    </StrictMode>,
)
