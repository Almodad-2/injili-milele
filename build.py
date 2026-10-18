#!/usr/bin/env python3
"""Static site generator for Injili Milele (articles, PDFs, video, audio and links, with a digital store).

    python3 build.py                        # build the site into docs/
    .venv/bin/python build.py --pdf         # also (re)generate every PDF, preview and page thumbnail
    .venv/bin/python build.py --pdf --upload   # ...and upload changed PDFs to the payments KV store

Articles: content/articles/<lang>/<slug>.html  (JSON front matter in a leading <!-- --> block)
Products: content/products.json      Settings: content/site.json
"""
import json, os, re, shutil, html, sys, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'docs')
SITE = json.load(open(os.path.join(ROOT, 'content/site.json')))
PRODUCTS = json.load(open(os.path.join(ROOT, 'content/products.json')))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FONTS = ('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800'
         '&family=Fira+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&display=swap')
LOGO = '91060cb46f'
ART = '<div class="aurora"><span></span><span></span><span></span><span></span></div><div class="grid-lines"></div>'  # landing background

PATHS = {
    'sw': {'articles': 'makala', 'store': 'duka', 'cart': 'duka/kikapu', 'about': 'kuhusu', 'thanks': 'duka/asante'},
    'en': {'articles': 'articles', 'store': 'store', 'cart': 'store/cart', 'about': 'about', 'thanks': 'store/thank-you'},
}

