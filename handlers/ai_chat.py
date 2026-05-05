"""Adib bilan suhbat — Gemini AI orqali."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from locales import t
from keyboards import user_kb
from utils.gemini import get_rotator

logger = logging.getLogger(__name__)
router = Router()


class ChatState(StatesGroup):
    chatting = State()


def _btn_texts() -> list[str]:
    return [t("menu_chat", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_btn_texts()))
async def chat_start(message: Message, state: FSMContext, user_lang: str):
    await state.set_state(ChatState.chatting)
    await state.update_data(history=[])
    await message.answer(
        t("chat_intro", user_lang),
        parse_mode="HTML",
        reply_markup=user_kb.back_kb(user_lang),
    )


@router.message(ChatState.chatting, F.text)
async def chat_message(message: Message, state: FSMContext, user_lang: str):
    user_text = (message.text or "").strip()
    if not user_text:
        return

    data = await state.get_data()
    history: list[dict] = data.get("history", [])

    # "yozmoqda..." ni ko'rsatamiz
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    rotator = get_rotator()
    try:
        reply = await rotator.generate(history, user_text)
    except Exception as e:
        logger.exception(f"Gemini xato: {e}")
        await message.answer(t("chat_error", user_lang))
        return

    if not reply:
        await message.answer(t("chat_error", user_lang))
        return

    # History'ga qo'shamiz, lekin oxirgi 12 ta xabardan saqlamaymiz
    history.append({"role": "user", "parts": [user_text]})
    history.append({"role": "model", "parts": [reply]})
    history = history[-24:]
    await state.update_data(history=history)

    # Telegram'da matn 4096 ga cheklangan — bo'lib yuboramiz
    CHUNK = 4000
    if len(reply) <= CHUNK:
        await message.answer(reply)
    else:
        for i in range(0, len(reply), CHUNK):
            await message.answer(reply[i:i + CHUNK])
