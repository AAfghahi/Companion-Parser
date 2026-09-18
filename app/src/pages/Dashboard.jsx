import { useEffect, useState, useMemo } from 'react';
import { useStandings } from '../context/StandingsContext';
import '../styles/pages.css';

const DISCORD_WEBHOOK = import.meta.env.VITE_DISCORD_WEBHOOK_URL || '';
const ITEMS_PER_PAGE = 10;

export default function Dashboard() {
  const { standings, loading, loadStandings } = useStandings();
  const [weekFilter, setWeekFilter] = useState('');
  const [searchPlayer, setSearchPlayer] = useState('');
  const [weeklyPage, setWeeklyPage] = useState(1);
  const [leaderboardPage, setLeaderboardPage] = useState(1);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportData, setReportData] = useState({
    playerName: '',
    week: '',
    reportedScore: '',
    expectedScore: ''
  });
  const [reportSuccess, setReportSuccess] = useState(false);

  useEffect(() => {
    loadStandings();
  }, [loadStandings]);

  const weeks = useMemo(() => {
    if (!standings.length) return [];
    const uniqueWeeks = [...new Set(standings.map(s => s.week))];
    return uniqueWeeks.sort().reverse();
  }, [standings]);

  const allPlayers = useMemo(() => {
    if (!standings.length) return [];
    const players = [...new Set(standings.map(s => s.name))];
    return players.sort();
  }, [standings]);

  const filteredWeeklyData = useMemo(() => {
    let data = standings;

    if (weekFilter) {
      data = data.filter(s => s.week === weekFilter);
    }

    if (searchPlayer) {
      data = data.filter(s => s.name.toLowerCase().includes(searchPlayer.toLowerCase()));
    }

    // Sort by points descending
    data = data.sort((a, b) => b.points - a.points);

    // Add rank preserving original position
    return data.map((item, idx) => ({
      ...item,
      rank: idx + 1
    }));
  }, [standings, weekFilter, searchPlayer]);

  const paginatedWeekly = useMemo(() => {
    const start = (weeklyPage - 1) * ITEMS_PER_PAGE;
    return filteredWeeklyData.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredWeeklyData, weeklyPage]);

  const leaderboardData = useMemo(() => {
    const playerStats = {};

    standings.forEach(entry => {
      if (!playerStats[entry.name]) {
        playerStats[entry.name] = {
          name: entry.name,
          total: 0,
          count: 0,
          omwPercent: 0
        };
      }
      playerStats[entry.name].total += entry.points;
      playerStats[entry.name].count += 1;
    });

    const leaderboard = Object.values(playerStats)
      .map(player => ({
        ...player,
        avg: (player.total / player.count).toFixed(1)
      }))
      .sort((a, b) => b.total - a.total);

    return leaderboard.map((player, idx) => ({
      ...player,
      rank: idx + 1
    }));
  }, [standings]);

  const paginatedLeaderboard = useMemo(() => {
    const start = (leaderboardPage - 1) * ITEMS_PER_PAGE;
    return leaderboardData.slice(start, start + ITEMS_PER_PAGE);
  }, [leaderboardData, leaderboardPage]);

  const stats = useMemo(() => ({
    totalEntries: standings.length,
    uniquePlayers: allPlayers.length,
    weeksTracked: weeks.length
  }), [standings.length, allPlayers.length, weeks.length]);

  const currentWeek = weeks.length > 0 ? weeks[0] : '';

  useEffect(() => {
    if (currentWeek && !weekFilter) {
      setWeekFilter(currentWeek);
    }
  }, [currentWeek, weekFilter]);

  const handleReportOpen = () => {
    setReportData({
      playerName: '',
      week: currentWeek,
      reportedScore: '',
      expectedScore: ''
    });
    setReportSuccess(false);
    setShowReportModal(true);
  };

  const handleReportClose = () => {
    setShowReportModal(false);
  };

  const handleReportChange = (e) => {
    const { name, value } = e.target;
    setReportData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleReportSubmit = async (e) => {
    e.preventDefault();

    try {
      const message = {
        content: `**Score Discrepancy Report**\n` +
                `Player: ${reportData.playerName}\n` +
                `Week: ${reportData.week}\n` +
                `Reported Score: ${reportData.reportedScore}\n` +
                `Expected Score: ${reportData.expectedScore}`
      };

      await fetch(DISCORD_WEBHOOK, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message)
      });

      setReportSuccess(true);
      setTimeout(() => {
        setShowReportModal(false);
      }, 2000);
    } catch (error) {
      console.error('Error sending report:', error);
      alert('Error sending report. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="container">
        <header>
          <h1>🧙‍♂️ Colorado Pauper</h1>
          <p className="subtitle">Current season standings powered by Google Sheets</p>
        </header>
        <div className="loading">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <h1>🧙‍♂️ Colorado Pauper</h1>
        <p className="subtitle">Current season standings powered by Google Sheets</p>
      </header>

      {/* Weekly Scores Section */}
      <h2>Weekly Scores</h2>
      <div className="filter-section">
        <label htmlFor="weekFilter">Week:</label>
        <select
          id="weekFilter"
          value={weekFilter}
          onChange={(e) => {
            setWeekFilter(e.target.value);
            setWeeklyPage(1);
          }}
        >
          {weeks.map(week => (
            <option key={week} value={week}>{week}</option>
          ))}
        </select>

        <label htmlFor="searchPlayer">Search Player:</label>
        <input
          type="text"
          id="searchPlayer"
          placeholder="Start typing a player name..."
          value={searchPlayer}
          onChange={(e) => {
            setSearchPlayer(e.target.value);
            setWeeklyPage(1);
          }}
          list="playerNames"
          autoComplete="off"
        />
        <datalist id="playerNames">
          {allPlayers.map(player => (
            <option key={player} value={player} />
          ))}
        </datalist>

        <button className="report-button" onClick={handleReportOpen}>
          Report Discrepancy
        </button>
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
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {filteredWeeklyData.length > ITEMS_PER_PAGE && (
        <div className="pagination-controls">
          <button
            onClick={() => setWeeklyPage(p => p - 1)}
            disabled={weeklyPage === 1}
          >
            ← Previous
          </button>
          <span id="pageInfo">
            Page {weeklyPage} of {Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE)}
          </span>
          <button
            onClick={() => setWeeklyPage(p => p + 1)}
            disabled={weeklyPage >= Math.ceil(filteredWeeklyData.length / ITEMS_PER_PAGE)}
          >
            Next →
          </button>
        </div>
      )}

      {/* Leaderboard Section */}
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

      {leaderboardData.length > ITEMS_PER_PAGE && (
        <div className="pagination-controls">
          <button
            onClick={() => setLeaderboardPage(p => p - 1)}
            disabled={leaderboardPage === 1}
          >
            ← Previous
          </button>
          <span id="leaderboardPageInfo">
            Page {leaderboardPage} of {Math.ceil(leaderboardData.length / ITEMS_PER_PAGE)}
          </span>
          <button
            onClick={() => setLeaderboardPage(p => p + 1)}
            disabled={leaderboardPage >= Math.ceil(leaderboardData.length / ITEMS_PER_PAGE)}
          >
            Next →
          </button>
        </div>
      )}

      {/* Statistics Card */}
      <div className="stat-card">
        <div className="stat-label">Data Statistics</div>
        <div style={{ marginTop: '10px' }}>
          <p>Total Entries: <span>{stats.totalEntries}</span></p>
          <p>Unique Players: <span>{stats.uniquePlayers}</span></p>
          <p>Weeks Tracked: <span>{stats.weeksTracked}</span></p>
        </div>
      </div>

      {/* Report Modal */}
      <div className={`modal ${showReportModal ? 'active' : ''}`} onClick={handleReportClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>Report Score Discrepancy</h2>
            <button className="modal-close" onClick={handleReportClose}>×</button>
          </div>

          {reportSuccess && (
            <div className="success-message active">
              Report sent successfully!
            </div>
          )}

          <form onSubmit={handleReportSubmit}>
            <div className="form-group">
              <label htmlFor="playerName">Player Name:</label>
              <select
                id="playerName"
                name="playerName"
                value={reportData.playerName}
                onChange={handleReportChange}
                required
              >
                <option value="">-- Select a player --</option>
                {allPlayers.map(player => (
                  <option key={player} value={player}>{player}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="week">Week:</label>
              <select
                id="week"
                name="week"
                value={reportData.week}
                onChange={handleReportChange}
                required
              >
                <option value="">-- Select a week --</option>
                {weeks.map(week => (
                  <option key={week} value={week}>{week}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="reportedScore">Reported Score:</label>
              <input
                type="number"
                id="reportedScore"
                name="reportedScore"
                value={reportData.reportedScore}
                onChange={handleReportChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="expectedScore">Expected Score:</label>
              <select
                id="expectedScore"
                name="expectedScore"
                value={reportData.expectedScore}
                onChange={handleReportChange}
                required
              >
                <option value="">-- Select a score --</option>
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(score => (
                  <option key={score} value={score}>{score}</option>
                ))}
              </select>
            </div>

            <div className="form-actions">
              <button type="button" className="cancel" onClick={handleReportClose}>
                Cancel
              </button>
              <button type="submit">
                Submit Report
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