T = {
    'sw': {
        'site': 'Injili <em>Milele</em>', 'siteText': 'Injili Milele',
        'tagline': 'Makala za kina zinazofafanua Imani za Msingi za Biblia — kwa lugha rahisi, kwa moyo wa ibada.',
        'home': 'Mwanzo', 'articles': 'Maktaba', 'store': 'Dukani', 'about': 'Kuhusu', 'cart': 'Kikapu',
        'other': 'EN', 'otherName': 'English', 'theme': 'Badili mwonekano',
        'heroKicker': 'Makala · Vitabu · Video · Sauti',
        'heroTitle': 'Neno lililo <em>hai</em>,<br>kwa kina.',
        'latest': 'Makala mpya', 'readFeatured': 'Soma makala mpya', 'browse': 'Tazama makala zote', 'scroll': 'Shuka chini',
        'verse': 'Neno lako ni taa ya miguu yangu, na mwanga wa njia yangu.', 'verseRef': 'Zaburi 119:105',
        'allArticles': 'Makala, vitabu <em>na zaidi</em>', 'library': 'Maktaba',
        'search': 'Tafuta katika maktaba…', 'all': 'Zote', 'noResults': 'Hakuna makala inayolingana na utafutaji wako.',
        'read': 'Soma', 'min': 'dak.', 'minRead': 'dakika {n} za kusoma', 'video': 'Video',
        'bandKicker': 'Duka la Kidijitali', 'bandTitle': 'Beba makala hizi <em>popote</em> uendapo.',
        'bandText': 'Kila makala ni PDF iliyopangwa kwa ustadi — kwa ajili ya kujisomea, vikundi vya Biblia na kuchapisha.',
        'visitStore': 'Tembelea Duka',
        'by': 'Na', 'share': 'Shiriki', 'copy': 'Nakili kiungo', 'copied': 'Kiungo kimenakiliwa',
        'smaller': 'Punguza maandishi', 'bigger': 'Ongeza maandishi', 'print': 'Chapisha',
        'prev': 'Iliyotangulia', 'next': 'Inayofuata', 'related': 'Makala <em>zinazohusiana</em>',
        'translation': 'Makala hii inapatikana pia kwa Kiingereza:', 'readIn': 'Soma kwa Kiingereza →',
        'authorBio': 'Mchungaji aliyewekwa wakfu wa Kanisa la Waadventista Wasabato, mwandishi na mtengenezaji wa programu ya Imani za Msingi.',
        'guestBio': 'Makala hii imetafsiriwa na kuandaliwa kutoka Biblical Research Institute ya Kanisa la Waadventista Wasabato.',
        'play': 'Cheza video',
        'storeKicker': 'Dukani · Bidhaa za Kidijitali', 'storeTitle': 'Vitabu pepe kwa ajili ya <em>kujifunza</em> Neno.',
        'storeText': 'Nunua kwa urahisi kwa M-Pesa, Mixx by Yas, Airtel Money au HaloPesa. Utapokea PDF yako kupitia WhatsApp au barua pepe.',
        'trust1': 'Malipo ya simu', 'trust2': 'Upokeaji wa haraka', 'trust3': 'Inasaidia huduma ya Injili',
        'products': 'Bidhaa <em>zote</em>', 'addToCart': 'Weka kikapuni', 'inCart': 'Kikapuni', 'buyNow': 'Nunua sasa',
        'getFree': 'Pakua bure', 'free': 'Bure', 'added': 'Imewekwa kikapuni.', 'viewCart': 'Fungua kikapu',
        'includes': 'Kilichomo', 'contents': 'Yaliyomo', 'format': 'Muundo: PDF · Inasomeka kwenye simu, kompyuta na kuchapishwa',
        'payNow': 'Lipa sasa mtandaoni', 'langBadge': {'sw': 'Kiswahili', 'en': 'English'},
        'sellKicker': 'Uza Nasi', 'sellTitle': 'Una kitabu, somo au wimbo wa kidijitali?',
        'sellText': 'Waandishi, wahubiri na wanamuziki wa Injili wanakaribishwa kuuza bidhaa zao za kidijitali hapa. Tuma maelezo nasi tutawasiliana nawe.',
        'product': 'Bidhaa', 'aboutProduct': 'Maelezo mafupi', 'sendWa': 'Tuma kwa WhatsApp',
        'sellHello': 'Habari! Ningependa kuuza bidhaa yangu kwenye duka la Injili Milele.',
        'coupon': 'Msimbo wa punguzo', 'apply': 'Tumia', 'couponOk': 'Punguzo limetumika!', 'couponBad': 'Msimbo huu si sahihi.',
        'couponExpired': 'Msimbo huu umekwisha muda wake.', 'couponUsed': 'Msimbo huu umeshatumika mara zote zilizoruhusiwa.',
        'couponNotFor': 'Msimbo huu hauhusiani na bidhaa zilizo kikapuni.', 'discount': 'Punguzo', 'subtotal': 'Jumla ndogo',
        'checking': 'Inakagua…', 'sending': 'Inatuma…', 'unavailable': 'Haipatikani kwa sasa',
        'haveCoupon': 'Una msimbo wa punguzo?',
        'emailWhy': '(tutakutumia vitabu hapa)', 'payPesapal': 'Lipa sasa kwa Pesapal',
        'pesapalNote': 'Kadi, M-Pesa, Mixx by Yas, Airtel Money na mengineyo — malipo salama kupitia Pesapal. Utapakua vitabu vyako papo hapo.',
        'orManual': 'Au lipa moja kwa moja kwa simu na utume oda kwa WhatsApp',
        'redirecting': 'Inakupeleka Pesapal…', 'payError': 'Imeshindikana kuanzisha malipo. Jaribu tena au lipa kwa simu hapa chini.',
        'thanksTitle': 'Asante kwa <em>kununua</em>', 'checkingPay': 'Tunathibitisha malipo yako…',
        'paidTitle': 'Malipo yamepokelewa!', 'paidText': 'Pakua vitabu vyako hapa chini. Viungo vinafanya kazi kwa siku 7.',
        'emailSent': 'Nakala ya viungo imetumwa kwa', 'notYet': 'Bado hatujapokea uthibitisho wa malipo. Kama umeshalipa, subiri kidogo kisha bonyeza “Kagua tena”.',
        'checkAgain': 'Kagua tena', 'needHelp': 'Unahitaji msaada? Tuandikie WhatsApp', 'download': 'Pakua',
        'cartTitle': 'Kikapu <em>chako</em>', 'emptyCart': 'Kikapu chako kiko tupu kwa sasa.', 'continue': 'Endelea kununua',
        'remove': 'Ondoa', 'total': 'Jumla', 'yourDetails': 'Taarifa zako', 'name': 'Jina', 'phone': 'Namba ya simu',
        'email': 'Barua pepe', 'optional': '(si lazima)', 'txn': 'Namba ya muamala',
        'howToPay': 'Jinsi ya kulipa', 'step1': 'Lipa jumla ya kiasi kwa namba ifuatayo kwa mtandao wowote:',
        'step2': 'Andika namba ya kumbukumbu ya oda yako kama maelezo ya malipo:',
        'step3': 'Tuma oda yako kwa WhatsApp (au barua pepe). Utapokea PDF yako mara malipo yatakapothibitishwa.',
        'payName': 'Jina', 'copyNum': 'Nakili namba', 'orderRef': 'Kumbukumbu ya oda', 'sendOrderWa': 'Tuma oda kwa WhatsApp', 'sendOrderMail': 'Tuma kwa barua pepe',
        'freeReady': 'Bidhaa za bure ziko tayari kupakuliwa:', 'needDetails': 'Tafadhali jaza jina na namba ya simu.',
        'waHello': 'Habari! Ningependa kununua kutoka Duka la Injili Milele.', 'waOrder': 'Oda',
        'privacy': 'Taarifa zako zinatumika kukamilisha oda yako tu.',
        'aboutTitle': 'Kuhusu <em>Injili Milele</em>',
        'aboutBody': [
            'Injili Milele ni maktaba ya kidijitali ya makala, vitabu, video na sauti zinazojibu maswali muhimu ya imani — Sabato, Uungu, unabii, ibada na pambano kuu kati ya wema na uovu — kwa kuongozwa na Biblia. Kila makala ni PDF iliyopangwa kwa ustadi, tayari kusomwa kwenye simu au kuchapishwa.',
            'Makala hizi zimeandaliwa na Mch. Almodad Amos Yaragwiller, mchungaji aliyewekwa wakfu wa Kanisa la Waadventista Wasabato na mtengenezaji wa programu ya simu ya <a href="https://play.google.com/store/apps/details?id=org.almo.imani.imanizamsingi">Imani za Msingi</a>. Lengo ni kuunganisha teknolojia na utume wa Injili ili kila mtu apate rasilimali za kujifunza Neno la Mungu.',
            'Mapato yote ya duka yanasaidia kuendeleza huduma hii ya kuandaa na kusambaza rasilimali za Biblia bure.',
        ],
        'contact': 'Wasiliana nasi', 'call': 'Piga simu',
        'footerAbout': 'Maktaba ya makala, vitabu, video na sauti juu ya Imani za Msingi za Biblia.',
        'explore': 'Gundua', 'connect': 'Wasiliana', 'rights': 'Haki zote zimehifadhiwa.',
        'app': 'Pakua App ya Imani za Msingi', 'notFound': 'Ukurasa haukupatikana', 'notFoundText': 'Samahani, ukurasa unaoutafuta haupo. Huenda umehamishwa.',
        'backHome': 'Rudi Mwanzo', 'top': 'Juu',
        'fmt': {'pdf': 'PDF', 'video': 'Video', 'audio': 'Sauti', 'link': 'Kiungo', 'book': 'Kitabu'},
        'pages': 'kurasa {n}', 'readPdf': 'Soma PDF', 'downloadPdf': 'Pakua PDF', 'buyPdf': 'Nunua PDF kamili',
        'previewNote': 'Hakiki ya bure: kurasa za mwanzo tu.', 'previewEnd': 'Umefika mwisho wa hakiki ya bure',
        'previewEndText': 'Pata PDF kamili usome yote — kwenye simu, kompyuta au uichapishe.',
        'lockedTitle': 'PDF hii inapatikana kwa kununua', 'lockedText': 'Nunua mara moja na uisome kwenye simu, kompyuta au uichapishe.',
        'inside': 'Ndani ya PDF hii', 'samplePages': 'Kurasa za mfano', 'loadingPdf': 'Inapakia PDF…',
        'pdfError': 'Imeshindikana kupakia PDF.', 'retry': 'Jaribu tena', 'fullscreen': 'Skrini nzima', 'page': 'Ukurasa',
        'listen': 'Sikiliza', 'openLink': 'Fungua', 'freeAccess': 'Bure kusoma na kupakua',
        'collections': 'Mikusanyiko <em>kamili</em>', 'singles': 'Makala na vitabu <em>moja moja</em>', 'audios': 'Sauti <em>na mahubiri</em>',
        'bundleSave': 'Pata zote kwa pamoja', 'printReady': 'PDF ya A5 · Inasomeka kwenye simu, kompyuta na kuchapishwa',
        'fullPdf': 'PDF kamili', 'formats': 'Aina', 'any': 'Zote', 'previewBadge': 'hakiki ya bure',
    },
    'en': {
        'site': 'Injili <em>Milele</em>', 'siteText': 'Injili Milele',
        'tagline': 'In-depth articles on the Fundamental Beliefs of the Bible — clear, careful and written with a heart of worship.',
        'home': 'Home', 'articles': 'Library', 'store': 'Store', 'about': 'About', 'cart': 'Cart',
        'other': 'SW', 'otherName': 'Kiswahili', 'theme': 'Toggle theme',
        'heroKicker': 'Articles · Books · Video · Audio',
        'heroTitle': 'The living <em>Word</em>,<br>in depth.',
        'latest': 'Latest articles', 'readFeatured': 'Read the latest', 'browse': 'Browse all articles', 'scroll': 'Scroll',
        'verse': 'Your word is a lamp to my feet and a light to my path.', 'verseRef': 'Psalm 119:105',
        'allArticles': 'Articles, books <em>&amp; more</em>', 'library': 'Library',
        'search': 'Search the library…', 'all': 'All', 'noResults': 'No articles match your search.',
        'read': 'Read', 'min': 'min', 'minRead': '{n} min read', 'video': 'Video',
        'bandKicker': 'Digital Store', 'bandTitle': 'Take these articles <em>anywhere</em>.',
        'bandText': 'Every article is a beautifully typeset PDF for personal study, Bible study groups and printing.',
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
        'sellHello': 'Hello! I would like to sell my product in the Injili Milele store.',
        'coupon': 'Discount code', 'apply': 'Apply', 'couponOk': 'Discount applied!', 'couponBad': 'This code is not valid.',
        'couponExpired': 'This code has expired.', 'couponUsed': 'This code has reached its usage limit.',
        'couponNotFor': 'This code does not apply to the items in your cart.', 'discount': 'Discount', 'subtotal': 'Subtotal',
        'checking': 'Checking…', 'sending': 'Sending…', 'unavailable': 'Currently unavailable',
        'haveCoupon': 'Have a discount code?',
        'emailWhy': '(we send your books here)', 'payPesapal': 'Pay now with Pesapal',
        'pesapalNote': 'Card, M-Pesa, Mixx by Yas, Airtel Money and more — secure payment through Pesapal. Download your books instantly.',
        'orManual': 'Or pay directly by mobile money and send the order on WhatsApp',
        'redirecting': 'Taking you to Pesapal…', 'payError': 'Could not start the payment. Try again or pay by mobile money below.',
        'thanksTitle': 'Thank you for your <em>order</em>', 'checkingPay': 'Confirming your payment…',
        'paidTitle': 'Payment received!', 'paidText': 'Download your books below. Links work for 7 days.',
        'emailSent': 'A copy of the links was sent to', 'notYet': 'We have not received payment confirmation yet. If you have paid, wait a moment and tap “Check again”.',
        'checkAgain': 'Check again', 'needHelp': 'Need help? Message us on WhatsApp', 'download': 'Download',
        'cartTitle': 'Your <em>cart</em>', 'emptyCart': 'Your cart is empty for now.', 'continue': 'Continue shopping',
        'remove': 'Remove', 'total': 'Total', 'yourDetails': 'Your details', 'name': 'Name', 'phone': 'Phone number',
        'email': 'Email', 'optional': '(optional)', 'txn': 'Transaction ID',
        'howToPay': 'How to pay', 'step1': 'Send the total amount to this number from any network:',
        'step2': 'Use your order reference as the payment description:',
        'step3': 'Send your order by WhatsApp (or email). Your PDF is delivered as soon as payment is confirmed.',
        'payName': 'Name', 'copyNum': 'Copy number', 'orderRef': 'Order reference', 'sendOrderWa': 'Send order on WhatsApp', 'sendOrderMail': 'Send by email',
        'freeReady': 'Your free items are ready to download:', 'needDetails': 'Please enter your name and phone number.',
        'waHello': 'Hello! I would like to buy from the Injili Milele store.', 'waOrder': 'Order',
        'privacy': 'Your details are only used to complete your order.',
        'aboutTitle': 'About <em>Injili Milele</em>',
        'aboutBody': [
            'Injili Milele is a digital library of articles, books, video and audio answering important questions of faith — the Sabbath, the Godhead, prophecy, worship and the great controversy between good and evil — guided by Scripture. Every article is a carefully typeset PDF, ready to read on a phone or to print.',
            'The articles are prepared by Pr. Almodad Amos Yaragwiller, an ordained pastor of the Seventh-day Adventist Church and developer of the <a href="https://play.google.com/store/apps/details?id=org.almodad.imani.sdafundamentalbeliefs">SDA Fundamental Beliefs</a> app, joining technology with the Gospel commission so that everyone can access resources for studying God’s Word.',
            'All store proceeds support this ministry of preparing and freely sharing Bible resources.',
        ],
        'contact': 'Contact us', 'call': 'Call',
        'footerAbout': 'A library of articles, books, video and audio on the Fundamental Beliefs of the Bible.',
        'explore': 'Explore', 'connect': 'Connect', 'rights': 'All rights reserved.',
        'app': 'Get the SDA Fundamental Beliefs app', 'notFound': 'Page not found', 'notFoundText': 'Sorry, the page you are looking for does not exist. It may have moved.',
        'backHome': 'Back home', 'top': 'Top',
        'fmt': {'pdf': 'PDF', 'video': 'Video', 'audio': 'Audio', 'link': 'Link', 'book': 'Book'},
        'pages': '{n} pages', 'readPdf': 'Read the PDF', 'downloadPdf': 'Download PDF', 'buyPdf': 'Buy the full PDF',
        'previewNote': 'Free preview: the first pages only.', 'previewEnd': 'You have reached the end of the free preview',
        'previewEndText': 'Get the full PDF to read it all — on your phone, computer or in print.',
        'lockedTitle': 'This PDF is available to buy', 'lockedText': 'Buy once and read it on your phone or computer, or print it.',
        'inside': 'Inside this PDF', 'samplePages': 'Sample pages', 'loadingPdf': 'Loading the PDF…',
        'pdfError': 'Could not load the PDF.', 'retry': 'Try again', 'fullscreen': 'Full screen', 'page': 'Page',
        'listen': 'Listen', 'openLink': 'Open', 'freeAccess': 'Free to read and download',
        'collections': 'Complete <em>collections</em>', 'singles': 'Single articles <em>&amp; books</em>', 'audios': 'Audio <em>&amp; sermons</em>',
        'bundleSave': 'Get them all together', 'printReady': 'A5 PDF · Reads on phone and computer, prints beautifully',
        'fullPdf': 'Full PDF', 'formats': 'Format', 'any': 'All', 'previewBadge': 'free preview',
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
            # format: pdf (text, rendered to a designed PDF), video, audio or link
            meta['format'] = meta.get('format') or ('video' if meta['has_video'] else 'pdf')
            if meta['format'] == 'video' and not meta['has_video']:
                meta['format'] = 'pdf'
            meta['has_pdf'] = bool(meta.get('pdfFile')) or meta['format'] == 'pdf' or (
                meta['format'] == 'video' and meta['words'] >= 300)
            meta['pid'] = 'a-' + meta['slug']
            arts[lang].append(meta)
        arts[lang].sort(key=lambda a: a['order'])
    return arts


ARTS = load_articles()
PDFMETA_FILE = os.path.join(ROOT, 'content/pdfmeta.json')
PDFMETA = json.load(open(PDFMETA_FILE)) if os.path.exists(PDFMETA_FILE) else {}


def art_path(a):
    return f"{a['lang']}/{PATHS[a['lang']]['articles']}/{a['slug']}/"


def article_products():
    """Every PDF or audio item in the library is also a product (free until a price is set in the dashboard)."""
    out = []
    for lang in ('sw', 'en'):
        t = T[lang]
        for a in ARTS[lang]:
            if not (a['has_pdf'] or a['format'] == 'audio'):
                continue
            n = PDFMETA.get(a['pid'], {}).get('pages')
            kind = 'audio' if a['format'] == 'audio' else ('book' if a.get('kind') == 'book' else 'article')
            out.append({
                'id': a['pid'], 'lang': lang, 'type': kind, 'kind': kind, 'price': a.get('price', 0), 'preview': True,
                'pdf': a['pid'], 'articles': f"{lang}:{a['slug']}", 'image': a['card'], 'slug': a['slug'],
                'title': a['title'], 'category': a['category'], 'format': a['format'],
                'subtitle': ' · '.join(x for x in (a['category'], t['pages'].format(n=n) if n else '', t['fmt']['audio'] if kind == 'audio' else 'PDF') if x),
                'description': a['excerpt'], 'includes': [],
            })
    return out


def fill_counts(p):
    """Bundles may say {n} in their texts: the number of articles they contain."""
    n = len(articles_for(p))
    for k in ('title', 'subtitle', 'description'):
        p[k] = p[k].replace('{n}', str(n))
    p['includes'] = [i.replace('{n}', str(n)) for i in p['includes']]
    p.setdefault('kind', 'bundle')
    p.setdefault('preview', True)
    return p


def prod_path(lang, p):
    if p.get('kind') in ('article', 'book', 'audio'):
        return art_path(next(a for a in ARTS[lang] if a['pid'] == p['id']))
    return f"{lang}/{PATHS[lang]['store']}/{p['id']}/"


def read_url(pid, dl=False):
    return f"{SITE['paymentsUrl']}read/{pid}" + ('?dl=1' if dl else '')


def articles_for(p):
    res = []
    for spec in p['articles'].split(','):
        lang, slug = spec.split(':')
        res += [a for a in ARTS[lang] if (slug == '*' and a['has_pdf'] and not a.get('pdfFile')) or slug == a['slug']]
    return res


BUNDLES = [fill_counts(p) for p in PRODUCTS]
ALL_PRODUCTS = BUNDLES + article_products()
PROD = {p['id']: p for p in ALL_PRODUCTS}


# ------------------------------------------------------------------ layout
def cover(p, lang, root):
    cls = 'cover free' if p.get('free') else 'cover'
    top = T[lang]['free'] if p.get('free') else {'book': T[lang]['fmt']['book'], 'audio': T[lang]['fmt']['audio']}.get(p.get('kind'), 'PDF')
    return (f'<div class="{cls}" aria-hidden="true"><img src="{root}assets/img/{p["image"]}.jpg" alt="" loading="lazy">'
            f'<div class="cover-top">{e(top)}</div><div class="cover-title">{e(p["title"])}</div>'
            f'<div class="cover-author">{e(SITE["author"])}</div></div>')


def price_html(p, lang):
    if not p['price']:
        inner = f'<span class="price free">{T[lang]["free"]}</span>'
    else:
        inner = f'<span class="price"><small>TSh</small>{p["price"]:,}</span>'
    return f'<span class="price-slot" data-price-of="{p["id"]}">{inner}</span>'


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
        'lang': lang, 'root': root, 'cartUrl': root + lang + '/' + p['cart'] + '/',
        'whatsapp': SITE['whatsapp'], 'email': SITE['email'],
        't': {k: v for k, v in t.items() if isinstance(v, str) and k in (
            'copied', 'play', 'free', 'inCart', 'added', 'viewCart', 'remove', 'total', 'name', 'phone', 'email',
            'txn', 'needDetails', 'waHello', 'waOrder', 'sellHello', 'product', 'couponOk', 'couponBad',
            'couponExpired', 'couponUsed', 'couponNotFor', 'discount', 'subtotal', 'coupon', 'checking', 'sending',
            'unavailable', 'redirecting', 'payError', 'checkingPay', 'paidTitle', 'paidText', 'emailSent', 'notYet',
            'checkAgain', 'download', 'loadingPdf', 'pdfError', 'retry', 'page', 'pages', 'previewNote', 'fullPdf')},
        'payments': SITE['paymentsUrl'],
        'fb': {'apiKey': SITE['firebase']['apiKey'], 'projectId': SITE['firebase']['projectId']},
    }
    if products_js:
        mm['products'] = {
            x['id']: {
                'title': x['title'], 'subtitle': x['subtitle'], 'price': x['price'], 'preview': x.get('preview', True),
                'coverHtml': cover(x, lang, root), 'download': read_url(x['id'], dl=True),
            } for x in ALL_PRODUCTS if x['lang'] == lang
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
<meta name="theme-color" content="#1d2747">
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
      <a class="icon-btn" href="{root}{lang}/{p['cart']}/" aria-label="{t['cart']}">{ICON['bag']}<span class="cart-count">0</span></a>
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


def badges(a):
    """Format badges for a library item: PDF, Video (+ PDF), Audio, Link."""
    t = T[a['lang']]
    out = ''
    if a['format'] == 'video':
        out += f'<span class="badge video">▶ {t["fmt"]["video"]}</span>'
    elif a['format'] == 'audio':
        out += f'<span class="badge audio">♪ {t["fmt"]["audio"]}</span>'
    elif a['format'] == 'link':
        out += f'<span class="badge link">↗ {t["fmt"]["link"]}</span>'
    if a['has_pdf']:
        out += f'<span class="badge pdf">{t["fmt"]["book"] if a.get("kind") == "book" else "PDF"}</span>'
    return out


def card(a, root, idx):
    t = T[a['lang']]
    num = f'{idx + 1:02d}'
    search = ' '.join([a['title'], a['category'], a['excerpt'], strip_tags(a['body'])[:4000]])
    feature = ' feature' if idx == 0 else ''
    pages = PDFMETA.get(a['pid'], {}).get('pages')
    if a['format'] == 'link':
        href, extra, info = e(a['url']), ' target="_blank" rel="noopener"', ''
    else:
        href, extra = root + art_path(a), ''
        info = t['pages'].format(n=pages) if pages and a['has_pdf'] else f"{a['minutes']} {t['min']}"
    price = (f'<span class="price-slot" data-price-of="{a["pid"]}">{price_html(PROD[a["pid"]], a["lang"])}</span>'
             if a['pid'] in PROD else '')
    go = {'video': t['play'], 'audio': t['listen'], 'link': t['openLink']}.get(a['format'], t['read'])
    fmts = ' '.join(f for f in (a['format'], 'pdf' if a['has_pdf'] else '') if f)
    return f'''<a class="card reveal{feature}" href="{href}"{extra} data-cat="{e(a['category'])}" data-format="{fmts}" data-search="{e(search)}">
  <div class="card-media"><img src="{root}assets/img/{a['card']}.jpg" alt="" loading="{'eager' if idx < 2 else 'lazy'}"></div>
  <div class="card-body"><span class="card-num" aria-hidden="true">{num}</span>
    <div class="card-meta"><span class="cat">{e(a['category'])}</span>{badges(a)}</div>
    <h3>{e(a['title'])}</h3>
    <p>{e(a['excerpt'])}</p>
    <div class="card-foot"><span class="info">{info}{price}</span><span class="go">{go} {ICON['arrow']}</span></div>
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
    present = [f for f in ('pdf', 'video', 'audio', 'link') if any(f == a['format'] or (f == 'pdf' and a['has_pdf']) for a in arts)]
    fchips = ''
    if len(present) > 1:
        fchips = (f'<div class="chips formats" role="group" aria-label="{t["formats"]}">'
                  f'<button class="chip" type="button" data-format-filter="all" aria-pressed="true">{t["any"]}</button>' + ''.join(
                      f'<button class="chip" type="button" data-format-filter="{f}" aria-pressed="false">{t["fmt"][f]}</button>' for f in present) + '</div>')
    featured_products = [p for p in ALL_PRODUCTS if p['lang'] == lang and p['kind'] != 'audio'][:3]
    books = ''.join(cover(p, lang, root) for p in featured_products)
    stack = ''.join(
        f'<a class="glass" href="{root}{art_path(a)}">'
        f'<img src="{root}assets/img/{a["card"]}.jpg" alt="" loading="eager">'
        f'<div><small>{e(a["category"])}</small><b>{e(a["title"])}</b><span>{t["minRead"].format(n=a["minutes"])}</span></div></a>'
        for a in arts[:3])
    body = f'''
<section class="hero">
  <div class="hero-bg">{ART}</div>
  <div class="wrap hero-grid">
   <div class="hero-copy">
    <span class="eyebrow rise">{t['heroKicker']}</span>
    <h1 class="rise d1">{t['heroTitle']}</h1>
    <p class="lede rise d2">{t['tagline']}</p>
    <div class="hero-actions rise d3">
      <a class="btn btn-primary" href="{root}{art_path(lead)}">{t['readFeatured']} {ICON['arrow']}</a>
      <a class="btn btn-ghost" href="#makala">{t['browse']}</a>
    </div>
    <p class="hero-verse rise d4"><b>{t['verseRef']}</b><span>“{t['verse']}”</span></p>
   </div>
   <div class="hero-stack rise d3" aria-label="{t['latest']}">
    <p class="stack-label">{t['latest']}</p>
    {stack}
   </div>
  </div>
  <a class="scroll-cue" href="#makala" aria-label="{t['browse']}"><span>{t['scroll']}</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></a>
</section>
<section class="section" id="makala">
  <div class="wrap">
    <div class="section-head">
      <div><span class="kicker">{t['library']} · {len(arts)}</span><h2>{t['allArticles']}</h2></div>
    </div>
    <div class="toolbar">
      <label class="search">{ICON['search']}<span class="sr-only">{t['search']}</span><input type="search" data-search placeholder="{t['search']}" autocomplete="off"></label>
      {fchips}
      <div class="chips cats" role="group">{chips}</div>
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
      <a class="btn btn-primary" href="{root}{lang}/{PATHS[lang]['store']}/">{ICON['store']} {t['visitStore']}</a>
    </div>
    <div class="band-books" style="font-size:16px">{books}</div>
  </div>
</section>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(f'{lang}/', page(lang, f'{lang}/', f"{t['siteText']} — {strip_tags(t['heroTitle'].replace('<br>', ' '))}", body,
                           image=lead['image'], active='articles', other_url=f'{other}/', products_js=True, body_class='home'))


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
    pid = a['pid']
    prod = PROD.get(pid)
    meta = PDFMETA.get(pid, {})
    info = (t['pages'].format(n=meta['pages']) if meta.get('pages') and a['has_pdf'] else t['minRead'].format(n=a['minutes']))
    fmt_label = t['fmt']['book'] if a.get('kind') == 'book' else t['fmt'][a['format']]
    share_bar = f"""<div class="share">
      <span>{t['share']}</span>
      <a class="btn btn-wa" href="https://wa.me/?text={e(quote(share_text))}" target="_blank" rel="noopener">{ICON['wa']} WhatsApp</a>
      <a class="btn btn-line" href="https://www.facebook.com/sharer/sharer.php?u={e(quote(url))}" target="_blank" rel="noopener">{ICON['fb']} Facebook</a>
      <button class="btn btn-line" type="button" data-share="copy">{ICON['link']} {t['copy']}</button>
    </div>"""

    # ---- media first: video, audio player or external link
    media = ''
    if a['format'] == 'video':
        media = '\n'.join(re.findall(r'<div class="video"[^>]*></div>', body_html))
    elif a['format'] == 'audio':
        media = (f'<div class="audio-card" data-audio="{pid}"><div class="audio-art"><img src="{root}assets/img/{a["card"]}.jpg" alt=""></div>'
                 f'<div><span class="kicker">{t["fmt"]["audio"]}</span><h2>{e(a["title"])}</h2>'
                 f'<audio controls preload="none" data-src="{read_url(pid)}"></audio></div></div>')
    elif a['format'] == 'link':
        host = re.sub(r'^https?://(www\.)?([^/]+).*$', r'\2', a['url'])
        media = (f'<a class="link-card" href="{e(a["url"])}" target="_blank" rel="noopener"><span class="kicker">{t["fmt"]["link"]} · {e(host)}</span>'
                 f'<b>{e(a["title"])}</b><span class="go">{t["openLink"]} {ICON["arrow"]}</span></a>')

    # ---- what is inside: the article's section headings
    heads = [strip_tags(h) for h in re.findall(r'<h2[^>]*>(.*?)</h2>', a['body'], re.S)]
    outline = ''.join(f'<li>{e(h)}</li>' for h in heads[:14])
    facts = [f'{ICON["book"]} {fmt_label}', f'{ICON["check"]} {t["langBadge"][lang]}']
    if meta.get('pages'):
        facts.insert(1, f'{ICON["check"]} {t["pages"].format(n=meta["pages"])}')
    thumbs = ''.join(f'<img src="{root}assets/img/pages/{pid}-{n}.jpg" alt="{t["page"]} {n}" loading="lazy">'
                     for n in range(1, (meta.get('thumbs') or 0) + 1))
    access = 'free' if not (prod and prod['price']) else 'preview'
    doc = ''
    if a['has_pdf'] and prod:
        doc = f"""
<section class="doc wrap" data-doc="{pid}" data-access="{access}">
  <div class="doc-grid">
    <div class="doc-info">
      <p class="lead">{e(a['excerpt'])}</p>
      {f'<h4 class="kicker">{t["inside"]}</h4><ol class="outline">{outline}</ol>' if outline else ''}
      <ul class="facts">{''.join(f'<li>{x}</li>' for x in facts)}</ul>
    </div>
    <aside class="buybox doc-buy" data-buybox="{pid}">
      <div class="doc-cover">{cover(prod, lang, root)}</div>
      <div class="doc-price">{price_html(prod, lang)}</div>
      <div class="acts" data-when="free">
        <a class="btn btn-primary btn-block" href="#soma">{ICON['book']} {t['readPdf']}</a>
        <a class="btn btn-line btn-block" href="{read_url(pid, dl=True)}" rel="nofollow">{ICON['down']} {t['downloadPdf']}</a>
        <span class="note ok">{ICON['check']} {t['freeAccess']}</span>
      </div>
      <div class="acts" data-when="preview locked">
        <button class="btn btn-primary btn-block" type="button" data-buy="{pid}">{t['buyPdf']} {ICON['arrow']}</button>
        <button class="btn btn-line btn-block" type="button" data-add="{pid}">{t['addToCart']}</button>
        <a class="btn btn-ghost-dark btn-block" href="#soma" data-when="preview">{t['readPdf']} · {t['previewBadge']}</a>
      </div>
      <span class="note">{t['printReady']}</span>
    </aside>
  </div>
</section>
<section class="reader" id="soma" data-reader="{pid}" data-access="{access}" data-src="{read_url(pid)}">
  <div class="reader-bar"><div class="wrap">
    <span class="reader-state" data-reader-state>{t['loadingPdf']}</span>
    <span class="spacer"></span>
    <span class="pageinfo" data-pageinfo></span>
    <button class="tool" type="button" data-fs aria-label="{t['fullscreen']}">⤢</button>
    <a class="tool" data-when="free" href="{read_url(pid, dl=True)}" rel="nofollow" aria-label="{t['downloadPdf']}">{ICON['down']}</a>
  </div></div>
  <div class="pages" data-pages></div>
  <div class="reader-end panel" data-preview-end hidden>
    <span class="kicker">{t['previewNote']}</span>
    <h3>{t['previewEnd']}</h3>
    <p>{t['previewEndText']}</p>
    <div class="row-btns"><button class="btn btn-primary" type="button" data-buy="{pid}">{t['buyPdf']} {ICON['arrow']}</button>
    <span class="price-slot" data-price-of="{pid}">{price_html(prod, lang)}</span></div>
  </div>
  <div class="reader-locked panel" data-locked hidden>
    <span class="kicker">{t['fullPdf']}</span>
    <h3>{t['lockedTitle']}</h3>
    <p>{t['lockedText']}</p>
    {f'<div class="thumbs">{thumbs}</div>' if thumbs else ''}
    <div class="row-btns"><button class="btn btn-primary" type="button" data-buy="{pid}">{t['buyPdf']} {ICON['arrow']}</button>
    <span class="price-slot" data-price-of="{pid}">{price_html(prod, lang)}</span></div>
  </div>
</section>"""
    elif a['format'] != 'link':
        # no PDF (e.g. a short video or an audio item): show the text as it is
        rest = re.sub(r'<div class="video"[^>]*></div>', '', body_html).strip()
        if rest:
            doc = f'<div class="wrap"><div class="prose short">{rest}</div></div>'
    if a['format'] == 'audio' and prod:
        doc = f"""
<section class="doc wrap" data-doc="{pid}" data-access="{access}">
  <aside class="buybox doc-buy audio-buy" data-buybox="{pid}">
    <div class="doc-price">{price_html(prod, lang)}</div>
    <div class="acts" data-when="free"><a class="btn btn-line btn-block" href="{read_url(pid, dl=True)}" rel="nofollow">{ICON['down']} {t['download']}</a></div>
    <div class="acts" data-when="preview locked"><button class="btn btn-primary btn-block" type="button" data-buy="{pid}">{t['buyNow']} {ICON['arrow']}</button></div>
  </aside>
</section>""" + doc

    body = f"""
<header class="article-hero">
  <img class="bg" src="{root}assets/img/{a['image']}.jpg" alt="">
  <div class="wrap">
    <nav class="crumbs rise" aria-label="Breadcrumb"><a href="{root}{lang}/">{t['home']}</a><span>/</span><a href="{root}{lang}/#makala">{t['articles']}</a><span>/</span><span>{e(a['category'])}</span></nav>
    <div class="hero-badges rise">{badges(a)}</div>
    <h1 class="rise d1">{e(a['title'])}</h1>
    <div class="byline rise d2">
      <span class="author"><span class="avatar">{e(initials)}</span>{e(a['author'])}</span>
      <span class="dot"></span><span>{info}</span>
      <span class="dot"></span><span>{e(a['category'])}</span>
    </div>
  </div>
</header>
{f'<div class="wrap media-wrap">{media}</div>' if media else ''}
{doc}
<div class="wrap">
  <div class="article-end">
    {share_bar}
    <div class="author-box">
      <span class="avatar">{e(initials)}</span>
      <div><h4>{e(a['author'])}</h4><p>{t['guestBio'] if guest else t['authorBio']}</p></div>
    </div>
    {pager}
  </div>
</div>
<section class="wrap" style="padding-top:8px">
  <div class="section-head"><h2>{t['related']}</h2></div>
  <div class="grid">{''.join(card(b, root, arts.index(b)).replace(' feature', '') for b in related)}</div>
</section>"""
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    write(rel, page(lang, rel, f"{a['title']} · {t['siteText']}", body, desc=a['excerpt'], image=a['image'],
                    active='articles', other_url=other_url, extra_head=head, products_js=True))


def quote(s):
    from urllib.parse import quote as q
    return q(s, safe='')


def product_card(x, lang, root):
    t = T[lang]
    href = root + prod_path(lang, x)
    if x['kind'] in ('article', 'book', 'audio'):
        # free items download straight away; priced items go to the cart (the dashboard decides)
        btn = (f'<a class="btn btn-ink add" href="{href}" data-when-free="{x["id"]}">{t["read"] if x["kind"] != "audio" else t["listen"]}</a>'
               f'<button class="btn btn-ink add" type="button" data-add="{x["id"]}" data-when-paid="{x["id"]}">{t["addToCart"]}</button>')
    else:
        btn = (f'<a class="btn btn-ink add" href="{x and read_url(x["id"], dl=True)}" rel="nofollow" data-when-free="{x["id"]}">{ICON["down"]} {t["getFree"]}</a>'
               f'<button class="btn btn-ink add" type="button" data-add="{x["id"]}" data-when-paid="{x["id"]}">{t["addToCart"]}</button>')
    meta = PDFMETA.get(x['id'], {})
    label = t['fmt']['audio'] if x['kind'] == 'audio' else (t['fmt']['book'] if x['kind'] == 'book' else 'PDF')
    pages = f' · {t["pages"].format(n=meta["pages"])}' if meta.get('pages') else ''
    return f'''<article class="product reveal" data-product="{x['id']}" data-free="{0 if x['price'] else 1}">
  <a class="cover-link" href="{href}">{cover(x, lang, root)}</a>
  <div class="card-meta"><span class="cat">{label}{pages}</span></div>
  <h3><a href="{href}">{e(x['title'])}</a></h3>
  <p class="sub">{e(x['subtitle'] if x['kind'] == 'bundle' else x['category'])}</p>
  <div class="row">{price_html(x, lang)}{btn}</div>
</article>'''


def build_store(lang):
    t, p = T[lang], PATHS[lang]
    rel = f"{lang}/{p['store']}/"
    root = '../../'
    own = [x for x in ALL_PRODUCTS if x['lang'] == lang]
    groups = [
        ('collections', [x for x in own if x['kind'] == 'bundle']),
        ('singles', [x for x in own if x['kind'] in ('article', 'book')]),
        ('audios', [x for x in own if x['kind'] == 'audio']),
    ]
    sections = ''.join(f'''
  <div class="store-group" id="{key}">
    <div class="section-head"><div><span class="kicker">{t['store']} · {len(items)}</span><h2>{t[key]}</h2></div></div>
    <div class="products">{''.join(product_card(x, lang, root) for x in items)}</div>
  </div>''' for key, items in groups if items)
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
    <div class="store-top"><a class="btn btn-line" href="{root}{lang}/{p['cart']}/">{ICON['bag']} {t['cart']}</a></div>
    {sections}
  </div>
</section>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{t['store']} · {t['siteText']}", body, desc=strip_tags(t['storeText']), active='store',
                    other_url=f"{other}/{PATHS[other]['store']}/", products_js=True))

    for x in own:
        if x['kind'] == 'bundle':
            build_product(lang, x)


