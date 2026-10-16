// Makala Maalum payments — Cloudflare Worker between the website, Pesapal (API 3.0) and the admin dashboard.
//
//   POST /pay           buyer starts a Pesapal payment (server recomputes the price)
//   GET  /ipn           Pesapal payment notification (verified with GetTransactionStatus)
//   GET  /status        thank-you page polls; returns download links once paid
//   GET  /dl/:token     signed, expiring PDF download (files live in KV, never public)
//   GET  /admin/sync    paid orders for the dashboard (Firebase ID token of an admin required)
//   GET  /admin/links   fresh download links for an order (admin)
//
// KV keys (binding STORE):  order:<ref>  ·  pesa:<merchantRef> -> ref  ·  paid:<ref>  ·  pdf:<productId>  ·  cfg:ipn

const LINK_DAYS = 7;
const enc = new TextEncoder();

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const cors = corsHeaders(req, env);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    try {
      let res;
      if (url.pathname === '/pay' && req.method === 'POST') res = await pay(req, env, url);
      else if (url.pathname === '/ipn') res = await ipn(url, env, ctx);
      else if (url.pathname === '/status') res = await status(url, env, ctx);
      else if (url.pathname.startsWith('/dl/')) return await download(url, env);
      else if (url.pathname === '/admin/sync') res = await adminSync(req, env);
      else if (url.pathname === '/admin/links') res = await adminLinks(req, url, env);
      else if (url.pathname === '/') res = json({ ok: true, service: 'makala-payments' });
      else res = json({ error: 'not_found' }, 404);
      for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
      return res;
    } catch (err) {
      console.error(err && err.stack || err);
      return json({ error: 'server_error', message: String(err && err.message || err) }, 500, cors);
    }
  },
};

/* ------------------------------------------------------------------ helpers */
function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', ...headers } });
}
function corsHeaders(req, env) {
  const origin = req.headers.get('Origin') || '';
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim());
  return {
    'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : allowed[0],
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Vary': 'Origin',
  };
}
const clean = (s, n) => String(s ?? '').replace(/[\u0000-\u001f]/g, '').trim().slice(0, n);
const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64urlText = (s) => b64url(enc.encode(s));
const fromB64url = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
const money = (n) => 'TSh ' + Math.round(n).toLocaleString('en-US');

/* Firestore REST (public reads with the web API key). */
function fsValue(x) {
  if (!x) return null;
  if ('stringValue' in x) return x.stringValue;
  if ('integerValue' in x) return Number(x.integerValue);
  if ('doubleValue' in x) return x.doubleValue;
  if ('booleanValue' in x) return x.booleanValue;
  if ('timestampValue' in x) return new Date(x.timestampValue);
  if ('arrayValue' in x) return (x.arrayValue.values || []).map(fsValue);
  if ('mapValue' in x) return fsFields(x.mapValue.fields);
  return null;
}
function fsFields(f = {}) {
  const o = {};
  for (const k of Object.keys(f)) o[k] = fsValue(f[k]);
  return o;
}
async function fsGet(env, path, idToken) {
  const base = `https://firestore.googleapis.com/v1/projects/${env.FIREBASE_PROJECT_ID}/databases/(default)/documents/`;
  const headers = idToken ? { Authorization: 'Bearer ' + idToken } : {};
  const r = await fetch(base + path + (idToken ? '' : (path.includes('?') ? '&' : '?') + 'key=' + env.FIREBASE_API_KEY), { headers });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error('firestore ' + r.status);
  return r.json();
}

