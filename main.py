"""
Telegram Consultation Bot — Crypto / Gaming / Forex Licenses
Requirements: pip install python-telegram-bot==20.*
Run: BOT_TOKEN= python fintecharbor_bot.py
"""

import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Replace with your token and manager username ───────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "YOUR_BOT_TOKEN_HERE")
MANAGER_CHAT_ID  = os.getenv("MANAGER_CHAT_ID", "YOUR_BOT_TOKEN_HERE")
# ────────────────────────────────────────────────────────────────────────────

# ConversationHandler states
WAITING_LEAD_NAME  = 1
WAITING_LEAD_PHONE = 2
WAITING_LEAD_MSG   = 3

# ─── VALIDATION ──────────────────────────────────────────────────────────────

PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")

# Blocks numbers with 6+ identical digits in a row (e.g. 777777, 111111)
REPEAT_RE = re.compile(r"(\d)\1{5,}")

# Known valid country code prefixes (1–3 digits)
VALID_COUNTRY_PREFIXES = {
    "1", "7",
    "20","27","30","31","32","33","34","36","39","40","41","43","44","45","46","47","48","49",
    "51","52","53","54","55","56","57","58","60","61","62","63","64","65","66",
    "81","82","84","86","90","91","92","93","94","95","98",
    "212","213","216","218","220","221","222","223","224","225","226","227","228","229",
    "230","231","232","233","234","235","236","237","238","239","240","241","242","243",
    "244","245","246","247","248","249","250","251","252","253","254","255","256","257",
    "258","260","261","262","263","264","265","266","267","268","269",
    "290","291","297","298","299",
    "350","351","352","353","354","355","356","357","358","359",
    "370","371","372","373","374","375","376","377","378","380","381","382","385","386",
    "387","389","420","421","423",
    "500","501","502","503","504","505","506","507","508","509",
    "590","591","592","593","594","595","596","597","598","599",
    "670","672","673","674","675","676","677","678","679","680","681","682","683","685",
    "686","687","688","689","690","691","692",
    "850","852","853","855","856","880","886",
    "960","961","962","963","964","965","966","967","968","970","971","972","973","974",
    "975","976","977","992","993","994","995","996","998",
}

def validate_name(text: str) -> str | None:
    text = text.strip()
    if len(text) < 3:
        return f"❗ Name must be at least 3 characters long. You entered {len(text)}."
    if len(text) > 100:
        return "❗ Name is too long (max 100 characters)."
    return None

def validate_phone(text: str) -> str | None:
    text = text.strip()

    # Allow Telegram username as alternative contact
    if text.startswith("@"):
        if len(text) < 5:
            return "❗ Telegram username is too short (e.g. @username)."
        if not re.match(r"^@[a-zA-Z0-9_]{4,32}$", text):
            return "❗ Invalid Telegram username. Use letters, digits and underscores (e.g. @username)."
        return None

    digits = re.sub(r"\D", "", text)

    # Length check
    if len(digits) < 7:
        return "❗ Phone number is too short. Please enter a valid number (e.g. +44 20 7946 0958)."
    if len(digits) > 15:
        return "❗ Phone number is too long (max 15 digits). Please check and re-enter."

    # Block repeated digits: 7777777, 1111111, etc.
    if REPEAT_RE.search(digits):
        return "❗ This doesn't look like a real phone number. Please enter your actual number."

    # Block sequential runs: 1234567, 9876543, etc.
    seq_fwd = "01234567890123456"
    seq_rev = "98765432109876543"
    if any(seq_fwd[i:i+7] in digits for i in range(len(seq_fwd) - 6)):
        return "❗ This doesn't look like a real phone number. Please enter your actual number."
    if any(seq_rev[i:i+7] in digits for i in range(len(seq_rev) - 6)):
        return "❗ This doesn't look like a real phone number. Please enter your actual number."

    # Must use at least 3 different digits
    if len(set(digits)) < 3:
        return "❗ This doesn't look like a real phone number. Please enter your actual number."

    # Format check: only allowed characters
    if not PHONE_RE.match(text):
        return (
            "❗ Invalid format. Use digits, spaces, dashes or parentheses "
            "(e.g. +44 20 7946 0958 or @username)."
        )

    # Country code check
    normalized = digits[2:] if digits.startswith("00") else digits
    if not any(normalized[:n] in VALID_COUNTRY_PREFIXES for n in (1, 2, 3)):
        return (
            "❗ Unrecognized country code. Please include your country code "
            "(e.g. +1 for USA, +44 for UK, +380 for Ukraine)."
        )

    return None

