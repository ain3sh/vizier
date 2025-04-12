import { useState } from 'react';
import './App.css';

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

  return (
    <div className="perplexity-app">
      {/* Sidebar Navigation */}
      <div className="sidebar">
        <div className="logo">
          <h2>Vizier</h2>
        </div>
        <div className="nav-item">
          <span className="nav-icon">🔍</span>
          <span className="nav-text">Home</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">🌎</span>
          <span className="nav-text">Discover</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">✨</span>
          <span className="nav-text">Spaces</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">📚</span>
          <span className="nav-text">Library</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="query-section">
          <h1 className="center-text">Good {timeOfDay}</h1>
          <div className="search-container">
            <input 
              type="text" 
              className="search-input" 
              placeholder="Ask anything..." 
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
