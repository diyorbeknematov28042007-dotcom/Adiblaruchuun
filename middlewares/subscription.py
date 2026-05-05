"""Foydalanuvchi tildni va obunani tekshiruvchi yordamchi funksiyalar."""
import logging
from typing import Awaitable, Callable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, User
from aiogram.exceptions import TelegramBadRequest

import database as db
import config

logger = logging.getLogger(__name__)


async def is_user_subscribed(bot, user_id: int) -> tuple[bool, list[dict]]:
    """Foydalanuvchi barcha majburiy kanallarga obuna bo'lganmi?
    Qaytaradi: (obuna_bo'lganmi, obuna_bo'lmagan_kanallar)
    """
    channels = db.get_channels(active_only=True)
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        chat_id = ch.get("chat_id")
        if not chat_id:
            continue
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except TelegramBadRequest as e:
            logger.warning(f"Kanal {chat_id} tekshirishda xato: {e}")
            # Botni o'sha kanalga admin qilish kerak; tekshira olmagan ekan, o'tkazib yuboramiz
            continue
        except Exception as e:
            logger.exception(f"Kanal {chat_id} kutilmagan xato: {e}")
            continue

    return len(not_subscribed) == 0, not_subscribed


class UserContextMiddleware(BaseMiddleware):
    """Har bir update'da foydalanuvchini DB'ga qo'shadi/yangilaydi va tilini olib data'ga qo'shadi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user and not user.is_bot:
            try:
                existing = db.get_user(user.id)
                if not existing:
                    db.upsert_user(
                        user_id=user.id,
                        username=user.username,
                        full_name=user.full_name,
                        language=config.DEFAULT_LANGUAGE,
                    )
                    existing = db.get_user(user.id)
                else:
                    db.upsert_user(
                        user_id=user.id,
                        username=user.username,
                        full_name=user.full_name,
                    )
                data["user_lang"] = (existing or {}).get("language") or config.DEFAULT_LANGUAGE
                data["db_user"] = existing
            except Exception as e:
                logger.exception(f"UserContextMiddleware xato: {e}")
                data["user_lang"] = config.DEFAULT_LANGUAGE
                data["db_user"] = None
        else:
            data["user_lang"] = config.DEFAULT_LANGUAGE
            data["db_user"] = None

        return await handler(event, data)
