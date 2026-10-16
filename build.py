#!/usr/bin/env python3
"""Static site generator for Makala Maalum / Featured Articles.

    python3 build.py          # build the site into docs/
    python3 build.py --pdf    # also (re)generate store PDFs with headless Chrome

Articles: content/articles/<lang>/<slug>.html  (JSON front matter in a leading <!-- --> block)
Products: content/products.json      Settings: content/site.json
"""
import json, os, re, shutil, html, sys, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'docs')
SITE = json.load(open(os.path.join(ROOT, 'content/site.json')))
PRODUCTS = json.load(open(os.path.join(ROOT, 'content/products.json')))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FONTS = ('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,300..700,0..100;'
         '1,9..144,300..700,0..100&family=Literata:ital,opsz,wght@0,7..72,400..700;1,7..72,400..600'
         '&family=Instrument+Sans:wght@400..700&display=swap')
LOGO = '91060cb46f'

PATHS = {
    'sw': {'articles': 'makala', 'store': 'duka', 'cart': 'duka/kikapu', 'about': 'kuhusu'},
    'en': {'articles': 'articles', 'store': 'store', 'cart': 'store/cart', 'about': 'about'},
}

T = {
    'sw': {
        'site': 'Makala <em>Maalum</em>', 'siteText': 'Makala Maalum',
        'tagline': 'Makala za kina zinazofafanua Imani za Msingi za Biblia — kwa lugha rahisi, kwa moyo wa ibada.',
        'home': 'Mwanzo', 'articles': 'Makala', 'store': 'Duka', 'about': 'Kuhusu', 'cart': 'Kikapu',
        'other': 'EN', 'otherName': 'English', 'theme': 'Badili mwonekano',
        'heroKicker': 'Injili Milele · Makala Maalum',
        'heroTitle': 'Neno lililo<br><em>hai</em>, kwa kina.',
        'readFeatured': 'Soma makala mpya', 'browse': 'Tazama makala zote',
        'verse': 'Neno lako ni taa ya miguu yangu, na mwanga wa njia yangu.', 'verseRef': 'Zaburi 119:105',
        'allArticles': 'Makala <em>zote</em>', 'library': 'Maktaba',
        'search': 'Tafuta makala…', 'all': 'Zote', 'noResults': 'Hakuna makala inayolingana na utafutaji wako.',
        'read': 'Soma', 'min': 'dak.', 'minRead': 'dakika {n} za kusoma', 'video': 'Video',
        'bandKicker': 'Duka la Kidijitali', 'bandTitle': 'Beba makala hizi <em>popote</em> uendapo.',
        'bandText': 'Pakua vitabu pepe (PDF) vilivyopangwa kwa ustadi — kwa ajili ya kujisomea, vikundi vya Biblia na kuchapisha.',
        'visitStore': 'Tembelea Duka',
        'by': 'Na', 'share': 'Shiriki', 'copy': 'Nakili kiungo', 'copied': 'Kiungo kimenakiliwa',
        'smaller': 'Punguza maandishi', 'bigger': 'Ongeza maandishi', 'print': 'Chapisha',
        'prev': 'Iliyotangulia', 'next': 'Inayofuata', 'related': 'Makala <em>zinazohusiana</em>',
        'translation': 'Makala hii inapatikana pia kwa Kiingereza:', 'readIn': 'Soma kwa Kiingereza →',
        'authorBio': 'Mchungaji aliyewekwa wakfu wa Kanisa la Waadventista Wasabato, mwandishi na mtengenezaji wa programu ya Imani za Msingi.',
        'guestBio': 'Makala hii imetafsiriwa na kuandaliwa kutoka Biblical Research Institute ya Kanisa la Waadventista Wasabato.',
        'play': 'Cheza video',
        'storeKicker': 'Duka · Bidhaa za Kidijitali', 'storeTitle': 'Vitabu pepe kwa ajili ya <em>kujifunza</em> Neno.',
        'storeText': 'Nunua kwa urahisi kwa M-Pesa, Mixx by Yas, Airtel Money au HaloPesa. Utapokea PDF yako kupitia WhatsApp au barua pepe.',
        'trust1': 'Malipo ya simu', 'trust2': 'Upokeaji wa haraka', 'trust3': 'Inasaidia huduma ya Injili',
        'products': 'Bidhaa <em>zote</em>', 'addToCart': 'Weka kikapuni', 'inCart': 'Kikapuni', 'buyNow': 'Nunua sasa',
        'getFree': 'Pakua bure', 'free': 'Bure', 'added': 'Imewekwa kikapuni.', 'viewCart': 'Fungua kikapu',
        'includes': 'Kilichomo', 'contents': 'Yaliyomo', 'format': 'Muundo: PDF · Inasomeka kwenye simu, kompyuta na kuchapishwa',
        'payNow': 'Lipa sasa mtandaoni', 'langBadge': {'sw': 'Kiswahili', 'en': 'English'},
        'sellKicker': 'Uza Nasi', 'sellTitle': 'Una kitabu, somo au wimbo wa kidijitali?',
        'sellText': 'Waandishi, wahubiri na wanamuziki wa Injili wanakaribishwa kuuza bidhaa zao za kidijitali hapa. Tuma maelezo nasi tutawasiliana nawe.',
        'product': 'Bidhaa', 'aboutProduct': 'Maelezo mafupi', 'sendWa': 'Tuma kwa WhatsApp',
        'sellHello': 'Habari! Ningependa kuuza bidhaa yangu kwenye duka la Makala Maalum.',
        'cartTitle': 'Kikapu <em>chako</em>', 'emptyCart': 'Kikapu chako kiko tupu kwa sasa.', 'continue': 'Endelea kununua',
        'remove': 'Ondoa', 'total': 'Jumla', 'yourDetails': 'Taarifa zako', 'name': 'Jina', 'phone': 'Namba ya simu',
        'email': 'Barua pepe', 'optional': '(si lazima)', 'txn': 'Namba ya muamala',
        'howToPay': 'Jinsi ya kulipa', 'step1': 'Lipa jumla ya kiasi kwa namba ifuatayo kwa mtandao wowote:',
        'step2': 'Andika namba ya kumbukumbu ya oda yako kama maelezo ya malipo:',
        'step3': 'Tuma oda yako kwa WhatsApp (au barua pepe). Utapokea PDF yako mara malipo yatakapothibitishwa.',
        'payName': 'Jina', 'orderRef': 'Kumbukumbu ya oda', 'sendOrderWa': 'Tuma oda kwa WhatsApp', 'sendOrderMail': 'Tuma kwa barua pepe',
        'freeReady': 'Bidhaa za bure ziko tayari kupakuliwa:', 'needDetails': 'Tafadhali jaza jina na namba ya simu.',
        'waHello': 'Habari! Ningependa kununua kutoka Duka la Makala Maalum.', 'waOrder': 'Oda',
        'privacy': 'Taarifa zako zinatumika kukamilisha oda yako tu.',
        'aboutTitle': 'Kuhusu <em>Makala Maalum</em>',
        'aboutBody': [
            'Makala Maalum ni mkusanyiko wa makala za kina zinazojibu maswali muhimu ya imani — Sabato, Uungu, unabii, ibada na pambano kuu kati ya wema na uovu — kwa kuongozwa na Biblia.',
            'Makala hizi zimeandaliwa na Mch. Almodad Amos Yaragwiller, mchungaji aliyewekwa wakfu wa Kanisa la Waadventista Wasabato na mtengenezaji wa programu ya simu ya <a href="https://play.google.com/store/apps/details?id=org.almo.imani.imanizamsingi">Imani za Msingi</a>. Lengo ni kuunganisha teknolojia na utume wa Injili ili kila mtu apate rasilimali za kujifunza Neno la Mungu.',
            'Mapato yote ya duka yanasaidia kuendeleza huduma hii ya kuandaa na kusambaza rasilimali za Biblia bure.',
        ],
        'contact': 'Wasiliana nasi', 'call': 'Piga simu',
        'footerAbout': 'Makala za kina juu ya Imani za Msingi za Biblia, kutoka huduma ya Injili Milele.',
        'explore': 'Gundua', 'connect': 'Wasiliana', 'rights': 'Haki zote zimehifadhiwa.',
        'app': 'Pakua App ya Imani za Msingi', 'notFound': 'Ukurasa haukupatikana', 'notFoundText': 'Samahani, ukurasa unaoutafuta haupo. Huenda umehamishwa.',
        'backHome': 'Rudi Mwanzo', 'top': 'Juu',
    },
    'en': {
        'site': 'Featured <em>Articles</em>', 'siteText': 'Featured Articles',
        'tagline': 'In-depth articles on the Fundamental Beliefs of the Bible — clear, careful and written with a heart of worship.',
        'home': 'Home', 'articles': 'Articles', 'store': 'Store', 'about': 'About', 'cart': 'Cart',
        'other': 'SW', 'otherName': 'Kiswahili', 'theme': 'Toggle theme',
        'heroKicker': 'Injili Milele · Featured Articles',
        'heroTitle': 'The living<br><em>Word</em>, in depth.',
        'readFeatured': 'Read the latest', 'browse': 'Browse all articles',
        'verse': 'Your word is a lamp to my feet and a light to my path.', 'verseRef': 'Psalm 119:105',
        'allArticles': 'All <em>articles</em>', 'library': 'Library',
        'search': 'Search articles…', 'all': 'All', 'noResults': 'No articles match your search.',
        'read': 'Read', 'min': 'min', 'minRead': '{n} min read', 'video': 'Video',
        'bandKicker': 'Digital Store', 'bandTitle': 'Take these articles <em>anywhere</em>.',
        'bandText': 'Download beautifully typeset PDF e-books for personal study, Bible study groups and printing.',
        'visitStore': 'Visit the Store',
        'by': 'By', 'share': 'Share', 'copy': 'Copy link', 'copied': 'Link copied',
        'smaller': 'Smaller text', 'bigger': 'Larger text', 'print': 'Print',
        'prev': 'Previous', 'next': 'Next', 'related': 'Related <em>articles</em>',
        'translation': 'This article is also available in Swahili:', 'readIn': 'Read in Kiswahili →',
        'authorBio': 'Ordained pastor of the Seventh-day Adventist Church, writer, and developer of the Imani za Msingi / SDA Fundamental Beliefs app.',
        'guestBio': 'This article is adapted from the Biblical Research Institute of the Seventh-day Adventist Church.',
        'play': 'Play video',
        'storeKicker': 'Store · Digital Products', 'storeTitle': 'E-books for deeper <em>study</em> of the Word.',
        'storeText': 'Pay easily by M-Pesa, Mixx by Yas, Airtel Money or HaloPesa. Your PDF is delivered by WhatsApp or email.',
        'trust1': 'Mobile money', 'trust2': 'Fast delivery', 'trust3': 'Supports Gospel ministry',
        'products': 'All <em>products</em>', 'addToCart': 'Add to cart', 'inCart': 'In cart', 'buyNow': 'Buy now',
        'getFree': 'Download free', 'free': 'Free', 'added': 'Added to your cart.', 'viewCart': 'View cart',
        'includes': 'What’s included', 'contents': 'Contents', 'format': 'Format: PDF · Reads on phone, computer and in print',
        'payNow': 'Pay online now', 'langBadge': {'sw': 'Kiswahili', 'en': 'English'},
        'sellKicker': 'Sell With Us', 'sellTitle': 'Have a digital book, study or song?',
        'sellText': 'Authors, preachers and Gospel musicians are welcome to sell their digital products here. Send us the details and we will get in touch.',
        'product': 'Product', 'aboutProduct': 'Short description', 'sendWa': 'Send on WhatsApp',
        'sellHello': 'Hello! I would like to sell my product in the Featured Articles store.',
        'cartTitle': 'Your <em>cart</em>', 'emptyCart': 'Your cart is empty for now.', 'continue': 'Continue shopping',
        'remove': 'Remove', 'total': 'Total', 'yourDetails': 'Your details', 'name': 'Name', 'phone': 'Phone number',
        'email': 'Email', 'optional': '(optional)', 'txn': 'Transaction ID',
        'howToPay': 'How to pay', 'step1': 'Send the total amount to this number from any network:',
        'step2': 'Use your order reference as the payment description:',
        'step3': 'Send your order by WhatsApp (or email). Your PDF is delivered as soon as payment is confirmed.',
        'payName': 'Name', 'orderRef': 'Order reference', 'sendOrderWa': 'Send order on WhatsApp', 'sendOrderMail': 'Send by email',
        'freeReady': 'Your free items are ready to download:', 'needDetails': 'Please enter your name and phone number.',
        'waHello': 'Hello! I would like to buy from the Featured Articles store.', 'waOrder': 'Order',
        'privacy': 'Your details are only used to complete your order.',
        'aboutTitle': 'About <em>Featured Articles</em>',
        'aboutBody': [
            'Featured Articles is a collection of in-depth studies answering important questions of faith — the Sabbath, the Godhead, prophecy, worship and the great controversy between good and evil — guided by Scripture.',
            'The articles are prepared by Pr. Almodad Amos Yaragwiller, an ordained pastor of the Seventh-day Adventist Church and developer of the <a href="https://play.google.com/store/apps/details?id=org.almodad.imani.sdafundamentalbeliefs">SDA Fundamental Beliefs</a> app, joining technology with the Gospel commission so that everyone can access resources for studying God’s Word.',
            'All store proceeds support this ministry of preparing and freely sharing Bible resources.',
        ],
        'contact': 'Contact us', 'call': 'Call',
        'footerAbout': 'In-depth articles on the Fundamental Beliefs of the Bible, from the Injili Milele ministry.',
        'explore': 'Explore', 'connect': 'Connect', 'rights': 'All rights reserved.',
        'app': 'Get the SDA Fundamental Beliefs app', 'notFound': 'Page not found', 'notFoundText': 'Sorry, the page you are looking for does not exist. It may have moved.',
        'backHome': 'Back home', 'top': 'Top',
    },
}

