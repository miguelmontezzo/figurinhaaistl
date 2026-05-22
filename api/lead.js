const getRawBody = (req) =>
  new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => (data += chunk));
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  // Parse body — Vercel às vezes entrega como string, às vezes já parseado
  let body = req.body;
  if (!body || typeof body === 'string') {
    try {
      const raw = typeof body === 'string' ? body : await getRawBody(req);
      body = JSON.parse(raw);
    } catch (e) {
      console.error('[lead] body parse error:', e.message);
      body = {};
    }
  }

  const { nome, email, whatsapp } = body;
  console.log('[lead] recebido:', { nome, email, whatsapp: whatsapp ? '***' : undefined });

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error('[lead] SUPABASE_URL ou SUPABASE_ANON_KEY não configurados no Vercel');
    return res.status(200).json({ success: false, error: 'env_not_set' });
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
      const errorText = await response.text();
      console.error('[lead] Supabase recusou:', response.status, errorText);
      return res.status(200).json({ success: false, supabaseStatus: response.status, detail: errorText });
    }

    console.log('[lead] salvo com sucesso');
    return res.status(200).json({ success: true });
  } catch (err) {
    console.error('[lead] erro de rede:', err.message);
    return res.status(200).json({ success: false, error: err.message });
  }
};
