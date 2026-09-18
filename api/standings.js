const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwjPEX1hKkJfgfbgUSvWJ7DuMmQrOhlDMknhrkwSvId3QGp2JCeR3i9ligKTZCGJWnojQ/exec';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const params = new URLSearchParams();

    if (req.query.listSeasons) {
      params.append('listSeasons', 'true');
    }

    if (req.query.season) {
      params.append('season', req.query.season);
    }

    const url = `${GOOGLE_SCRIPT_URL}?${params.toString()}`;
    console.log(`Fetching: ${url}`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    console.log(`Status: ${response.status}`);

    if (!response.ok) {
      const text = await response.text();
      console.error(`Error from Google Apps Script: ${text.substring(0, 200)}`);
      return res.status(502).json({
        error: 'Failed to fetch from Google Apps Script',
        status: response.status
      });
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (error) {
    console.error('API Error:', error.message);
    return res.status(502).json({
      error: error.message || 'Failed to fetch data'
    });
  }
}
