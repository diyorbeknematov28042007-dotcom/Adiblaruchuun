"""/start komandasi, til tanlash, majburiy obuna."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

import database as db
import config
from locales import t
from keyboards import user_kb
from middlewares.subscription import is_user_subscribed

logger = logging.getLogger(__name__)
router = Router()


async def show_main_menu(message: Message, lang: str):
    """Asosiy menyuni ko'rsatish + welcome posti."""
    welcome = db.get_welcome(lang)
    extra_kb = None
    if welcome:
        if welcome.get("extra_button_text") and welcome.get("extra_button_url"):
            extra_kb = user_kb.welcome_extra_kb(
                welcome["extra_button_text"],
                welcome["extra_button_url"],
            )
        text = welcome.get("text") or t("main_menu", lang)
        photo = welcome.get("photo_file_id")
        if photo:
            try:
                await message.answer_photo(photo, caption=text, parse_mode="HTML",
                                            reply_markup=extra_kb)
            except Exception:
                await message.answer(text, parse_mode="HTML", reply_markup=extra_kb)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=extra_kb)

    # Reply menyu
    await message.answer(t("main_menu", lang), parse_mode="HTML",
                          reply_markup=user_kb.main_menu_kb(lang))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: dict | None,
                    user_lang: str):
    await state.clear()
    # Yangi foydalanuvchi bo'lsa - til tanlatamiz
    if not db_user or not db_user.get("language"):
        await message.answer(t("choose_language", "uz"),
                              reply_markup=user_kb.language_kb())
        return

    # Obuna tekshirish
    ok, not_subbed = await is_user_subscribed(message.bot, message.from_user.id)
    if not ok:
        await message.answer(
            t("must_subscribe", user_lang),
            reply_markup=user_kb.subscription_kb(not_subbed, user_lang),
        )
        return

    await show_main_menu(message, user_lang)


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = call.data.split(":", 1)[1]
    if lang not in config.LANGUAGES:
        await call.answer("?")
        return

    db.set_user_language(call.from_user.id, lang)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer(t("language_set", lang))

    # Obuna tekshirish
    ok, not_subbed = await is_user_subscribed(call.bot, call.from_user.id)
    if not ok:
        await call.message.answer(
            t("must_subscribe", lang),
            reply_markup=user_kb.subscription_kb(not_subbed, lang),
        )
        return

    await show_main_menu(call.message, lang)


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, user_lang: str):
    ok, not_subbed = await is_user_subscribed(call.bot, call.from_user.id)
    if not ok:
        await call.answer(t("subscribe_failed", user_lang), show_alert=True)
        # Qayta tugmalarni yangilash
        try:
            await call.message.edit_reply_markup(
                reply_markup=user_kb.subscription_kb(not_subbed, user_lang)
            )
        except Exception:
            pass
        return

    await call.answer(t("subscribe_done", user_lang), show_alert=True)
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_main_menu(call.message, user_lang)


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("choose_language", "uz"),
                          reply_markup=user_kb.language_kb())