/* Catalogue = website defaults + live overrides from the admin dashboard. */
async function catalogue(env) {
  const base = await (await fetch(env.SITE_URL + 'data/products.json', { cf: { cacheTtl: 60 } })).json();
  let live = {};
  try {
    const res = await fsGet(env, 'store_products?pageSize=200');
    for (const d of (res && res.documents) || []) live[d.name.split('/').pop()] = fsFields(d.fields);
  } catch (e) { live = {}; }
  const out = {};
  for (const p of base) {
    const o = live[p.id] || {};
    let price = typeof o.price === 'number' ? o.price : p.price;
    if (typeof o.salePrice === 'number' && o.salePrice >= 0 && o.salePrice < price) price = o.salePrice;
    out[p.id] = { id: p.id, lang: p.lang, title: p.title, price, active: o.active !== false, free: !!p.free, pdf: p.pdf };
  }
  return out;
}

/* ------------------------------------------------------------------ Pesapal */
async function pesapalToken(env) {
  const r = await fetch(env.PESAPAL_BASE + '/api/Auth/RequestToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ consumer_key: env.PESAPAL_CONSUMER_KEY, consumer_secret: env.PESAPAL_CONSUMER_SECRET }),
  });
  const d = await r.json();
  if (!d.token) throw new Error('pesapal auth failed: ' + JSON.stringify(d.error || d));
  return d.token;
}
async function pesapal(env, token, path, body) {
  const r = await fetch(env.PESAPAL_BASE + path, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', Authorization: 'Bearer ' + token },
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json();
}
async function ipnId(env, token, workerOrigin) {
  const ipnUrl = workerOrigin + '/ipn';
  const cached = await env.STORE.get('cfg:ipn', 'json');
  if (cached && cached.url === ipnUrl) return cached.id;
  const d = await pesapal(env, token, '/api/URLSetup/RegisterIPN', { url: ipnUrl, ipn_notification_type: 'GET' });
  if (!d.ipn_id) throw new Error('pesapal IPN registration failed: ' + JSON.stringify(d.error || d));
  await env.STORE.put('cfg:ipn', JSON.stringify({ url: ipnUrl, id: d.ipn_id }));
  return d.ipn_id;
}

/* ------------------------------------------------------------------ POST /pay */
async function pay(req, env, url) {
  const body = await req.json().catch(() => ({}));
  const ref = clean(body.ref, 40);
  if (!/^MM-[0-9]{6}-[A-Z0-9]{4,8}$/.test(ref)) return json({ error: 'bad_ref' }, 400);
  const lang = body.lang === 'en' ? 'en' : 'sw';
  const buyer = { name: clean(body.buyer?.name, 120), phone: clean(body.buyer?.phone, 40), email: clean(body.buyer?.email, 120) };
  if (!buyer.name || !(buyer.phone || buyer.email)) return json({ error: 'buyer_details' }, 400);

  const cat = await catalogue(env);
  const ids = [...new Set((body.items || []).map(String))].filter((id) => cat[id] && cat[id].active && cat[id].lang === lang && cat[id].price > 0);
  if (!ids.length) return json({ error: 'no_items' }, 400);
  const items = ids.map((id) => ({ id, title: cat[id].title, price: cat[id].price }));
  const subtotal = items.reduce((s, i) => s + i.price, 0);

  // Discount code (same rules as the website).
  let discount = 0;
  let couponCode = null;
  const code = clean(body.coupon, 30).toUpperCase().replace(/\s+/g, '');
  if (code) {
    const doc = await fsGet(env, 'store_coupons/' + encodeURIComponent(code)).catch(() => null);
    const c = doc && fsFields(doc.fields);
    const valid = c && c.active !== false && !(c.expiresAt && c.expiresAt < new Date()) && !(c.maxUses && (c.uses || 0) >= c.maxUses);
    if (valid) {
      const eligible = items.filter((i) => !c.products || !c.products.length || c.products.includes(i.id)).reduce((s, i) => s + i.price, 0);
      discount = Math.max(0, Math.min(c.type === 'fixed' ? Number(c.value) || 0 : Math.round(eligible * (Number(c.value) || 0) / 100), eligible));
      if (discount) couponCode = code;
    }
  }
  const amount = subtotal - discount;
  if (amount < 100) return json({ error: 'amount_too_small' }, 400);

  const existing = await env.STORE.get('order:' + ref, 'json');
  if (existing && existing.status === 'paid') return json({ error: 'already_paid' }, 409);
  const attempt = ((existing && existing.attempt) || 0) + 1;
  const merchantRef = `${ref}-P${attempt}`;

  const token = await pesapalToken(env);
  const notification_id = await ipnId(env, token, url.origin);
  const [first, ...rest] = buyer.name.split(/\s+/);
  const thanks = env.SITE_URL + (lang === 'en' ? 'en/store/thank-you/' : 'sw/duka/asante/') + '?ref=' + encodeURIComponent(ref);
  const d = await pesapal(env, token, '/api/Transactions/SubmitOrderRequest', {
    id: merchantRef,
    currency: 'TZS',
    amount,
    description: clean((lang === 'en' ? 'Featured Articles order ' : 'Oda ya Makala Maalum ') + ref, 100),
    callback_url: thanks,
    notification_id,
    billing_address: {
      email_address: buyer.email || undefined,
      phone_number: buyer.phone || undefined,
      country_code: 'TZ',
      first_name: first || buyer.name,
      last_name: rest.join(' ') || undefined,
    },
  });
  if (!d.redirect_url) return json({ error: 'pesapal_rejected', detail: d.error || d }, 502);

  const order = {
    ref, lang, items, subtotal, discount, couponCode, amount, currency: 'TZS', buyer,
    status: 'pending', attempt, merchantRef, trackingId: d.order_tracking_id, createdAt: new Date().toISOString(),
  };
  await env.STORE.put('order:' + ref, JSON.stringify(order));
  await env.STORE.put('pesa:' + merchantRef, ref);
  return json({ redirect_url: d.redirect_url, amount });
}

/* ------------------------------------------------------------------ verification */
async function verify(env, ctx, ref, trackingId) {
  const order = await env.STORE.get('order:' + ref, 'json');
  if (!order) return null;
  if (order.status === 'paid') return order;
  const tid = trackingId || order.trackingId;
  if (!tid) return order;
  const token = await pesapalToken(env);
  const s = await pesapal(env, token, '/api/Transactions/GetTransactionStatus?orderTrackingId=' + encodeURIComponent(tid));
  const merchantRefOk = !s.merchant_reference || (await env.STORE.get('pesa:' + s.merchant_reference)) === ref;
  if (Number(s.status_code) === 1 && merchantRefOk && String(s.currency || 'TZS').toUpperCase() === 'TZS' && Number(s.amount) >= order.amount) {
    order.status = 'paid';
    order.trackingId = tid;
    order.payment = {
      provider: 'pesapal', method: s.payment_method || '', confirmation: s.confirmation_code || '',
      amount: Number(s.amount), account: s.payment_account || '', paidAt: new Date().toISOString(),
    };
    await env.STORE.put('order:' + ref, JSON.stringify(order));
    await env.STORE.put('paid:' + ref, order.payment.paidAt);
    ctx.waitUntil(sendEmails(env, order).catch((e) => console.error('email', e)));
  } else if ([2, 3].includes(Number(s.status_code))) {
    order.lastStatus = s.payment_status_description || 'Failed';
    await env.STORE.put('order:' + ref, JSON.stringify(order));
  }
  return order;
}

async function ipn(url, env, ctx) {
  const tid = url.searchParams.get('OrderTrackingId') || '';
  const merchantRef = url.searchParams.get('OrderMerchantReference') || '';
  const ref = merchantRef ? await env.STORE.get('pesa:' + merchantRef) : null;
  if (ref) await verify(env, ctx, ref, tid);
  return json({ orderNotificationType: url.searchParams.get('OrderNotificationType') || 'IPNCHANGE', orderTrackingId: tid, orderMerchantReference: merchantRef, status: ref ? 200 : 500 });
}

/* ------------------------------------------------------------------ GET /status */
async function status(url, env, ctx) {
  const ref = clean(url.searchParams.get('ref'), 40);
  const tid = clean(url.searchParams.get('OrderTrackingId'), 80);
  const order = await env.STORE.get('order:' + ref, 'json');
  // The tracking id (only known to the payer, from Pesapal's redirect) proves this is the buyer.
  if (!order || !tid || tid !== order.trackingId) return json({ status: 'unknown' }, 404);
  const o = await verify(env, ctx, ref, tid);
  if (o.status !== 'paid') return json({ status: 'pending', message: o.lastStatus || '' });
  return json({ status: 'paid', ref, amount: o.amount, email: o.buyer.email ? o.buyer.email.replace(/^(.).*(@.*)$/, '$1•••$2') : '', downloads: await links(env, o, url.origin) });
}

/* ------------------------------------------------------------------ signed downloads */
async function hmac(env, data) {
  const key = await crypto.subtle.importKey('raw', enc.encode(env.LINK_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return b64url(await crypto.subtle.sign('HMAC', key, enc.encode(data)));
}
async function links(env, order, origin) {
  const exp = Math.floor(Date.now() / 1000) + LINK_DAYS * 86400;
  const out = [];
  for (const it of order.items) {
    const payload = b64urlText(`${order.ref}|${it.id}|${exp}`);
    out.push({ id: it.id, title: it.title, url: `${origin}/dl/${payload}.${await hmac(env, payload)}` });
  }
  return out;
}
async function download(url, env) {
  const [payload, sig] = url.pathname.slice(4).split('.');
  if (!payload || !sig || sig !== (await hmac(env, payload))) return new Response('Invalid link', { status: 403 });
  const [ref, id, exp] = new TextDecoder().decode(fromB64url(payload)).split('|');
  if (Number(exp) < Date.now() / 1000) return new Response('This download link has expired. Please contact us on WhatsApp for a new one.', { status: 410 });
  const order = await env.STORE.get('order:' + ref, 'json');
  if (!order || order.status !== 'paid' || !order.items.some((i) => i.id === id)) return new Response('Not available', { status: 403 });
  const file = await env.STORE.get('pdf:' + id, 'arrayBuffer');
  if (!file) return new Response('File not uploaded yet. Please contact us on WhatsApp.', { status: 404 });
  const name = (order.items.find((i) => i.id === id).title || id).replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-') + '.pdf';
  return new Response(file, { headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename="${name}"`, 'Cache-Control': 'private, no-store' } });
}

/* ------------------------------------------------------------------ email (Brevo) */
async function sendEmails(env, order) {
  if (!env.BREVO_API_KEY) return;
  const dl = await links(env, order, env.WORKER_URL);
  const sw = order.lang !== 'en';
  const list = dl.map((d) => `<li style="margin:0 0 10px"><a href="${d.url}" style="color:#5a73aa;font-weight:600">${escapeHtml(d.title)}</a></li>`).join('');
  const send = (to, subject, html) => fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: { 'api-key': env.BREVO_API_KEY, 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ sender: { name: sw ? 'Makala Maalum' : 'Featured Articles', email: env.SENDER_EMAIL }, to: [to], subject, htmlContent: html }),
  }).then(async (r) => { if (!r.ok) console.error('brevo', r.status, await r.text()); });
  const wrap = (inner) => `<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#172018;line-height:1.6">${inner}<p style="color:#5b6270;font-size:13px;margin-top:28px">Injili Milele · ${env.SITE_URL}</p></div>`;
  if (order.buyer.email) {
    await send({ email: order.buyer.email, name: order.buyer.name },
      sw ? `Vitabu vyako — Oda ${order.ref}` : `Your books — Order ${order.ref}`,
      wrap(sw
        ? `<h2>Asante, ${escapeHtml(order.buyer.name)}!</h2><p>Malipo yako ya <b>${money(order.amount)}</b> kwa oda <b>${order.ref}</b> yamepokelewa. Pakua vitabu vyako hapa (viungo vinafanya kazi kwa siku ${LINK_DAYS}):</p><ul>${list}</ul><p>Mungu akubariki!</p>`
        : `<h2>Thank you, ${escapeHtml(order.buyer.name)}!</h2><p>Your payment of <b>${money(order.amount)}</b> for order <b>${order.ref}</b> has been received. Download your books here (links work for ${LINK_DAYS} days):</p><ul>${list}</ul><p>God bless you!</p>`));
  }
  await send({ email: env.ADMIN_EMAIL }, `Paid order ${order.ref} — ${money(order.amount)}`,
    wrap(`<h3>New Pesapal payment</h3><p><b>${escapeHtml(order.buyer.name)}</b> · ${escapeHtml(order.buyer.phone)} · ${escapeHtml(order.buyer.email)}</p><ul>${order.items.map((i) => `<li>${escapeHtml(i.title)} — ${money(i.price)}</li>`).join('')}</ul><p>Total ${money(order.amount)}${order.couponCode ? ` (code ${order.couponCode})` : ''} · ${escapeHtml(order.payment.method)} · ${escapeHtml(order.payment.confirmation)}</p><p>${order.buyer.email ? 'The books were emailed to the buyer automatically.' : 'No email given — send the books from the dashboard.'}</p>`));
}
function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* ------------------------------------------------------------------ admin (Firebase ID token) */
let jwks = null;
async function adminFromRequest(req, env) {
  const token = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  const [h, p, s] = token.split('.');
  if (!h || !p || !s) return null;
  const header = JSON.parse(new TextDecoder().decode(fromB64url(h)));
  const claims = JSON.parse(new TextDecoder().decode(fromB64url(p)));
  const now = Date.now() / 1000;
  if (claims.aud !== env.FIREBASE_PROJECT_ID || claims.iss !== 'https://securetoken.google.com/' + env.FIREBASE_PROJECT_ID) return null;
  if (!(claims.exp > now) || !(claims.iat < now + 60) || !claims.email_verified) return null;
  if (!jwks) jwks = (await (await fetch('https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com')).json()).keys;
  const jwk = jwks.find((k) => k.kid === header.kid);
  if (!jwk) { jwks = null; return null; }
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, fromB64url(s), enc.encode(h + '.' + p));
  if (!ok) return null;
  const email = String(claims.email || '').toLowerCase();
  if (email === env.SUPER_ADMIN.toLowerCase()) return email;
  // Other admins: ask Firestore as that user (rules allow admins to read store_admins).
  const doc = await fsGet(env, 'store_admins/' + encodeURIComponent(email), token).catch(() => null);
  return doc ? email : null;
}
async function adminSync(req, env) {
  if (!(await adminFromRequest(req, env))) return json({ error: 'forbidden' }, 403);
  const list = await env.STORE.list({ prefix: 'paid:', limit: 1000 });
  const orders = [];
  for (const k of list.keys) {
    const o = await env.STORE.get('order:' + k.name.slice(5), 'json');
    if (o) orders.push(o);
  }
  return json({ orders });
}
async function adminLinks(req, url, env) {
  if (!(await adminFromRequest(req, env))) return json({ error: 'forbidden' }, 403);
  const ref = clean(url.searchParams.get('ref'), 40);
  let order = await env.STORE.get('order:' + ref, 'json');
  // Orders paid by mobile money (outside Pesapal) can also get download links once the admin marks them paid.
  if (!order || order.status !== 'paid') {
    const items = String(url.searchParams.get('items') || '').split(',').filter(Boolean);
    const cat = await catalogue(env);
    const chosen = items.filter((id) => cat[id]).map((id) => ({ id, title: cat[id].title, price: cat[id].price }));
    order = { ...(order || {}), ref, status: 'paid', manual: true, items: chosen.length ? chosen : (order && order.items) || [] };
    await env.STORE.put('order:' + ref, JSON.stringify(order));
  }
  return json({ links: await links(env, order, url.origin) });
}