CAT_EN = {}  # categories are already language-specific in front matter

ICON = {
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    'bag': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l1 13H5L6 7Z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>',
    'moon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/></svg>',
    'book': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Z"/><path d="M4 19a2 2 0 0 1 2-2h13"/></svg>',
    'store': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9 5.5 4h13L20 9"/><path d="M4 9h16v2a3 3 0 0 1-5.3 2A3 3 0 0 1 12 14a3 3 0 0 1-2.7-1A3 3 0 0 1 4 11V9Z"/><path d="M5 14v6h14v-6"/></svg>',
    'arrow': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    'up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M6 11l6-6 6 6"/></svg>',
    'wa': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 2s.8 2.3.9 2.5c.1.2 1.6 2.5 4 3.5 1.5.6 2 .7 2.8.6.4-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></svg>',
    'fb': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M14 8h3V4h-3a4 4 0 0 0-4 4v2H8v4h2v8h4v-8h3l1-4h-4V8.5c0-.3.2-.5.5-.5Z"/></svg>',
    'link': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 14a4 4 0 0 0 5.7 0l3-3A4 4 0 0 0 13 5.3l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3A4 4 0 0 0 11 18.7l1-1"/></svg>',
    'share': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>',
    'print': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V3h12v6M6 18H4v-7h16v7h-2"/><path d="M6 14h12v7H6z"/></svg>',
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 4.5 4.5L19 7"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>',
    'bolt': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/></svg>',
    'heart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    'yt': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8ZM10 15V9l5.2 3L10 15Z"/></svg>',
    'down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12M6 11l6 6 6-6M5 20h14"/></svg>',
}


