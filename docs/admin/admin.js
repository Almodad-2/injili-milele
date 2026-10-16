// Injili Milele — store dashboard (Firebase Auth + Firestore).
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {
  getAuth, onAuthStateChanged, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider,
  sendPasswordResetEmail, sendEmailVerification, signOut,
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';
import {
  getFirestore, collection, doc, getDoc, setDoc, updateDoc, deleteDoc, onSnapshot,
  query, orderBy, limit, serverTimestamp, Timestamp,
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

const CFG = window.ADMIN_CONFIG;
const app = initializeApp({ apiKey: CFG.apiKey, authDomain: CFG.authDomain, projectId: CFG.projectId });
const auth = getAuth(app);
const db = getFirestore(app);

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const money = (n) => 'TSh ' + Math.round(n || 0).toLocaleString('en-US');
const STATUSES = ['pending', 'paid', 'delivered', 'cancelled'];
const PAID = new Set(['paid', 'delivered']);

let catalog = [];          // from ../data/products.json
let live = {};             // store_products overrides
let orders = [];
let coupons = [];
let isSuper = false;
let filter = 'all';
const unsubs = [];

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('on');
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove('on'), 3000);
}
function show(id) {
  ['loginView', 'denyView', 'dash'].forEach((v) => { $('#' + v).hidden = v !== id; });
}
function permissionProblem(err) {
  console.warn(err);
  if (err && (err.code === 'permission-denied' || /permission/i.test(err.message || ''))) {
    $('#rulesWarn').hidden = false;
  }
}
function waPhone(p) {
  let d = String(p || '').replace(/\D/g, '');
  if (d.startsWith('0')) d = '255' + d.slice(1);
  if (d.length === 9) d = '255' + d;
  return d;
}
function title(id) {
  const p = catalog.find((x) => x.id === id);
  return p ? p.title : id;
}
function date(ts) {
  const d = ts && ts.toDate ? ts.toDate() : null;
  return d ? d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
}

/* ---------------- auth ---------------- */
$('#rulesText').textContent = CFG.rules;
$('#copyRules').addEventListener('click', async () => {
  await navigator.clipboard.writeText(CFG.rules);
  $('#copyMsg').textContent = 'Copied ✓';
});

$('#loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('#loginErr').textContent = '';
  try {
    await signInWithEmailAndPassword(auth, $('#lEmail').value.trim(), $('#lPass').value);
  } catch (err) {
    $('#loginErr').textContent = err.code === 'auth/invalid-credential' || err.code === 'auth/wrong-password'
      ? 'Wrong email or password. If you normally use Google sign-in, use “send a password link” below to create a password.'
      : err.message;
  }
});
$('#googleBtn').addEventListener('click', async () => {
  $('#loginErr').textContent = '';
  try {
    await signInWithPopup(auth, new GoogleAuthProvider());
  } catch (err) {
    $('#loginErr').textContent = err.code === 'auth/unauthorized-domain'
      ? 'Google sign-in is not enabled for this website yet (see Setup step 2). Use email + password for now.'
      : err.message;
  }
});
$('#resetLink').addEventListener('click', async (e) => {
  e.preventDefault();
  const email = $('#lEmail').value.trim();
  if (!email) { $('#loginErr').textContent = 'Type your email first.'; return; }
  try {
    await sendPasswordResetEmail(auth, email);
    $('#loginErr').innerHTML = '<span class="okmsg">Password link sent to ' + esc(email) + '. Check your inbox (and spam).</span>';
  } catch (err) { $('#loginErr').textContent = err.message; }
});
$('#signOut').addEventListener('click', () => signOut(auth));
$('#verifyBtn').addEventListener('click', async () => {
  await sendEmailVerification(auth.currentUser);
  $('#verifyMsg').textContent = 'Verification email sent. Open the link, then sign out and in again.';
});

