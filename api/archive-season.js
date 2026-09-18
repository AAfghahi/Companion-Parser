import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { currentSeasonName, newSeasonName, archiveKey } = req.body;

    // Security: require an archive key (you should set this in env vars)
    if (archiveKey !== process.env.ARCHIVE_KEY) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!currentSeasonName || !newSeasonName) {
      return res.status(400).json({ error: 'Missing season names' });
    }

    // Step 1: Get all current standings data
    const { data: standings, error: standingsError } = await supabase
      .from('standings')
      .select('*');

    if (standingsError) throw standingsError;

    // Step 2: Archive standings to season_data
    if (standings && standings.length > 0) {
      const seasonDataRows = standings.map(row => ({
        season_name: currentSeasonName,
        name: row.name,
        record: row.record,
        points: row.points,
        week: row.week,
        omwPercent: row.omwPercent
      }));

      const { error: insertError } = await supabase
        .from('season_data')
        .insert(seasonDataRows);

      if (insertError) throw insertError;
    }

    // Step 3: Update current season to archived
    const { error: updateSeasonError } = await supabase
      .from('seasons')
      .update({ is_current: false, archived_at: new Date().toISOString() })
      .eq('season_name', currentSeasonName);

    if (updateSeasonError) throw updateSeasonError;

    // Step 4: Create new season
    const { error: newSeasonError } = await supabase
      .from('seasons')
      .insert({
        season_name: newSeasonName,
        is_current: true
      });

    if (newSeasonError) throw newSeasonError;

    // Step 5: Clear standings table
    const { error: deleteError } = await supabase
      .from('standings')
      .delete()
      .neq('id', 0); // Delete all rows

    if (deleteError) throw deleteError;

    return res.status(200).json({
      success: true,
      message: `Season archived successfully. ${standings.length} records moved from standings to season_data.`,
      archivedRecords: standings.length,
      currentSeason: currentSeasonName,
      newSeason: newSeasonName
    });

  } catch (error) {
    console.error('Archive error:', error);
    return res.status(500).json({
      error: 'Failed to archive season',
      details: error.message
    });
  }
}
