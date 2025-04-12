import { ReactElement, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { House, Earth, LayoutPanelLeft, LibraryBig, Settings } from 'lucide-react';
import './App.css';
import NavBar from '../components/navigation/navbar';
import Query from './pages/query/query';

function App() {
    const navigate = useNavigate();
    const [timeOfDay, setTimeOfDay] = useState('...');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('jwt');
        if (!token) {
            console.log("🔐 No JWT found, redirecting to login...");
            navigate('/login');
        } else {
            console.log("✅ JWT found, loading app...");
            setLoading(false);
            setTimeOfDay(getTimeOfDay());
        }
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
            {/* Sidebar Navigation */}
            <NavBar li={navItems} />

            {/* Main Content */}
            <div className="main-content">
                <div className="query-section">
                    <h1 className="center-text">Good {timeOfDay}</h1>
                    <Query />
                    <div className="additional-info" />
                    <div className="footer" />
                </div>
            </div>
        </div>
    );
}

export default App;
