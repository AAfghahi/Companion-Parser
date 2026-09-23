import { useEffect, useState, useMemo } from 'react';
import { useStandings } from '../context/StandingsContext';
import '../styles/pages.css';

const ITEMS_PER_PAGE = 10;

const formatWeekDate = (dateStr) => {
  if (!dateStr) return dateStr;
  const str = String(dateStr);
  if (str.includes('T')) {
    const date = new Date(str);
    return (date.getMonth() + 1) + '/' + date.getDate() + '/' + String(date.getFullYear()).slice(-2);
  }
  return str;
};

export default function SeasonHistory() {
  const { loadSeasons, loadSeason } = useStandings();
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [seasonData, setSeasonData] = useState([]);
  const [weekFilter, setWeekFilter] = useState('');
  const [searchPlayer, setSearchPlayer] = useState('');
  const [weeklyPage, setWeeklyPage] = useState(1);
  const [leaderboardPage, setLeaderboardPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const weeks = useMemo(() => {
    if (!seasonData.length) return [];
    const uniqueWeeks = [...new Set(seasonData.slice(1).map(s => s.week || s[3]))];
    return uniqueWeeks.sort().reverse();
  }, [seasonData]);

  const allPlayers = useMemo(() => {
    if (!seasonData.length) return [];
    const players = [...new Set(seasonData.slice(1).map(s => s.name || s[0]))];
    return players.sort();
  }, [seasonData]);

  const filteredWeeklyData = useMemo(() => {
    let data = seasonData.slice(1).map(item => ({
      name: item.name || item[0],
      record: item.record || item[1],
      points: item.points || parseInt(item[2]),
      week: item.week || item[3],
      gwPercent: item.gwPercent || item[4],
      omwPercent: item.omwPercent || item[5]
    }));

    if (weekFilter) {
      data = data.filter(s => s.week === weekFilter);
    }

    // Sort by points (desc) → GW% (desc) → OMW% (desc)
    data = data.sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points;
      const bGw = parseFloat(b.gwPercent) || 0;
      const aGw = parseFloat(a.gwPercent) || 0;
      if (bGw !== aGw) return bGw - aGw;
      const bOmw = parseFloat(b.omwPercent) || 0;
      const aOmw = parseFloat(a.omwPercent) || 0;
      return bOmw - aOmw;
    });
    data = data.map((item, idx) => ({
      ...item,
      rank: idx + 1
    }));

    // Apply search filter after ranking (keeps original ranks)
    if (searchPlayer) {
      data = data.filter(s => s.name.toLowerCase().includes(searchPlayer.toLowerCase()));
    }

    return data;
  }, [seasonData, weekFilter, searchPlayer]);

  const paginatedWeekly = useMemo(() => {
    const start = (weeklyPage - 1) * ITEMS_PER_PAGE;
    return filteredWeeklyData.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredWeeklyData, weeklyPage]);

  const leaderboardData = useMemo(() => {
    const playerStats = {};

    seasonData.slice(1).forEach(entry => {
      const name = entry.name || entry[0];
      const points = entry.points || parseInt(entry[2]);
      const gwPercent = entry.gwPercent || entry[4];
      const omwPercent = entry.omwPercent || entry[5];

      if (!playerStats[name]) {
        playerStats[name] = { name, total: 0, count: 0, gwTotal: 0, omwTotal: 0 };
      }
      playerStats[name].total += points;
      playerStats[name].count += 1;
      if (gwPercent) {
        playerStats[name].gwTotal += parseFloat(gwPercent);
      }
      if (omwPercent) {
        playerStats[name].omwTotal += parseFloat(omwPercent);
      }
    });

    const leaderboard = Object.values(playerStats)
      .map(player => ({
        ...player,
        avg: (player.total / player.count).toFixed(1),
        gwPercent: player.gwTotal > 0 ? (player.gwTotal / player.count).toFixed(1) : '-',
        omwPercent: player.omwTotal > 0 ? (player.omwTotal / player.count).toFixed(1) : '-'
      }))
      .sort((a, b) => {
        if (b.total !== a.total) return b.total - a.total;
        const bGw = parseFloat(b.gwPercent) || 0;
        const aGw = parseFloat(a.gwPercent) || 0;
        if (bGw !== aGw) return bGw - aGw;
        const bOmw = parseFloat(b.omwPercent) || 0;
        const aOmw = parseFloat(a.omwPercent) || 0;
        return bOmw - aOmw;
      });

    return leaderboard.map((player, idx) => ({ ...player, rank: idx + 1 }));
  }, [seasonData]);

  const filteredLeaderboard = useMemo(() => {
    if (!searchPlayer) return leaderboardData;
    return leaderboardData.filter(player =>
      player.name.toLowerCase().includes(searchPlayer.toLowerCase())
    );
  }, [leaderboardData, searchPlayer]);

  const paginatedLeaderboard = useMemo(() => {
    const start = (leaderboardPage - 1) * ITEMS_PER_PAGE;
    return filteredLeaderboard.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredLeaderboard, leaderboardPage]);

  useEffect(() => {
    const fetchSeasons = async () => {
      const data = await loadSeasons();
      const filtered = (data || []).filter(s => s !== 'MTG Standings' && s !== 'Main Standings');
      setSeasons(filtered);
      if (filtered && filtered.length > 0) {
        setSelectedSeason(filtered[0]);
      }
    };
    fetchSeasons();
  }, [loadSeasons]);

  useEffect(() => {
    const fetchSeason = async () => {
      if (selectedSeason) {
        setLoading(true);
        const data = await loadSeason(selectedSeason);
        setSeasonData(data || []);
        setWeekFilter('');
        setSearchPlayer('');
        setWeeklyPage(1);
        setLeaderboardPage(1);
        setLoading(false);
      }
    };
    fetchSeason();
  }, [selectedSeason, loadSeason]);

  useEffect(() => {
    if (weeks.length > 0 && !weekFilter) {
      setWeekFilter(weeks[0]);
    }
  }, [weeks]);

  return (
    <>
      <header>
        <div className="container">
          <h1>🧙‍♂️ Colorado Pauper</h1>
          <p className="subtitle">Past season standings</p>
        </div>
      </header>

      <div className="container">
        <div className="filter-section">
          <label htmlFor="seasonSelect">Season:</label>
          <select id="seasonSelect" value={selectedSeason} onChange={(e) => setSelectedSeason(e.target.value)}>
            {seasons.map(season => <option key={season} value={season}>{season}</option>)}
          </select>
        </div>

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading season data...</p>
          </div>
        ) : (
          <>
            <h2>Weekly Scores</h2>
            <div className="filter-section">
              <label htmlFor="weekFilter">Week:</label>
              <select id="weekFilter" value={weekFilter} onChange={(e) => { setWeekFilter(e.target.value); setWeeklyPage(1); }}>
                {weeks.map(week => <option key={week} value={week}>{formatWeekDate(week)}</option>)}
              </select>

              <label htmlFor="searchPlayer">Search Player:</label>
              <input type="text" id="searchPlayer" placeholder="Start typing a player name..." value={searchPlayer} onChange={(e) => { setSearchPlayer(e.target.value); setWeeklyPage(1); }} list="playerNames" autoComplete="off" />
              <datalist id="playerNames">
                {allPlayers.map(player => <option key={player} value={player} />)}
              </datalist>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Player Name</th>
                    <th>Points</th>
                    <th>Record</th>
                    <th>OMW%</th>
                    <th>GW%</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedWeekly.length > 0 ? (
                    paginatedWeekly.map(entry => (
                      <tr key={`${entry.name}-${entry.week}`}>
                        <td>{entry.rank}</td>
                        <td>{entry.name}</td>
                        <td><strong>{entry.points}</strong></td>
                        <td>{entry.record || '-'}</td>
                        <td>{entry.omwPercent || '-'}</td>
                        <td>{entry.gwPercent || '-'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {filteredWeeklyData.length > ITEMS_PER_PAGE && (
              <div className="pagination-controls">
                <button onClick={() => setWeeklyPage(1)} disabled={weeklyPage === 1}>
                  ⬅ First
                </button>
                <button onClick={() => setWeeklyPage(p => p - 1)} disabled={weeklyPage === 1}>
                  ← Previous
                </button>
                <span id="pageInfo">
                  Page {weeklyPage} of {Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE)}
                </span>
                <button onClick={() => setWeeklyPage(p => p + 1)} disabled={weeklyPage >= Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE)}>
                  Next →
                </button>
                <button onClick={() => setWeeklyPage(Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE))} disabled={weeklyPage >= Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE)}>
                  Last ➡
                </button>
              </div>
            )}

            <h2>Leaderboard</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Total Points</th>
                    <th>Tournaments</th>
                    <th>Avg Points</th>
                    <th>OMW%</th>
                    <th>GW%</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLeaderboard.length > 0 ? (
                    paginatedLeaderboard.map(player => (
                      <tr key={player.name}>
                        <td>{player.rank}</td>
                        <td>{player.name}</td>
                        <td><strong>{player.total}</strong></td>
                        <td>{player.count}</td>
                        <td>{player.avg}</td>
                        <td>{player.omwPercent || '-'}</td>
                        <td>{player.gwPercent || '-'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {filteredLeaderboard.length > ITEMS_PER_PAGE && (
              <div className="pagination-controls">
                <button onClick={() => setLeaderboardPage(1)} disabled={leaderboardPage === 1}>
                  ⬅ First
                </button>
                <button onClick={() => setLeaderboardPage(p => p - 1)} disabled={leaderboardPage === 1}>
                  ← Previous
                </button>
                <span id="leaderboardPageInfo">
                  Page {leaderboardPage} of {Math.ceil(filteredLeaderboard.length / ITEMS_PER_PAGE)}
                </span>
                <button onClick={() => setLeaderboardPage(p => p + 1)} disabled={leaderboardPage >= Math.ceil(filteredLeaderboard.length / ITEMS_PER_PAGE)}>
                  Next →
                </button>
                <button onClick={() => setLeaderboardPage(Math.ceil(filteredLeaderboard.length / ITEMS_PER_PAGE))} disabled={leaderboardPage >= Math.ceil(filteredLeaderboard.length / ITEMS_PER_PAGE)}>
                  Last ➡
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
