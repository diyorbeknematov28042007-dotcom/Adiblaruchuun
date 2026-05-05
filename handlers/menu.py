"""«Orqaga» va «Tilni o'zgartirish» tugmalarini ushlash."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from locales import t
from keyboards import user_kb

router = Router()


def _back_texts() -> list[str]:
    return [t("back", l) for l in ("uz", "ru", "en")] + \
           [t("back_to_menu", l) for l in ("uz", "ru", "en")]


def _lang_btn_texts() -> list[str]:
    return [t("menu_language", l) for l in ("uz", "ru", "en")]


@router.message(F.text.in_(_back_texts()))
async def go_back(message: Message, state: FSMContext, user_lang: str):
    await state.clear()
    await message.answer(
        t("main_menu", user_lang),
        parse_mode="HTML",
        reply_markup=user_kb.main_menu_kb(user_lang),
    )


@router.message(F.text.in_(_lang_btn_texts()))
async def change_language_btn(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        t("choose_language", "uz"),
        reply_markup=user_kb.language_kb(),
    )