def build_product(lang, x):
    t = T[lang]
    rel = prod_path(lang, x)
    root = '../../../'
    contents = ''.join(f'<li><a href="{root}{art_path(a)}">{e(a["title"])}</a></li>' for a in articles_for(x))
    includes = ''.join(f'<li>{ICON["check"]}<span>{e(i)}</span></li>' for i in x['includes'])
    meta = PDFMETA.get(x['id'], {})
    if meta.get('pages'):
        includes += f'<li>{ICON["check"]}<span>{t["pages"].format(n=meta["pages"])}</span></li>'
    thumbs = ''.join(f'<img src="{root}assets/img/pages/{x["id"]}-{n}.jpg" alt="{t["page"]} {n}" loading="lazy">'
                     for n in range(1, (meta.get('thumbs') or 0) + 1))
    actions = (f'<div class="acts" data-when="free"><a class="btn btn-primary btn-block" href="{read_url(x["id"], dl=True)}" rel="nofollow">{ICON["down"]} {t["getFree"]}</a></div>'
               f'<div class="acts" data-when="preview locked"><button class="btn btn-primary btn-block" type="button" data-buy="{x["id"]}">{t["buyNow"]} {ICON["arrow"]}</button>'
               f'<button class="btn btn-line btn-block" type="button" data-add="{x["id"]}">{t["addToCart"]}</button>')
    if x.get('paymentUrl'):
        actions += f'<a class="btn btn-ink btn-block" href="{e(x["paymentUrl"])}" target="_blank" rel="noopener">{t["payNow"]}</a>'
    actions += '</div>'
    access = 'preview' if x['price'] else 'free'
    body = f'''
<div class="wrap">
  <nav class="crumbs" style="color:var(--muted);padding-top:28px" aria-label="Breadcrumb"><a style="color:var(--accent)" href="{root}{lang}/{PATHS[lang]['store']}/">{t['store']}</a><span>/</span><span>{e(x['title'])}</span></nav>
  <div class="product-page" data-doc="{x['id']}" data-access="{access}">
    <div class="stage rise">{cover(x, lang, root)}</div>
    <div>
      <div class="card-meta rise"><span class="cat">PDF</span></div>
      <h1 class="rise d1">{e(x['title'])}</h1>
      <p class="lead rise d2">{e(x['description'])}</p>
      <div class="buybox rise d3" data-buybox="{x['id']}">
        {price_html(x, lang)}
        {actions}
        <span class="note">{t['format']}</span>
      </div>
      {f'<h4 class="kicker">{t["samplePages"]}</h4><div class="thumbs">{thumbs}</div>' if thumbs else ''}
      <h4 class="kicker">{t['includes']}</h4>
      <ul class="includes">{includes}</ul>
      <div class="contents"><h4>{t['contents']}</h4><ol>{contents}</ol></div>
    </div>
  </div>
</div>'''
    other = 'en' if lang == 'sw' else 'sw'
    twin = next((y for y in BUNDLES if y['lang'] == other and y.get('pair') and y.get('pair') == x.get('pair')), None)
    write(rel, page(lang, rel, f"{x['title']} · {t['store']}", body, desc=x['description'], image=x['image'],
                    active='store', other_url=prod_path(other, twin) if twin else f"{other}/{PATHS[other]['store']}/", products_js=True))


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
    <a class="btn btn-primary" href="{root}{lang}/{p['store']}/">{t['continue']}</a>
  </div>
  <div class="checkout" data-filled>
    <div class="stack">
      <div class="panel">
        <div data-lines></div>
        <div class="subtotals" data-subtotals hidden>
          <div><span>{t['subtotal']}</span><span data-subtotal></span></div>
          <div class="disc"><span>{t['discount']} <b data-coupon-label></b></span><span data-discount></span></div>
        </div>
        <div class="totals"><span>{t['total']}</span><span class="price" data-total></span></div>
        <form class="coupon" data-coupon-form>
          <label for="c-coupon">{t['haveCoupon']}</label>
          <div class="coupon-row"><input id="c-coupon" name="coupon" autocomplete="off" autocapitalize="characters" placeholder="{t['coupon']}"><button class="btn btn-line" type="submit">{t['apply']}</button></div>
          <p class="coupon-msg" data-coupon-msg role="status"></p>
        </form>
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
        <div class="field"><label for="c-email">{t['email']} <span class="note">{t['emailWhy']}</span></label><input id="c-email" name="email" type="email" autocomplete="email"></div>
        <div data-pay>
          <h2 style="margin-top:10px">{t['howToPay']}</h2>
          <button class="btn btn-primary btn-block" type="button" data-pesapal>{ICON['bolt']} {t['payPesapal']}</button>
          <p class="note" style="margin:8px 0 0">{t['pesapalNote']}</p>
          <details class="alt-pay">
          <summary>{t['orManual']}</summary>
          <ol class="steps">
            <li><div>{t['step1']}
              <div class="paybox"><span class="num">{e(pay['number'])}</span><span>{t['payName']}: <b>{e(pay['name'])}</b></span><div class="methods">{methods}</div>
              <button class="btn btn-line" type="button" data-copy-num="{e(pay['number'].replace(' ', ''))}" style="justify-self:start;padding:8px 14px">{ICON['link']} {t['copyNum']}</button></div></div></li>
            <li><div>{t['step2']} <div class="paybox"><span>{t['orderRef']}</span><span class="ref" data-ref></span></div></div></li>
            <li><div>{t['step3']}</div></li>
          </ol>
          <div class="field"><label for="c-txn">{t['txn']} <span class="note">{t['optional']}</span></label><input id="c-txn" name="txn" placeholder="e.g. 8GH3K2LQ"></div>
          <div class="stack">
            <button class="btn btn-wa btn-block" type="button" data-send-wa>{ICON['wa']} {t['sendOrderWa']}</button>
            <button class="btn btn-line btn-block" type="button" data-send-mail>{ICON['mail']} {t['sendOrderMail']}</button>
          </div>
          </details>
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


