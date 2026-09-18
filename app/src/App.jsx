import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { StandingsProvider } from './context/StandingsContext';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import SeasonHistory from './pages/SeasonHistory';
import Calendar from './pages/Calendar';
import Rules from './pages/Rules';
import './App.css';

function App() {
  return (
    <StandingsProvider>
      <Router basename="/Companion-Parser">
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/seasons" element={<SeasonHistory />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </Router>
    </StandingsProvider>
  );
}

export default App;
