"""Foydalanuvchi uchun klaviaturalar."""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from locales import t


def language_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    kb.button(text="🇷🇺 Русский", callback_data="lang:ru")
    kb.button(text="🇬🇧 English", callback_data="lang:en")
    kb.adjust(1)
    return kb.as_markup()


def subscription_kb(channels: list[dict], lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        url = ch.get("invite_link") or _channel_url(ch.get("chat_id", ""))
        title = ch.get("title") or "Kanal"
        if url:
            kb.row(InlineKeyboardButton(text=f"📢 {title}", url=url))
    kb.row(InlineKeyboardButton(text=t("check_subscription", lang),
                                 callback_data="check_sub"))
    return kb.as_markup()


def _channel_url(chat_id: str) -> str:
    if not chat_id:
        return ""
    if chat_id.startswith("@"):
        return f"https://t.me/{chat_id[1:]}"
    return ""


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t("menu_chat", lang))
    kb.button(text=t("menu_about", lang))
    kb.button(text=t("menu_works", lang))
    kb.button(text=t("menu_contests", lang))
    kb.button(text=t("menu_questions", lang))
    kb.button(text=t("menu_language", lang))
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


def back_kb(lang: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t("back", lang))
    return kb.as_markup(resize_keyboard=True)


def works_kb(lang: str, counts: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("works_asar", lang, n=counts.get("asar", 0)),
              callback_data="works:asar")
    kb.button(text=t("works_hikoya", lang, n=counts.get("hikoya", 0)),
              callback_data="works:hikoya")
    kb.button(text=t("works_sher", lang, n=counts.get("sher", 0)),
              callback_data="works:sher")
    kb.adjust(1)
    return kb.as_markup()


def works_list_kb(items: list[dict], work_type: str, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for it in items:
        kb.button(text=it["title"], callback_data=f"work:{it['id']}")
    kb.button(text=t("back", lang), callback_data="works:back")
    kb.adjust(1)
    return kb.as_markup()


def work_detail_kb(work_type: str, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("back", lang), callback_data=f"works:{work_type}")
    return kb.as_markup()


def contest_link_kb(link: str, lang: str) -> InlineKeyboardMarkup | None:
    if not link:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text=t("contest_link", lang), url=link)
    return kb.as_markup()


def welcome_extra_kb(button_text: str, button_url: str) -> InlineKeyboardMarkup | None:
    if not button_text or not button_url:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text=button_text, url=button_url)
    return kb.as_markup()
