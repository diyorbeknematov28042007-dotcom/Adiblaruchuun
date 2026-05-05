"""Admin paneli - barcha admin funksiyalari shu yerda."""
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import database as db
import config
from keyboards import admin_kb
from utils import scheduler as sched_mod

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    add_channel = State()
    welcome_lang = State()
    welcome_input = State()
    welcome_button = State()
    broadcast_input = State()
    broadcast_confirm = State()

    bio_lang = State()
    bio_input = State()

    work_lang = State()
    work_title = State()
    work_content = State()

    contest_lang = State()
    contest_title = State()
    contest_content = State()
    contest_link = State()

    quote_input = State()
    quote_lang = State()
    schedule_custom = State()

    answer_question = State()


def _admin_only(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ============= /admin =============
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not _admin_only(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🛠 <b>Admin paneli</b>\n\nKerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_kb.admin_main_kb(),
    )


@router.callback_query(F.data == "adm:back")
async def cb_admin_back(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.clear()
    try:
        await call.message.edit_text(
            "🛠 <b>Admin paneli</b>\n\nKerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_kb.admin_main_kb(),
        )
    except Exception:
        await call.message.answer(
            "🛠 <b>Admin paneli</b>",
            parse_mode="HTML",
            reply_markup=admin_kb.admin_main_kb(),
        )
    await call.answer()


# ============= STATISTIKA =============
@router.callback_query(F.data == "adm:stats")
async def cb_stats(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    counts = db.count_users()
    works = db.count_works(lang="uz")
    contests = len(db.get_contests(lang="uz"))
    quotes = len(db.get_all_quotes(lang="uz"))
    sched = db.get_schedule() or {}

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{counts['total']}</b>\n"
        f"✅ Faol: <b>{counts['active']}</b>\n"
        f"🚫 Bloklagan: <b>{counts['blocked']}</b>\n\n"
        f"📚 Asarlar: <b>{works.get('asar', 0)}</b>\n"
        f"📝 Hikoyalar: <b>{works.get('hikoya', 0)}</b>\n"
        f"🪶 She'rlar: <b>{works.get('sher', 0)}</b>\n"
        f"🏆 Tanlovlar: <b>{contests}</b>\n"
        f"💡 Iqtiboslar: <b>{quotes}</b>\n\n"
        f"⏰ Kun hikmati: "
        f"{'🟢 Yoniq' if sched.get('is_enabled') else '🔴 O''chiq'}\n"
        f"   Interval: <b>{sched.get('interval_hours', 24)}</b> soat"
    )
    try:
        await call.message.edit_text(text, parse_mode="HTML",
                                      reply_markup=admin_kb.admin_back_kb())
    except Exception:
        await call.message.answer(text, parse_mode="HTML",
                                   reply_markup=admin_kb.admin_back_kb())
    await call.answer()


# ============= MAJBURIY OBUNA =============
@router.callback_query(F.data == "adm:channels")
async def cb_channels(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    channels = db.get_channels(active_only=False)
    text = "📢 <b>Majburiy obuna kanallari</b>\n\n"
    if channels:
        for ch in channels:
            text += f"• {ch.get('title') or ch.get('chat_id')}\n  <code>{ch.get('chat_id')}</code>\n"
    else:
        text += "<i>Kanallar yo'q.</i>\n"
    text += "\n<i>O'chirish uchun kanal tugmasini bosing.</i>"

    try:
        await call.message.edit_text(text, parse_mode="HTML",
                                      reply_markup=admin_kb.channels_kb(channels))
    except Exception:
        await call.message.answer(text, parse_mode="HTML",
                                   reply_markup=admin_kb.channels_kb(channels))
    await call.answer()


@router.callback_query(F.data == "adm:ch_add")
async def cb_ch_add(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.add_channel)
    await call.message.answer(
        "📢 Kanal ma'lumotini yuboring:\n\n"
        "Format: <code>@username Sarlavha https://t.me/...</code>\n"
        "Yoki: <code>-1001234567890 Sarlavha https://t.me/+invite</code>\n\n"
        "<b>Eslatma:</b> Botni ushbu kanalga ADMIN qilib qo'shing!",
        parse_mode="HTML",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.add_channel, F.text)
async def add_channel_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 1:
        await message.answer("❌ Format noto'g'ri.")
        return

    chat_id = parts[0]
    title = parts[1] if len(parts) > 1 else chat_id
    invite_link = parts[2] if len(parts) > 2 else None

    # Kanal mavjudligini tekshirib, sarlavhani olamiz
    try:
        chat = await message.bot.get_chat(chat_id)
        title = title or chat.title
        if not invite_link:
            if chat.username:
                invite_link = f"https://t.me/{chat.username}"
    except Exception as e:
        await message.answer(
            f"⚠️ Kanal ma'lumotini olishda xato: {e}\n"
            f"Botni kanal admin qildingizmi? Baribir saqlayman."
        )

    db.add_channel(chat_id=chat_id, title=title, invite_link=invite_link)
    await state.clear()
    await message.answer("✅ Kanal qo'shildi.",
                          reply_markup=admin_kb.cancel_kb().__class__())
    # Asosiy admin paneliga qaytarish
    await message.answer(
        "🛠 <b>Admin paneli</b>",
        parse_mode="HTML",
        reply_markup=admin_kb.admin_main_kb(),
    )


@router.callback_query(F.data.startswith("adm:ch_del:"))
async def cb_ch_del(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    cid = int(call.data.split(":")[2])
    channels = db.get_channels(active_only=False)
    target = next((c for c in channels if c["id"] == cid), None)
    if target:
        db.remove_channel(target["chat_id"])
    await call.answer("✅ O'chirildi.")
    # Ro'yxatni yangilab ko'rsatamiz
    await cb_channels(call)


# ============= KIRISH POSTI =============
@router.callback_query(F.data == "adm:welcome")
async def cb_welcome(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.welcome_lang)
    try:
        await call.message.edit_text(
            "👋 <b>Kirish posti</b>\n\nQaysi til uchun?",
            parse_mode="HTML",
            reply_markup=admin_kb.lang_select_kb("adm:wlang"),
        )
    except Exception:
        await call.message.answer(
            "Qaysi til uchun?",
            reply_markup=admin_kb.lang_select_kb("adm:wlang"),
        )
    await call.answer()


@router.callback_query(F.data.startswith("adm:wlang:"))
async def cb_welcome_lang(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    lang = call.data.split(":")[2]
    await state.set_state(AdminStates.welcome_input)
    await state.update_data(welcome_lang=lang)
    await call.message.answer(
        f"👋 <b>{lang.upper()}</b> uchun kirish posti.\n\n"
        "Matn yoki rasm + matn yuboring.\n"
        "Keyingi qadamda qo'shimcha tugma so'raladi.",
        parse_mode="HTML",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.welcome_input, F.text | F.photo)
async def welcome_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    photo_id = None
    text = ""
    if message.photo:
        photo_id = message.photo[-1].file_id
        text = message.caption or ""
    else:
        text = message.text or ""

    await state.update_data(welcome_text=text, welcome_photo=photo_id)
    await state.set_state(AdminStates.welcome_button)
    await message.answer(
        "🔘 Qo'shimcha tugma kerakmi?\n\n"
        "Format: <code>Tugma matni | https://...</code>\n"
        "Yoki <code>yo'q</code> deb yozing.",
        parse_mode="HTML",
    )


@router.message(AdminStates.welcome_button, F.text)
async def welcome_button_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    btn_text = btn_url = None
    if message.text.strip().lower() not in ("yo'q", "yoq", "no", "нет"):
        if "|" in message.text:
            parts = message.text.split("|", 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()
        else:
            await message.answer("❌ Format: <code>Matn | URL</code>", parse_mode="HTML")
            return

    data = await state.get_data()
    db.set_welcome(
        lang=data["welcome_lang"],
        text=data.get("welcome_text"),
        photo_file_id=data.get("welcome_photo"),
        button_text=btn_text,
        button_url=btn_url,
    )
    await state.clear()
    await message.answer("✅ Saqlandi.",
                          reply_markup=admin_kb.admin_main_kb().__class__() if False else None)
    await message.answer(
        "🛠 <b>Admin paneli</b>",
        parse_mode="HTML",
        reply_markup=admin_kb.admin_main_kb(),
    )


# ============= OMMAVIY POST =============
@router.callback_query(F.data == "adm:broadcast")
async def cb_broadcast(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.broadcast_input)
    await call.message.answer(
        "📣 <b>Ommaviy post</b>\n\n"
        "Yubormoqchi bo'lgan xabarni shu yerga yuboring (matn / rasm / fayl). "
        "Forward qilingan xabar ham ishlaydi.",
        parse_mode="HTML",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.broadcast_input)
async def broadcast_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    await state.update_data(broadcast_msg_id=message.message_id,
                             broadcast_chat_id=message.chat.id)
    await state.set_state(AdminStates.broadcast_confirm)

    users = db.get_all_active_users()
    await message.answer(
        f"📣 Yuqoridagi xabar <b>{len(users)}</b> foydalanuvchiga yuboriladi.\n\n"
        "Tasdiqlash uchun «✅ Yuborish» yozing yoki ❌ Bekor qiling.",
        parse_mode="HTML",
    )


@router.message(AdminStates.broadcast_confirm, F.text)
async def broadcast_confirm(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.",
                              reply_markup=admin_kb.admin_main_kb().__class__() if False else None)
        return

    if "✅" not in message.text and "yuborish" not in message.text.lower():
        await message.answer("Tasdiqlash uchun «✅ Yuborish» yozing.")
        return

    data = await state.get_data()
    src_msg_id = data.get("broadcast_msg_id")
    src_chat_id = data.get("broadcast_chat_id")
    await state.clear()

    users = db.get_all_active_users()
    await message.answer(f"⏳ Boshlandi... ({len(users)} ta)")

    sent = blocked = errors = 0
    for u in users:
        try:
            await message.bot.copy_message(
                chat_id=u["id"],
                from_chat_id=src_chat_id,
                message_id=src_msg_id,
            )
            sent += 1
        except TelegramForbiddenError:
            db.set_user_blocked(u["id"], True)
            blocked += 1
        except TelegramBadRequest:
            errors += 1
        except Exception as e:
            logger.warning(f"Broadcast user {u['id']}: {e}")
            errors += 1
        await asyncio.sleep(0.05)

    await message.answer(
        f"✅ Yakunlandi.\n\n"
        f"📤 Yuborildi: {sent}\n"
        f"🚫 Bloklagan: {blocked}\n"
        f"⚠️ Xato: {errors}",
        reply_markup=admin_kb.admin_main_kb(),
    )


# ============= MA'LUMOT QO'SHISH =============
@router.callback_query(F.data == "adm:content")
async def cb_content(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    try:
        await call.message.edit_text(
            "📝 <b>Ma'lumot qo'shish</b>\n\nQaysi turdagi?",
            parse_mode="HTML",
            reply_markup=admin_kb.content_type_kb(),
        )
    except Exception:
        await call.message.answer(
            "📝 Ma'lumot qo'shish:",
            reply_markup=admin_kb.content_type_kb(),
        )
    await call.answer()


# Biografiya
@router.callback_query(F.data == "adm:c_bio")
async def cb_c_bio(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.bio_lang)
    await call.message.answer(
        "👤 Biografiya qaysi til uchun?",
        reply_markup=admin_kb.lang_select_kb("adm:blang"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:blang:"))
async def cb_bio_lang(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    lang = call.data.split(":")[2]
    await state.set_state(AdminStates.bio_input)
    await state.update_data(bio_lang=lang)
    await call.message.answer(
        f"📝 <b>{lang.upper()}</b> tilda biografiyani yuboring.\n\n"
        "Matn yoki rasm + matn (caption) yuboring.\n"
        "HTML formatlash ishlatishingiz mumkin: <b>qalin</b>, <i>kursiv</i>",
        parse_mode="HTML",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.bio_input, F.text | F.photo)
async def bio_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    photo = None
    text = ""
    if message.photo:
        photo = message.photo[-1].file_id
        text = message.caption or ""
    else:
        text = message.text or ""

    if not text:
        await message.answer("❌ Matn yuboring.")
        return

    data = await state.get_data()
    db.set_biography(lang=data["bio_lang"], text=text, photo_file_id=photo)
    await state.clear()
    await message.answer("✅ Biografiya saqlandi.",
                          reply_markup=admin_kb.admin_main_kb())


# Asar/hikoya/she'r qo'shish
@router.callback_query(F.data.startswith("adm:c_work:"))
async def cb_c_work(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    work_type = call.data.split(":")[2]
    await state.set_state(AdminStates.work_lang)
    await state.update_data(work_type=work_type)
    await call.message.answer(
        f"➕ Yangi {work_type}.\n\nQaysi til uchun?",
        reply_markup=admin_kb.lang_select_kb("adm:wklang"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:wklang:"))
async def cb_work_lang(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    lang = call.data.split(":")[2]
    await state.set_state(AdminStates.work_title)
    await state.update_data(work_lang=lang)
    await call.message.answer(
        "📌 Sarlavhani yuboring:",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.work_title, F.text)
async def work_title_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(work_title=message.text.strip())
    await state.set_state(AdminStates.work_content)
    await message.answer(
        "📝 Endi mazmun(matn) yuboring.\n"
        "Yoki PDF/audio/rasm fayl yuborishingiz mumkin (caption ham yozish mumkin).",
    )


@router.message(AdminStates.work_content)
async def work_content_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    file_id = None
    file_type = None
    content = ""

    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        content = message.caption or ""
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
        content = message.caption or ""
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "audio"
        content = message.caption or ""
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        content = message.caption or ""
    elif message.text:
        content = message.text

    if not content and not file_id:
        await message.answer("❌ Mazmun bo'sh.")
        return

    data = await state.get_data()
    db.add_work(
        work_type=data["work_type"],
        title=data["work_title"],
        content=content,
        file_id=file_id,
        file_type=file_type,
        lang=data["work_lang"],
    )
    await state.clear()
    await message.answer(
        f"✅ Saqlandi: <b>{data['work_title']}</b>",
        parse_mode="HTML",
        reply_markup=admin_kb.admin_main_kb(),
    )


# Tanlov / stipendiya
@router.callback_query(F.data == "adm:c_contest")
async def cb_c_contest(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.contest_lang)
    await call.message.answer(
        "🏆 Tanlov/stipendiya qaysi til uchun?",
        reply_markup=admin_kb.lang_select_kb("adm:cnlang"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:cnlang:"))
async def cb_contest_lang(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    lang = call.data.split(":")[2]
    await state.update_data(contest_lang=lang)
    await state.set_state(AdminStates.contest_title)
    await call.message.answer(
        "📌 Tanlov sarlavhasini yuboring:",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.contest_title, F.text)
async def contest_title_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(contest_title=message.text.strip())
    await state.set_state(AdminStates.contest_content)
    await message.answer("📝 Tanlov tafsilotlari (matn yoki rasm + caption):")


@router.message(AdminStates.contest_content)
async def contest_content_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    photo = None
    content = ""
    if message.photo:
        photo = message.photo[-1].file_id
        content = message.caption or ""
    else:
        content = message.text or ""
    await state.update_data(contest_content=content, contest_photo=photo)
    await state.set_state(AdminStates.contest_link)
    await message.answer(
        "🔗 Tanlovga havola (URL) yoki <code>yo'q</code> deb yozing:",
        parse_mode="HTML",
    )


@router.message(AdminStates.contest_link, F.text)
async def contest_link_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    link = message.text.strip()
    if link.lower() in ("yo'q", "yoq", "no", "нет"):
        link = None

    data = await state.get_data()
    db.add_contest(
        title=data["contest_title"],
        content=data.get("contest_content") or "",
        photo_file_id=data.get("contest_photo"),
        link=link,
        lang=data["contest_lang"],
    )
    await state.clear()
    await message.answer("✅ Tanlov qo'shildi.",
                          reply_markup=admin_kb.admin_main_kb())


# ============= SAVOLLAR =============
@router.callback_query(F.data == "adm:questions")
async def cb_questions(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    qs = db.get_unanswered_questions()
    if not qs:
        try:
            await call.message.edit_text(
                "❓ Javob kutilayotgan savollar yo'q.",
                reply_markup=admin_kb.admin_back_kb(),
            )
        except Exception:
            await call.message.answer("Savollar yo'q.")
        await call.answer()
        return

    lines = [f"❓ <b>Javob kutilayotgan: {len(qs)} ta</b>\n"]
    for q in qs[:10]:
        lines.append(f"• #{q['id']}: {q['text'][:80]}")
    await call.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=admin_kb.admin_back_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:ans:"))
async def cb_answer_start(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    qid = int(call.data.split(":")[2])
    q = db.get_question(qid)
    if not q:
        await call.answer("Savol topilmadi.", show_alert=True)
        return
    if q.get("is_answered"):
        await call.answer("Bu savolga allaqachon javob berilgan.", show_alert=True)
        return

    await state.set_state(AdminStates.answer_question)
    await state.update_data(answer_qid=qid)
    await call.message.answer(
        f"✍️ #{qid} savoliga javobingizni yozing:",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.answer_question, F.text)
async def cb_answer_send(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    data = await state.get_data()
    qid = data.get("answer_qid")
    answer = message.text.strip()

    q = db.get_question(qid)
    if not q:
        await state.clear()
        await message.answer("Savol topilmadi.")
        return

    db.answer_question(qid, answer)

    # Foydalanuvchiga jo'natish
    user_data = db.get_user(q["user_id"])
    user_lang = (user_data or {}).get("language") or "uz"
    from locales import t as tr
    final = tr("answer_received", user_lang, answer=answer, question=q["text"])
    try:
        await message.bot.send_message(q["user_id"], final, parse_mode="HTML")
        await message.answer("✅ Javob yuborildi.",
                              reply_markup=admin_kb.admin_main_kb())
    except Exception as e:
        await message.answer(f"⚠️ Javob saqlandi, lekin yuborib bo'lmadi: {e}",
                              reply_markup=admin_kb.admin_main_kb())
    await state.clear()


# ============= KUN HIKMATI =============
@router.callback_query(F.data == "adm:quotes")
async def cb_quotes(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    sched = db.get_schedule() or {}
    quotes_count = len(db.get_all_quotes(lang="uz"))
    text = (
        "💡 <b>Kun hikmati</b>\n\n"
        f"📋 Iqtiboslar: <b>{quotes_count}</b> ta\n"
        f"⏰ Holat: {'🟢 Yoniq' if sched.get('is_enabled') else '🔴 O''chiq'}\n"
        f"⏱ Interval: <b>{sched.get('interval_hours', 24)}</b> soat\n"
        f"🕐 Vaqt: <b>{sched.get('send_time', '09:00')}</b>"
    )
    try:
        await call.message.edit_text(text, parse_mode="HTML",
                                      reply_markup=admin_kb.quotes_menu_kb())
    except Exception:
        await call.message.answer(text, parse_mode="HTML",
                                   reply_markup=admin_kb.quotes_menu_kb())
    await call.answer()


@router.callback_query(F.data == "adm:q_add")
async def cb_q_add(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.quote_lang)
    await call.message.answer(
        "💡 Iqtibos qaysi til uchun?",
        reply_markup=admin_kb.lang_select_kb("adm:qlang"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:qlang:"))
async def cb_quote_lang(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    lang = call.data.split(":")[2]
    await state.update_data(quote_lang=lang)
    await state.set_state(AdminStates.quote_input)
    await call.message.answer(
        "✍️ Iqtibos matnini yuboring (manba bo'lsa, oxirida | belgisidan keyin yozing):",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.quote_input, F.text)
async def quote_input_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    text = message.text.strip()
    source = None
    if "|" in text:
        text, source = [p.strip() for p in text.split("|", 1)]

    data = await state.get_data()
    db.add_quote(text=text, source=source, lang=data["quote_lang"])
    await state.clear()
    await message.answer("✅ Iqtibos qo'shildi.",
                          reply_markup=admin_kb.admin_main_kb())


@router.callback_query(F.data == "adm:q_list")
async def cb_q_list(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    quotes = db.get_all_quotes(lang="uz")
    if not quotes:
        await call.answer("Iqtiboslar yo'q.", show_alert=True)
        return
    lines = ["💡 <b>Iqtiboslar (uz):</b>\n"]
    for q in quotes[:30]:
        text = q["text"][:100]
        lines.append(f"#{q['id']}: «{text}»")
    await call.message.answer("\n".join(lines), parse_mode="HTML",
                               reply_markup=admin_kb.admin_back_kb())
    await call.answer()


@router.callback_query(F.data == "adm:q_toggle")
async def cb_q_toggle(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    sched = db.get_schedule()
    if not sched:
        return
    new_val = not sched.get("is_enabled", True)
    db.update_schedule(is_enabled=new_val)
    sched_mod.reload_schedule()
    await call.answer(f"{'🟢 Yoqildi' if new_val else '🔴 O''chirildi'}")
    await cb_quotes(call)


@router.callback_query(F.data == "adm:q_schedule")
async def cb_q_schedule(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    try:
        await call.message.edit_text(
            "⏰ Yuborish jadvalini tanlang:",
            reply_markup=admin_kb.schedule_kb(),
        )
    except Exception:
        await call.message.answer(
            "⏰ Jadval:", reply_markup=admin_kb.schedule_kb(),
        )
    await call.answer()


@router.callback_query(F.data.startswith("adm:sch_set:"))
async def cb_sch_set(call: CallbackQuery):
    if not _admin_only(call.from_user.id):
        return
    parts = call.data.split(":")
    # adm:sch_set:24:09:00
    interval = int(parts[2])
    send_time = f"{parts[3]}:{parts[4]}"
    db.update_schedule(interval_hours=interval, send_time=send_time, is_enabled=True)
    sched_mod.reload_schedule()
    await call.answer("✅ Saqlandi.")
    await cb_quotes(call)


@router.callback_query(F.data == "adm:sch_custom")
async def cb_sch_custom(call: CallbackQuery, state: FSMContext):
    if not _admin_only(call.from_user.id):
        return
    await state.set_state(AdminStates.schedule_custom)
    await call.message.answer(
        "✏️ Maxsus interval kiriting.\n\n"
        "Format: <code>SOAT VAQT</code>\n"
        "Misol:\n"
        "• <code>24 09:00</code> — har kuni 09:00 da\n"
        "• <code>6 00:00</code> — har 6 soatda\n"
        "• <code>48 12:00</code> — har 2 kunda 12:00 da",
        parse_mode="HTML",
        reply_markup=admin_kb.cancel_kb(),
    )
    await call.answer()


@router.message(AdminStates.schedule_custom, F.text)
async def sch_custom_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    try:
        parts = message.text.strip().split()
        interval = int(parts[0])
        send_time = parts[1] if len(parts) > 1 else "09:00"
        # validatsiya
        hh, mm = map(int, send_time.split(":"))
        if not (0 <= hh < 24 and 0 <= mm < 60) or interval < 1:
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("❌ Format noto'g'ri. Misol: <code>24 09:00</code>",
                              parse_mode="HTML")
        return

    db.update_schedule(interval_hours=interval, send_time=send_time, is_enabled=True)
    sched_mod.reload_schedule()
    await state.clear()
    await message.answer("✅ Jadval yangilandi.",
                          reply_markup=admin_kb.admin_main_kb())
