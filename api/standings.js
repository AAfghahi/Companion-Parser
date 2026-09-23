import { createClient } from '@supabase/supabase-js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const supabaseUrl = process.env.VITE_SUPABASE_URL;
    const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

    console.log('Supabase URL:', supabaseUrl ? 'set' : 'missing');
    console.log('Supabase Key:', supabaseAnonKey ? 'set' : 'missing');

    if (!supabaseUrl || !supabaseAnonKey) {
      return res.status(500).json({
        error: 'Missing Supabase environment variables',
        url: supabaseUrl ? 'set' : 'missing',
        key: supabaseAnonKey ? 'set' : 'missing'
      });
    }

    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    // List archived seasons
    if (req.query.listSeasons) {
      const { data, error } = await supabase
        .from('seasons')
        .select('season_name')
        .eq('is_current', false)
        .order('season_name', { ascending: false });

      if (error) throw error;
      return res.status(200).json(data.map(row => row.season_name));
    }

    // Get specific season data (archived)
    if (req.query.season) {
      const { data, error } = await supabase
        .from('season_data')
        .select('name, record, points, week, omwPercent, gwPercent')
        .eq('season_name', req.query.season)
        .order('week', { ascending: false });

      if (error) throw error;
      return res.status(200).json(data);
    }

    // Get current standings
    const { data, error } = await supabase
      .from('standings')
      .select('name, record, points, week, omwPercent, gwPercent')
      .order('week', { ascending: false });

    if (error) throw error;
    return res.status(200).json(data);

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      error: error.message || 'Failed to fetch data',
      details: error.toString()
    });
  }
}
