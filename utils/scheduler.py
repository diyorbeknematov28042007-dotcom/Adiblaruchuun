"""Kun hikmati avtomatik yuborilish (APScheduler)."""
import logging
import asyncio
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import config
import database as db
from locales import t

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None
_bot: Bot | None = None


async def send_daily_quote_to_all():
    """Barcha foydalanuvchilarga tasodifiy iqtibos jo'natish."""
    if not _bot:
        return
    sched = db.get_schedule()
    if not sched or not sched.get("is_enabled"):
        return

    users = db.get_all_active_users()
    if not users:
        return

    last_id = sched.get("last_quote_id")

    blocked_count = 0
    sent_count = 0

    for user in users:
        lang = user.get("language") or "uz"
        quote = db.get_random_quote(lang=lang, exclude_id=last_id)
        if not quote:
            # Boshqa tilda ham urinib ko'ramiz
            quote = db.get_random_quote(lang="uz", exclude_id=last_id)
        if not quote:
            continue

        text = (
            f"{t('daily_quote_title', lang)}\n\n"
            f"<i>«{quote['text']}»</i>\n\n"
            f"{t('quote_source', lang)}"
        )
        try:
            await _bot.send_message(user["id"], text, parse_mode="HTML")
            sent_count += 1
        except TelegramForbiddenError:
            db.set_user_blocked(user["id"], True)
            blocked_count += 1
        except TelegramBadRequest as e:
            logger.warning(f"BadRequest user {user['id']}: {e}")
        except Exception as e:
            logger.exception(f"Xato user {user['id']}: {e}")

        await asyncio.sleep(0.05)  # flood control

    if quote:
        db.update_schedule(last_quote_id=quote["id"])
    logger.info(f"Kun hikmati: {sent_count} yuborildi, {blocked_count} bloklangan.")


def setup_scheduler(bot: Bot):
    """Schedulerni ishga tushirish va kun hikmati jobini qo'shish."""
    global scheduler, _bot
    _bot = bot
    tz = pytz.timezone(config.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    sched_data = db.get_schedule()
    if not sched_data:
        logger.warning("quote_schedule jadvali bo'sh, joblar qo'shilmadi.")
        return scheduler

    interval_hours = sched_data.get("interval_hours") or 24

    if interval_hours == 24:
        # Kunlik - ko'rsatilgan vaqtda
        send_time = sched_data.get("send_time") or "09:00"
        try:
            hh, mm = map(int, send_time.split(":"))
        except ValueError:
            hh, mm = 9, 0
        scheduler.add_job(
            send_daily_quote_to_all,
            CronTrigger(hour=hh, minute=mm, timezone=tz),
            id="daily_quote",
            replace_existing=True,
        )
    else:
        # Har N soatda
        scheduler.add_job(
            send_daily_quote_to_all,
            IntervalTrigger(hours=interval_hours, timezone=tz),
            id="daily_quote",
            replace_existing=True,
        )

    scheduler.start()
    logger.info(f"Scheduler ishga tushdi. Interval: {interval_hours}h")
    return scheduler


def reload_schedule():
    """Sozlamalar o'zgarganda schedulerni yangilash."""
    global scheduler
    if not scheduler or not _bot:
        return
    sched_data = db.get_schedule()
    if not sched_data:
        return
    # Eski jobni o'chirib, yangidan qo'shamiz
    try:
        scheduler.remove_job("daily_quote")
    except Exception:
        pass

    interval_hours = sched_data.get("interval_hours") or 24
    tz = pytz.timezone(config.TIMEZONE)

    if interval_hours == 24:
        send_time = sched_data.get("send_time") or "09:00"
        try:
            hh, mm = map(int, send_time.split(":"))
        except ValueError:
            hh, mm = 9, 0
        scheduler.add_job(
            send_daily_quote_to_all,
            CronTrigger(hour=hh, minute=mm, timezone=tz),
            id="daily_quote",
        )
    else:
        scheduler.add_job(
            send_daily_quote_to_all,
            IntervalTrigger(hours=interval_hours, timezone=tz),
            id="daily_quote",
        )
    logger.info(f"Scheduler yangilandi. Interval: {interval_hours}h")
