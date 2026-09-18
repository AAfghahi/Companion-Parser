import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { StandingsProvider } from './context/StandingsContext';
import { useEffect } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import SeasonHistory from './pages/SeasonHistory';
import Calendar from './pages/Calendar';
import Rules from './pages/Rules';
import './App.css';

function AppRoutes() {
  const navigate = useNavigate();

  useEffect(() => {
    const redirect = sessionStorage.redirect;
    if (redirect) {
      delete sessionStorage.redirect;
      const { pathname } = JSON.parse(redirect);
      navigate(pathname);
    }
  }, [navigate]);

  return (
    <>
      <Navigation />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/seasons" element={<SeasonHistory />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/rules" element={<Rules />} />
      </Routes>
    </>
  );
}

function App() {
  const basename = import.meta.env.BASE_URL;

  return (
    <StandingsProvider>
      <Router basename={basename}>
        <AppRoutes />
      </Router>
    </StandingsProvider>
  );
}

export default App;