def e(s):
    return html.escape(str(s), quote=True)


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


# ------------------------------------------------------------------ content
def load_articles():
    arts = {'sw': [], 'en': []}
    for lang in arts:
        d = os.path.join(ROOT, 'content/articles', lang)
        for f in sorted(os.listdir(d)):
            if not f.endswith('.html'):
                continue
            raw = open(os.path.join(d, f), encoding='utf-8').read()
            m = re.match(r'\s*<!--(.*?)-->\s*(.*)', raw, re.S)
            meta = json.loads(m.group(1))
            meta['body'] = m.group(2).strip()
            meta['minutes'] = max(1, round(meta['words'] / 200))
            meta['has_video'] = 'data-yt=' in meta['body']
            arts[lang].append(meta)
        arts[lang].sort(key=lambda a: a['order'])
    return arts


ARTS = load_articles()


def art_path(a):
    return f"{a['lang']}/{PATHS[a['lang']]['articles']}/{a['slug']}/"


def prod_path(lang, p):
    return f"{lang}/{PATHS[lang]['store']}/{p['id']}/"


def articles_for(p):
    res = []
    for spec in p['articles'].split(','):
        lang, slug = spec.split(':')
        res += [a for a in ARTS[lang] if slug in ('*', a['slug'])]
    return res


# ------------------------------------------------------------------ layout
def cover(p, lang, root):
    cls = 'cover free' if p.get('free') else 'cover'
    top = T[lang]['free'] if p.get('free') else ('PDF · ' + T[lang]['langBadge'][p['lang']])
    return (f'<div class="{cls}" aria-hidden="true"><img src="{root}assets/img/{p["image"]}.jpg" alt="" loading="lazy">'
            f'<div class="cover-top">{e(top)}</div><div class="cover-title">{e(p["title"][lang])}</div>'
            f'<div class="cover-author">{e(SITE["author"])}</div></div>')


def price_html(p, lang):
    if not p['price']:
        return f'<span class="price free">{T[lang]["free"]}</span>'
    return f'<span class="price"><small>TSh</small>{p["price"]:,}</span>'


def page(lang, rel, title, body, *, desc='', image=None, active='', other_url=None, extra_head='', products_js=False, body_class=''):
    """Wrap body in the site shell. rel = output path relative to docs (directory, ending with /)."""
    depth = rel.count('/')
    root = '../' * depth
    t = T[lang]
    p = PATHS[lang]
    other = 'en' if lang == 'sw' else 'sw'
    other_url = other_url or f'{other}/'
    url = SITE['baseUrl'] + rel
    img = SITE['baseUrl'] + f'assets/img/{image or LOGO}.jpg'
    mm = {
        'lang': lang, 'root': root, 'cartUrl': root + p['cart'] + '/',
        'whatsapp': SITE['whatsapp'], 'email': SITE['email'],
        't': {k: v for k, v in t.items() if isinstance(v, str) and k in (
            'copied', 'play', 'free', 'inCart', 'added', 'viewCart', 'remove', 'total', 'name', 'phone', 'email',
            'txn', 'needDetails', 'waHello', 'waOrder', 'sellHello', 'product')},
    }
    if products_js:
        mm['products'] = {
            x['id']: {
                'title': x['title'][lang], 'subtitle': x['subtitle'][lang], 'price': x['price'],
                'coverHtml': cover(x, lang, root),
                'download': (root + f"downloads/{x['pdf']}.pdf") if x.get('free') else None,
            } for x in PRODUCTS
        }

    def nav(key, href, label, icon):
        cur = ' aria-current="page"' if active == key else ''
        return f'<a class="nav-{key}" href="{root}{href}"{cur}>{ICON[icon]}<span class="nav-text">{label}</span></a>'

    year = datetime.date.today().year
    articles_links = ''.join(f'<li><a href="{root}{art_path(a)}">{e(a["title"])}</a></li>' for a in ARTS[lang][:4])
    app_url = ('https://play.google.com/store/apps/details?id=org.almo.imani.imanizamsingi' if lang == 'sw'
               else 'https://play.google.com/store/apps/details?id=org.almodad.imani.sdafundamentalbeliefs')
    return f'''<!doctype html>
<html lang="{lang}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc or strip_tags(t['tagline']))}">
<meta name="theme-color" content="#12172e">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{other}" href="{SITE['baseUrl']}{other_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(t['siteText'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc or strip_tags(t['tagline']))}">
<meta property="og:image" content="{img}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/img/icon-192.png">
<link rel="apple-touch-icon" href="{root}assets/img/icon-192.png">
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/css/site.css?v={BUILD_ID}">
<script>try{{var th=localStorage.getItem('mm-theme');if(th)document.documentElement.setAttribute('data-theme',JSON.parse(th))}}catch(e){{}}</script>
{extra_head}
</head>
<body class="{body_class}">
<a class="sr-only" href="#main">Skip</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}{lang}/"><img src="{root}assets/img/icon-192.png" alt="" width="36" height="36"><span class="brand-name">{t['site']}</span></a>
    <nav class="nav" aria-label="Main">
      {nav('articles', lang + '/#makala', t['articles'], 'book')}
      {nav('store', p['store'] and lang + '/' + p['store'] + '/', t['store'], 'store')}
      <a class="lang-switch" href="{root}{other_url}" hreflang="{other}" title="{t['otherName']}">{t['other']}</a>
      <button class="icon-btn" type="button" data-theme-toggle aria-label="{t['theme']}">{ICON['moon']}</button>
      <a class="icon-btn" href="{root}{p['cart']}/" aria-label="{t['cart']}">{ICON['bag']}<span class="cart-count">0</span></a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="about-col">
      <span class="brand-name">{t['site']}</span>
      <p>{t['footerAbout']}</p>
      <a class="btn btn-ghost" href="{app_url}" target="_blank" rel="noopener">{ICON['phone']} {t['app']}</a>
    </div>
    <div>
      <h4>{t['explore']}</h4>
      <ul>
        <li><a href="{root}{lang}/">{t['home']}</a></li>
        <li><a href="{root}{lang}/#makala">{t['articles']}</a></li>
        <li><a href="{root}{lang}/{p['store']}/">{t['store']}</a></li>
        <li><a href="{root}{lang}/{p['about']}/">{t['about']}</a></li>
        <li><a href="{root}{other_url}">{t['otherName']}</a></li>
      </ul>
    </div>
    <div>
      <h4>{t['connect']}</h4>
      <ul>
        <li><a href="https://wa.me/{SITE['whatsapp']}" target="_blank" rel="noopener">WhatsApp</a></li>
        <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
        <li><a href="tel:+{SITE['whatsapp']}">{SITE['phoneDisplay']}</a></li>
        <li><a href="{SITE['youtube']}" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </div>
    <div class="legal"><span>© {year} {e(SITE['author'])}. {t['rights']}</span><span>Injili Milele</span></div>
  </div>
</footer>
<button class="back-top" type="button" aria-label="{t['top']}">{ICON['up']}</button>
<script>window.MM={json.dumps(mm, ensure_ascii=False)};</script>
<script src="{root}assets/js/app.js?v={BUILD_ID}" defer></script>
</body>
</html>
'''


