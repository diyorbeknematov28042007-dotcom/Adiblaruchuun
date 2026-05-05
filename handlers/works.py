"""Adib ijodi: asarlar, hikoyalar, she'rlar."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import database as db
from locales import t
from keyboards import user_kb

router = Router()


def _btn_texts() -> list[str]:
    return [t("menu_works", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_btn_texts()))
async def works_root(message: Message, user_lang: str):
    counts = db.count_works(lang=user_lang)
    # Agar foydalanuvchi tilida ma'lumot yo'q - uz'dan ko'rsatamiz
    if sum(counts.values()) == 0 and user_lang != "uz":
        counts = db.count_works(lang="uz")

    await message.answer(
        t("works_menu", user_lang, **counts),
        parse_mode="HTML",
        reply_markup=user_kb.works_kb(user_lang, counts),
    )


@router.callback_query(F.data.startswith("works:"))
async def works_callback(call: CallbackQuery, user_lang: str):
    payload = call.data.split(":", 1)[1]

    if payload == "back":
        counts = db.count_works(lang=user_lang)
        if sum(counts.values()) == 0 and user_lang != "uz":
            counts = db.count_works(lang="uz")
        try:
            await call.message.edit_text(
                t("works_menu", user_lang, **counts),
                parse_mode="HTML",
                reply_markup=user_kb.works_kb(user_lang, counts),
            )
        except Exception:
            await call.message.answer(
                t("works_menu", user_lang, **counts),
                parse_mode="HTML",
                reply_markup=user_kb.works_kb(user_lang, counts),
            )
        await call.answer()
        return

    work_type = payload  # asar | hikoya | sher
    items = db.get_works_by_type(work_type, lang=user_lang)
    if not items and user_lang != "uz":
        items = db.get_works_by_type(work_type, lang="uz")

    if not items:
        await call.answer(t("works_empty", user_lang), show_alert=True)
        return

    title = t("works_list_title", user_lang).get(work_type, "")
    try:
        await call.message.edit_text(
            title,
            parse_mode="HTML",
            reply_markup=user_kb.works_list_kb(items, work_type, user_lang),
        )
    except Exception:
        await call.message.answer(
            title,
            parse_mode="HTML",
            reply_markup=user_kb.works_list_kb(items, work_type, user_lang),
        )
    await call.answer()


@router.callback_query(F.data.startswith("work:"))
async def open_work(call: CallbackQuery, user_lang: str):
    work_id = int(call.data.split(":", 1)[1])
    w = db.get_work(work_id)
    if not w:
        await call.answer("?", show_alert=True)
        return

    title = w.get("title") or ""
    content = w.get("content") or ""
    file_id = w.get("file_id")
    file_type = w.get("file_type")
    work_type = w.get("type") or "asar"

    full_text = f"<b>{title}</b>\n\n{content}".strip()

    kb = user_kb.work_detail_kb(work_type, user_lang)

    # File bilan
    if file_id:
        try:
            caption = full_text if len(full_text) <= 1024 else f"<b>{title}</b>"
            if file_type == "audio":
                await call.message.answer_audio(file_id, caption=caption,
                                                 parse_mode="HTML", reply_markup=kb)
            elif file_type == "photo":
                await call.message.answer_photo(file_id, caption=caption,
                                                 parse_mode="HTML", reply_markup=kb)
            else:
                await call.message.answer_document(file_id, caption=caption,
                                                    parse_mode="HTML", reply_markup=kb)
            if len(full_text) > 1024:
                await call.message.answer(full_text[1024:], parse_mode="HTML")
            await call.answer()
            return
        except Exception:
            pass

    # Faqat matn — uzun bo'lsa bo'lib yuboramiz
    CHUNK = 4000
    if len(full_text) <= CHUNK:
        await call.message.answer(full_text, parse_mode="HTML", reply_markup=kb)
    else:
        for i in range(0, len(full_text), CHUNK):
            chunk = full_text[i:i + CHUNK]
            is_last = (i + CHUNK) >= len(full_text)
            await call.message.answer(
                chunk,
                parse_mode="HTML",
                reply_markup=kb if is_last else None,
            )
    await call.answer()
