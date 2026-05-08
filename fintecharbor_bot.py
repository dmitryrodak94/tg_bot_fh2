"""
Telegram Consultation Bot — Crypto / Gaming / Forex Licenses
Requirements: pip install python-telegram-bot==20.*
Run: BOT_TOKEN= python fintecharbor_bot.py
"""

import logging
import os
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
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "YOUR_BOT_TOKEN_HERE")         # shown in CTAs
MANAGER_CHAT_ID  = os.getenv("MANAGER_CHAT_ID", "YOUR_BOT_TOKEN_HERE")                  # int chat_id to forward leads
# ────────────────────────────────────────────────────────────────────────────

# ConversationHandler states
WAITING_LEAD_NAME  = 1
WAITING_LEAD_PHONE = 2
WAITING_LEAD_MSG   = 3

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
            ("crypto_mica",       "🇪🇺 EU (MiCA)"),
            ("crypto_swiss",      "🇨🇭 Switzerland (CASP)"),
            ("crypto_canada",     "🇨🇦 Canada (MSB)"),
            ("crypto_mauritius",  "🇲🇺 Mauritius (VASP)"),
            ("crypto_elsalvador", "🇸🇻 El Salvador (DASP)"),
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
        ],
    },
}

# ─── OTHER SERVICES items (shown when "Other Services" button is pressed) ────
# Each item: ("callback_key", "Button Label", "Full text shown to user")
OTHER_SERVICES = [
    (
        "os_company",
        "🏢 Company Registration",
        (
            "🏢 <b>Company Registration</b>\n\n"
            "We handle the full incorporation process — from jurisdiction selection and document "
            "preparation to nominee services and registered office setup.\n\n"
            "🌍 Popular jurisdictions: UK, USA, EU, UAE, Singapore, Hong Kong, Cyprus, "
            "BVI, Cayman, Seychelles and other offshore jurisdictions.\n"
            "⏱ Timeline: 1–4 weeks depending on jurisdiction"
        ),
    ),
    (
        "os_bank",
        "🏦 Business Bank Account",
        (
            "🏦 <b>Business Bank Account Opening</b>\n\n"
            "Opening a business bank account is often the hardest part — but we have "
            "established relationships with banks and EMIs globally.\n\n"
            "💳 <b>We work with:</b>\n"
            "• Traditional banks in EU, UK, Asia, Caribbean\n"
            "• EMI/IBAN providers (fast & remote-friendly)\n"
            "• Crypto-friendly banks for VASPs\n\n"
            "⏱ Timeline: 2–8 weeks"
        ),
    ),
    (
        "os_trademark",
        "™️ Trademark Registration",
        (
            "™️ <b>Trademark Registration &amp; IP Protection</b>\n\n"
            "Protect your brand in key markets before competitors do.\n\n"
            "🌍 <b>We register trademarks in:</b>\n"
            "• EU (EUIPO) — covers all 27 member states\n"
            "• USA (USPTO)\n"
            "• UK (UKIPO)\n"
            "• International (WIPO Madrid Protocol — 130+ countries)\n\n"
            "⏱ Timeline: 3–18 months (varies by jurisdiction)"
        ),
    ),
    (
        "os_lawyer",
        "⚖️ Lawyer Consultation",
        (
            "⚖️ <b>Consultation with a Lawyer</b>\n\n"
            "Get expert legal assistance tailored to your situation.\n\n"
            "📋 <b>We cover:</b>\n"
            "• License selection & jurisdiction strategy\n"
            "• Regulatory compliance & AML/KYC policies\n"
            "• Corporate structuring\n"
            "• Contract review & due diligence\n\n"
            "⏱ Session: 1 hour"
        ),
    ),
    (
        "os_other",
        "📋 Other / Custom Services",
        (
            "📋 <b>Other Services</b>\n\n"
            "We offer a wide range of additional services for financial and gaming businesses:\n\n"
            "• 📝 AML/KYC Policy Development\n"
            "• 🔍 Compliance Audits\n"
            "• 💹 MT4/MT5 White Label Setup\n"
            "• 🌐 Payment Processing Solutions\n"
            "• 📊 Risk Management Frameworks\n"
            "• 🤝 Nominee Director / Shareholder Services\n"
            "• 📄 Drafting contracts, terms, policies & legal opinions\n\n"
            "Tell us what you need and we'll find the right solution!"
        ),
    ),
]

# Build a quick lookup dict: callback_key → full text
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
    """Keyboard listing all Other Services items."""
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
    """Return the category key that contains this license."""
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

    # ── Main menu ──
    if data == "main_menu":
        await query.edit_message_text(
            MAIN_MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML"
        )

    # ── No-op (section divider) ──
    elif data == "noop":
        return

    # ── Category ──
    elif data.startswith("cat_"):
        cat_key = data[4:]
        cat = CATEGORIES[cat_key]
        await query.edit_message_text(
            cat["intro"], reply_markup=category_keyboard(cat_key), parse_mode="HTML"
        )

    # ── Specific license ──
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

    # ── Other Services list (main menu button) ──
    elif data == "other_list":
        await query.edit_message_text(
            "📋 <b>Other Services</b>\n\nChoose a service below:",
            reply_markup=other_services_keyboard(),
            parse_mode="HTML",
        )

    # ── Individual Other Service item ──
    elif data.startswith("os_"):
        # callback_data is like "os_company", "os_bank", etc.
        # Our keys in OTHER_SERVICES_TEXTS are "os_company", "os_bank", etc.
        full_key = data  # e.g. "os_company"
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

    # ── Contact ──
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

    # ── Free Consult → start ConversationHandler ──
    elif data == "free_consult":
        await query.edit_message_text(
            "🆓 <b>Free Consultation Request</b>\n\n"
            "Let's get you connected with our expert team!\n\n"
            "👤 Please enter your <b>name</b>:",
            reply_markup=lead_cancel_keyboard(),
            parse_mode="HTML",
        )
        return WAITING_LEAD_NAME

    # ── Cancel lead form ──
    elif data == "cancel_lead":
        await query.edit_message_text(
            "❌ Request cancelled.\n\n" + MAIN_MENU_TEXT,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return ConversationHandler.END


# ─── CONVERSATION: Lead Capture ──────────────────────────────────────────────

async def lead_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Nice to meet you, <b>{context.user_data['lead_name']}</b>!\n\n"
        "📱 Now please enter your <b>phone number or Telegram username</b> "
        "so we can reach you:",
        reply_markup=lead_cancel_keyboard(),
        parse_mode="HTML",
    )
    return WAITING_LEAD_PHONE


async def lead_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead_phone"] = update.message.text.strip()
    await update.message.reply_text(
        "📋 Almost done! Please briefly describe <b>what you need</b> "
        "(e.g. 'Crypto license in EU', 'Gaming license for online casino', etc.):",
        reply_markup=lead_cancel_keyboard(),
        parse_mode="HTML",
    )
    return WAITING_LEAD_MSG


async def lead_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead_msg"] = update.message.text.strip()

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
        try:
            await update.get_bot().send_message(
                MANAGER_CHAT_ID, lead_text, parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to forward lead: {e}")

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