import { ReactElement, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { House, Earth, LayoutPanelLeft, LibraryBig, Settings } from 'lucide-react';

import './App.css';
import NavBar from '../components/navigation/navbar';
import Query from './pages/query/query';

function App() {
    const navigate = useNavigate();
    const [timeOfDay, setTimeOfDay] = useState('...');
    const [userName, setUserName] = useState('');
    const [loading, setLoading] = useState(true);

    const handleLogout = () => {
        localStorage.removeItem('jwt');
        navigate('/login');
    };

    useEffect(() => {
        const token = localStorage.getItem('jwt');
        if (!token) {
            console.log("🔐 No JWT found, redirecting to login...");
            navigate('/login');
            return;
        }

        const fetchUserName = async () => {
            try {
                console.log("✅ JWT found, fetching user info...");
                const res = await axios.get('http://localhost:8000/user/me', {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
                setUserName(res.data.name || '');
                console.log("👤 User name:", res.data.name);
                setTimeOfDay(getTimeOfDay());
                setLoading(false);
            } catch (err) {
                console.error("❌ Error fetching user info:", err);
                localStorage.removeItem('jwt');
                navigate('/login');
            }
        };

        fetchUserName();
    }, [navigate]);

    const getTimeOfDay = () => {
        const hour = new Date().getHours();
        if (hour < 12 && hour >= 4) return 'Morning';
        if (hour < 18 && hour >= 12) return 'Afternoon';
        return 'Evening';
    };

    const navItems: [string, ReactElement][] = [
        ['Home', <House />],
        ['Discover', <Earth />],
        ['Spaces', <LayoutPanelLeft />],
        ['Library', <LibraryBig />],
        ['Settings', <Settings />],
    ];

    if (loading) return <div className="loading-screen">🔄 Verifying token...</div>;

    return (
        <div className="vizier-app">
            <div className="top-bar">
                <button className="logout-button" onClick={handleLogout}>Logout</button>
            </div>
            {/* Sidebar Navigation */}
            <NavBar li={navItems} />

            {/* Main Content */}
            <div className="main-content">
                <div className="query-section">
                    <h1 className="center-text">Good {timeOfDay}{userName ? `, ${userName.split(' ')[0]}` : ''}</h1>
                    <Query />
                    <div className="additional-info" />
                    <div className="footer" />
                </div>
            </div>
        </div>
    );
}

export default App;
