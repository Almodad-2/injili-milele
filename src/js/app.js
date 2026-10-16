/* Injili Milele — site behaviour. window.MM is injected per page. pdf.js is loaded on demand for the PDF reader. */
(function () {
  'use strict';
  var MM = window.MM || { lang: 'sw', t: {}, root: './' };
  var T = MM.t;
  var doc = document.documentElement;
  doc.classList.remove('no-js');

  /* ---------- safe storage ---------- */
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } }
  };

  /* ---------- theme ---------- */
  var theme = store.get('mm-theme', null);
  if (theme) doc.setAttribute('data-theme', theme);
  document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
    b.addEventListener('click', function () {
      var dark = doc.getAttribute('data-theme') ? doc.getAttribute('data-theme') === 'dark'
        : window.matchMedia('(prefers-color-scheme: dark)').matches;
      var next = dark ? 'light' : 'dark';
      doc.setAttribute('data-theme', next);
      store.set('mm-theme', next);
    });
  });

  /* ---------- toast ---------- */
  var toastEl;
  function toast(html, ms) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      toastEl.setAttribute('role', 'status');
      document.body.appendChild(toastEl);
    }
    toastEl.innerHTML = html;
    toastEl.classList.add('on');
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove('on'); }, ms || 3200);
  }

  /* ---------- reveal on scroll ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el, i) { el.style.transitionDelay = (i % 3) * 70 + 'ms'; io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- back to top + reading progress ---------- */
  var backTop = document.querySelector('.back-top');
  var progress = document.querySelector('.progress');
  var prose = document.querySelector('.prose');
  function onScroll() {
    var y = window.scrollY;
    if (backTop) backTop.classList.toggle('on', y > 900);
    if (progress && prose) {
      var start = prose.offsetTop - window.innerHeight * .3;
      var end = prose.offsetTop + prose.offsetHeight - window.innerHeight * .8;
      var p = Math.min(1, Math.max(0, (y - start) / Math.max(1, end - start)));
      progress.style.transform = 'scaleX(' + p + ')';
    }
  }
  var header = document.querySelector('.site-header');
  var isHome = document.body.classList.contains('home');
  var onHeader = function () { if (isHome && header) header.classList.toggle('scrolled', window.scrollY > 40); };
  window.addEventListener('scroll', onHeader, { passive: true });
  onHeader();
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (backTop) backTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ---------- reader font size ---------- */
  var sizes = [1, 1.0625, 1.125, 1.25, 1.375];
  var si = store.get('mm-size', 2);
  function applySize() { doc.style.setProperty('--reader-size', sizes[si] + 'rem'); }
  applySize();
  document.querySelectorAll('[data-size]').forEach(function (b) {
    b.addEventListener('click', function () {
      si = Math.min(sizes.length - 1, Math.max(0, si + (b.getAttribute('data-size') === '+' ? 1 : -1)));
      store.set('mm-size', si);
      applySize();
    });
  });

  /* ---------- share ---------- */
  document.querySelectorAll('[data-share]').forEach(function (b) {
    b.addEventListener('click', function (ev) {
      var kind = b.getAttribute('data-share');
      var url = location.href.split('#')[0];
      var title = document.title;
      if (kind === 'native' && navigator.share) {
        ev.preventDefault();
        navigator.share({ title: title, url: url }).catch(function () {});
      } else if (kind === 'copy' || kind === 'native') {
        ev.preventDefault();
        var done = function () { toast('✓ ' + T.copied); };
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { prompt('', url); });
        else { prompt('', url); }
      }
    });
  });

  /* ---------- lite YouTube ---------- */
  document.querySelectorAll('.video[data-yt]').forEach(function (v) {
    var id = v.getAttribute('data-yt');
    v.style.backgroundImage = 'url(https://i.ytimg.com/vi/' + id + '/hqdefault.jpg)';
    v.innerHTML = '<button class="play" aria-label="' + T.play + '"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button>' +
      '<span class="vt"></span>';
    v.querySelector('.vt').textContent = v.getAttribute('data-title') || '';
    v.addEventListener('click', function () {
      v.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0" title="YouTube" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
    }, { once: true });
  });

  /* ---------- search & category filter (home) ---------- */
  var grid = document.querySelector('[data-articles]');
  if (grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
    var input = document.querySelector('[data-search]');
    var empty = document.querySelector('.empty');
    var cat = 'all', fmt = 'all';
    var fold = function (s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
    var apply = function () {
      var q = fold(input ? input.value.trim() : '');
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (cat === 'all' || c.getAttribute('data-cat') === cat) &&
          (fmt === 'all' || (' ' + c.getAttribute('data-format') + ' ').indexOf(' ' + fmt + ' ') !== -1) &&
          (!q || fold(c.getAttribute('data-search')).indexOf(q) !== -1);
        c.hidden = !ok;
        if (ok) shown++;
        c.classList.toggle('feature', ok && !q && cat === 'all' && fmt === 'all' && c === cards[0]);
      });
      if (empty) empty.style.display = shown ? 'none' : 'block';
    };
    if (input) input.addEventListener('input', apply);
    var group = function (sel, set) {
      var list = document.querySelectorAll(sel);
      list.forEach(function (ch) {
        ch.addEventListener('click', function () {
          list.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
          ch.setAttribute('aria-pressed', 'true');
          set(ch);
          apply();
        });
      });
    };
    group('.chips.cats .chip', function (ch) { cat = ch.getAttribute('data-filter'); });
    group('.chips.formats .chip', function (ch) { fmt = ch.getAttribute('data-format-filter'); });
    var qs = new URLSearchParams(location.search).get('q');
    if (qs && input) { input.value = qs; apply(); }
  }

  /* =================== STORE =================== */
  var PRODUCTS = MM.products || {};

  /* ---------- Firestore (REST, no SDK) ---------- */
  var FB = MM.fb;
  var DB = FB ? 'projects/' + FB.projectId + '/databases/(default)/documents' : null;
  var API = 'https://firestore.googleapis.com/v1/';
  function toFs(v) {
    if (v === null || v === undefined) return { nullValue: null };
    if (typeof v === 'boolean') return { booleanValue: v };
    if (typeof v === 'number') return Number.isInteger(v) ? { integerValue: String(v) } : { doubleValue: v };
    if (typeof v === 'string') return { stringValue: v };
    if (Array.isArray(v)) return { arrayValue: { values: v.map(toFs) } };
    var f = {};
    Object.keys(v).forEach(function (k) { f[k] = toFs(v[k]); });
    return { mapValue: { fields: f } };
  }
  function fromFs(x) {
    if ('stringValue' in x) return x.stringValue;
    if ('integerValue' in x) return Number(x.integerValue);
    if ('doubleValue' in x) return x.doubleValue;
    if ('booleanValue' in x) return x.booleanValue;
    if ('timestampValue' in x) return new Date(x.timestampValue);
    if ('arrayValue' in x) return (x.arrayValue.values || []).map(fromFs);
    if ('mapValue' in x) return docData(x.mapValue);
    return null;
  }
  function docData(d) {
    var o = {};
    var f = d.fields || {};
    Object.keys(f).forEach(function (k) { o[k] = fromFs(f[k]); });
    return o;
  }
  function withTimeout(p, ms) {
    return Promise.race([p, new Promise(function (_, rej) { setTimeout(function () { rej(new Error('timeout')); }, ms); })]);
  }
  function fsGet(path) {
    return withTimeout(fetch(API + DB + '/' + path + '?key=' + FB.apiKey), 8000).then(function (r) {
      if (r.status === 404) return null;
      if (!r.ok) throw new Error('http ' + r.status);
      return r.json();
    });
  }

  function money(n) {
    if (!n) return T.free;
    return 'TSh ' + n.toLocaleString('en-US');
  }
  function priceHtml(p) {
    if (!p.price) return '<span class="price free">' + T.free + '</span>';
    var h = '<span class="price"><small>TSh</small>' + p.price.toLocaleString('en-US') + '</span>';
    if (p.was && p.was > p.price) {
      h += '<s>' + p.was.toLocaleString('en-US') + '</s><span class="sale-tag">−' + Math.round(100 - p.price * 100 / p.was) + '%</span>';
    }
    return h;
  }

  /* free -> read & download; preview -> buy, read the first pages; locked -> buy only */
  function accessOf(p) { return !p.price ? 'free' : (p.preview === false ? 'locked' : 'preview'); }
  function applyAccess(id) {
    var p = PRODUCTS[id];
    if (!p) return;
    var a = accessOf(p);
    document.querySelectorAll('[data-doc="' + id + '"], [data-reader="' + id + '"]').forEach(function (el) {
      if (el.getAttribute('data-access') !== a) {
        el.setAttribute('data-access', a);
        el.dispatchEvent(new CustomEvent('access'));
      }
    });
    document.querySelectorAll('[data-when-free="' + id + '"]').forEach(function (el) { el.hidden = a !== 'free'; });
    document.querySelectorAll('[data-when-paid="' + id + '"]').forEach(function (el) { el.hidden = a === 'free'; });
  }
  Object.keys(PRODUCTS).forEach(applyAccess);

  /* Live prices / sale prices / visibility set by the admin dashboard. */
  var livePrices = FB ? fsGet('store_products?pageSize=300').then(function (res) {
    (res && res.documents || []).forEach(function (d) {
      var id = d.name.split('/').pop();
      var o = docData(d);
      var p = PRODUCTS[id];
      if (!p) return;
      if (typeof o.price === 'number') p.price = o.price;
      if (typeof o.preview === 'boolean') p.preview = o.preview;
      p.was = null;
      if (typeof o.salePrice === 'number' && o.salePrice >= 0 && o.salePrice < p.price) {
        p.was = p.price;
        p.price = o.salePrice;
      }
      p.active = o.active !== false;
    });
    Object.keys(PRODUCTS).forEach(function (id) {
      var p = PRODUCTS[id];
      document.querySelectorAll('[data-price-of="' + id + '"]').forEach(function (el) { el.innerHTML = priceHtml(p); });
      applyAccess(id);
      if (p.active === false) {
        document.querySelectorAll('[data-product="' + id + '"]').forEach(function (el) { el.hidden = true; });
        document.querySelectorAll('[data-buybox="' + id + '"]').forEach(function (el) {
          el.querySelectorAll('button, a.btn').forEach(function (b) { b.remove(); });
          var n = document.createElement('p');
          n.className = 'unavailable';
          n.textContent = T.unavailable;
          el.insertBefore(n, el.querySelector('.note'));
        });
      }
    });
  }).catch(function () { /* rules not deployed yet or offline: keep static prices */ }) : Promise.resolve();

  var cart = store.get('mm-cart', []).filter(function (id) { return PRODUCTS[id]; });
  function saveCart() { store.set('mm-cart', cart); renderBadge(); }
  function renderBadge() {
    document.querySelectorAll('.cart-count').forEach(function (b) {
      b.textContent = cart.length;
      b.classList.toggle('on', cart.length > 0);
    });
    document.querySelectorAll('[data-add]').forEach(function (b) {
      var inCart = cart.indexOf(b.getAttribute('data-add')) !== -1;
      b.classList.toggle('added', inCart);
      b.innerHTML = inCart ? '✓ ' + T.inCart : b.getAttribute('data-label');
    });
  }
  document.querySelectorAll('[data-add]').forEach(function (b) {
    b.setAttribute('data-label', b.innerHTML);
    b.addEventListener('click', function () {
      var id = b.getAttribute('data-add');
      if (cart.indexOf(id) === -1) {
        cart.push(id);
        saveCart();
        toast(T.added + ' <a href="' + MM.cartUrl + '">' + T.viewCart + ' →</a>', 4000);
      } else {
        location.href = MM.cartUrl;
      }
    });
  });
  document.querySelectorAll('[data-buy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var id = b.getAttribute('data-buy');
      if (cart.indexOf(id) === -1) { cart.push(id); saveCart(); }
      location.href = MM.cartUrl;
    });
  });
  renderBadge();

  /* ---------- checkout page ---------- */
  var co = document.querySelector('[data-checkout]');
  if (co) {
    var list = co.querySelector('[data-lines]');
    var totalEl = co.querySelector('[data-total]');
    var form = co.querySelector('form.panel');
    var payPanel = co.querySelector('[data-pay]');
    var emptyEl = co.querySelector('[data-empty]');
    var filled = co.querySelector('[data-filled]');
    var couponForm = co.querySelector('[data-coupon-form]');
    var couponMsg = co.querySelector('[data-coupon-msg]');
    var coupon = null;   // { code, type, value, products }

    var randomCode = function (n) {
      var abc = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', out = '';
      var buf = new Uint8Array(n);
      (window.crypto || window.msCrypto).getRandomValues(buf);
      for (var i = 0; i < n; i++) out += abc[buf[i] % abc.length];
      return out;
    };
    var newRef = function () {
      var d = new Date();
      return 'MM-' + String(d.getFullYear()).slice(2) + ('0' + (d.getMonth() + 1)).slice(-2) + ('0' + d.getDate()).slice(-2) + '-' +
        randomCode(5);
    };
    var ref = store.get('mm-ref', null) || newRef();
    var signature = function () { return cart.slice().sort().join(',') + '|' + (coupon ? coupon.code : ''); };
    var lastSent = store.get('mm-sent', null);
    // An order already saved under this reference with different contents needs a new reference.
    var ensureRef = function () {
      if (lastSent && lastSent.ref === ref && lastSent.sig !== signature()) {
        ref = newRef();
        lastSent = null;
      }
      store.set('mm-ref', ref);
      co.querySelectorAll('[data-ref]').forEach(function (e) { e.textContent = ref; });
    };

    var subtotal = function () { return cart.reduce(function (s, id) { return s + (PRODUCTS[id].price || 0); }, 0); };
    var discount = function () {
      if (!coupon) return 0;
      var eligible = cart.filter(function (id) { return !coupon.products || !coupon.products.length || coupon.products.indexOf(id) !== -1; })
        .reduce(function (s, id) { return s + (PRODUCTS[id].price || 0); }, 0);
      var d = coupon.type === 'fixed' ? coupon.value : Math.round(eligible * coupon.value / 100);
      return Math.max(0, Math.min(d, eligible));
    };
    var total = function () { return subtotal() - discount(); };

    var render = function () {
      list.innerHTML = '';
      cart.forEach(function (id) {
        var p = PRODUCTS[id];
        var row = document.createElement('div');
        row.className = 'line-item';
        row.innerHTML = p.coverHtml + '<div><b></b><small></small><br><button class="rm" type="button">' + T.remove + '</button></div><div class="price-slot"></div>';
        row.querySelector('b').textContent = p.title;
        row.querySelector('small').textContent = p.subtitle;
        row.querySelector('.price-slot').innerHTML = priceHtml(p);
        row.querySelector('.rm').addEventListener('click', function () {
          cart.splice(cart.indexOf(id), 1);
          saveCart();
          render();
        });
        list.appendChild(row);
      });
      var disc = discount();
      co.querySelector('[data-subtotals]').hidden = !disc;
      co.querySelector('[data-subtotal]').textContent = money(subtotal());
      co.querySelector('[data-discount]').textContent = '− ' + money(disc);
      co.querySelector('[data-coupon-label]').textContent = coupon ? '(' + coupon.code + ')' : '';
      totalEl.textContent = money(total());
      var has = cart.length > 0;
      emptyEl.hidden = has;
      filled.hidden = !has;
      couponForm.hidden = subtotal() === 0;
      // free-only orders can be downloaded right away
      var free = cart.filter(function (id) { return !PRODUCTS[id].price && PRODUCTS[id].download; });
      var freeBox = co.querySelector('[data-free]');
      if (freeBox) {
        freeBox.hidden = free.length === 0;
        freeBox.querySelector('div').innerHTML = '';
        free.forEach(function (id) {
          var a = document.createElement('a');
          a.className = 'btn btn-line btn-block';
          a.href = PRODUCTS[id].download;
          a.setAttribute('download', '');
          a.textContent = '⬇ ' + PRODUCTS[id].title;
          freeBox.querySelector('div').appendChild(a);
        });
      }
      payPanel.hidden = total() === 0;
      ensureRef();
    };
    render();
    livePrices.then(render);

    var setMsg = function (text, ok) {
      couponMsg.textContent = text;
      couponMsg.className = 'coupon-msg ' + (ok ? 'ok' : 'bad');
    };
    couponForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var code = couponForm.elements.coupon.value.trim().toUpperCase().replace(/\s+/g, '');
      if (!code) return;
      if (!FB) { setMsg(T.couponBad, false); return; }
      setMsg(T.checking, true);
      fsGet('store_coupons/' + encodeURIComponent(code)).then(function (doc) {
        if (!doc) throw new Error('missing');
        var c = docData(doc);
        if (c.active === false) throw new Error('missing');
        if (c.expiresAt && c.expiresAt < new Date()) { coupon = null; render(); return setMsg(T.couponExpired, false); }
        if (c.maxUses && (c.uses || 0) >= c.maxUses) { coupon = null; render(); return setMsg(T.couponUsed, false); }
        var products = c.products || [];
        if (products.length && !cart.some(function (id) { return products.indexOf(id) !== -1; })) {
          coupon = null; render(); return setMsg(T.couponNotFor, false);
        }
        coupon = { code: code, type: c.type === 'fixed' ? 'fixed' : 'percent', value: Number(c.value) || 0, products: products };
        render();
        setMsg(T.couponOk + ' −' + money(discount()), true);
      }).catch(function () {
        coupon = null;
        render();
        setMsg(T.couponBad, false);
      });
    });

    var saved = store.get('mm-buyer', {});
    ['name', 'phone', 'email'].forEach(function (k) { if (saved[k] && form.elements[k]) form.elements[k].value = saved[k]; });

    var message = function () {
      var f = form.elements;
      var lines = [T.waHello, '', T.waOrder + ' ' + ref];
      cart.forEach(function (id) { lines.push('• ' + PRODUCTS[id].title + ' — ' + money(PRODUCTS[id].price)); });
      if (discount()) {
        lines.push('', T.subtotal + ': ' + money(subtotal()));
        lines.push(T.discount + ' (' + coupon.code + '): −' + money(discount()));
      }
      lines.push('', T.total + ': ' + money(total()));
      lines.push('', T.name + ': ' + f.name.value.trim());
      lines.push(T.phone + ': ' + f.phone.value.trim());
      if (f.email.value.trim()) lines.push(T.email + ': ' + f.email.value.trim());
      if (f.txn && f.txn.value.trim()) lines.push(T.txn + ': ' + f.txn.value.trim());
      return lines.join('\n');
    };
    var valid = function () {
      var f = form.elements;
      store.set('mm-buyer', { name: f.name.value, phone: f.phone.value, email: f.email.value });
      if (!f.name.value.trim() || !f.phone.value.trim()) {
        toast(T.needDetails);
        (f.name.value.trim() ? f.phone : f.name).focus();
        return false;
      }
      return true;
    };

    /* Save the order in Firestore (status "pending") so it shows in the admin dashboard.
       The coupon's use counter goes up in the same atomic commit. */
    var saveOrder = function (channel) {
      ensureRef();
      if (!FB || (lastSent && lastSent.ref === ref)) return Promise.resolve();
      var f = form.elements;
      var order = {
        ref: ref,
        items: cart.map(function (id) { return { id: id, title: PRODUCTS[id].title, price: PRODUCTS[id].price || 0 }; }),
        subtotal: subtotal(), discount: discount(), couponCode: coupon ? coupon.code : null, total: total(),
        currency: 'TZS', lang: MM.lang, status: 'pending', channel: channel, source: 'web',
        buyer: { name: f.name.value.trim().slice(0, 120), phone: f.phone.value.trim().slice(0, 40), email: f.email.value.trim().slice(0, 120) },
        txn: (f.txn && f.txn.value.trim().slice(0, 60)) || ''
      };
      var fields = toFs(order).mapValue.fields;
      var writes = [{
        update: { name: DB + '/store_orders/' + ref, fields: fields },
        currentDocument: { exists: false },
        updateTransforms: [{ fieldPath: 'createdAt', setToServerValue: 'REQUEST_TIME' }]
      }];
      if (coupon && discount()) {
        writes.push({ transform: { document: DB + '/store_coupons/' + coupon.code, fieldTransforms: [{ fieldPath: 'uses', increment: { integerValue: '1' } }] } });
      }
      return withTimeout(fetch(API + DB + ':commit?key=' + FB.apiKey, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ writes: writes })
      }), 8000).then(function (r) {
        if (r.ok) {
          lastSent = { ref: ref, sig: signature() };
          store.set('mm-sent', lastSent);
        }
      }).catch(function () { /* still send by WhatsApp/email */ });
    };
    var send = function (btn, channel, url) {
      if (!valid()) return;
      var label = btn.innerHTML;
      btn.innerHTML = T.sending;
      btn.disabled = true;
      saveOrder(channel).then(function () {
        btn.innerHTML = label;
        btn.disabled = false;
        window.location.href = url();
      });
    };
    var waBtn = co.querySelector('[data-send-wa]');
    waBtn.addEventListener('click', function () {
      send(waBtn, 'whatsapp', function () { return 'https://wa.me/' + MM.whatsapp + '?text=' + encodeURIComponent(message()); });
    });
    var mailBtn = co.querySelector('[data-send-mail]');
    mailBtn.addEventListener('click', function () {
      send(mailBtn, 'email', function () {
        return 'mailto:' + MM.email + '?subject=' + encodeURIComponent(T.waOrder + ' ' + ref) + '&body=' + encodeURIComponent(message());
      });
    });
    /* Pesapal: save the order, ask the payments service for a payment page, go there. */
    var pesaBtn = co.querySelector('[data-pesapal]');
    if (pesaBtn) pesaBtn.addEventListener('click', function () {
      if (!valid() || !MM.payments) return;
      var f = form.elements;
      var label = pesaBtn.innerHTML;
      pesaBtn.disabled = true;
      pesaBtn.innerHTML = T.redirecting;
      saveOrder('pesapal').then(function () {
        return withTimeout(fetch(MM.payments + 'pay', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ref: ref, lang: MM.lang, items: cart.slice(), coupon: coupon ? coupon.code : '',
            buyer: { name: f.name.value.trim(), phone: f.phone.value.trim(), email: f.email.value.trim() }
          })
        }), 20000);
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (!d.redirect_url) throw new Error(d.error || 'pay');
        store.set('mm-pending', { ref: ref, at: Date.now() });
        window.location.href = d.redirect_url;
      }).catch(function () {
        pesaBtn.disabled = false;
        pesaBtn.innerHTML = label;
        toast(T.payError, 6000);
      });
    });

    var copyBtn = co.querySelector('[data-copy-num]');
    if (copyBtn) copyBtn.addEventListener('click', function () {
      var n = copyBtn.getAttribute('data-copy-num');
      if (navigator.clipboard) navigator.clipboard.writeText(n).then(function () { toast('✓ ' + T.copied); });
    });
  }

  /* ---------- thank-you page (back from Pesapal) ---------- */
  var ty = document.querySelector('[data-thanks]');
  if (ty && MM.payments) {
    var qp = new URLSearchParams(location.search);
    var pref = qp.get('ref') || qp.get('OrderMerchantReference') || '';
    var tid = qp.get('OrderTrackingId') || '';
    var show = function (state) {
      ty.querySelectorAll('[data-state]').forEach(function (el) { el.hidden = el.getAttribute('data-state') !== state; });
    };
    var tries = 0;
    var check = function () {
      show('checking');
      fetch(MM.payments + 'status?ref=' + encodeURIComponent(pref) + '&OrderTrackingId=' + encodeURIComponent(tid))
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.status === 'paid') {
            var box = ty.querySelector('[data-downloads]');
            box.innerHTML = '';
            d.downloads.forEach(function (it) {
              var a = document.createElement('a');
              a.className = 'btn btn-primary btn-block';
              a.href = it.url;
              a.textContent = '⬇ ' + T.download + ': ' + it.title;
              box.appendChild(a);
            });
            ty.querySelector('[data-email-note]').textContent = d.email ? T.emailSent + ' ' + d.email : '';
            show('paid');
            // Order complete: empty the cart and start a fresh reference next time.
            cart = [];
            saveCart();
            ['mm-ref', 'mm-sent', 'mm-pending'].forEach(function (k) { try { localStorage.removeItem(k); } catch (e) {} });
          } else if (++tries < 20) {
            setTimeout(check, 3000);
          } else {
            show('pending');
          }
        })
        .catch(function () { if (++tries < 20) setTimeout(check, 3000); else show('pending'); });
    };
    ty.querySelector('[data-recheck]').addEventListener('click', function () { tries = 0; check(); });
    check();
  }

  /* =================== PDF READER =================== */
  var PDFJS = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';
  var pdfjsReady = null;
  function loadPdfJs() {
    if (!pdfjsReady) {
      pdfjsReady = new Promise(function (res, rej) {
        var s = document.createElement('script');
        s.src = PDFJS + 'pdf.min.js';
        s.onload = function () { window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS + 'pdf.worker.min.js'; res(window.pdfjsLib); };
        s.onerror = function () { pdfjsReady = null; rej(new Error('pdf.js')); };
        document.head.appendChild(s);
      });
    }
    return pdfjsReady;
  }

  document.querySelectorAll('[data-reader]').forEach(function (rd) {
    var pagesEl = rd.querySelector('[data-pages]');
    var stateEl = rd.querySelector('[data-reader-state]');
    var infoEl = rd.querySelector('[data-pageinfo]');
    var endEl = rd.querySelector('[data-preview-end]');
    var lockEl = rd.querySelector('[data-locked]');
    var loadedAs = null, busy = false, pdf = null;
    var setState = function (html) { stateEl.innerHTML = html; };

    var renderPage = function (box) {
      if (!pdf || box._done) return;
      box._done = true;
      pdf.getPage(Number(box.getAttribute('data-n'))).then(function (page) {
        var w = box.clientWidth;
        var v1 = page.getViewport({ scale: 1 });
        var ratio = Math.min(window.devicePixelRatio || 1, 2.5);
        var vp = page.getViewport({ scale: (w / v1.width) * ratio });
        var c = document.createElement('canvas');
        c.width = Math.floor(vp.width);
        c.height = Math.floor(vp.height);
        return page.render({ canvasContext: c.getContext('2d'), viewport: vp }).promise.then(function () {
          box.innerHTML = '';
          box.appendChild(c);
          box.classList.add('ready');
        });
      }).catch(function () { box._done = false; });
    };
    var lazy = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) renderPage(en.target); });
    }, { rootMargin: '900px 0px' }) : null;
    var current = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting && pdf) infoEl.textContent = T.page + ' ' + en.target.getAttribute('data-n') + ' / ' + pdf.numPages;
      });
    }, { rootMargin: '-45% 0px -45% 0px' }) : null;

    var load = function () {
      var access = rd.getAttribute('data-access');
      if (access === 'locked') {
        loadedAs = 'locked';
        pagesEl.innerHTML = '';
        endEl.hidden = true;
        lockEl.hidden = false;
        setState(T.fullPdf);
        return;
      }
      if (busy || loadedAs === access) return;
      busy = true;
      lockEl.hidden = true;
      setState('<span class="spin"></span>' + T.loadingPdf);
      var got;
      loadPdfJs().then(function () {
        return withTimeout(fetch(rd.getAttribute('data-src'), { cache: 'no-store' }), 30000);
      }).then(function (r) {
        if (r.status === 402) { got = 'locked'; return null; }
        if (!r.ok) throw new Error('http ' + r.status);
        got = r.headers.get('X-Access') || (access === 'free' ? 'full' : 'preview');
        return r.arrayBuffer();
      }).then(function (buf) {
        if (!buf) return null;
        return window.pdfjsLib.getDocument({ data: new Uint8Array(buf) }).promise;
      }).then(function (doc) {
        busy = false;
        if (!doc) { rd.setAttribute('data-access', 'locked'); load(); return; }
        pdf = doc;
        loadedAs = access;
        return doc.getPage(1).then(function (p1) {
          var v = p1.getViewport({ scale: 1 });
          pagesEl.innerHTML = '';
          for (var n = 1; n <= doc.numPages; n++) {
            var box = document.createElement('div');
            box.className = 'pg';
            box.setAttribute('data-n', n);
            box.style.aspectRatio = v.width + ' / ' + v.height;
            pagesEl.appendChild(box);
            if (lazy) lazy.observe(box); else renderPage(box);
            if (current) current.observe(box);
          }
          var preview = got === 'preview';
          endEl.hidden = !preview;
          setState(preview ? '<b class="tag">' + T.previewNote + '</b>' : '<b class="tag ok">PDF</b> ' + T.pages.replace('{n}', doc.numPages));
          infoEl.textContent = T.page + ' 1 / ' + doc.numPages;
        });
      }).catch(function () {
        busy = false;
        setState(T.pdfError + ' <button class="tool" type="button" data-retry>' + T.retry + '</button>');
        var b = stateEl.querySelector('[data-retry]');
        if (b) b.addEventListener('click', load);
      });
    };

    // start when the reader comes near the screen; reload when the dashboard changes the access
    if ('IntersectionObserver' in window) {
      var near = new IntersectionObserver(function (es) {
        if (es.some(function (en) { return en.isIntersecting; })) { near.disconnect(); livePrices.then(load); }
      }, { rootMargin: '600px 0px' });
      near.observe(rd);
    } else {
      livePrices.then(load);
    }
    rd.addEventListener('access', function () { if (loadedAs) { loadedAs = null; pdf = null; load(); } });

    var resizeT;
    window.addEventListener('resize', function () {
      clearTimeout(resizeT);
      resizeT = setTimeout(function () {
        pagesEl.querySelectorAll('.pg.ready').forEach(function (b) { b._done = false; b.classList.remove('ready'); renderPage(b); });
      }, 400);
    });
    var fs = rd.querySelector('[data-fs]');
    if (fs) fs.addEventListener('click', function () {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (rd.requestFullscreen) rd.requestFullscreen();
      else rd.scrollIntoView();
    });
  });

  /* ---------- audio: only free items get a source; paid audio is bought and downloaded ---------- */
  document.querySelectorAll('[data-audio]').forEach(function (box) {
    var id = box.getAttribute('data-audio');
    var au = box.querySelector('audio');
    var set = function () {
      var p = PRODUCTS[id];
      var free = !p || !p.price;
      au.hidden = !free;
      if (free && !au.getAttribute('src')) au.src = au.getAttribute('data-src');
    };
    set();
    livePrices.then(set);
  });

})();
