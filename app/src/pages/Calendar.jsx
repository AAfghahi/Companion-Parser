import 'temporal-polyfill/global';
import { useEffect, useMemo, useState } from 'react';
import { ScheduleXCalendar, useCalendarApp } from '@schedule-x/react';
import {
  createViewList,
  createViewMonthAgenda,
  createViewMonthGrid,
  createViewWeek
} from '@schedule-x/calendar';
import { createEventRecurrencePlugin } from '@schedule-x/event-recurrence';
import { createEventModalPlugin } from '@schedule-x/event-modal';
import '@schedule-x/theme-default/dist/index.css';
import { useStandings } from '../context/StandingsContext';
import '../styles/pages.css';

const TIMEZONE = 'America/Denver';
// Events don't have a published end time; assume a typical 3-hour event.
const EVENT_HOURS = 3;
// Recurring events are generated starting from the first matching weekday on
// or after this date.
const SERIES_START = '2026-01-01';

// day: ISO weekday (1 = Monday … 7 = Sunday), time: 24h HH:MM
// aliases: other names the store goes by in the standings data
const WEEKLY_EVENTS = [
  { region: 'metro', day: 1, time: '19:00', store: 'Lovo Games', location: 'Parker' },
  { region: 'metro', day: 2, time: '19:00', store: 'Enchanted Grounds', location: 'Highlands Ranch', aliases: ['EG'] },
  { region: 'metro', day: 3, time: '19:00', store: "All C's", location: 'Aurora' },
  { region: 'metro', day: 3, time: '19:00', store: 'MeH Games', location: 'Greenwood Village' },
  { region: 'metro', day: 4, time: '18:30', store: 'Mythic Games', location: 'Littleton' },
  { region: 'metro', day: 7, time: '13:00', store: 'Denver Central Games', location: 'Denver', aliases: ['DCG'] },
  { region: 'state', day: 1, time: '18:30', store: 'Card Cosmos', location: 'Colorado Springs' },
  { region: 'state', day: 3, time: '19:00', store: 'Grandmaster Games', location: 'Boulder', aliases: ['GMG'] },
  { region: 'state', day: 4, time: '18:00', store: 'Mountain Table Top Gaming', location: 'Eagle', aliases: ['MTTG'] },
  { region: 'state', day: 5, time: '18:00', store: 'Foxfire Games', location: 'Fort Collins' }
];

const REGIONS = {
  metro: {
    colorName: 'metro',
    label: 'Metro Denver',
    lightColors: { main: '#6366f1', container: '#e0e7ff', onContainer: '#1e1b4b' },
    darkColors: { main: '#818cf8', container: '#312e81', onContainer: '#e0e7ff' }
  },
  state: {
    colorName: 'state',
    label: 'Around the State',
    lightColors: { main: '#059669', container: '#d1fae5', onContainer: '#064e3b' },
    darkColors: { main: '#34d399', container: '#064e3b', onContainer: '#d1fae5' }
  }
};

const DAY_NAMES = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const RRULE_DAYS = ['', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];

// Compare store names loosely: ignore case, punctuation and a trailing
// "Games"/"Gaming", so "Lovo" matches "Lovo Games".
const storeKey = (name) => String(name || '')
  .toLowerCase()
  .replace(/[^a-z0-9]/g, '')
  .replace(/(games|gaming)$/, '');

const matchesEvent = (storeName, event) => {
  const key = storeKey(storeName);
  if (!key) return false;
  return [event.store, ...(event.aliases || [])].some(name => {
    const eventKey = storeKey(name);
    // Also allow extra detail after the name, e.g. "Enchanted Grounds Highlands Ranch"
    return key === eventKey || (eventKey.length >= 4 && key.startsWith(eventKey));
  });
};

// Average number of players per event at a store, from the current season's
// standings (one event = one store on one week).
const averageEventSize = (standings, event) => {
  const playersByWeek = {};
  standings.forEach(row => {
    if (!row.name || !matchesEvent(row.store, event)) return;
    (playersByWeek[row.week] ||= new Set()).add(row.name);
  });
  const sizes = Object.values(playersByWeek).map(players => players.size);
  if (!sizes.length) return null;
  return { average: Math.round(sizes.reduce((a, b) => a + b, 0) / sizes.length), events: sizes.length };
};

