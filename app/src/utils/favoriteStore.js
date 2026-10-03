// Track how often a player has played at each store, remembering the most
// recent week so ties can be broken in favor of where they played last.
export const addStoreVisit = (stores, store, week) => {
  if (!store) return;
  const time = Date.parse(week) || 0;
  const visit = stores[store] || { count: 0, last: 0 };
  visit.count += 1;
  visit.last = Math.max(visit.last, time);
  stores[store] = visit;
};

// The store with the most visits; ties go to the most recently visited.
export const getFavoriteStore = (stores) => {
  let favorite = null;
  for (const [store, visit] of Object.entries(stores)) {
    if (!favorite ||
        visit.count > stores[favorite].count ||
        (visit.count === stores[favorite].count && visit.last > stores[favorite].last)) {
      favorite = store;
    }
  }
  return favorite;
};
