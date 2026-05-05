"""Stipendiya va ko'rik-tanlovlar bo'limi."""
from aiogram import Router, F
from aiogram.types import Message

import database as db
from locales import t
from keyboards import user_kb

router = Router()


def _btn_texts() -> list[str]:
    return [t("menu_contests", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_btn_texts()))
async def show_contests(message: Message, user_lang: str):
    items = db.get_contests(lang=user_lang)
    if not items and user_lang != "uz":
        items = db.get_contests(lang="uz")

    if not items:
        await message.answer(t("contests_empty", user_lang))
        return

    await message.answer(t("contests_title", user_lang), parse_mode="HTML")

    for it in items:
        title = it.get("title") or ""
        content = it.get("content") or ""
        photo = it.get("photo_file_id")
        link = it.get("link")
        text = f"<b>{title}</b>\n\n{content}".strip()
        kb = user_kb.contest_link_kb(link, user_lang) if link else None

        if photo:
            try:
                cap = text if len(text) <= 1024 else f"<b>{title}</b>"
                await message.answer_photo(photo, caption=cap, parse_mode="HTML",
                                            reply_markup=kb)
                if len(text) > 1024:
                    await message.answer(text[1024:], parse_mode="HTML")
                continue
            except Exception:
                pass

        await message.answer(text[:4000], parse_mode="HTML", reply_markup=kb)
