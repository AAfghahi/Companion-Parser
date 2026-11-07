// Forwards score discrepancy reports to Discord. The webhook URL lives only in
// the server-side DISCORD_WEBHOOK_URL env var so it is never shipped to browsers.

const MAX_FIELD_LENGTH = 100;

const clean = (value) => String(value ?? '')
  .replace(/[\r\n]+/g, ' ')
  .trim()
  .slice(0, MAX_FIELD_LENGTH);

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
  if (!webhookUrl) {
    return res.status(503).json({ error: 'Reporting is currently unavailable' });
  }

  const { playerName, week, reportedScore, expectedScore } = req.body || {};
  const fields = {
    playerName: clean(playerName),
    week: clean(week),
    reportedScore: clean(reportedScore),
    expectedScore: clean(expectedScore)
  };
  if (Object.values(fields).some(v => !v)) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: `**Score Discrepancy Report**\n` +
                 `Player: ${fields.playerName}\n` +
                 `Week: ${fields.week}\n` +
                 `Reported Score: ${fields.reportedScore}\n` +
                 `Expected Score: ${fields.expectedScore}`,
        // Never let report text ping @everyone, roles or users
        allowed_mentions: { parse: [] }
      })
    });

    if (!response.ok) {
      console.error('Discord webhook error:', response.status);
      return res.status(502).json({ error: 'Failed to send report' });
    }
    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Report error:', error);
    return res.status(502).json({ error: 'Failed to send report' });
  }
}