onAuthStateChanged(auth, async (user) => {
  unsubs.splice(0).forEach((u) => u());
  $('#who').hidden = !user;
  if (!user) { show('loginView'); return; }
  $('#whoEmail').textContent = user.email;
  const email = (user.email || '').toLowerCase();
  isSuper = email === CFG.superAdmin.toLowerCase();
  if (!user.emailVerified) {
    $('#denyText').textContent = 'Your email address is not verified yet. Verify it to unlock the dashboard.';
    $('#verifyBtn').hidden = false;
    show('denyView');
    return;
  }
  let allowed = isSuper;
  if (!allowed) {
    try { allowed = (await getDoc(doc(db, 'store_admins', email))).exists(); } catch (err) { allowed = false; }
  }
  if (!allowed) {
    $('#denyText').textContent = user.email + ' is not a store admin. Ask the super admin to add you.';
    $('#verifyBtn').hidden = true;
    show('denyView');
    return;
  }
  $('#adminsTab').hidden = !isSuper;
  show('dash');
  start();
});

/* ---------------- tabs ---------------- */
$$('.tabs button').forEach((b) => b.addEventListener('click', () => {
  $$('.tabs button').forEach((x) => x.setAttribute('aria-selected', String(x === b)));
  $$('.view').forEach((v) => { v.hidden = v.dataset.view !== b.dataset.tab; });
}));

/* ---------------- data ---------------- */
async function start() {
  catalog = await fetch('../data/products.json', { cache: 'no-store' }).then((r) => r.json());
  renderProductChecks();
  unsubs.push(onSnapshot(collection(db, 'store_products'), (s) => {
    live = {};
    s.forEach((d) => { live[d.id] = d.data(); });
    renderProducts();
  }, (err) => { permissionProblem(err); renderProducts(); }));
  let firstLoad = true;
  unsubs.push(onSnapshot(query(collection(db, 'store_orders'), orderBy('createdAt', 'desc'), limit(1000)), (s) => {
    orders = s.docs.map((d) => ({ id: d.id, ...d.data() }));
    renderOrders();
    renderOverview();
    if (firstLoad) { firstLoad = false; syncPayments(); }
  }, (err) => { permissionProblem(err); renderOrders(); renderOverview(); }));
  const timer = setInterval(syncPayments, 60000);
  unsubs.push(() => clearInterval(timer));
  unsubs.push(onSnapshot(collection(db, 'store_coupons'), (s) => {
    coupons = s.docs.map((d) => ({ id: d.id, ...d.data() })).sort((a, b) => (b.createdAt?.seconds || 0) - (a.createdAt?.seconds || 0));
    renderCoupons();
  }, permissionProblem));
  if (isSuper) {
    unsubs.push(onSnapshot(collection(db, 'store_admins'), (s) => {
      $('#admins').innerHTML = s.docs.length
        ? s.docs.map((d) => `<li><span>${esc(d.id)}</span><button class="btn btn-line btn-sm" data-rm-admin="${esc(d.id)}">Remove</button></li>`).join('')
        : '<li class="muted">No extra admins. Only you have access.</li>';
    }, permissionProblem));
  }
}

/* ---------------- Pesapal payments (Cloudflare payments service) ---------------- */
async function payments(path) {
  const token = await auth.currentUser.getIdToken();
  const r = await fetch(CFG.payments + path, { headers: { Authorization: 'Bearer ' + token } });
  if (!r.ok) throw new Error('payments ' + r.status);
  return r.json();
}
// Orders confirmed by Pesapal are stored by the payments service; copy them into Firestore as "paid".
async function syncPayments() {
  if (!CFG.payments || !auth.currentUser) return;
  let res;
  try { res = await payments('admin/sync'); } catch (err) { console.warn(err); return; }
  let changed = 0;
  for (const p of res.orders || []) {
    const existing = orders.find((o) => o.id === p.ref);
    const payment = { ...p.payment, merchantRef: p.merchantRef || '', trackingId: p.trackingId || '' };
    if (existing && existing.payment && existing.payment.provider === 'pesapal') continue;
    if (existing) {
      if (!['pending', 'cancelled'].includes(existing.status)) continue;
      await updateDoc(doc(db, 'store_orders', p.ref), { status: 'paid', total: p.amount, payment, channel: 'pesapal', updatedAt: serverTimestamp() });
    } else {
      await setDoc(doc(db, 'store_orders', p.ref), {
        ref: p.ref, items: p.items, subtotal: p.subtotal, discount: p.discount || 0, couponCode: p.couponCode || null, total: p.amount,
        currency: 'TZS', buyer: p.buyer, txn: '', lang: p.lang, status: 'paid', channel: 'pesapal', source: 'pesapal', payment,
        createdAt: p.createdAt ? Timestamp.fromDate(new Date(p.createdAt)) : serverTimestamp(),
      });
    }
    changed++;
  }
  if (changed) toast(`${changed} Pesapal payment${changed > 1 ? 's' : ''} received`);
}

