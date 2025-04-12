import { ReactElement, useState } from 'react';
import { House, Earth, LayoutPanelLeft, LibraryBig, Settings } from 'lucide-react';
import './App.css';
import NavBar from '../components/navigation/navbar';
import Query from './pages/query/query';

function App() {
    const getTimeOfDay = () => {
        const hour = new Date().getHours();
        if (hour < 12 && hour >= 4) {
            return 'Morning';
        } else if (hour < 18 && hour >= 12) {
            return 'Afternoon';
        } else {
        /* hours 19-3 */
            return 'Evening';
        }
    };

    const [timeOfDay] = useState(getTimeOfDay());

    const navItems: [string, ReactElement][] = [
        ['Home', <House/>],
        ['Discover', <Earth/>],
        ['Spaces', <LayoutPanelLeft/>],
        ['Library', <LibraryBig/>],
        ['Settings', <Settings/>],
    ];

    return (
        <div className="vizier-app">
        {/* Sidebar Navigation */}
        <NavBar li={navItems} />
            {/* Main Content */}
            <div className="main-content">
                <div className="query-section">
                    <h1 className="center-text">Good {timeOfDay}</h1>
                        <Query />
                    <div className="additional-info">
                        {/* Additional content can go here */}
                    </div>
                    <div className="footer">
                        {/* Footer content can go here */}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
