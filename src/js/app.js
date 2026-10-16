/* Makala Maalum — site behaviour (no dependencies). window.MM is injected per page. */
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
    var chips = document.querySelectorAll('.chip');
    var empty = document.querySelector('.empty');
    var cat = 'all';
    var fold = function (s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
    var apply = function () {
      var q = fold(input ? input.value.trim() : '');
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (cat === 'all' || c.getAttribute('data-cat') === cat) &&
          (!q || fold(c.getAttribute('data-search')).indexOf(q) !== -1);
        c.hidden = !ok;
        if (ok) shown++;
        c.classList.toggle('feature', ok && !q && cat === 'all' && c === cards[0]);
      });
      if (empty) empty.style.display = shown ? 'none' : 'block';
    };
    if (input) input.addEventListener('input', apply);
    chips.forEach(function (ch) {
      ch.addEventListener('click', function () {
        chips.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
        ch.setAttribute('aria-pressed', 'true');
        cat = ch.getAttribute('data-filter');
        apply();
      });
    });
    var qs = new URLSearchParams(location.search).get('q');
    if (qs && input) { input.value = qs; apply(); }
  }

  /* =================== STORE =================== */
  var PRODUCTS = MM.products || {};
  var cart = store.get('mm-cart', []).filter(function (id) { return PRODUCTS[id]; });
  function saveCart() { store.set('mm-cart', cart); renderBadge(); }
  function money(n) {
    if (!n) return T.free;
    return 'TSh ' + n.toLocaleString('en-US');
  }
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
    var form = co.querySelector('form');
    var payPanel = co.querySelector('[data-pay]');
    var emptyEl = co.querySelector('[data-empty]');
    var filled = co.querySelector('[data-filled]');
    var ref = store.get('mm-ref', null);
    if (!ref) {
      var d = new Date();
      ref = 'MM-' + String(d.getFullYear()).slice(2) + ('0' + (d.getMonth() + 1)).slice(-2) + ('0' + d.getDate()).slice(-2) + '-' +
        Math.random().toString(36).slice(2, 6).toUpperCase();
      store.set('mm-ref', ref);
    }
    co.querySelectorAll('[data-ref]').forEach(function (e) { e.textContent = ref; });

    var total = function () { return cart.reduce(function (s, id) { return s + (PRODUCTS[id].price || 0); }, 0); };
    var render = function () {
      list.innerHTML = '';
      cart.forEach(function (id) {
        var p = PRODUCTS[id];
        var row = document.createElement('div');
        row.className = 'line-item';
        row.innerHTML = p.coverHtml + '<div><b></b><small></small><br><button class="rm" type="button">' + T.remove + '</button></div><div class="price"></div>';
        row.querySelector('b').textContent = p.title;
        row.querySelector('small').textContent = p.subtitle;
        row.querySelector('.price').textContent = money(p.price);
        if (!p.price) row.querySelector('.price').classList.add('free');
        row.querySelector('.rm').addEventListener('click', function () {
          cart.splice(cart.indexOf(id), 1);
          saveCart();
          render();
        });
        list.appendChild(row);
      });
      totalEl.textContent = money(total());
      var has = cart.length > 0;
      emptyEl.hidden = has;
      filled.hidden = !has;
      // free-only orders can be downloaded right away
      var free = cart.filter(function (id) { return !PRODUCTS[id].price; });
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
    };
    render();

    var saved = store.get('mm-buyer', {});
    ['name', 'phone', 'email'].forEach(function (k) { if (saved[k] && form.elements[k]) form.elements[k].value = saved[k]; });

    var message = function () {
      var f = form.elements;
      var lines = [T.waHello, '', T.waOrder + ' ' + ref];
      cart.forEach(function (id) { lines.push('• ' + PRODUCTS[id].title + ' — ' + money(PRODUCTS[id].price)); });
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
    co.querySelector('[data-send-wa]').addEventListener('click', function () {
      if (!valid()) return;
      window.location.href = 'https://wa.me/' + MM.whatsapp + '?text=' + encodeURIComponent(message());
    });
    co.querySelector('[data-send-mail]').addEventListener('click', function () {
      if (!valid()) return;
      window.location.href = 'mailto:' + MM.email + '?subject=' + encodeURIComponent(T.waOrder + ' ' + ref) + '&body=' + encodeURIComponent(message());
    });
    var copyBtn = co.querySelector('[data-copy-num]');
    if (copyBtn) copyBtn.addEventListener('click', function () {
      var n = copyBtn.getAttribute('data-copy-num');
      if (navigator.clipboard) navigator.clipboard.writeText(n).then(function () { toast('✓ ' + T.copied); });
    });
  }

  /* ---------- sell-with-us form ---------- */
  var sell = document.querySelector('[data-sell]');
  if (sell) {
    sell.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = sell.elements;
      var msg = [T.sellHello, '', T.name + ': ' + f.name.value, T.phone + ': ' + f.phone.value, T.product + ': ' + f.product.value, '', f.about.value].join('\n');
      window.location.href = 'https://wa.me/' + MM.whatsapp + '?text=' + encodeURIComponent(msg);
    });
  }
})();