def card(a, root, idx):
    t = T[a['lang']]
    num = f'{idx + 1:02d}'
    vid = f'<span class="badge video">▶ {t["video"]}</span>' if a['has_video'] else ''
    search = ' '.join([a['title'], a['category'], a['excerpt'], strip_tags(a['body'])[:4000]])
    feature = ' feature' if idx == 0 else ''
    return f'''<a class="card reveal{feature}" href="{root}{art_path(a)}" data-cat="{e(a['category'])}" data-search="{e(search)}">
  <div class="card-media"><img src="{root}assets/img/{a['card']}.jpg" alt="" loading="{'eager' if idx < 2 else 'lazy'}"></div>
  <div class="card-body"><span class="card-num" aria-hidden="true">{num}</span>
    <div class="card-meta"><span class="cat">{e(a['category'])}</span>{vid}</div>
    <h3>{e(a['title'])}</h3>
    <p>{e(a['excerpt'])}</p>
    <div class="card-foot"><span>{a['minutes']} {t['min']}</span><span class="go">{t['read']} {ICON['arrow']}</span></div>
  </div>
</a>'''


# ------------------------------------------------------------------ pages
def build_home(lang):
    t, root, arts = T[lang], '../', ARTS[lang]
    lead = arts[0]
    cats = []
    for a in arts:
        if a['category'] not in cats:
            cats.append(a['category'])
    chips = f'<button class="chip" type="button" data-filter="all" aria-pressed="true">{t["all"]}</button>' + ''.join(
        f'<button class="chip" type="button" data-filter="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in cats)
    featured_products = [p for p in PRODUCTS if p.get('featured') or p.get('free')][:3]
    books = ''.join(cover(p, lang, root) for p in featured_products)
    body = f'''
<section class="hero">
  <div class="hero-bg"><img src="{root}assets/img/{lead['image']}.jpg" alt=""></div>
  <div class="wrap">
    <span class="eyebrow rise">{t['heroKicker']}</span>
    <h1 class="rise d1">{t['heroTitle']}</h1>
    <p class="lede rise d2">{t['tagline']}</p>
    <div class="hero-actions rise d3">
      <a class="btn btn-gold" href="{root}{art_path(lead)}">{t['readFeatured']} {ICON['arrow']}</a>
      <a class="btn btn-ghost" href="#makala">{t['browse']}</a>
    </div>
    <p class="hero-verse rise d4"><b>{t['verseRef']}</b><span>“{t['verse']}”</span></p>
  </div>
</section>
<section class="section" id="makala">
  <div class="wrap">
    <div class="section-head">
      <div><span class="kicker">{t['library']} · {len(arts)}</span><h2>{t['allArticles']}</h2></div>
    </div>
    <div class="toolbar">
      <label class="search">{ICON['search']}<span class="sr-only">{t['search']}</span><input type="search" data-search placeholder="{t['search']}" autocomplete="off"></label>
      <div class="chips" role="group">{chips}</div>
    </div>
    <div class="grid" data-articles>
      {''.join(card(a, root, i) for i, a in enumerate(arts))}
    </div>
    <p class="empty">{t['noResults']}</p>
  </div>
</section>
<section class="wrap">
  <div class="band reveal">
    <div>
      <span class="kicker">{t['bandKicker']}</span>
      <h2>{t['bandTitle']}</h2>
      <p>{t['bandText']}</p>
      <a class="btn btn-gold" href="{root}{lang}/{PATHS[lang]['store']}/">{ICON['store']} {t['visitStore']}</a>
    </div>
    <div class="band-books" style="font-size:16px">{books}</div>
  </div>
</section>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(f'{lang}/', page(lang, f'{lang}/', f"{t['siteText']} — {strip_tags(t['heroTitle'].replace('<br>', ' '))}", body,
                           image=lead['image'], active='articles', other_url=f'{other}/', products_js=True))


def build_article(a, i):
    lang, t = a['lang'], T[a['lang']]
    rel = art_path(a)
    root = '../' * rel.count('/')
    arts = ARTS[lang]
    other = 'en' if lang == 'sw' else 'sw'
    twin = next((b for b in ARTS[other] if a['pair'] and b['pair'] == a['pair']), None)
    other_url = art_path(twin) if twin else f'{other}/'
    prev_a = arts[i - 1] if i > 0 else None
    next_a = arts[i + 1] if i + 1 < len(arts) else None
    related = [b for b in arts if b is not a and b['category'] == a['category']]
    related += [b for b in arts if b is not a and b not in related]
    related = related[:3]
    guest = 'Rodr' in a['author']
    initials = ''.join(w[0] for w in a['author'].replace('Pr. ', '').replace('Mch. ', '').split()[:2])
    url = SITE['baseUrl'] + rel
    share_text = f"{a['title']} — {url}"
    body_html = a['body'].replace('{{root}}', root)
    trans = (f'<p class="translation">{ICON["book"]}<span>{t["translation"]} <a href="{root}{art_path(twin)}" hreflang="{other}">{t["readIn"]}</a></span></p>'
             if twin else '')
    pager = '<nav class="pager">'
    if prev_a:
        pager += f'<a href="{root}{art_path(prev_a)}"><small>← {t["prev"]}</small><b>{e(prev_a["title"])}</b></a>'
    if next_a:
        pager += f'<a class="next" href="{root}{art_path(next_a)}"><small>{t["next"]} →</small><b>{e(next_a["title"])}</b></a>'
    pager += '</nav>'
    ld = {
        '@context': 'https://schema.org', '@type': 'Article', 'headline': a['title'], 'inLanguage': lang,
        'author': {'@type': 'Person', 'name': a['author']}, 'image': SITE['baseUrl'] + f"assets/img/{a['image']}.jpg",
        'description': a['excerpt'], 'mainEntityOfPage': url,
    }
    body = f'''
<div class="progress" aria-hidden="true"></div>
<header class="article-hero">
  <img class="bg" src="{root}assets/img/{a['image']}.jpg" alt="">
  <div class="wrap">
    <nav class="crumbs rise" aria-label="Breadcrumb"><a href="{root}{lang}/">{t['home']}</a><span>/</span><a href="{root}{lang}/#makala">{t['articles']}</a><span>/</span><span>{e(a['category'])}</span></nav>
    <h1 class="rise d1">{e(a['title'])}</h1>
    <div class="byline rise d2">
      <span class="author"><span class="avatar">{e(initials)}</span>{e(a['author'])}</span>
      <span class="dot"></span><span>{t['minRead'].format(n=a['minutes'])}</span>
      <span class="dot"></span><span>{e(a['category'])}</span>
    </div>
  </div>
</header>
<div class="reader-tools">
  <div class="wrap">
    <button class="tool" type="button" data-size="-" aria-label="{t['smaller']}">A−</button>
    <button class="tool" type="button" data-size="+" aria-label="{t['bigger']}">A+</button>
    <span class="spacer"></span>
    <a class="tool" href="https://wa.me/?text={e(quote(share_text))}" target="_blank" rel="noopener" aria-label="WhatsApp">{ICON['wa']}</a>
    <button class="tool" type="button" data-share="native" aria-label="{t['share']}">{ICON['share']}</button>
  </div>
</div>
<article class="wrap">
  <div class="prose">
    {trans}
    {body_html}
  </div>
  <div class="article-end">
    <div class="share">
      <span>{t['share']}</span>
      <a class="btn btn-wa" href="https://wa.me/?text={e(quote(share_text))}" target="_blank" rel="noopener">{ICON['wa']} WhatsApp</a>
      <a class="btn btn-line" href="https://www.facebook.com/sharer/sharer.php?u={e(quote(url))}" target="_blank" rel="noopener">{ICON['fb']} Facebook</a>
      <button class="btn btn-line" type="button" data-share="copy">{ICON['link']} {t['copy']}</button>
    </div>
    <div class="author-box">
      <span class="avatar">{e(initials)}</span>
      <div><h4>{e(a['author'])}</h4><p>{t['guestBio'] if guest else t['authorBio']}</p></div>
    </div>
    {pager}
  </div>
</article>
<section class="wrap" style="padding-top:8px">
  <div class="section-head"><h2>{t['related']}</h2></div>
  <div class="grid">{''.join(card(b, root, arts.index(b)).replace(' feature', '') for b in related)}</div>
</section>'''
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    write(rel, page(lang, rel, f"{a['title']} · {t['siteText']}", body, desc=a['excerpt'], image=a['image'],
                    active='articles', other_url=other_url, extra_head=head, products_js=True))


def quote(s):
    from urllib.parse import quote as q
    return q(s, safe='')


def build_store(lang):
    t, p = T[lang], PATHS[lang]
    rel = f"{lang}/{p['store']}/"
    root = '../../'
    items = []
    for x in PRODUCTS:
        btn = (f'<button class="btn btn-gold add" type="button" data-buy="{x["id"]}">{ICON["down"]} {t["getFree"]}</button>' if x.get('free')
               else f'<button class="btn btn-ink add" type="button" data-add="{x["id"]}">{t["addToCart"]}</button>')
        items.append(f'''<article class="product reveal">
  <a class="cover-link" href="{root}{prod_path(lang, x)}">{cover(x, lang, root)}</a>
  <div class="card-meta"><span class="cat">PDF</span><span class="badge">{T[lang]['langBadge'][x['lang']]}</span></div>
  <h3><a href="{root}{prod_path(lang, x)}">{e(x['title'][lang])}</a></h3>
  <p class="sub">{e(x['subtitle'][lang])}</p>
  <div class="row">{price_html(x, lang)}{btn}</div>
</article>''')
    body = f'''
<section class="store-hero">
  <div class="wrap">
    <span class="eyebrow rise">{t['storeKicker']}</span>
    <h1 class="rise d1">{t['storeTitle']}</h1>
    <p class="rise d2">{t['storeText']}</p>
    <div class="trust rise d3"><span>{ICON['phone']} {t['trust1']}</span><span>{ICON['bolt']} {t['trust2']}</span><span>{ICON['heart']} {t['trust3']}</span></div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head"><div><span class="kicker">{t['store']} · {len(PRODUCTS)}</span><h2>{t['products']}</h2></div>
      <a class="btn btn-line" href="{root}{p['cart']}/">{ICON['bag']} {t['cart']}</a></div>
    <div class="products">{''.join(items)}</div>
  </div>
</section>
<section class="wrap">
  <div class="sell reveal">
    <div>
      <span class="kicker">{t['sellKicker']}</span>
      <h2>{t['sellTitle']}</h2>
      <p>{t['sellText']}</p>
    </div>
    <form data-sell>
      <div class="field"><label for="s-name">{t['name']}</label><input id="s-name" name="name" required autocomplete="name"></div>
      <div class="field"><label for="s-phone">{t['phone']}</label><input id="s-phone" name="phone" type="tel" required autocomplete="tel"></div>
      <div class="field"><label for="s-product">{t['product']}</label><input id="s-product" name="product" required></div>
      <div class="field"><label for="s-about">{t['aboutProduct']}</label><textarea id="s-about" name="about" rows="3"></textarea></div>
      <button class="btn btn-wa btn-block" type="submit">{ICON['wa']} {t['sendWa']}</button>
    </form>
  </div>
</section>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{t['store']} · {t['siteText']}", body, desc=strip_tags(t['storeText']), active='store',
                    other_url=f"{other}/{PATHS[other]['store']}/", products_js=True))

    for x in PRODUCTS:
        build_product(lang, x)


