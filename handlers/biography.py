"""Adib haqida (biografiya) bo'limi."""
from aiogram import Router, F
from aiogram.types import Message

import database as db
from locales import t

router = Router()


def _btn_texts() -> list[str]:
    return [t("menu_about", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_btn_texts()))
async def show_biography(message: Message, user_lang: str):
    bio = db.get_biography(user_lang)
    if not bio:
        # Fallback - boshqa tildagi bo'lsa ko'rsatamiz
        for l in ("uz", "ru", "en"):
            if l == user_lang:
                continue
            bio = db.get_biography(l)
            if bio:
                break

    if not bio or not bio.get("text"):
        await message.answer(t("biography_empty", user_lang))
        return

    text = bio["text"]
    photo = bio.get("photo_file_id")
    if photo:
        try:
            await message.answer_photo(photo, caption=text[:1024], parse_mode="HTML")
            if len(text) > 1024:
                await message.answer(text[1024:], parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(text, parse_mode="HTML")