def validate_message(text: str) -> str | None:
    text = text.strip()
    if len(text) < 5:
        return f"❗ Request is too short. Please describe your needs in at least 5 characters (you entered {len(text)})."
    if len(text) > 2000:
        return "❗ Message is too long (max 2000 characters). Please shorten it."
    return None

# ─── DATA ────────────────────────────────────────────────────────────────────

LICENSES = {
    # ── CRYPTO ──────────────────────────────────────────────────────────────
    "crypto_mica": {
        "title": "🇪🇺 Crypto License in EU (CASP under MiCA)",
        "emoji": "🇪🇺",
        "description": (
            "MiCA is the first EU-wide crypto regulation, "
            "allowing your business to operate across all EU "
            "member states with a single license.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Valid across all 27 EU member states\n"
            "• Covers exchanges, custodians, issuers & advisors\n"
            "• Fully enforced from December 2024\n"
            "• Requires AML/KYC program, capital requirements & technical standards\n\n"
            "⏱ <b>Timeline:</b> 4–6 months\n"
            "✅ Best for companies targeting the European market with full regulatory compliance."
        ),
    },
    "crypto_swiss": {
        "title": "🇨🇭 Crypto License in Switzerland (CASP)",
        "emoji": "🇨🇭",
        "description": (
            "License provides strong legal clarity for crypto, reliable banking access, "
            "and high investor trust in a top-tier financial jurisdiction.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Mandatory SRO membership (e.g. VQF)\n"
            "• Covers exchanges, wallets, DeFi & token issuers\n"
            "• Switzerland is not an EU state — separate passport\n\n"
            "⏱ <b>Timeline:</b> 5–6 months\n"
            "✅ Ideal for companies wanting a premium European brand with Swiss credibility."
        ),
    },
    "crypto_canada": {
        "title": "🇨🇦 Crypto License in Canada (MSB)",
        "emoji": "🇨🇦",
        "description": (
            "License provides strong regulatory credibility, "
            "access to banking and payment systems, and enables crypto projects "
            "to legally operate, process transactions, and build trusted global services.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Covers crypto exchanges & money transfer\n"
            "• No minimum capital requirement\n"
            "• Can be obtained 100% remotely\n\n"
            "⏱ <b>Timeline:</b> 5–7 months\n"
            "✅ Perfect for startups needing a regulated entity quickly and cost-effectively."
        ),
    },
    "crypto_mauritius": {
        "title": "🇲🇺 Crypto License in Mauritius (VASP)",
        "emoji": "🇲🇺",
        "description": (
            "Fast licensing, low operational costs, flexible regulation, "
            "and access to international markets.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Regulated by the FSC — FATF-compliant jurisdiction\n"
            "• Covers exchanges, custodians, portfolio managers\n"
            "• Tax-efficient jurisdiction (0–15% corporate tax)\n"
            "• Growing fintech hub in Africa/Asia corridor\n\n"
            "⏱ <b>Timeline:</b> 3–6 months\n"
            "✅ Great for companies serving African and Asian markets."
        ),
    },
    "crypto_elsalvador": {
        "title": "🇸🇻 Crypto License in El Salvador (DASP)",
        "emoji": "🇸🇻",
        "description": (
            "Legal recognition of crypto, fast setup, low taxes on crypto activities, "
            "and a supportive regulatory environment.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Pioneer crypto-friendly jurisdiction\n"
            "• Regulated by the Central Reserve Bank (BCR)\n"
            "• Low tax environment, no capital gains tax on Bitcoin\n"
            "• Covers exchanges, custodians & payment providers\n\n"
            "⏱ <b>Timeline:</b> 3–4 months\n"
            "✅ Excellent for innovative crypto businesses seeking a progressive jurisdiction."
        ),
    },
    "crypto_alternative": {
        "title": "🌐 Alternative Crypto Setup",
        "emoji": "🌐",
        "description": (
            "This setup provides a fast, cost-effective, and highly flexible legal foundation "
            "for your project, utilizing Legal Opinions instead of formal licensing to operate "
            "compliantly in business-friendly jurisdictions.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• No formal VASP/CASP license required (Opinion-backed compliance)\n"
            "• Low barrier to entry with minimal regulatory and reporting burdens\n"
            "• Supported by professional Non-Security and Tokenomics Legal Opinions\n"
            "• Tax-efficient corporate structures\n\n"
            "⏱ <b>Timeline:</b> 3–4 weeks\n"
            "✅ Ideal for: Web3 startups, DeFi protocols, DAOs, and utility token issuers "
            "needing a rapid, budget-friendly legal wrapper to launch globally."
        ),
    },
    # ── GAMING ──────────────────────────────────────────────────────────────
    "gaming_anjouan": {
        "title": "🎰 Anjouan Gaming License",
        "emoji": "🎰",
        "description": (
            "No physical presence or local office requirement, "
            "with broad acceptance by many PSPs, payment platforms, and processors.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Covers online casino, sports betting & poker\n"
            "• Fast issuance, low government fees\n"
            "• Competitive annual renewal costs\n\n"
            "⏱ <b>Timeline:</b> 2–3 months\n"
            "✅ Ideal for startups entering online gaming quickly."
        ),
    },
    "gaming_tobique": {
        "title": "🎲 Tobique Gaming License",
        "emoji": "🎲",
        "description": (
            "A straightforward remote registration process, "
            "no need for a physical office, and no requirement for local shareholders.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Canadian First Nation jurisdiction\n"
            "• Excellent banking access — accepted by Visa/Mastercard\n"
            "• Covers casino, sports betting, skill games\n"
            "• Responsive regulator with reasonable compliance requirements\n\n"
            "⏱ <b>Timeline:</b> 2–4 months\n"
            "✅ Great for operators who need strong payment processing options."
        ),
    },
    "gaming_nevis": {
        "title": "🏝 Nevis Gaming License",
        "emoji": "🏝",
        "description": (
            "Quick licensing procedure with 0% tax "
            "on gross gaming revenue earned from other countries.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Caribbean jurisdiction with strong asset protection laws\n"
            "• Low tax & no corporate tax on offshore income\n"
            "• Covers casino, poker & sports betting\n"
            "• Flexible company structure options\n\n"
            "⏱ <b>Timeline:</b> 2–3 months\n"
            "✅ Good for operators prioritizing privacy and asset protection."
        ),
    },
    "gaming_kahnawake": {
        "title": "🍁 Kahnawake Gaming License",
        "emoji": "🍁",
        "description": (
            "A single license covering a wide range of activities "
            "with a simplified licensing process.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Highly recognized by major payment processors\n"
            "• Covers online casino, poker rooms & sports books\n"
            "• Strict compliance requirements — adds legitimacy\n\n"
            "⏱ <b>Timeline:</b> 3–4 months\n"
            "✅ One of the most credible licenses for established operators."
        ),
    },
    "gaming_costarica": {
        "title": "🌴 Costa Rica Gaming License",
        "emoji": "🌴",
        "description": (
            "Fast incorporation with no lengthy approval process, "
            "local director, or physical office required.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• No formal gaming regulator — minimal compliance burden\n"
            "• Very low operating costs\n"
            "• Popular for crypto gambling & sportsbooks\n"
            "• Not accepted by Visa/Mastercard for payment processing\n\n"
            "⏱ <b>Timeline:</b> 2–4 weeks\n"
            "✅ Best for crypto-first gambling operations on a tight budget."
        ),
    },
    "gaming_curacao": {
        "title": "🌊 Curaçao Gaming License",
        "emoji": "🌊",
        "description": (
            "Widely recognized by players, partners, and payment providers, "
            "with a quick and straightforward licensing process.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Newly reformed under the National Ordinance on Offshore Games of Hazard\n"
            "• Covers casino, sports betting, lottery, poker\n"
            "• Now requires full KYC/AML compliance program\n"
            "• 2% gaming tax on gross gaming revenue\n\n"
            "⏱ <b>Timeline:</b> 4–5 months\n"
            "✅ The industry standard for mid-size operators worldwide."
        ),
    },
    # ── FOREX ───────────────────────────────────────────────────────────────
    "forex_mauritius": {
        "title": "🇲🇺 Forex License in Mauritius",
        "emoji": "🇲🇺",
        "description": (
            "Fast and cost-effective licensing with flexible requirements, "
            "making it ideal for quickly launching and operating in global markets.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• FATF-compliant, IOSCO member\n"
            "• Covers Forex, CFDs, equities & derivatives\n"
            "• Excellent banking access and double tax treaties\n\n"
            "⏱ <b>Timeline:</b> 3–4 months\n"
            "✅ Premium Forex license with strong global recognition."
        ),
    },
    "forex_seychelles": {
        "title": "🏝 Forex License in Seychelles",
        "emoji": "🏝",
        "description": (
            "A regulated and reputable jurisdiction with access "
            "to banking and international infrastructure while maintaining reasonable costs.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Regulated by FSA Seychelles (IOSCO associate)\n"
            "• Covers Forex, CFDs, crypto brokerage\n"
            "• Very favorable tax regime (0% corporate tax offshore)\n\n"
            "⏱ <b>Timeline:</b> 3–5 months\n"
            "✅ The go-to license for new brokers — affordable, fast, globally accepted."
        ),
    },
    "forex_labuan": {
        "title": "🇲🇾 Forex License in Labuan, Malaysia (Money Broking)",
        "emoji": "🇲🇾",
        "description": (
            "Labuan FSA offers a Money Broking License in a well-regulated "
            "Asian financial hub with strong international credibility and "
            "access to Asian banking infrastructure.\n\n"
            "📌 <b>Key facts:</b>\n"
            "• Regulated by Labuan FSA — FATF-compliant, IOSCO member\n"
            "• Covers Forex, CFDs, money broking & financial advisory\n"
            "• Low corporate tax: 3% on net profit (or flat RM 20,000/year)\n"
            "• Access to Malaysia's extensive double tax treaty network (70+ countries)\n"
            "• Strong banking access — local and international banks\n"
            "• 100% foreign ownership permitted\n\n"
            "⏱ <b>Timeline:</b> 3–6 months\n"
            "✅ Ideal for brokers targeting Asian markets who need a reputable, "
            "cost-efficient regulated entity."
        ),
    },
}