def build_product(lang, x):
    t = T[lang]
    rel = prod_path(lang, x)
    root = '../../../'
    contents = ''.join(f'<li><a href="{root}{art_path(a)}">{e(a["title"])}</a></li>' for a in articles_for(x))
    includes = ''.join(f'<li>{ICON["check"]}<span>{e(i)}</span></li>' for i in x['includes'][lang])
    if x.get('free'):
        actions = (f'<a class="btn btn-gold btn-block" href="{root}downloads/{x["pdf"]}.pdf" download>{ICON["down"]} {t["getFree"]}</a>')
    else:
        actions = (f'<button class="btn btn-gold btn-block" type="button" data-buy="{x["id"]}">{t["buyNow"]} {ICON["arrow"]}</button>'
                   f'<button class="btn btn-line btn-block" type="button" data-add="{x["id"]}">{t["addToCart"]}</button>')
        if x.get('paymentUrl'):
            actions += f'<a class="btn btn-ink btn-block" href="{e(x["paymentUrl"])}" target="_blank" rel="noopener">{t["payNow"]}</a>'
    body = f'''
<div class="wrap">
  <nav class="crumbs" style="color:var(--muted);padding-top:28px" aria-label="Breadcrumb"><a style="color:var(--gold)" href="{root}{lang}/{PATHS[lang]['store']}/">{t['store']}</a><span>/</span><span>{e(x['title'][lang])}</span></nav>
  <div class="product-page">
    <div class="stage rise">{cover(x, lang, root)}</div>
    <div>
      <div class="card-meta rise"><span class="cat">PDF · {T[lang]['langBadge'][x['lang']]}</span></div>
      <h1 class="rise d1">{e(x['title'][lang])}</h1>
      <p class="lead rise d2">{e(x['description'][lang])}</p>
      <div class="buybox rise d3">
        {price_html(x, lang)}
        {actions}
        <span class="note">{t['format']}</span>
      </div>
      <h4 class="kicker">{t['includes']}</h4>
      <ul class="includes">{includes}</ul>
      <div class="contents"><h4>{t['contents']}</h4><ol>{contents}</ol></div>
    </div>
  </div>
</div>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{x['title'][lang]} · {t['store']}", body, desc=x['description'][lang], image=x['image'],
                    active='store', other_url=prod_path(other, x), products_js=True))


def build_cart(lang):
    t, p = T[lang], PATHS[lang]
    rel = f"{lang}/{p['cart']}/"
    root = '../../../'
    pay = SITE['payment']
    methods = ''.join(f'<span>{e(m)}</span>' for m in pay['methods'])
    body = f'''
