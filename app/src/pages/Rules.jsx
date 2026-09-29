import '../styles/pages.css';

const rulesStyles = `
  .rules-content {
    max-width: 900px;
    margin: 0 auto;
    text-align: left;
    line-height: 1.8;
  }

  .rules-content h2 {
    text-align: center;
    margin-top: 0;
    margin-bottom: 10px;
  }

  .rules-content .subtitle-text {
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
    margin-bottom: 30px;
  }

  .rules-content h3 {
    margin-top: 35px;
    margin-bottom: 15px;
    color: var(--text-primary);
    border-bottom: 2px solid var(--accent);
    padding-bottom: 8px;
  }

  .rules-content h4 {
    margin-top: 20px;
    margin-bottom: 12px;
    color: var(--text-primary);
  }

  .rules-content p {
    margin-bottom: 15px;
    color: var(--text-primary);
  }

  .rules-content ul, .rules-content ol {
    margin-left: 20px;
    margin-bottom: 15px;
  }

  .rules-content li {
    margin-bottom: 8px;
    color: var(--text-primary);
  }

  .rules-content a {
    color: var(--accent);
    text-decoration: none;
  }

  .rules-content a:hover {
    text-decoration: underline;
  }
`;

export default function Rules() {
  return (
    <>
      <style>{rulesStyles}</style>
      <header>
        <div className="container">
          <h1>🧙‍♂️ Colorado Pauper</h1>
          <p className="subtitle">Tournament rules and format</p>
        </div>
      </header>

      <div className="container">
        <div className="rules-content">
          <h2>Colorado Pauper League – Season 1</h2>
          <div className="subtitle-text">Adapted from the Summer Brew Challenge (thanks Rob!)</div>

          <h3>Goals</h3>
          <ol>
            <li>Give players a reason to show up to weeklies across Colorado and play consistently.</li>
            <li>Deepen engagement for existing community members and give new players an easy way to get involved.</li>
            <li>Boost numbers for smaller events.</li>
          </ol>

          <h3>What is it?</h3>
          <p>
            The Colorado Pauper League is a two-phase season. Play any Pauper deck at weekly events at any Colorado LGS from October 5 through November 29. Your scores will be collated, and the top 8 (depending on player count and interest this could be top 12 or top 16) players meet in a championship event after the season closes.
          </p>
          <p>
            This first league is shorter and considered a Proof of Concept to make sure that this is a feasible event that people are interested in continuing. There likely will be pitfalls and things that organizers had not considered. All constructive and well thought out feedback is welcome, the objective is to make this continually better and to have a system that feels authentic to the people playing in it.
          </p>
          <p>
            All results are tracked on <a href="http://colorado-pauper.org" target="_blank" rel="noopener noreferrer">colorado-pauper.org</a>
          </p>

          <h3>How Do I Join?</h3>
          <p>
            Mostly by existing and going to pauper events! As long as someone is making sure that the event that you are going to is consistently being sent to Arash then you're automatically enrolled.
          </p>
          <p>
            If you do not want to participate, let Arash know and he will opt you out of the tracking! This is also covered in the FAQ.
          </p>

          <h3>Season Timeline</h3>
          <ul>
            <li>Season 1 run window: October 5 – November 29, 2026</li>
            <li>Final standings / Top 8 announced: December 4, 2026</li>
            <li>Championship: December 2026, date TBD, at Mythic</li>
          </ul>

          <h3>Phase 1: Season Play</h3>
          <p>From October 5 through November 29, play in Pauper events at any LGS in Colorado.</p>

          <ul>
            <li><strong>What counts as an eligible event:</strong> any Pauper event at a Colorado LGS with at least 3 rounds of Swiss. There is no minimum player count.</li>
            <li><strong>Proof of result:</strong> Send a screenshot from the Companion app showing the event and everyone's final records. Results without a Companion screenshot will not be counted.</li>
            <li><strong>Counting:</strong> At the end of the league, your worst result will be dropped. Only one event per week (Monday–Sunday) counts; if you play more than one in a week, your best result that week is used.</li>
            <li><strong>Scoring (Swiss rounds only, no top-cut matches):</strong>
              <ul>
                <li>Win = 3 points</li>
                <li>Draw = 1 point</li>
                <li>Loss = 0 points</li>
              </ul>
            </li>
          </ul>

          <h4>Tiebreakers for Final Standings</h4>
          <ol>
            <li>Total season points</li>
            <li>OMW%</li>
            <li>Total events played</li>
            <li>total number of 3-0s, then 2-0-1s, and so forth until the tie is broken.</li>
          </ol>

          <h4>Logistics</h4>
          <ul>
            <li>Standings are tracked on colorado-pauper.org and visible to the whole community.</li>
            <li>Send your Companion screenshot to Arash after each event. Please submit within 7 days of playing so standings stay current.</li>
            <li>You are not locked into a deck during the season. Play different decks, make radical changes, whatever you like.</li>
          </ul>

          <h4>Rewards</h4>
          <ul>
            <li>Top 16 – Stamped Basic of your choice</li>
            <li>Top 8 - Stamped Card of your choice</li>
            <li>Top 4 - Dice Box</li>
            <li>Winner - Eternal Glory, Deck Box, and a Trophy</li>
          </ul>

          <h3>Phase 2: Championship</h3>
          <ul>
            <li><strong>When:</strong> December 2026, date TBD</li>
            <li><strong>Where:</strong> TBD</li>
            <li><strong>Eligibility:</strong> Top 8 (potentially top 12 or 16) players in the final season standings. If a qualifier cannot attend, the invitation passes to the next player in the standings.</li>
            <li><strong>Decklists:</strong> any legal Pauper deck. Submit your decklist to Arash before the event starts.</li>
            <li><strong>Format:</strong> single-elimination bracket seeded by season standings (1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5). Matches are best-of-three and untimed. The higher seed chooses to play or draw.</li>
          </ul>

          <h3>What Is Necessary in a Screenshot</h3>
          <p>
            In order to get an accurate assessment of all players, Arash needs a screenshot, or shots, of all players at the events. That means that if there are more players than fits one phone screenshot, please take multiple. If a person's name shows up multiple times, that's fine the parser accounts for that (as does Arash's eyes when he reviews the spreadsheet).
          </p>

          <h3>FAQ</h3>

          <h4>1. My LGS only fires with 4 players, what should I do?</h4>
          <p>
            That's totally fine! There is an option for round robin in Companion app, simply ask your LGS to choose this option so that 3 games are played.
          </p>

          <h4>2. My LGS has a four round pauper event every week, how does that work?</h4>
          <p>
            All events that are tracked will be done with 3 games as cap, so that there isn't an unfair advantage to four round events. However, playing in a four round event will mean that your worst result will be dropped. So for example if you go 2-1-1 your result for the week would be 2-0-1, similarly a 3-0-1 would be a 3-0 and so forth.
          </p>

          <h4>3. What happens if I forget to submit a companion app screenshot?</h4>
          <p>
            Unfortunately if you or someone else at the event does not submit a companion app, either in the Colorado Pauper discord or to Arash directly then the event will not be counted. Best would be for either the person who runs the event to send a weekly screenshot or to have a dedicated tracker.
          </p>

          <h4>4. I do not want my results to be tracked, what should I do?</h4>
          <p>
            That's totally fine! Competitive play and the like is not for everyone, and under no circumstances would we want to disincentivize people from actively going out and playing pauper.
          </p>
          <p>
            If you do not want to participate in tracking or in the league we understand, Arash maintains an opt out list that automatically takes out names when he parses companion app results. Let him know, either in the discord or privately, that you are not interested and your results will not show up in the online tracker. If at anytime you change your mind that's obviously also fine and we can put you back in, though your previous results will be likely lost.
          </p>
        </div>
      </div>
    </>
  );
}
