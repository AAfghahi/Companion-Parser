// A player can have several entries for the same week (e.g. they played at
// more than one store). Keep only their best one: most points, then OMW%.
export const keepBestScores = (entries) => {
  const best = new Map();
  for (const entry of entries) {
    const key = `${String(entry.name).trim().toLowerCase()}|${entry.week}`;
    const current = best.get(key);
    if (!current ||
        entry.points > current.points ||
        (entry.points === current.points &&
          (parseFloat(entry.omwPercent) || 0) > (parseFloat(current.omwPercent) || 0))) {
      best.set(key, entry);
    }
  }
  return [...best.values()];
};