# ─── MENUS ───────────────────────────────────────────────────────────────────

MAIN_MENU_TEXT = (
    "👋 Welcome to <b>Fintech Harbor Consulting!</b>\n\n"
    "We help businesses register, obtain licenses in crypto, fintech, and gaming, "
    "open bank accounts, and operate legally anywhere in the world. "
    "We cover the entire cycle — from choosing "
    "the right jurisdiction to delivering the final documents.\n\n"
    "📂 Please choose a category to get started:"
)

CATEGORIES = {
    "crypto": {
        "label": "₿  CRYPTO & MSB LICENSES",
        "emoji": "₿",
        "intro": (
            "🔐 <b>CRYPTO &amp; MSB LICENSES</b>\n\n"
            "We help crypto companies get regulated across the globe — from "
            "the EU's MiCA framework to fast options in other jurisdictions.\n\n"
            "Choose a service below:"
        ),
        "items": [
            ("crypto_mica",        "🇪🇺 EU (MiCA)"),
            ("crypto_swiss",       "🇨🇭 Switzerland (CASP)"),
            ("crypto_canada",      "🇨🇦 Canada (MSB)"),
            ("crypto_mauritius",   "🇲🇺 Mauritius (VASP)"),
            ("crypto_elsalvador",  "🇸🇻 El Salvador (DASP)"),
            ("crypto_alternative", "🌐 Alternative Crypto Setup"),
        ],
    },
    "gaming": {
        "label": "🎰 Gaming Licenses",
        "emoji": "🎰",
        "intro": (
            "🎮 <b>Gaming Licenses</b>\n\n"
            "We cover the full spectrum of iGaming jurisdictions — from "
            "budget-friendly options to premium regulated markets.\n\n"
            "Choose a service below:"
        ),
        "items": [
            ("gaming_curacao",   "🌊 Curaçao Gaming License"),
            ("gaming_tobique",   "🎲 Tobique Gaming License"),
            ("gaming_nevis",     "🏝 Nevis Gaming License"),
            ("gaming_kahnawake", "🍁 Kahnawake Gaming License"),
            ("gaming_costarica", "🌴 Costa Rica Gaming License"),
            ("gaming_anjouan",   "🎰 Anjouan Gaming License"),
        ],
    },
    "forex": {
        "label": "📈 Forex Licenses",
        "emoji": "📈",
        "intro": (
            "📊 <b>Forex &amp; Brokerage Licenses</b>\n\n"
            "We help Forex brokers and financial companies get properly regulated.\n\n"
            "Choose a jurisdiction or service:"
        ),
        "items": [
            ("forex_mauritius",  "🇲🇺 Forex License in Mauritius"),
            ("forex_seychelles", "🏝 Forex License in Seychelles"),
            ("forex_labuan",     "🇲🇾 Forex License in Labuan (Malaysia)"),
        ],
    },
}