/* ---------------- overview ---------------- */
function renderOverview() {
  const paid = orders.filter((o) => PAID.has(o.status));
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const sum = (arr) => arr.reduce((s, o) => s + (o.total || 0), 0);
  $('#kRevenue').textContent = money(sum(paid));
  $('#kMonth').textContent = money(sum(paid.filter((o) => o.createdAt && o.createdAt.toDate() >= monthStart)));
  const pending = orders.filter((o) => o.status === 'pending').length;
  $('#kPending').textContent = pending;
  $('#pendingCount').hidden = !pending;
  $('#pendingCount').textContent = pending;
  $('#kSold').textContent = paid.reduce((s, o) => s + (o.items || []).length, 0);
  $('#kDisc').textContent = money(paid.reduce((s, o) => s + (o.discount || 0), 0));

  const days = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
    days.push({ d, total: 0 });
  }
  paid.forEach((o) => {
    if (!o.createdAt) return;
    const t = o.createdAt.toDate();
    const day = days.find((x) => x.d.toDateString() === t.toDateString());
    if (day) day.total += o.total || 0;
  });
  const max = Math.max(1, ...days.map((x) => x.total));
  $('#chart').innerHTML = days.map((x) => `<div class="bar" title="${x.d.toDateString()}: ${money(x.total)}"><i style="height:${Math.round(x.total / max * 100)}%"></i><span>${x.d.getDate()}</span></div>`).join('');

  const counts = {};
  paid.forEach((o) => (o.items || []).forEach((it) => { counts[it.id] = (counts[it.id] || 0) + 1; }));
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  $('#rank').innerHTML = top.length
    ? top.map(([id, n]) => `<li><span>${esc(title(id))}</span><b>${n}</b></li>`).join('')
    : '<li class="muted">No paid sales yet.</li>';
}

/* ---------------- orders ---------------- */
$('#oSearch').addEventListener('input', renderOrders);
$$('#oFilter .chip').forEach((c) => c.addEventListener('click', () => {
  $$('#oFilter .chip').forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
  filter = c.dataset.f;
  renderOrders();
}));

