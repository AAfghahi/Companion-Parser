import '../styles/pages.css';

export default function Calendar() {
  const events = [
    {
      name: 'Metro Denver Tuesday Pauper',
      location: 'Denver, CO',
      schedule: 'Every Tuesday at 6:00 PM'
    },
    {
      name: 'Fort Collins Thursday Pauper',
      location: 'Fort Collins, CO',
      schedule: 'Every Thursday at 6:00 PM'
    },
    {
      name: 'Boulder Saturday Pauper',
      location: 'Boulder, CO',
      schedule: 'Every Saturday at 1:00 PM'
    },
    {
      name: 'Springs Wednesday Pauper',
      location: 'Colorado Springs, CO',
      schedule: 'Every Wednesday at 6:00 PM'
    },
    {
      name: 'Western Slope Friday Pauper',
      location: 'Grand Junction, CO',
      schedule: 'Every Friday at 5:00 PM'
    }
  ];

  return (
    <div className="container">
      <header>
        <h1>🧙‍♂️ Colorado Pauper</h1>
        <p className="subtitle">Weekly tournament schedule across Colorado</p>
      </header>

      <h2>Upcoming Events</h2>
      <div className="content">
        {events.map((event, idx) => (
          <div key={idx} className="stat-card">
            <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
              {event.name}
            </h3>
            <p style={{ margin: '5px 0' }}>
              <strong>Location:</strong> {event.location}
            </p>
            <p style={{ margin: '5px 0', color: 'var(--text-secondary)' }}>
              {event.schedule}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
