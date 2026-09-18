import '../styles/pages.css';

export default function Rules() {
  return (
    <div className="container">
      <header>
        <h1>🧙‍♂️ Colorado Pauper</h1>
        <p className="subtitle">Tournament rules and format</p>
      </header>

      <h2>Format Rules</h2>
      <div className="stat-card">
        <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
          Pauper Format
        </h3>
        <p>
          Pauper is a Magic: The Gathering format that is restricted to commons.
          Only cards that have been printed at common rarity in Magic's regular sets are legal to play.
        </p>
      </div>

      <div className="stat-card">
        <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
          Deck Construction
        </h3>
        <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
          <li>Minimum 60 cards in main deck</li>
          <li>No maximum deck size</li>
          <li>Sideboard: 15 cards (optional)</li>
          <li>Maximum 4 copies of any card except basic lands</li>
          <li>All cards must be legal at common rarity</li>
        </ul>
      </div>

      <div className="stat-card">
        <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
          Tournament Structure
        </h3>
        <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
          <li>Best of 1 (Swiss format)</li>
          <li>Games are played in English</li>
          <li>Standard Magic tournament rules apply</li>
          <li>Games are timed at 25 minutes</li>
        </ul>
      </div>

      <div className="stat-card">
        <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
          Scoring
        </h3>
        <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
          <li>Win: 3 points</li>
          <li>Draw: 1 point each</li>
          <li>Loss: 0 points</li>
          <li>Tiebreaker: Win percentage, then opponent's win percentage</li>
        </ul>
      </div>

      <div className="stat-card">
        <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
          Banned Cards
        </h3>
        <p>
          Banned cards are determined by Wizards of the Coast's official Pauper banned list.
          Check the official list before each tournament to ensure your deck is legal.
        </p>
      </div>
    </div>
  );
}
