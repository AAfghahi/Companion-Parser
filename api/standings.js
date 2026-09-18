const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwjPEX1hKkJfgfbgUSvWJ7DuMmQrOhlDMknhrkwSvId3QGp2JCeR3i9ligKTZCGJWnojQ/exec';

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Build the URL with query parameters
    const params = new URLSearchParams();

    if (req.query.listSeasons) {
      params.append('listSeasons', 'true');
    }

    if (req.query.season) {
      params.append('season', req.query.season);
    }

    const url = `${GOOGLE_SCRIPT_URL}?${params.toString()}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      return res.status(response.status).json({
        error: `Google Apps Script returned ${response.status}`
      });
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      error: error.message || 'Failed to fetch standings data'
    });
  }
}