def build_thanks(lang):
    """Pesapal sends buyers back here; the page confirms payment with the payments service and shows downloads."""
    t, p = T[lang], PATHS[lang]
    rel = f"{lang}/{p['thanks']}/"
    root = '../../../'
    body = f'''
<div class="wrap" data-thanks>
  <div class="about" style="max-width:40rem">
    <span class="kicker">{t['store']}</span>
    <h1>{t['thanksTitle']}</h1>
    <div class="panel" data-state="checking"><p style="margin:0">{t['checkingPay']}</p></div>
    <div class="panel" data-state="paid" hidden>
      <h2>{t['paidTitle']}</h2>
      <p class="muted" style="margin-top:0">{t['paidText']}</p>
      <div class="stack" data-downloads></div>
      <p class="note" data-email-note></p>
    </div>
    <div class="panel" data-state="pending" hidden>
      <p style="margin-top:0">{t['notYet']}</p>
      <button class="btn btn-primary" type="button" data-recheck>{t['checkAgain']}</button>
    </div>
    <p style="margin-top:24px"><a class="btn btn-wa" href="https://wa.me/{SITE['whatsapp']}" target="_blank" rel="noopener">{ICON['wa']} {t['needHelp']}</a></p>
  </div>
</div>'''
    other = 'en' if lang == 'sw' else 'sw'
    write(rel, page(lang, rel, f"{strip_tags(t['thanksTitle'])} · {t['siteText']}", body, active='store',
                    other_url=f"{other}/{PATHS[other]['store']}/", products_js=True,
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
<title>Injili Milele</title>
<meta name="description" content="Maktaba ya makala, vitabu, video na sauti juu ya Imani za Msingi za Biblia · A library of articles, books, video and audio on the Fundamental Beliefs of the Bible.">
<meta name="theme-color" content="#1d2747">
<meta property="og:title" content="Injili Milele">
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
  <div class="bg">{ART}</div>
  <div>
    <img class="logo rise" src="assets/img/icon-192.png" alt="Injili Milele">
    <h1 class="rise d1">Injili <em>Milele</em></h1>
    <p class="rise d2">Makala, vitabu, video na sauti juu ya Imani za Msingi za Biblia.<br><i>Articles, books, video and audio on the Fundamental Beliefs of the Bible.</i></p>
    <div class="choices rise d3">
      <a class="btn btn-primary" href="sw/" onclick="remember('sw')">Kiswahili {ICON['arrow']}</a>
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
  <p><a class="btn btn-primary" href="{SITE['baseUrl']}sw/">{T['sw']['backHome']}</a> <a class="btn btn-line" href="{SITE['baseUrl']}en/">{T['en']['backHome']}</a></p>
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
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)
    json.dump([dict(p, url=SITE['baseUrl'] + prod_path(p['lang'], p), pages=PDFMETA.get(p['id'], {}).get('pages')) for p in ALL_PRODUCTS],
              open(os.path.join(OUT, 'data/products.json'), 'w'), ensure_ascii=False, indent=1)
    build_admin()
    json.dump({
        'name': 'Injili Milele', 'short_name': 'Injili Milele',
        'start_url': './', 'display': 'standalone', 'background_color': '#1d2747', 'theme_color': '#1d2747',
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
    'gregory-calendar-and-the-sabbath': [
        'Did the calendar change of 1582 affect the dates of the month or the cycle of the days of the week? Explain.',
        'How do the names of the seventh day in many of the world’s languages confirm the Sabbath of the Bible?',
        'What does Isaiah 66:22–23 teach about the Sabbath in the new earth?',
        'How does the sequence of Friday, Sabbath and Sunday in Luke 23:54–24:1 help us identify the Sabbath today?',
        'How would you explain to a friend, gently and wisely, that the Sabbath has not been lost?',
    ],
}


PRIVATE = os.path.join(ROOT, 'store-private')
VIDEO_RE = r'<div class="video" data-yt="([^"]+)" data-title="([^"]*)"></div>'
PDF_TEXT = {
    'sw': {'contents': 'Yaliyomo', 'questions': 'Maswali ya Kujadili', 'more': 'Zaidi kutoka Injili Milele',
           'moreText': 'Makala, vitabu, video na sauti zaidi zinapatikana kwenye maktaba ya Injili Milele:',
           'continue': 'Endelea kusoma', 'continueText': 'Hii ni hakiki ya bure ya kurasa za mwanzo. Pata PDF kamili kwenye Injili Milele usome yote — kwenye simu, kompyuta au uichapishe.',
           'getFull': 'Pata PDF kamili hapa:', 'preview': 'Hakiki ya bure', 'rights': 'Haki zote zimehifadhiwa. Usiuze nakala hii bila ruhusa ya maandishi ya mwandishi.',
           'contact': 'Wasiliana nasi', 'by': 'Na'},
    'en': {'contents': 'Contents', 'questions': 'Discussion Questions', 'more': 'More from Injili Milele',
           'moreText': 'More articles, books, video and audio are waiting in the Injili Milele library:',
           'continue': 'Keep reading', 'continueText': 'This is a free preview of the first pages. Get the full PDF from Injili Milele to read it all — on your phone, computer or in print.',
           'getFull': 'Get the full PDF here:', 'preview': 'Free preview', 'rights': 'All rights reserved. Do not sell this copy without the author’s written permission.',
           'contact': 'Contact us', 'by': 'By'},
}

PDF_CSS = """
@page { size: A5; margin: 17mm 15mm 19mm;
  @top-left { content: "INJILI MILELE"; font: 600 6.5pt 'Fira Sans', sans-serif; letter-spacing: .2em; color: #8a93ab; }
  @top-right { content: "__RUNNING__"; font: 400 7pt 'Fira Sans', sans-serif; color: #8a93ab; }
  @bottom-center { content: counter(page); font: 700 8pt 'Sora', sans-serif; color: #5a73aa; } }
@page :first { margin: 0; @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; } }
@page plain { @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Fira Sans', sans-serif; font-size: 10.2pt; line-height: 1.62; color: #1b2233; margin: 0; }
.cover { height: 210mm; width: 148mm; display: flex; flex-direction: column; color: #f2f4fa; background: #0e1530; overflow: hidden; break-after: page; position: relative; }
.cover .art { position: relative; height: 134mm; flex: none; }
.cover .art img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover .art::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(14,21,48,.55) 0%, rgba(14,21,48,0) 16%, rgba(14,21,48,0) 80%, #0e1530 100%); }
.cover .k { position: absolute; z-index: 2; top: 8mm; left: 12mm; right: 12mm; font-size: 6.8pt; font-weight: 700; letter-spacing: .28em; text-transform: uppercase; color: #fff; display: flex; justify-content: space-between; align-items: center; text-shadow: 0 1px 3px rgba(0,0,0,.5); }
.cover .k b { color: #0e1530; background: #f2c14e; padding: 1mm 2.4mm; border-radius: 1mm; letter-spacing: .16em; text-shadow: none; }
.cover .info { flex: 1; display: flex; flex-direction: column; padding: 3mm 13mm 10mm; }
.cover .cat { font-size: 6.8pt; font-weight: 700; letter-spacing: .24em; text-transform: uppercase; color: #a3b7ea; margin-bottom: 2.5mm; }
.cover h1 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 16pt; line-height: 1.14; letter-spacing: -.015em; margin: 0 0 2.5mm;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.cover p { font-size: 8.2pt; line-height: 1.45; color: #c4cbdd; margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cover .a { margin-top: auto; font-size: 6.8pt; font-weight: 600; letter-spacing: .18em; text-transform: uppercase; padding-top: 3mm; border-top: .3mm solid rgba(213,222,245,.25); display: flex; justify-content: space-between; color: #d5def5; }
.toc { break-after: page; page: plain; padding-top: 6mm; }
.toc h2 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 22pt; letter-spacing: -.02em; margin: 0 0 7mm; }
.toc ol { padding: 0; margin: 0; list-style: none; counter-reset: t; }
.toc li { counter-increment: t; display: grid; grid-template-columns: 9mm 1fr; padding: 2.6mm 0; border-bottom: .25mm solid #e3e7f2; }
.toc li::before { content: counter(t, decimal-leading-zero); font-family: 'Sora', sans-serif; font-weight: 800; color: #7c93cc; font-size: 10pt; }
.toc a { color: inherit; text-decoration: none; font-family: 'Sora', sans-serif; font-weight: 700; font-size: 10.5pt; line-height: 1.3; }
.toc span { display: block; font-size: 7.5pt; color: #6b7285; font-family: 'Fira Sans', sans-serif; font-weight: 400; margin-top: .6mm; }
.art { break-before: page; }
.art .hero { width: 100%; height: 44mm; object-fit: cover; border-radius: 2.5mm; display: block; }
.art .cat { font-size: 7pt; font-weight: 700; letter-spacing: .22em; text-transform: uppercase; color: #5a73aa; margin: 6mm 0 2mm; }
.art h1 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 18.5pt; line-height: 1.12; letter-spacing: -.02em; margin: 0 0 3mm; color: #121a33; }
.by { font-size: 8pt; color: #6b7285; margin-bottom: 6mm; padding-bottom: 4mm; border-bottom: .25mm solid #e3e7f2; }
.prose h2 { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 12.5pt; line-height: 1.25; letter-spacing: -.01em; margin: 7mm 0 2.5mm; color: #121a33; break-after: avoid; break-inside: avoid; }
.prose h2::before { content: ""; display: block; width: 9mm; height: .8mm; background: #7c93cc; border-radius: .4mm; margin-bottom: 2.5mm; }
.prose h3 { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 10.6pt; margin: 5mm 0 1.5mm; color: #34457e; break-after: avoid; break-inside: avoid; }
.prose p { margin: 0 0 2.8mm; text-align: justify; hyphens: auto; orphans: 2; widows: 2; }
.prose > p:first-of-type::first-letter { float: left; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 31pt; line-height: .86; color: #5a73aa; margin: 1mm 1.6mm 0 0; }
.prose blockquote { margin: 3.5mm 0; padding: 3mm 4mm 3mm 4.5mm; background: #eef1f8; border-left: .8mm solid #7c93cc; border-radius: 0 2mm 2mm 0; break-inside: avoid; font-size: 9.6pt; }
.prose blockquote p { margin: 0; text-align: left; }
.prose blockquote cite { display: block; margin-top: 1.5mm; font-style: normal; font-weight: 700; font-size: 7.5pt; letter-spacing: .08em; text-transform: uppercase; color: #5a73aa; }
.prose blockquote.spirit { background: #e4e8f4; border-left-color: #5a73aa; font-style: italic; }
.prose blockquote.spirit cite { color: #34457e; font-style: normal; }
.prose p.key { background: #121a33; color: #eef1f8; padding: 3.2mm 4mm; border-radius: 2mm; font-weight: 500; text-align: left; break-inside: avoid; }
.prose p.source { font-size: 7.6pt; color: #6b7285; font-style: italic; text-align: left; }
.prose ul, .prose ol { margin: 0 0 3mm; padding-left: 5.5mm; }
.prose li { margin: 0 0 1.2mm; }
.prose li::marker { color: #5a73aa; font-weight: 700; }
.prose strong { font-weight: 700; color: #121a33; }
.prose blockquote.spirit strong, .prose p.key strong { color: inherit; }
.prose img { width: 100%; border-radius: 2mm; margin: 3mm 0; }
.prose a { color: #4257b8; }
.prose sup { font-size: .7em; }
.vid { font-size: 8.6pt; background: #eef1f8; padding: 3mm; border-radius: 2mm; }
.qs { margin-top: 7mm; padding: 5mm; border: .3mm solid #dfe4f1; border-radius: 3mm; break-inside: avoid; }
.qs h3 { font-family: 'Sora', sans-serif; font-weight: 700; margin: 0 0 3mm; color: #5a73aa; font-size: 11pt; }
.qs li { margin-bottom: 3mm; } .qs .lines { height: 11mm; border-bottom: .3mm dotted #c4cbdd; }
.end { break-before: page; page: plain; height: 172mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.end .k { font-size: 7pt; font-weight: 700; letter-spacing: .24em; text-transform: uppercase; color: #5a73aa; }
.end h2 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 20pt; letter-spacing: -.02em; margin: 3mm 0 4mm; }
.end p { font-size: 9.6pt; color: #4b5266; margin: 0 auto 5mm; max-width: 95mm; }
.end .url { display: inline-block; margin: 2mm auto; padding: 3mm 5mm; border-radius: 10mm; background: #121a33; color: #fff; font-weight: 700; font-size: 8.6pt; text-decoration: none; }
.back { break-before: page; page: plain; display: flex; flex-direction: column; min-height: 172mm; }
.back h2 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 17pt; letter-spacing: -.02em; margin: 0 0 2mm; }
.back > p { font-size: 9pt; color: #4b5266; margin: 0 0 5mm; }
.back ul { list-style: none; padding: 0; margin: 0 0 6mm; }
.back li { padding: 2.2mm 0; border-bottom: .25mm solid #e3e7f2; font-family: 'Sora', sans-serif; font-weight: 700; font-size: 9.4pt; line-height: 1.3; }
.back li span { display: block; font-family: 'Fira Sans', sans-serif; font-weight: 400; font-size: 7.4pt; color: #6b7285; }
.back .site { margin-top: auto; background: #0e1530; color: #eef1f8; border-radius: 3mm; padding: 5mm; font-size: 8.4pt; line-height: 1.7; }
.back .site b { font-family: 'Sora', sans-serif; font-size: 12pt; display: block; margin-bottom: 1mm; }
.back .site a { color: #a3b7ea; text-decoration: none; }
.back .legal { font-size: 7pt; color: #8a93ab; margin-top: 4mm; text-align: center; }
"""


def pdf_body(a):
    body = re.sub(VIDEO_RE, r'<p class="vid">▶ YouTube: <a href="https://youtu.be/\1">\2</a></p>', a['body'])
    return body.replace('{{root}}', SITE['baseUrl'])


def top_blocks(body):
    return [m.group(0) for m in re.finditer(r'<(p|h2|h3|blockquote|ul|ol|div|figure|section)\b[^>]*>.*?</\1>', body, re.S)]


def preview_cut(body, share=.3):
    """First ~30% of an article, never ending on a heading."""
    blocks = top_blocks(body)
    n = max(4, round(len(blocks) * share))
    keep = blocks[:n]
    while keep and re.match(r'<h[23]', keep[-1]):
        keep.pop()
    return ''.join(keep)


def pdf_html(spec):
    """spec: lang, title, subtitle, image, cat, arts, study, preview, url, kind ('single'|'bundle')."""
    lang, tx = spec['lang'], PDF_TEXT[spec['lang']]
    arts, single, preview = spec['arts'], spec['kind'] == 'single', spec['preview']
    year = datetime.date.today().year
    parts = []
    for i, a in enumerate(arts):
        body = pdf_body(a)
        if preview:
            body = preview_cut(body, .3 if single else .45)
        q = ''
        if spec.get('study') and a['slug'] in STUDY_QUESTIONS and not preview:
            q = f'<section class="qs"><h3>{tx["questions"]}</h3><ol>' + ''.join(
                f'<li>{e(s)}<div class="lines"></div></li>' for s in STUDY_QUESTIONS[a['slug']]) + '</ol></section>'
        hero = '' if single else f'<img class="hero" src="file://{ROOT}/assets/img/{a["image"]}.jpg">'
        head = '' if single else f'<div class="cat">{e(a["category"])}</div><h1>{e(a["title"])}</h1>'
        by = f'<div class="by">{tx["by"]} {e(a["author"])}</div>' if not single else ''
        parts.append(f'<section class="art" id="a{i}">{hero}{head}{by}<div class="prose">{body}</div>{q}</section>')
        if preview:
            break
    toc = ''
    if not single:
        toc = f'<section class="toc"><h2>{tx["contents"]}</h2><ol>' + ''.join(
            f'<li><a href="#a{i}">{e(a["title"])}<span>{e(a["category"])}</span></a></li>' for i, a in enumerate(arts)) + '</ol></section>'
    end = ''
    if preview:
        end = (f'<section class="end"><div class="k">{tx["preview"]}</div><h2>{tx["continue"]}…</h2><p>{tx["continueText"]}</p>'
               f'<p>{tx["getFull"]}</p><a class="url" href="{spec["url"]}">{spec["url"].replace("https://", "")}</a></section>')
    others = [b for b in ARTS[lang] if b not in arts and b['format'] != 'link'][:6]
    back = (f'<section class="back"><h2>{tx["more"]}</h2><p>{tx["moreText"]}</p><ul>' +
            ''.join(f'<li>{e(b["title"])}<span>{e(b["category"])} · {T[lang]["fmt"]["book"] if b.get("kind") == "book" else T[lang]["fmt"][b["format"]]}</span></li>' for b in others) +
            f'</ul><div class="site"><b>Injili Milele</b><a href="{SITE["baseUrl"]}{lang}/">{SITE["baseUrl"].replace("https://", "")}{lang}/</a><br>'
            f'WhatsApp {SITE["phoneDisplay"]} · {SITE["email"]}</div>'
            f'<p class="legal">© {year} {e(SITE["author"])} · Injili Milele. {tx["rights"]}</p></section>')
    single_by = e(arts[0]['author']) if single else e(SITE['author'])
    badge = f'<b>{tx["preview"]}</b>' if preview else '<span>PDF</span>'
    running = spec['title'] if len(spec['title']) < 48 else spec['title'][:46].rsplit(' ', 1)[0] + '…'
    css = PDF_CSS.replace('__RUNNING__', running.replace('"', '\\"'))
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{e(spec['title'])}</title>
<link rel="stylesheet" href="{FONTS}"><style>{css}</style></head><body>
<section class="cover"><div class="art"><img src="file://{ROOT}/assets/img/{spec['image']}.jpg">
<div class="k"><span>Injili Milele</span>{badge}</div></div>
<div class="info"><div class="cat">{e(spec['cat'])}</div><h1>{e(spec['title'])}</h1><p>{e(spec['subtitle'])}</p>
<div class="a"><span>{single_by}</span><span>{year}</span></div></div></section>
{toc}{''.join(parts)}{end}{back}
</body></html>'''


def chrome_pdf(doc, dest):
    tmp = os.path.join(ROOT, '.pdf-build')
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    src = os.path.join(tmp, os.path.basename(dest) + '.html')
    open(src, 'w', encoding='utf-8').write(doc)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files',
                    '--virtual-time-budget=20000', f'--print-to-pdf={dest}', 'file://' + src],
                   check=True, capture_output=True, timeout=240)


def pdf_specs():
    """Every PDF the site sells or gives away: one per library item, plus the bundles."""
    specs = []
    for lang in ('sw', 'en'):
        for a in ARTS[lang]:
            if a['has_pdf']:
                specs.append({'id': a['pid'], 'lang': lang, 'title': a['title'], 'subtitle': a['excerpt'][:180].rsplit(' ', 1)[0] + '…'
                              if len(a['excerpt']) > 180 else a['excerpt'], 'image': a['image'], 'cat': a['category'],
                              'arts': [a], 'kind': 'single', 'file': a.get('pdfFile'), 'url': SITE['baseUrl'] + art_path(a)})
    for x in BUNDLES:
        specs.append({'id': x['id'], 'lang': x['lang'], 'title': x['title'], 'subtitle': x['subtitle'], 'image': x['image'],
                      'cat': 'PDF', 'arts': articles_for(x), 'kind': 'bundle', 'study': x['type'] == 'study',
                      'url': SITE['baseUrl'] + prod_path(x['lang'], x)})
    return specs


def build_pdfs(only=None):
    """Full PDF -> store-private/pdf/<id>.pdf, free preview -> store-private/preview/<id>.pdf,
    page thumbnails -> assets/img/pages/, page counts -> content/pdfmeta.json."""
    try:
        import pymupdf
    except ImportError:
        sys.exit('PyMuPDF is needed for --pdf: python3 -m venv .venv && .venv/bin/pip install pymupdf, then use .venv/bin/python')
    meta = dict(PDFMETA)
    thumbs_dir = os.path.join(ROOT, 'assets/img/pages')
    os.makedirs(thumbs_dir, exist_ok=True)
    for spec in pdf_specs():
        if only and spec['id'] not in only:
            continue
        full = os.path.join(PRIVATE, 'pdf', spec['id'] + '.pdf')
        prev = os.path.join(PRIVATE, 'preview', spec['id'] + '.pdf')
        os.makedirs(os.path.dirname(prev), exist_ok=True)
        if spec.get('file'):
            # an uploaded PDF is sold as it is; its preview is the first pages
            shutil.copy(os.path.join(ROOT, 'content/files', spec['file']), full)
            d = pymupdf.open(full)
            p = pymupdf.open()
            p.insert_pdf(d, to_page=max(1, min(d.page_count // 3, 6)) - 1)
            p.save(prev)
        else:
            chrome_pdf(pdf_html(dict(spec, preview=False)), full)
            chrome_pdf(pdf_html(dict(spec, preview=True)), prev)
        d, p = pymupdf.open(full), pymupdf.open(prev)
        n = min(3, p.page_count)
        for i in range(n):
            pg = p[i]
            z = 420 / pg.rect.width
            pg.get_pixmap(matrix=pymupdf.Matrix(z, z)).save(os.path.join(thumbs_dir, f"{spec['id']}-{i + 1}.jpg"), jpg_quality=78)
        meta[spec['id']] = {'pages': d.page_count, 'previewPages': p.page_count, 'kb': os.path.getsize(full) // 1024, 'thumbs': n}
        print(f"pdf {spec['id']}: {d.page_count} pages ({meta[spec['id']]['kb']} KB), preview {p.page_count} pages")
    json.dump(meta, open(PDFMETA_FILE, 'w'), indent=1, sort_keys=True)
    shutil.rmtree(os.path.join(ROOT, '.pdf-build'), ignore_errors=True)
    PDFMETA.clear()
    PDFMETA.update(meta)


def upload():
    """Push changed files to the payments Worker's KV store (pdf:<id> = full file, preview:<id> = free preview)."""
    import hashlib
    state_file = os.path.join(PRIVATE, '.uploaded.json')
    state = json.load(open(state_file)) if os.path.exists(state_file) else {}
    jobs = []
    for folder, prefix in (('pdf', 'pdf'), ('preview', 'preview')):
        d = os.path.join(PRIVATE, folder)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith('.pdf'):
                jobs.append((f'{prefix}:{f[:-4]}', os.path.join(d, f), 'application/pdf'))
    for lang in ('sw', 'en'):
        for a in ARTS[lang]:
            if a['format'] == 'audio' and a.get('audio'):
                jobs.append((f"pdf:{a['pid']}", os.path.join(ROOT, 'content/files', a['audio']), 'audio/mpeg'))
    for key, path, ctype in jobs:
        digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        if state.get(key) == digest:
            continue
        subprocess.run(['npx', 'wrangler', 'kv', 'key', 'put', '--binding=STORE', '--remote', key, '--path', path,
                        '--metadata', json.dumps({'type': ctype})], cwd=os.path.join(ROOT, 'payments'), check=True,
                       capture_output=True)
        state[key] = digest
        json.dump(state, open(state_file, 'w'), indent=1)
        print('uploaded', key)


def build_admin():
    """Admin dashboard: a standalone page (Firebase Auth + Firestore), not linked from the site."""
    d = os.path.join(OUT, 'admin')
    os.makedirs(d, exist_ok=True)
    src = open(os.path.join(ROOT, 'src/admin/index.html'), encoding='utf-8').read()
    cfg = dict(SITE['firebase'], superAdmin=SITE['superAdmin'], whatsapp=SITE['whatsapp'], payments=SITE['paymentsUrl'],
               siteUrl=SITE['baseUrl'], rules=open(os.path.join(ROOT, 'firebase/store.rules')).read())
    src = src.replace('/*CONFIG*/', 'window.ADMIN_CONFIG = ' + json.dumps(cfg, ensure_ascii=False) + ';')
    src = src.replace('{{BUILD_ID}}', BUILD_ID)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(src)
    shutil.copy(os.path.join(ROOT, 'src/admin/admin.js'), os.path.join(d, 'admin.js'))


BUILD_ID = datetime.datetime.now().strftime('%Y%m%d%H%M')


def main():
    if '--pdf' in sys.argv or '--upload' in sys.argv:
        if '--pdf' in sys.argv:
            only = [x for x in sys.argv[sys.argv.index('--pdf') + 1:] if not x.startswith('--')]
            build_pdfs(only or None)
        if '--upload' in sys.argv:
            upload()
        # rebuild the site in a fresh process so page counts and thumbnails are picked up
        subprocess.run([sys.executable, os.path.abspath(__file__)], check=True)
        return
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for lang in ('sw', 'en'):
        build_home(lang)
        for i, a in enumerate(ARTS[lang]):
            build_article(a, i)
        build_store(lang)
        build_cart(lang)
        build_thanks(lang)
        build_about(lang)
    build_root()
    statics()
    print(f'built {len(WRITTEN)} pages -> docs/')


if __name__ == '__main__':
    main()