function renderOrders() {
  const q = $('#oSearch').value.trim().toLowerCase();
  const list = orders.filter((o) => (filter === 'all' || o.status === filter) && (!q || JSON.stringify([o.ref, o.buyer, o.couponCode, o.txn, o.items]).toLowerCase().includes(q)));
  if (!list.length) {
    $('#orders').innerHTML = `<p class="empty-state">${orders.length ? 'No orders match.' : 'No orders yet. They appear here as soon as a buyer sends an order from the cart.'}</p>`;
    return;
  }
  $('#orders').innerHTML = list.map((o) => `
    <article class="order" data-id="${esc(o.id)}">
      <div>
        <div class="ref">${esc(o.ref || o.id)} <span class="pill st-${esc(o.status)}">${esc(o.status)}</span></div>
        <div class="meta">${date(o.createdAt)} · ${esc(o.channel || o.source || '')} · ${esc((o.lang || '').toUpperCase())}</div>
        <p style="margin:8px 0 0"><b>${esc(o.buyer?.name)}</b><br>
          ${o.buyer?.phone ? `<a href="tel:${esc(o.buyer.phone)}">${esc(o.buyer.phone)}</a>` : ''}
          ${o.buyer?.email ? `<br><a href="mailto:${esc(o.buyer.email)}">${esc(o.buyer.email)}</a>` : ''}</p>
        ${o.txn ? `<div class="meta">Txn: <b>${esc(o.txn)}</b></div>` : ''}
        ${o.payment && o.payment.provider === 'pesapal' ? `<div class="meta">Pesapal · ${esc(o.payment.method)} · <b>${esc(o.payment.confirmation)}</b>${o.buyer?.email ? ' · books emailed automatically' : ''}</div>` : ''}
      </div>
      <div>
        <ul>${(o.items || []).map((it) => `<li>${esc(it.title || title(it.id))} — ${money(it.price)}</li>`).join('')}</ul>
        ${o.discount ? `<div class="meta" style="margin-top:6px">Subtotal ${money(o.subtotal)} · Code <b>${esc(o.couponCode)}</b> −${money(o.discount)}</div>` : ''}
        <div class="money">${money(o.total)}</div>
        <textarea rows="2" placeholder="Private note…" data-note>${esc(o.adminNote || '')}</textarea>
      </div>
      <div class="acts">
        <select data-status>${STATUSES.map((s) => `<option value="${s}" ${s === o.status ? 'selected' : ''}>${s[0].toUpperCase() + s.slice(1)}</option>`).join('')}</select>
        <button class="btn btn-wa btn-sm" type="button" data-send>Send books (WhatsApp)</button>
        <button class="btn btn-line btn-sm" type="button" data-wa>Message buyer</button>
        <button class="btn btn-line btn-sm" type="button" data-del>Delete</button>
      </div>
    </article>`).join('');
}

$('#orders').addEventListener('change', async (e) => {
  const card = e.target.closest('.order');
  if (!card || !e.target.matches('[data-status]')) return;
  try {
    await updateDoc(doc(db, 'store_orders', card.dataset.id), { status: e.target.value, updatedAt: serverTimestamp() });
    toast('Status saved');
  } catch (err) { toast(err.message); }
});
$('#orders').addEventListener('focusout', async (e) => {
  const card = e.target.closest('.order');
  if (!card || !e.target.matches('[data-note]')) return;
  const o = orders.find((x) => x.id === card.dataset.id);
  if ((o.adminNote || '') === e.target.value) return;
  await updateDoc(doc(db, 'store_orders', o.id), { adminNote: e.target.value, updatedAt: serverTimestamp() });
  toast('Note saved');
});
$('#orders').addEventListener('click', async (e) => {
  const card = e.target.closest('.order');
  if (!card) return;
  const o = orders.find((x) => x.id === card.dataset.id);
  const phone = waPhone(o.buyer?.phone);
  const sw = o.lang !== 'en';
  if (e.target.matches('[data-wa]')) {
    const msg = sw ? `Habari ${o.buyer?.name}, kuhusu oda yako ${o.ref} ya ${money(o.total)}:` : `Hello ${o.buyer?.name}, about your order ${o.ref} (${money(o.total)}):`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, '_blank');
  }
  if (e.target.matches('[data-send]')) {
    const win = window.open('', '_blank');   // opened now so pop-up blockers allow it
    let signed = {};
    try {
      const ids = (o.items || []).map((it) => it.id).join(',');
      const res = await payments(`admin/links?ref=${encodeURIComponent(o.ref)}&items=${encodeURIComponent(ids)}`);
      (res.links || []).forEach((l) => { signed[l.id] = l.url; });
    } catch (err) { console.warn(err); }
    const links = (o.items || []).map((it) => {
      const url = signed[it.id] || live[it.id]?.deliveryUrl;
      return `• ${it.title || title(it.id)}: ${url || '(attach the PDF)'}`;
    });
    const msg = (sw
      ? [`Habari ${o.buyer?.name}! Asante kwa kununua. Malipo ya oda ${o.ref} yamepokelewa.`, '', 'Pakua vitabu vyako hapa:', ...links, '', 'Mungu akubariki! — Injili Milele']
      : [`Hello ${o.buyer?.name}! Thank you for your purchase. Payment for order ${o.ref} has been received.`, '', 'Download your books here:', ...links, '', 'God bless you! — Injili Milele']).join('\n');
    const wa = `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`;
    if (win) win.location = wa; else window.open(wa, '_blank');
    if (o.status !== 'delivered') {
      await updateDoc(doc(db, 'store_orders', o.id), { status: 'delivered', updatedAt: serverTimestamp() });
      toast('Marked as delivered');
    }
  }
  if (e.target.matches('[data-del]') && confirm(`Delete order ${o.ref}? This cannot be undone.`)) {
    await deleteDoc(doc(db, 'store_orders', o.id));
    toast('Order deleted');
  }
});

