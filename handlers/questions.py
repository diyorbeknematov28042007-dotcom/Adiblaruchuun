"""Foydalanuvchi tomonidan adminlarga savol yuborish."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
import config
from locales import t
from keyboards import user_kb, admin_kb

router = Router()


class QuestionState(StatesGroup):
    waiting_text = State()


def _btn_texts() -> list[str]:
    return [t("menu_questions", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_btn_texts()))
async def ask_question_start(message: Message, state: FSMContext, user_lang: str):
    await state.set_state(QuestionState.waiting_text)
    await message.answer(
        t("ask_question", user_lang),
        reply_markup=user_kb.back_kb(user_lang),
    )


@router.message(QuestionState.waiting_text, F.text)
async def receive_question(message: Message, state: FSMContext, user_lang: str):
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer(t("question_too_short", user_lang))
        return

    qid = db.add_question(message.from_user.id, text)
    await state.clear()

    await message.answer(
        t("question_sent", user_lang),
        reply_markup=user_kb.main_menu_kb(user_lang),
    )

    # Adminlarga jo'natamiz
    user = message.from_user
    user_label = f"@{user.username}" if user.username else f"id:{user.id}"
    admin_text = (
        f"📩 <b>Yangi savol #{qid}</b>\n\n"
        f"👤 {user.full_name} ({user_label})\n"
        f"🌐 Til: {user_lang}\n\n"
        f"<b>Savol:</b>\n{text}"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id, admin_text, parse_mode="HTML",
                reply_markup=admin_kb.question_answer_kb(qid),
            )
        except Exception:
            pass