# ─── OTHER SERVICES ──────────────────────────────────────────────────────────

OTHER_SERVICES = [
    (
        "os_company",
        "🏢 Company Registration",
        (
            "🏢 <b>Company Registration</b>\n\n"
            "We handle the full incorporation process — from jurisdiction selection "
            "and document preparation to nominee services and registered office setup.\n\n"
            "🌍 <b>Available jurisdictions:</b>\n"
            "• UK, USA, EU countries\n"
            "• UAE, Singapore, Hong Kong, Cyprus\n"
            "• Offshore: BVI, Cayman, Seychelles and more\n\n"
            "📩 Contact us to find the right structure for your business."
        ),
    ),
    (
        "os_bank",
        "🏦 Bank Account Opening",
        (
            "🏦 <b>Bank Account Opening</b>\n\n"
            "We open corporate, crypto-friendly, and EMI accounts for both "
            "traditional and high-risk businesses.\n\n"
            "💳 <b>Account types:</b>\n"
            "• Corporate bank accounts (EU, UK, Asia, Caribbean)\n"
            "• EMI / IBAN accounts — fast & remote-friendly\n"
            "• Crypto-friendly accounts for VASPs & exchanges\n"
            "• High-risk business accounts (gaming, forex, crypto)\n\n"
            "📩 Tell us about your business and we'll match you with the right bank."
        ),
    ),
    (
        "os_trademark",
        "™️ Trademark & IP Protection",
        (
            "™️ <b>Trademark Registration &amp; IP Protection</b>\n\n"
            "Protect your brand in key markets before competitors do.\n\n"
            "🌍 <b>We register trademarks in:</b>\n"
            "• EU (EUIPO) — covers all 27 member states\n"
            "• USA (USPTO)\n"
            "• UK (UKIPO)\n"
            "• International (WIPO Madrid Protocol — 130+ countries)\n\n"
            "📩 Contact us to start protecting your brand today."
        ),
    ),
    (
        "os_lawyer",
        "⚖️ Lawyer Consultation",
        (
            "⚖️ <b>Lawyer Consultation</b>\n\n"
            "Get expert legal assistance tailored to your inquiry.\n\n"
            "📋 <b>We cover:</b>\n"
            "• License selection & jurisdiction strategy\n"
            "• Regulatory compliance & AML/KYC policies\n"
            "• Corporate structuring & due diligence\n"
            "• Contract review & legal risk assessment\n\n"
            "📩 Submit a request and our lawyer will get back to you shortly."
        ),
    ),
    (
        "os_other",
        "📋 Other Services",
        (
            "📋 <b>Other Services</b>\n\n"
            "We provide a full range of legal and compliance documents for "
            "crypto, fintech and gaming projects:\n\n"
            "• 📄 Drafting contracts & commercial agreements\n"
            "• 📝 Terms & Conditions, Privacy Policies\n"
            "• 🔐 AML/KYC frameworks & compliance programs\n"
            "• ⚖️ Legal opinions for crypto, fintech & gaming\n"
            "• 🔍 Regulatory gap analysis & compliance audits\n\n"
            "📩 Tell us what you need and we'll prepare the right documents."
        ),
    ),
]

