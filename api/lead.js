module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { nome, email, whatsapp } = req.body || {};

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.warn('Supabase env vars not set');
    return res.status(200).json({ success: true });
  }

  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/figurinhaai`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({
        Nome: nome || '',
        Email: email || '',
        whatsapp: whatsapp || '',
      }),
    });

    if (!response.ok) {
      console.error('Supabase error:', response.status, await response.text());
    }
  } catch (err) {
    console.error('Lead API error:', err);
  }

  // Sempre retorna 200 — nunca bloqueia o redirecionamento para o pagamento
  return res.status(200).json({ success: true });
};