<div class="wrap" data-checkout>
  <div class="section-head" style="margin:40px 0 0"><div><span class="kicker">{t['store']}</span><h2>{t['cartTitle']}</h2></div></div>
  <div class="panel empty-cart" data-empty hidden>
    <p>{t['emptyCart']}</p>
    <a class="btn btn-gold" href="{root}{lang}/{p['store']}/">{t['continue']}</a>
  </div>
  <div class="checkout" data-filled>
    <div class="stack">
      <div class="panel">
        <div data-lines></div>
        <div class="totals"><span>{t['total']}</span><span class="price" data-total></span></div>
      </div>
      <div class="panel" data-free hidden>
        <p style="margin-top:0">{t['freeReady']}</p>
        <div class="stack"></div>
      </div>
      <a class="btn btn-line" href="{root}{lang}/{p['store']}/">← {t['continue']}</a>
    </div>
    <div class="stack">
      <form class="panel" onsubmit="return false">
        <h2>{t['yourDetails']}</h2>
        <div class="field"><label for="c-name">{t['name']}</label><input id="c-name" name="name" autocomplete="name" required></div>
        <div class="field"><label for="c-phone">{t['phone']}</label><input id="c-phone" name="phone" type="tel" autocomplete="tel" placeholder="07XX XXX XXX" required></div>
        <div class="field"><label for="c-email">{t['email']} <span class="note">{t['optional']}</span></label><input id="c-email" name="email" type="email" autocomplete="email"></div>
        <div data-pay>
          <h2 style="margin-top:10px">{t['howToPay']}</h2>
          <ol class="steps">
            <li><div>{t['step1']}
              <div class="paybox"><span class="num">{e(pay['number'])}</span><span>{t['payName']}: <b>{e(pay['name'])}</b></span><div class="methods">{methods}</div>
              <button class="btn btn-line" type="button" data-copy-num="{e(pay['number'].replace(' ', ''))}" style="justify-self:start;padding:8px 14px">{ICON['link']} {t['copy']}</button></div></div></li>
            <li><div>{t['step2']} <div class="paybox"><span>{t['orderRef']}</span><span class="ref" data-ref></span></div></div></li>
            <li><div>{t['step3']}</div></li>
          </ol>
          <div class="field"><label for="c-txn">{t['txn']} <span class="note">{t['optional']}</span></label><input id="c-txn" name="txn" placeholder="e.g. 8GH3K2LQ"></div>
        </div>
        <div class="stack">
          <button class="btn btn-wa btn-block" type="button" data-send-wa>{ICON['wa']} {t['sendOrderWa']}</button>
          <button class="btn btn-line btn-block" type="button" data-send-mail>{ICON['mail']} {t['sendOrderMail']}</button>
        </div>
        <p class="note">{t['privacy']}</p>
      </form>
    </div>
  </div>
</div>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{strip_tags(t['cartTitle'])} · {t['siteText']}", body, active='store',
                    other_url=f"{other}/{PATHS[other]['cart']}/", products_js=True,
                    extra_head='<meta name="robots" content="noindex">'))


def build_about(lang):
    t, p = T[lang], PATHS[lang]
    rel = f"{lang}/{p['about']}/"
    root = '../../'
    paras = ''.join(f'<p>{x}</p>' for x in t['aboutBody'])
    body = f'''
<div class="wrap">
  <div class="about">
    <span class="kicker rise">{t['about']}</span>
    <h1 class="rise d1">{t['aboutTitle']}</h1>
    <div class="ornament">✦</div>
    {paras}
    <h2 style="font-family:var(--display);font-weight:500;margin-top:40px">{t['contact']}</h2>
    <div class="contact-cards">
      <a href="https://wa.me/{SITE['whatsapp']}" target="_blank" rel="noopener">{ICON['wa']}<span>WhatsApp<small>{SITE['phoneDisplay']}</small></span></a>
      <a href="mailto:{SITE['email']}">{ICON['mail']}<span>{t['email']}<small>{SITE['email']}</small></span></a>
      <a href="tel:+{SITE['whatsapp']}">{ICON['phone']}<span>{t['call']}<small>{SITE['phoneDisplay']}</small></span></a>
      <a href="{SITE['youtube']}" target="_blank" rel="noopener">{ICON['yt']}<span>YouTube<small>Pr. Almodad Amos</small></span></a>
    </div>
  </div>
</div>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{strip_tags(t['aboutTitle'])}", body, other_url=f"{other}/{PATHS[other]['about']}/"))


def build_root():
    lead = ARTS['sw'][0]
    gate = f'''<!doctype html>
