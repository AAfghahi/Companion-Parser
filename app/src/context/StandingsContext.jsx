import React, { createContext, useContext, useState, useCallback } from 'react';

const StandingsContext = createContext();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbyiVH_4CPYMiKyL5CBrvLWk40flxccReKSt6q9ClZcN2xztAn_6IrCn6wIEwjArPgnlZQ/exec';

export function StandingsProvider({ children }) {
  const [standings, setStandings] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getCacheKey = useCallback((key) => {
    return `mtg_cache_${key}`;
  }, []);

  const getCache = useCallback((key) => {
    try {
      const cached = localStorage.getItem(getCacheKey(key));
      if (!cached) return null;
      const { data, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp > CACHE_DURATION) {
        localStorage.removeItem(getCacheKey(key));
        return null;
      }
      return data;
    } catch (e) {
      return null;
    }
  }, [getCacheKey]);

  const setCache = useCallback((key, data) => {
    try {
      localStorage.setItem(getCacheKey(key), JSON.stringify({
        data,
        timestamp: Date.now()
      }));
    } catch (e) {
      console.warn('Failed to cache data:', e);
    }
  }, [getCacheKey]);

  const loadStandings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Try cache first
      const cached = getCache('standings');
      if (cached) {
        console.log('Loading standings from cache');
        setStandings(cached);
        return cached;
      }

      // Fetch from API
      const response = await fetch(SCRIPT_URL);
      const rawData = await response.json();

      // Map raw data to object format
      const data = rawData.map(row => ({
        name: row[0] || '',
        record: row[1] || '',
        points: parseInt(row[2]) || 0,
        week: row[3] || '',
        store: row[4] || '',
        omwPercent: row[5] || ''
      }));

      setCache('standings', data);
      setStandings(data);
      return data;
    } catch (err) {
      console.error('Error loading standings:', err);
      setError(err.message);

      // Try stale cache
      const staleCache = localStorage.getItem(getCacheKey('standings'));
      if (staleCache) {
        try {
          const { data } = JSON.parse(staleCache);
          setStandings(data);
          return data;
        } catch (e) {}
      }
    } finally {
      setLoading(false);
    }
  }, [getCache, setCache, getCacheKey]);

  const loadSeasons = useCallback(async () => {
    try {
      // Try cache first
      const cached = getCache('seasons');
      if (cached) {
        console.log('Loading seasons from cache');
        setSeasons(cached);
        return cached;
      }

      // Fetch from API
      const response = await fetch(SCRIPT_URL + '?listSeasons=true');
      const data = await response.json();

      if (Array.isArray(data) && typeof data[0] === 'string') {
        setCache('seasons', data);
        setSeasons(data);
        return data;
      } else {
        throw new Error('Invalid seasons response');
      }
    } catch (err) {
      console.error('Error loading seasons:', err);

      // Try stale cache
      const staleCache = localStorage.getItem(getCacheKey('seasons'));
      if (staleCache) {
        try {
          const { data } = JSON.parse(staleCache);
          setSeasons(data);
          return data;
        } catch (e) {}
      }
    }
  }, [getCache, setCache, getCacheKey]);

  const loadSeason = useCallback(async (seasonName) => {
    if (!seasonName) return [];

    try {
      // Try cache first
      const cached = getCache(`season_${seasonName}`);
      if (cached) {
        return cached;
      }

      // Fetch from API
      const response = await fetch(SCRIPT_URL + '?season=' + encodeURIComponent(seasonName));
      const rows = await response.json();

      if (rows.success === false) {
        throw new Error('Season not found');
      }

      setCache(`season_${seasonName}`, rows);
      return rows;
    } catch (err) {
      console.error('Error loading season:', err);

      // Try stale cache
      const staleCache = localStorage.getItem(getCacheKey(`season_${seasonName}`));
      if (staleCache) {
        try {
          const { data } = JSON.parse(staleCache);
          return data;
        } catch (e) {}
      }
      return [];
    }
  }, [getCache, setCache, getCacheKey]);

  const value = {
    standings,
    seasons,
    loading,
    error,
    loadStandings,
    loadSeasons,
    loadSeason,
    CACHE_DURATION,
  };

  return (
    <StandingsContext.Provider value={value}>
      {children}
    </StandingsContext.Provider>
  );
}

export function useStandings() {
  const context = useContext(StandingsContext);
  if (!context) {
    throw new Error('useStandings must be used within StandingsProvider');
  }
  return context;
}
