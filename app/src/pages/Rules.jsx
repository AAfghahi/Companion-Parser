import '../styles/pages.css';

export default function Rules() {
  return (
    <>
      <header>
        <div className="container">
          <h1>🧙‍♂️ Colorado Pauper</h1>
          <p className="subtitle">Tournament rules and format</p>
        </div>
      </header>

      <div className="container">
        <h2>Colorado Pauper League – Season 1</h2>
        <p style={{ fontStyle: 'italic' }}>Adapted from the Summer Brew Challenge (thanks Rob!)</p>

        <h3>Goals</h3>
        <ol>
          <li>Give players a reason to show up to events throughout the season</li>
          <li>Create an inclusive community focused on Pauper and Limited formats</li>
          <li>Determine a true champion based on performance across multiple tournaments</li>
        </ol>

        <h3>What Is It?</h3>
        <p>
          The Colorado Pauper League is a season-long tournament series consisting of two phases. In Phase 1 (Season Play), players earn points throughout the season by participating in sanctioned events. The top players from Phase 1 advance to Phase 2 (Championship) to determine the seasonal champion.
        </p>

        <h3>How Do I Join?</h3>
        <p>
          Automatic! Once you participate in a tracked event, you are automatically enrolled in the season. Your results are captured via the Companion app screenshot tracker. No registration is needed—just show up and play!
        </p>

        <h3>Season Timeline</h3>
        <ul>
          <li><strong>October 5 – November 29, 2026:</strong> Phase 1 Season Play</li>
          <li><strong>December 2026:</strong> Phase 2 Championship (date TBD)</li>
        </ul>

        <h3>Phase 1: Season Play</h3>

        <h4>Eligible Events</h4>
        <p>
          Events must be recognized Pauper or Limited format tournaments organized by local organizers or stores. Standard constructed tournaments, casual games, or unsanctioned events may be included at organizer discretion.
        </p>

        <h4>Scoring System</h4>
        <table style={{ marginTop: '15px', marginBottom: '15px', width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '2px solid var(--text-secondary)' }}>
              <th style={{ padding: '10px', textAlign: 'left' }}>Placement</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>Points</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--bg-secondary)' }}>
              <td style={{ padding: '10px' }}>1st Place</td>
              <td style={{ padding: '10px', textAlign: 'center' }}>9 points</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--bg-secondary)' }}>
              <td style={{ padding: '10px' }}>2nd Place</td>
              <td style={{ padding: '10px', textAlign: 'center' }}>6 points</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--bg-secondary)' }}>
              <td style={{ padding: '10px' }}>3rd Place</td>
              <td style={{ padding: '10px', textAlign: 'center' }}>3 points</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--bg-secondary)' }}>
              <td style={{ padding: '10px' }}>4th Place</td>
              <td style={{ padding: '10px', textAlign: 'center' }}>1 point</td>
            </tr>
            <tr>
              <td style={{ padding: '10px' }}>Participation</td>
              <td style={{ padding: '10px', textAlign: 'center' }}>0 points</td>
            </tr>
          </tbody>
        </table>

        <h4>Tiebreakers</h4>
        <p>
          When players are tied on total points, the following tiebreakers are applied in order:
        </p>
        <ol>
          <li><strong>Opponent Match Win Percentage (OMW%):</strong> The average win percentage of all opponents faced</li>
          <li><strong>Head-to-Head:</strong> If the tied players faced each other, the player with the higher record in that matchup</li>
          <li><strong>Recent Performance:</strong> Points from most recent tournament(s)</li>
        </ol>

        <h4>Logistics</h4>
        <p>
          Players must submit screenshot evidence of their placement and final record for each tournament. Screenshots must clearly show the player's name, final placement, record, and any relevant tiebreaker statistics (OMW%, GW%).
        </p>

        <h4>Rewards</h4>
        <p>
          Top finishers in Phase 1 will receive recognition and seeding advantages for the Phase 2 Championship event.
        </p>

        <h3>Phase 2: Championship</h3>

        <h4>Eligibility</h4>
        <p>
          The top 8 players from Phase 1 (based on total points and tiebreakers) automatically qualify for the Championship. Additional slots may be awarded at organizer discretion.
        </p>

        <h4>Format</h4>
        <p>
          The Championship will be held as a single-elimination tournament. Players are seeded based on their Phase 1 standings. The top seed plays the 8th seed, the 2nd seed plays the 7th seed, and so on. First match to 2 wins advances to the finals.
        </p>

        <h4>Tiebreakers in Championship</h4>
        <p>
          The same tiebreaker order applies: OMW%, then Head-to-Head, then Recent Performance.
        </p>

        <h3>What Is Necessary in a Screenshot</h3>
        <p>
          For your tournament results to count toward the league, your screenshot must clearly show:
        </p>
        <ul>
          <li>Your player name</li>
          <li>Your final placement (1st, 2nd, 3rd, etc.)</li>
          <li>Your match record (W-L or W-L-D format)</li>
          <li>Opponent Match Win Percentage (OMW%) if visible</li>
          <li>The event name and date</li>
        </ul>
        <p>
          The Companion app will help standardize screenshot capture. If quality is questionable, organizers may request clarification.
        </p>

        <h3>FAQ</h3>

        <h4>Q: Can I play in multiple events?</h4>
        <p>
          <strong>A:</strong> Yes! In fact, we encourage it. Your total points are the sum of all your tournament results during the season. The more you play, the better your chances at the championship.
        </p>

        <h4>Q: What if I miss a tournament?</h4>
        <p>
          <strong>A:</strong> No problem. Your points are cumulative, so missing an event only means you don't earn points that event. There are no penalties for not participating in every tournament.
        </p>

        <h4>Q: How are tiebreakers calculated?</h4>
        <p>
          <strong>A:</strong> OMW% is calculated by the tournament organizer and should be visible in standings or scoresheet screenshots. If missing, it will be calculated from available match data. GW% (Game Win %) is used as a reference but OMW% is the primary tiebreaker.
        </p>

        <h4>Q: What happens if there's a dispute about a result?</h4>
        <p>
          <strong>A:</strong> Submit a dispute report with clear screenshot evidence to the league organizers. They will review and make a determination. Results must be reported with proper documentation for league consideration.
        </p>
      </div>
    </>
  );
}