<html lang="sw">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Makala Maalum · Featured Articles</title>
<meta name="description" content="Makala za kina juu ya Imani za Msingi za Biblia · In-depth articles on the Fundamental Beliefs of the Bible.">
<meta name="theme-color" content="#12172e">
<meta property="og:title" content="Makala Maalum · Featured Articles">
<meta property="og:image" content="{SITE['baseUrl']}assets/img/{lead['image']}.jpg">
<link rel="icon" href="assets/img/icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/css/site.css?v={BUILD_ID}">
<script>
  // Remember the reader's language; first visit picks by browser language.
  (function () {{
    var q = new URLSearchParams(location.search).get('lang');
    var saved = null;
    try {{ saved = localStorage.getItem('mm-lang'); }} catch (e) {{}}
    var pick = q || saved;
    if (pick === 'sw' || pick === 'en') location.replace(pick + '/');
  }})();
  function remember(l) {{ try {{ localStorage.setItem('mm-lang', l); }} catch (e) {{}} }}
</script>
</head>
<body>
<main class="lang-gate">
  <img class="bg" src="assets/img/{lead['image']}.jpg" alt="">
  <div>
    <img class="logo rise" src="assets/img/icon-192.png" alt="Injili Milele">
    <h1 class="rise d1">Makala <em>Maalum</em></h1>
    <p class="rise d2">Makala za kina juu ya Imani za Msingi za Biblia.<br><i>In-depth articles on the Fundamental Beliefs of the Bible.</i></p>
    <div class="choices rise d3">
      <a class="btn btn-gold" href="sw/" onclick="remember('sw')">Kiswahili {ICON['arrow']}</a>
      <a class="btn btn-ghost" href="en/" onclick="remember('en')">English {ICON['arrow']}</a>
    </div>
  </div>
</main>
</body>
</html>'''
    write('', gate)

    nf = page('sw', '', 'Ukurasa haukupatikana · Page not found', f'''
<div class="wrap about" style="text-align:center">
  <span class="kicker">404</span>
  <h1>{T['sw']['notFound']}</h1>
  <p>{T['sw']['notFoundText']}<br><i>{T['en']['notFoundText']}</i></p>
  <p><a class="btn btn-gold" href="{SITE['baseUrl']}sw/">{T['sw']['backHome']}</a> <a class="btn btn-line" href="{SITE['baseUrl']}en/">{T['en']['backHome']}</a></p>
</div>''')
    # 404 is served from any depth: use absolute URLs
    nf = nf.replace('href="sw/', f'href="{SITE["baseUrl"]}sw/').replace('href="en/', f'href="{SITE["baseUrl"]}en/') \
        .replace('href="assets/', f'href="{SITE["baseUrl"]}assets/').replace('src="assets/', f'src="{SITE["baseUrl"]}assets/') \
        .replace('href="manifest', f'href="{SITE["baseUrl"]}manifest')
    with open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8') as f:
        f.write(nf)


# ------------------------------------------------------------------ files
WRITTEN = []


def write(rel, content):
    d = os.path.join(OUT, rel)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)
    WRITTEN.append(rel)


def statics():
    for sub in ('css', 'js'):
        shutil.copytree(os.path.join(ROOT, 'src', sub), os.path.join(OUT, 'assets', sub), dirs_exist_ok=True)
    shutil.copytree(os.path.join(ROOT, 'assets/img'), os.path.join(OUT, 'assets/img'), dirs_exist_ok=True)
    dl = os.path.join(ROOT, 'downloads')
    if os.path.isdir(dl):
        shutil.copytree(dl, os.path.join(OUT, 'downloads'), dirs_exist_ok=True)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    json.dump({
        'name': 'Makala Maalum · Featured Articles', 'short_name': 'Makala Maalum',
        'start_url': './', 'display': 'standalone', 'background_color': '#12172e', 'theme_color': '#12172e',
        'icons': [{'src': 'assets/img/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': 'assets/img/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}],
    }, open(os.path.join(OUT, 'manifest.webmanifest'), 'w'), indent=1)
    urls = ''.join(f'<url><loc>{SITE["baseUrl"]}{r}</loc></url>' for r in WRITTEN if '/cart/' not in r and 'kikapu' not in r)
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE["baseUrl"]}sitemap.xml\n')


# ------------------------------------------------------------------ PDFs
STUDY_QUESTIONS = {
    'sabato-kivuli-cha-mambo-yajayo': [
        'Kwa mujibu wa Mwanzo 2:1–3, Sabato ya siku ya saba ilianzishwa lini, na nani?',
        'Ni mambo gani mawili makuu ambayo Sabato ya kila juma inatukumbusha? (Kutoka 20:11; Kumbukumbu 5:15)',
        'Kuna tofauti gani kati ya Sabato ya uumbaji na sabato za sikukuu zilizotajwa katika Walawi 23?',
        'Wakolosai 2:16–17 inazungumzia sabato zipi? Kwa nini hizo ndizo “kivuli cha mambo yajayo”?',
        'Mfano wa Yesu na mitume (Luka 4:16; Matendo 17:2) unatufundisha nini kuhusu Sabato leo?',
    ],
    'kalenda-ya-gregory-na-sabato': [
        'Mabadiliko ya kalenda ya mwaka 1582 yaliathiri tarehe za mwezi au mzunguko wa siku za juma? Eleza.',
        'Majina ya siku ya saba katika lugha mbalimbali za dunia yanathibitishaje Sabato ya Biblia?',
        'Isaya 66:22–23 inatufundisha nini kuhusu Sabato katika nchi mpya?',
        'Mfuatano wa Ijumaa, Sabato na Jumapili katika Luka 23:54–24:1 unatusaidiaje kuitambua Sabato leo?',
        'Utamweleza vipi rafiki yako kwa upole na hekima kwamba Sabato haijapotea?',
    ],
}


def build_pdfs():
    """Render each product to PDF with headless Chrome. Paid -> store-private/, free -> downloads/."""
    tmp = os.path.join(ROOT, '.pdf-build')
    os.makedirs(tmp, exist_ok=True)
    for x in PRODUCTS:
        lang = x['lang']
        arts = articles_for(x)
        study = x['id'] == 'sabato-somo'
        toc = ''.join(f'<li><a href="#a{i}">{e(a["title"])}</a><span>{e(a["author"])}</span></li>' for i, a in enumerate(arts))
        parts = []
        for i, a in enumerate(arts):
            body = re.sub(r'<div class="video" data-yt="([^"]+)" data-title="([^"]*)"></div>',
                          r'<p class="vid">▶ YouTube: <a href="https://youtu.be/\1">\2</a></p>', a['body'])
            body = body.replace('{{root}}', ROOT + '/')
            q = ''
            if study and a['slug'] in STUDY_QUESTIONS:
                q = '<section class="qs"><h3>Maswali ya Kujadili</h3><ol>' + ''.join(
                    f'<li>{e(s)}<div class="lines"></div></li>' for s in STUDY_QUESTIONS[a['slug']]) + '</ol></section>'
            parts.append(f'''<section class="art" id="a{i}">