$('#csvBtn').addEventListener('click', () => {
  const rows = [['Reference', 'Date', 'Status', 'Name', 'Phone', 'Email', 'Items', 'Subtotal', 'Discount', 'Code', 'Total', 'Txn', 'Note']];
  orders.forEach((o) => rows.push([o.ref, o.createdAt ? o.createdAt.toDate().toISOString() : '', o.status, o.buyer?.name, o.buyer?.phone, o.buyer?.email,
    (o.items || []).map((i) => i.title || i.id).join(' | '), o.subtotal, o.discount, o.couponCode, o.total, o.txn, o.adminNote]));
  const csv = rows.map((r) => r.map((v) => '"' + String(v ?? '').replace(/"/g, '""') + '"').join(',')).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv' }));
  a.download = `orders-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
});

/* manual order */
function renderProductChecks() {
  const checks = catalog.map((p) => `<label><input type="checkbox" value="${esc(p.id)}"> ${esc(p.title)} <span class="pill st-paid">${esc(p.lang)}</span></label>`).join('');
  $('#couponProducts').innerHTML = checks;
  $('#orderProducts').innerHTML = checks;
}
$('#newOrderBtn').addEventListener('click', () => { $('#orderForm').reset(); $('#orderDialog').showModal(); });
$('#orderProducts').addEventListener('change', () => {
  const ids = $$('#orderProducts input:checked').map((i) => i.value);
  $('#orderForm').elements.total.value = ids.reduce((s, id) => s + currentPrice(id), 0);
});
$('#orderForm').addEventListener('submit', async (e) => {
  if (e.submitter && e.submitter.value === 'cancel') return;
  e.preventDefault();
  const f = e.target.elements;
  const ids = $$('#orderProducts input:checked').map((i) => i.value);
  if (!ids.length) { toast('Choose at least one book'); return; }
  const d = new Date();
  const ref = 'MM-' + String(d.getFullYear()).slice(2) + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0') + '-' + Array.from(crypto.getRandomValues(new Uint8Array(5)), (v) => 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[v % 32]).join('');
  const items = ids.map((id) => ({ id, title: title(id), price: currentPrice(id) }));
  const subtotal = items.reduce((s, i) => s + i.price, 0);
  const total = Number(f.total.value) || 0;
  await setDoc(doc(db, 'store_orders', ref), {
    ref, items, subtotal, discount: Math.max(0, subtotal - total), couponCode: null, total, currency: 'TZS',
    buyer: { name: f.name.value.trim(), phone: f.phone.value.trim(), email: '' }, txn: '', lang: 'sw',
    status: f.status.value, channel: 'manual', source: 'admin', adminNote: f.note.value.trim(), createdAt: serverTimestamp(),
  });
  $('#orderDialog').close();
  toast('Order saved');
});

/* ---------------- products ---------------- */
function currentPrice(id) {
  const p = catalog.find((x) => x.id === id);
  const o = live[id] || {};
  const base = typeof o.price === 'number' ? o.price : p.price;
  return typeof o.salePrice === 'number' && o.salePrice < base ? o.salePrice : base;
}
let prodKind = 'all';
let prodQuery = '';
const KIND_LABEL = { bundle: 'Collection', article: 'Article', book: 'Book', audio: 'Audio' };
function renderProducts() {
  const list = catalog.filter((p) => {
    const kind = p.kind || 'bundle';
    const okKind = prodKind === 'all' || (prodKind === 'singles' ? ['article', 'book'].includes(kind) : kind === prodKind);
    const q = prodQuery.toLowerCase();
    return okKind && (!q || (p.title + ' ' + (p.category || '') + ' ' + p.id).toLowerCase().includes(q));
  });
  $('#products').innerHTML = list.map((p) => {
    const o = live[p.id] || {};
    const price = typeof o.price === 'number' ? o.price : p.price;
    const preview = typeof o.preview === 'boolean' ? o.preview : p.preview !== false;
    const kind = p.kind || 'bundle';
    return `<form class="prod" data-id="${esc(p.id)}">
      <header><img src="../assets/img/${esc(p.image)}.jpg" alt=""><div><h3>${esc(p.title)}</h3>
        <div class="meta muted">${KIND_LABEL[kind] || kind} · ${p.lang === 'sw' ? 'Kiswahili' : 'English'}${p.pages ? ' · ' + p.pages + ' pages' : ''}</div>
        ${live[p.id] ? '<span class="live">● Live settings</span>' : '<span class="muted" style="font-size:.78rem">Using website default</span>'}</div></header>
      <div class="grid2">
        <label class="lbl">Price (TSh, 0 = free)<input class="in" name="price" type="number" min="0" step="100" value="${price}"></label>
        <label class="lbl">Sale price (blank = none)<input class="in" name="salePrice" type="number" min="0" step="100" value="${typeof o.salePrice === 'number' ? o.salePrice : ''}"></label>
      </div>
      ${kind === 'bundle' ? `<label class="lbl">Fallback delivery link (optional)<input class="in" name="deliveryUrl" type="url" placeholder="https://drive.google.com/…" value="${esc(o.deliveryUrl || '')}"></label>` : ''}
      <div class="row-actions" style="justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div style="display:grid;gap:6px">
          <label class="switch"><input type="checkbox" name="active" ${o.active === false ? '' : 'checked'}> Shown on the website</label>
          ${kind === 'audio' ? '' : `<label class="switch" title="When the price is above 0, readers can still read the first pages free"><input type="checkbox" name="preview" ${preview ? 'checked' : ''}> Free preview of first pages</label>`}
        </div>
        <div class="row-actions"><a class="btn btn-line btn-sm" href="${esc(p.url)}" target="_blank" rel="noopener">View</a><button class="btn btn-primary btn-sm" type="submit">Save</button></div>
      </div>
    </form>`;
  }).join('') || '<p class="muted">No items match.</p>';
}
$$('[data-prod-kind]').forEach((b) => b.addEventListener('click', () => {
  $$('[data-prod-kind]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  prodKind = b.dataset.prodKind;
  renderProducts();
}));
$('#prodSearch').addEventListener('input', (e) => { prodQuery = e.target.value.trim(); renderProducts(); });
$('#products').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target.elements;
  const id = e.target.dataset.id;
  const sale = f.salePrice.value === '' ? null : Number(f.salePrice.value);
  const price = Number(f.price.value) || 0;
  if (sale !== null && sale >= price) { toast('Sale price must be lower than the price'); return; }
  const data = { price, salePrice: sale, active: f.active.checked, updatedAt: serverTimestamp() };
  if (f.deliveryUrl) data.deliveryUrl = f.deliveryUrl.value.trim();
  if (f.preview) data.preview = f.preview.checked;
  try {
    await setDoc(doc(db, 'store_products', id), data, { merge: true });
    toast(price ? 'Saved — now sold for TSh ' + (sale ?? price).toLocaleString('en-US') : 'Saved — free to read and download');
  } catch (err) { permissionProblem(err); toast(err.message); }
});

/* ---------------- coupons ---------------- */
function renderCoupons() {
  $('#coupons').innerHTML = coupons.length ? coupons.map((c) => `<tr data-code="${esc(c.id)}">
      <td><b style="font-family:ui-monospace,Menlo,monospace">${esc(c.id)}</b>${c.note ? `<div class="muted" style="font-size:.8rem">${esc(c.note)}</div>` : ''}</td>
      <td>${c.type === 'fixed' ? money(c.value) : c.value + '%'}</td>
      <td>${c.uses || 0}${c.maxUses ? ' / ' + c.maxUses : ''}</td>
      <td>${c.expiresAt ? c.expiresAt.toDate().toLocaleDateString('en-GB') : '—'}</td>
      <td>${c.products && c.products.length ? c.products.map((id) => esc(title(id))).join('<br>') : 'All'}</td>
      <td><label class="switch"><input type="checkbox" data-toggle ${c.active ? 'checked' : ''}></label></td>
      <td><div class="row-actions"><button class="btn btn-line btn-sm" data-share>Share</button><button class="btn btn-line btn-sm" data-del>Delete</button></div></td>
    </tr>`).join('') : '<tr><td colspan="7" class="muted">No codes yet.</td></tr>';
}
$('#couponForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target.elements;
  const code = f.code.value.trim().toUpperCase();
  const value = Number(f.value.value);
  $('#couponErr').textContent = '';
  if (f.type.value === 'percent' && (value <= 0 || value > 100)) { $('#couponErr').textContent = 'Percent must be between 1 and 100.'; return; }
  try {
    if ((await getDoc(doc(db, 'store_coupons', code))).exists()) { $('#couponErr').textContent = 'That code already exists.'; return; }
    await setDoc(doc(db, 'store_coupons', code), {
      code, type: f.type.value, value, maxUses: Number(f.maxUses.value) || 0, uses: 0, active: true,
      expiresAt: f.expires.value ? Timestamp.fromDate(new Date(f.expires.value + 'T23:59:59')) : null,
      products: $$('#couponProducts input:checked').map((i) => i.value), note: f.note.value.trim(), createdAt: serverTimestamp(),
    });
    e.target.reset();
    toast(`Code ${code} created`);
  } catch (err) { permissionProblem(err); $('#couponErr').textContent = err.message; }
});
$('#coupons').addEventListener('change', async (e) => {
  const row = e.target.closest('tr');
  if (row && e.target.matches('[data-toggle]')) {
    await updateDoc(doc(db, 'store_coupons', row.dataset.code), { active: e.target.checked });
    toast(e.target.checked ? 'Code activated' : 'Code paused');
  }
});
$('#coupons').addEventListener('click', async (e) => {
  const row = e.target.closest('tr');
  if (!row) return;
  const c = coupons.find((x) => x.id === row.dataset.code);
  if (e.target.matches('[data-del]') && confirm(`Delete code ${c.id}?`)) {
    await deleteDoc(doc(db, 'store_coupons', c.id));
    toast('Code deleted');
  }
  if (e.target.matches('[data-share]')) {
    const off = c.type === 'fixed' ? money(c.value) : c.value + '%';
    const text = `Tumia msimbo ${c.id} kupata punguzo la ${off} kwenye Duka la Injili Milele: ${CFG.siteUrl}sw/duka/`;
    await navigator.clipboard.writeText(text);
    toast('Share message copied');
  }
});

/* ---------------- admins ---------------- */
$('#adminForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = e.target.elements.email.value.trim().toLowerCase();
  try {
    await setDoc(doc(db, 'store_admins', email), { email, addedAt: serverTimestamp() });
    e.target.reset();
    toast(email + ' is now an admin');
  } catch (err) { $('#adminErr').textContent = err.message; }
});
$('#admins').addEventListener('click', async (e) => {
  const email = e.target.dataset.rmAdmin;
  if (email && confirm(`Remove ${email} as admin?`)) {
    await deleteDoc(doc(db, 'store_admins', email));
    toast('Admin removed');
  }
});
