"""Admin paneli klaviaturalari."""
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def admin_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm:stats")
    kb.button(text="📢 Majburiy obuna", callback_data="adm:channels")
    kb.button(text="👋 Kirish posti", callback_data="adm:welcome")
    kb.button(text="📣 Ommaviy post", callback_data="adm:broadcast")
    kb.button(text="📝 Ma'lumot qo'shish", callback_data="adm:content")
    kb.button(text="❓ Savollar", callback_data="adm:questions")
    kb.button(text="💡 Kun hikmati", callback_data="adm:quotes")
    kb.adjust(1)
    return kb.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Admin paneli", callback_data="adm:back")
    return kb.as_markup()


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Bekor qilish")
    return kb.as_markup(resize_keyboard=True)


def channels_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Kanal qo'shish", callback_data="adm:ch_add")
    for ch in channels:
        title = ch.get("title") or ch.get("chat_id")
        kb.button(text=f"❌ {title}", callback_data=f"adm:ch_del:{ch['id']}")
    kb.button(text="⬅️ Admin paneli", callback_data="adm:back")
    kb.adjust(1)
    return kb.as_markup()


def lang_select_kb(prefix: str) -> InlineKeyboardMarkup:
    """Admin uchun til tanlash. prefix orqali keyingi action ajratiladi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbek", callback_data=f"{prefix}:uz")
    kb.button(text="🇷🇺 Русский", callback_data=f"{prefix}:ru")
    kb.button(text="🇬🇧 English", callback_data=f"{prefix}:en")
    kb.button(text="⬅️ Orqaga", callback_data="adm:back")
    kb.adjust(1)
    return kb.as_markup()


def content_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Adib haqida (biografiya)", callback_data="adm:c_bio")
    kb.button(text="📚 Asar qo'shish", callback_data="adm:c_work:asar")
    kb.button(text="📝 Hikoya qo'shish", callback_data="adm:c_work:hikoya")
    kb.button(text="🪶 She'r qo'shish", callback_data="adm:c_work:sher")
    kb.button(text="🏆 Tanlov/stipendiya qo'shish", callback_data="adm:c_contest")
    kb.button(text="⬅️ Orqaga", callback_data="adm:back")
    kb.adjust(1)
    return kb.as_markup()


def quotes_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Iqtibos qo'shish", callback_data="adm:q_add")
    kb.button(text="📋 Iqtiboslar ro'yxati", callback_data="adm:q_list")
    kb.button(text="⏰ Yuborish vaqti", callback_data="adm:q_schedule")
    kb.button(text="🔘 Yoqish/o'chirish", callback_data="adm:q_toggle")
    kb.button(text="⬅️ Admin paneli", callback_data="adm:back")
    kb.adjust(1)
    return kb.as_markup()


def schedule_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌅 Kunlik (09:00)", callback_data="adm:sch_set:24:09:00")
    kb.button(text="🌅 Kunlik (12:00)", callback_data="adm:sch_set:24:12:00")
    kb.button(text="🌅 Kunlik (18:00)", callback_data="adm:sch_set:24:18:00")
    kb.button(text="🕐 Har 6 soatda", callback_data="adm:sch_set:6:00:00")
    kb.button(text="🕐 Har 12 soatda", callback_data="adm:sch_set:12:00:00")
    kb.button(text="✏️ Maxsus vaqt", callback_data="adm:sch_custom")
    kb.button(text="⬅️ Orqaga", callback_data="adm:quotes")
    kb.adjust(1)
    return kb.as_markup()


def question_answer_kb(qid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Javob berish", callback_data=f"adm:ans:{qid}")
    return kb.as_markup()