<img class="hero" src="file://{ROOT}/assets/img/{a['image']}.jpg">
<div class="cat">{e(a['category'])}</div>
<h1>{e(a['title'])}</h1>
<div class="by">{e(a['author'])}</div>
<div class="prose">{body}</div>{q}</section>''')
        is_sw = x['lang'] == 'sw' and not x.get('free')
        toc_h = 'Yaliyomo' if x['lang'] == 'sw' else 'Contents'
        doc = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS}">
<style>
@page {{ size: A5; margin: 18mm 16mm 20mm; }}
@page :first {{ margin: 0; }}
body {{ font-family: Literata, Georgia, serif; font-size: 10.5pt; line-height: 1.6; color: #1c2033; margin: 0; }}
.cover {{ height: 210mm; width: 148mm; position: relative; color: #f6efe0; background: #12172e; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; justify-content: space-between; padding: 22mm 16mm 18mm 20mm; box-sizing: border-box; }}
.cover img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: .55; z-index: 0; }}
.cover::before {{ content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(18,23,46,.15), rgba(18,23,46,.95) 72%); z-index: 1; }}
.cover > * {{ position: relative; z-index: 2; }}
.cover .k {{ font-family: "Instrument Sans", sans-serif; letter-spacing: .25em; text-transform: uppercase; font-size: 8pt; color: #f1dcae; }}
.cover h1 {{ font-family: Fraunces, serif; font-weight: 400; font-size: 30pt; line-height: 1.02; margin: 0 0 8mm; letter-spacing: -.02em; }}
.cover p {{ font-size: 11pt; color: #ddd4c2; margin: 0 0 10mm; }}
.cover .a {{ font-family: "Instrument Sans", sans-serif; letter-spacing: .16em; text-transform: uppercase; font-size: 8pt; }}
.toc {{ page-break-after: always; }}
.toc h2 {{ font-family: Fraunces, serif; font-weight: 400; font-size: 24pt; margin: 0 0 6mm; }}
.toc ol {{ padding-left: 5mm; }} .toc li {{ margin: 0 0 4mm; }} .toc li::marker {{ color: #b8862f; font-family: Fraunces, serif; }}
.toc a {{ color: inherit; text-decoration: none; font-family: Fraunces, serif; font-size: 12pt; display: block; }}
.toc span {{ font-size: 8.5pt; color: #5d6175; }}
.art {{ page-break-before: always; }}
.art .hero {{ width: 100%; height: 48mm; object-fit: cover; border-radius: 3mm; }}
.cat {{ font-family: "Instrument Sans", sans-serif; text-transform: uppercase; letter-spacing: .2em; font-size: 7.5pt; color: #b8862f; margin: 6mm 0 2mm; font-weight: 700; }}
.art h1 {{ font-family: Fraunces, serif; font-weight: 400; font-size: 20pt; line-height: 1.1; margin: 0 0 3mm; letter-spacing: -.01em; }}
.by {{ font-family: "Instrument Sans", sans-serif; font-size: 8.5pt; color: #5d6175; margin-bottom: 6mm; }}
.prose h2 {{ font-family: Fraunces, serif; font-weight: 500; font-size: 13pt; margin: 6mm 0 2mm; page-break-after: avoid; }}
.prose p {{ margin: 0 0 3mm; text-align: justify; hyphens: auto; }}
.prose > p:first-of-type::first-letter {{ float: left; font-family: Fraunces, serif; font-size: 34pt; line-height: .85; color: #b8862f; margin: 1mm 1.5mm 0 0; }}
.prose blockquote {{ margin: 4mm 0; padding: 3mm 4mm; background: #f3ecdd; border-left: 2px solid #b8862f; font-style: italic; page-break-inside: avoid; }}
.prose blockquote p {{ margin: 0; }}
.prose img {{ width: 100%; border-radius: 2mm; margin: 3mm 0; }}
.prose a {{ color: #4257b8; }}
.prose .dl a {{ color: #4257b8; }}
.vid {{ font-family: "Instrument Sans", sans-serif; font-size: 9pt; background: #f3ecdd; padding: 3mm; border-radius: 2mm; }}
.qs {{ margin-top: 8mm; padding: 5mm; border: 1px solid #e3d9c4; border-radius: 3mm; page-break-inside: avoid; }}
.qs h3 {{ font-family: Fraunces, serif; font-weight: 500; margin: 0 0 3mm; color: #b8862f; }}
.qs li {{ margin-bottom: 3mm; }} .qs .lines {{ height: 12mm; border-bottom: 1px dotted #c9bfa9; }}
.colophon {{ page-break-before: always; text-align: center; padding-top: 50mm; font-size: 9pt; color: #5d6175; }}
.colophon b {{ font-family: Fraunces, serif; font-size: 14pt; color: #1c2033; font-weight: 500; display: block; margin-bottom: 3mm; }}
</style></head><body>
<section class="cover"><img src="file://{ROOT}/assets/img/{x['image']}.jpg">
<div class="k">Injili Milele · PDF</div>
<div><h1>{e(x['title'][x['lang']])}</h1><p>{e(x['subtitle'][x['lang']])}</p><div class="a">{e(SITE['author'])}</div></div></section>
<section class="toc"><h2>{toc_h}</h2><ol>{toc}</ol></section>
{''.join(parts)}
<section class="colophon"><b>{e(x['title'][x['lang']])}</b>
© {datetime.date.today().year} {e(SITE['author'])} · Injili Milele<br>{SITE['baseUrl']}<br>WhatsApp {SITE['phoneDisplay']} · {SITE['email']}</section>
</body></html>'''
        src = os.path.join(tmp, x['id'] + '.html')
        open(src, 'w', encoding='utf-8').write(doc)
        dest_dir = os.path.join(ROOT, 'downloads' if x.get('free') else 'store-private')
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, x['pdf'] + '.pdf')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files',
                        '--virtual-time-budget=15000', f'--print-to-pdf={dest}', 'file://' + src],
                       check=True, capture_output=True, timeout=180)
        print('pdf', os.path.relpath(dest, ROOT), os.path.getsize(dest) // 1024, 'KB')
    shutil.rmtree(tmp, ignore_errors=True)


BUILD_ID = datetime.datetime.now().strftime('%Y%m%d%H%M')


def main():
    if '--pdf' in sys.argv:
        build_pdfs()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for lang in ('sw', 'en'):
        build_home(lang)
        for i, a in enumerate(ARTS[lang]):
            build_article(a, i)
        build_store(lang)
        build_cart(lang)
        build_about(lang)
    build_root()
    statics()
    print(f'built {len(WRITTEN)} pages -> docs/')


if __name__ == '__main__':
    main()