const formatTime = (time) => {
  const [h, m] = time.split(':').map(Number);
  const suffix = h >= 12 ? 'pm' : 'am';
  const hour = h % 12 || 12;
  return m ? `${hour}:${String(m).padStart(2, '0')}${suffix}` : `${hour}${suffix}`;
};

const toCalendarEvent = (event, idx) => {
  const seriesStart = Temporal.PlainDate.from(SERIES_START);
  const firstDate = seriesStart.add({ days: (event.day - seriesStart.dayOfWeek + 7) % 7 });
  const start = firstDate
    .toZonedDateTime({ timeZone: TIMEZONE, plainTime: Temporal.PlainTime.from(event.time) });

  return {
    id: String(idx + 1),
    title: event.store,
    location: `${event.store} (${event.location})`,
    description: `Every ${DAY_NAMES[event.day]} at ${formatTime(event.time)}`,
    calendarId: event.region,
    start,
    end: start.add({ hours: EVENT_HOURS }),
    rrule: `FREQ=WEEKLY;BYDAY=${RRULE_DAYS[event.day]}`
  };
};

const prefersDark = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches;

export default function Calendar() {
  const [isDark, setIsDark] = useState(prefersDark);
  const { standings, loadStandings } = useStandings();

  useEffect(() => {
    loadStandings();
  }, [loadStandings]);

  const eventSizes = useMemo(() => new Map(
    WEEKLY_EVENTS.map(event => [event, averageEventSize(standings, event)])
  ), [standings]);

  const calendarApp = useCalendarApp({
    views: [createViewMonthGrid(), createViewWeek(), createViewList(), createViewMonthAgenda()],
    defaultView: 'month-grid',
    timezone: TIMEZONE,
    firstDayOfWeek: 1,
    isDark,
    calendars: REGIONS,
    dayBoundaries: { start: '10:00', end: '23:00' },
    events: WEEKLY_EVENTS.map(toCalendarEvent),
    plugins: [createEventRecurrencePlugin(), createEventModalPlugin()],
    callbacks: {
      // Decide compact (phone) mode from the window width. Schedule-X's default
      // measures its own element, which can read too narrow on first render
      // and leave desktop stuck in the compact list view.
      isCalendarSmall: () => window.innerWidth < 700
    }
  });

  // Follow the OS light/dark setting, like the rest of the site
  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!media) return;
    const onChange = (e) => setIsDark(e.matches);
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    calendarApp?.setTheme(isDark ? 'dark' : 'light');
  }, [calendarApp, isDark]);

  const byRegion = (region) => WEEKLY_EVENTS
    .filter(e => e.region === region)
    .sort((a, b) => a.day - b.day || a.time.localeCompare(b.time));

  return (
    <>
      <header>
        <div className="container">
          <h1>🧙‍♂️ Colorado Pauper</h1>
          <p className="subtitle">Weekly tournament schedule across Colorado</p>
        </div>
      </header>

      <div className="container calendar-page">
        <div className="calendar-legend">
          {Object.values(REGIONS).map(region => (
            <span key={region.colorName} className="calendar-legend-item">
              <span
                className="calendar-legend-swatch"
                style={{ background: (isDark ? region.darkColors : region.lightColors).main }}
              />
              {region.label}
            </span>
          ))}
        </div>

        <div className="calendar-wrapper">
          <ScheduleXCalendar calendarApp={calendarApp} />
        </div>

        <h2>Weekly Events</h2>
        <div className="content">
          {Object.entries(REGIONS).map(([key, region]) => (
            <div key={key} className="stat-card">
              <h3 style={{ margin: '0 0 10px 0', color: 'var(--text-primary)' }}>
                {region.label}
              </h3>
              {byRegion(key).map(event => (
                <p key={event.store} style={{ margin: '5px 0' }}>
                  <strong>{DAY_NAMES[event.day].slice(0, 3)}, {formatTime(event.time)}</strong>
                  {' '}@ {event.store}{' '}
                  <span style={{ color: 'var(--text-secondary)' }}>({event.location})</span>
                  {eventSizes.get(event) && (
                    <span
                      style={{ color: 'var(--text-secondary)' }}
                      title={`Average over ${eventSizes.get(event).events} event${eventSizes.get(event).events === 1 ? '' : 's'} this season`}
                    >
                      {' '}· avg {eventSizes.get(event).average} players
                    </span>
                  )}
                </p>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