OTHER_SERVICES_TEXTS = {key: text for key, _, text in OTHER_SERVICES}

# ─── KEYBOARDS ───────────────────────────────────────────────────────────────

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("₿  Crypto Licenses",   callback_data="cat_crypto")],
        [InlineKeyboardButton("🎰 Gaming Licenses",    callback_data="cat_gaming")],
        [InlineKeyboardButton("📈 Forex Licenses",     callback_data="cat_forex")],
        [
            InlineKeyboardButton("📋 Other Services",  callback_data="other_list"),
            InlineKeyboardButton("📞 Contact Us",      callback_data="contact"),
        ],
        [InlineKeyboardButton("🆓 Free Consultation",  callback_data="free_consult")],
    ])


def other_services_keyboard(active_key: str = ""):
    buttons = []
    for key, label, _ in OTHER_SERVICES:
        marker = "▶️ " if key == active_key else ""
        buttons.append([InlineKeyboardButton(f"{marker}{label}", callback_data=f"os_{key[3:]}")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def category_keyboard(cat_key: str):
    cat = CATEGORIES[cat_key]
    buttons = []
    for key, label in cat["items"]:
        buttons.append([InlineKeyboardButton(label, callback_data=f"lic_{key}")])
    buttons.append([InlineKeyboardButton("🌐 Interested in another jurisdiction? Let's discuss.", callback_data="contact")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def license_keyboard(cat_key: str, lic_key: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Request a Free Quote", callback_data="free_consult")],
        [InlineKeyboardButton("💬 Talk to a Manager",    callback_data="contact")],
        [
            InlineKeyboardButton("◀️ Back", callback_data=f"cat_{cat_key}"),
            InlineKeyboardButton("🏠 Menu",  callback_data="main_menu"),
        ],
    ])


def back_to_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])


def lead_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_lead")]
    ])


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def find_cat_for_license(lic_key: str) -> str:
    for cat_key, cat in CATEGORIES.items():
        all_keys = [k for k, _ in cat["items"]]
        if lic_key in all_keys:
            return cat_key
    return "crypto"


# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Use /start to open the main menu.\n\n"
        "You can also type /other_service to see other services,\n"
        "or /contact to get in touch with our team.",
        parse_mode="HTML",
    )


async def other_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 <b>Other Services</b>\n\nChoose a service below:",
        reply_markup=other_services_keyboard(),
        parse_mode="HTML",
    )


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 <b>Contact Us</b>\n\nReach our team directly:\n• Telegram: {MANAGER_USERNAME}\n"
        "• Response time: within 1 business day\n\nOr press below to leave a lead request 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Leave a Request", callback_data="free_consult")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]),
        parse_mode="HTML",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML"
        )

    elif data == "noop":
        return

    elif data.startswith("cat_"):
        cat_key = data[4:]
        cat = CATEGORIES[cat_key]
        await query.edit_message_text(
            cat["intro"], reply_markup=category_keyboard(cat_key), parse_mode="HTML"
        )

    elif data.startswith("lic_"):
        lic_key = data[4:]
        cat_key = find_cat_for_license(lic_key)
        if lic_key in LICENSES:
            info = LICENSES[lic_key]
            text = f"{info['title']}\n\n{info['description']}"
        else:
            text = "ℹ️ Details coming soon. Please contact our team."
        await query.edit_message_text(
            text, reply_markup=license_keyboard(cat_key, lic_key), parse_mode="HTML"
        )

    elif data == "other_list":
        await query.edit_message_text(
            "📋 <b>Other Services</b>\n\nChoose a service below:",
            reply_markup=other_services_keyboard(),
            parse_mode="HTML",
        )

    elif data.startswith("os_"):
        full_key = data
        text = OTHER_SERVICES_TEXTS.get(full_key)
        if text:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Request a Free Quote", callback_data="free_consult")],
                [InlineKeyboardButton("💬 Talk to a Manager",    callback_data="contact")],
                [
                    InlineKeyboardButton("◀️ Back", callback_data="other_list"),
                    InlineKeyboardButton("🏠 Menu",  callback_data="main_menu"),
                ],
            ])
            await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            await query.edit_message_text(
                "ℹ️ Details coming soon. Please contact our team.",
                reply_markup=back_to_main(),
                parse_mode="HTML",
            )

    elif data == "contact":
        await query.edit_message_text(
            f"📞 <b>Contact Our Team</b>\n\n"
            f"💬 Manager: {MANAGER_USERNAME}\n"
            "🕐 Response time: within 1 business day\n\n"
            "Or submit a request and we'll call you back! 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Submit a Request", callback_data="free_consult")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML",
        )

    elif data == "free_consult":
        await query.edit_message_text(
            "🆓 <b>Free Consultation Request</b>\n\n"
            "Let's get you connected with our expert team!\n\n"
            "👤 Please enter your <b>name</b>:\n"
            "<i>(minimum 3 characters)</i>",
            reply_markup=lead_cancel_keyboard(),
            parse_mode="HTML",
        )
        return WAITING_LEAD_NAME

    elif data == "cancel_lead":
        await query.edit_message_text(
            "❌ Request cancelled.\n\n" + MAIN_MENU_TEXT,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return ConversationHandler.END


# ─── CONVERSATION: Lead Capture ──────────────────────────────────────────────

async def lead_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    error = validate_name(text)
    if error:
        await update.message.reply_text(
            f"{error}\n\n"
            "👤 Please re-enter your <b>name</b>:\n"
            "<i>(minimum 3 characters)</i>",
            reply_markup=lead_cancel_keyboard(),
            parse_mode="HTML",
        )
        return WAITING_LEAD_NAME

    context.user_data["lead_name"] = text
    await update.message.reply_text(
        f"✅ Nice to meet you, <b>{text}</b>!\n\n"
        "📱 Now please enter your <b>phone number</b> or <b>Telegram username</b>:\n"
        "<i>(e.g. +1 234 567 8900 or @username)</i>",
        reply_markup=lead_cancel_keyboard(),
        parse_mode="HTML",
    )
    return WAITING_LEAD_PHONE


async def lead_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    error = validate_phone(text)
    if error:
        await update.message.reply_text(
            f"{error}\n\n"
            "📱 Please re-enter your <b>phone number</b> or <b>Telegram username</b>:\n"
            "<i>(e.g. +1 234 567 8900 or @username)</i>",
            reply_markup=lead_cancel_keyboard(),
            parse_mode="HTML",
        )
        return WAITING_LEAD_PHONE

    context.user_data["lead_phone"] = text
    await update.message.reply_text(
        "📋 Almost done! Please briefly describe <b>what you need</b>:\n"
        "<i>(minimum 5 characters, e.g. «Crypto license in EU»)</i>",
        reply_markup=lead_cancel_keyboard(),
        parse_mode="HTML",
    )
    return WAITING_LEAD_MSG


async def lead_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    error = validate_message(text)
    if error:
        await update.message.reply_text(
            f"{error}\n\n"
            "📋 Please describe <b>what you need</b>:\n"
            "<i>(minimum 5 characters)</i>",
            reply_markup=lead_cancel_keyboard(),
            parse_mode="HTML",
        )
        return WAITING_LEAD_MSG

    context.user_data["lead_msg"] = text

    user = update.effective_user
    name  = context.user_data.get("lead_name", "—")
    phone = context.user_data.get("lead_phone", "—")
    msg   = context.user_data.get("lead_msg", "—")
    tg_link = f"@{user.username}" if user.username else f"tg://user?id={user.id}"

    if MANAGER_CHAT_ID:
        lead_text = (
            "🔔 <b>New Lead!</b>\n\n"
            f"👤 Name: {name}\n"
            f"📱 Contact: {phone}\n"
            f"📋 Request: {msg}\n"
            f"🔗 Telegram: {tg_link}"
        )
        for manager in MANAGER_CHAT_ID:

            await update.get_bot().send_message(
                    manager, lead_text, parse_mode="HTML"
                )

    await update.message.reply_text(
        "🎉 <b>Request Submitted!</b>\n\n"
        f"Thank you, <b>{name}</b>! Our team will contact you shortly.\n\n"
        f"💬 You can also reach us directly: {MANAGER_USERNAME}",
        reply_markup=back_to_main(),
        parse_mode="HTML",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def lead_cancel_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Request cancelled.\n\nUse /start to return to the main menu.",
        parse_mode="HTML",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── ERROR HANDLER ───────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception:", exc_info=context.error)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^free_consult$")],
        states={
            WAITING_LEAD_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_name)],
            WAITING_LEAD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_phone)],
            WAITING_LEAD_MSG:   [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_message)],
        },
        fallbacks=[
            CommandHandler("cancel", lead_cancel_text),
            CallbackQueryHandler(button_handler, pattern="^cancel_lead$"),
        ],
        per_message=False,
    )

    app.add_handler(CommandHandler("start",         start))
    app.add_handler(CommandHandler("help",          help_command))
    app.add_handler(CommandHandler("other_service", other_command))
    app.add_handler(CommandHandler("contact",       contact_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("Bot started. Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()