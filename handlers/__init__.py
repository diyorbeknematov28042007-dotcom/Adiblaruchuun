"""Handler routerlari."""
from aiogram import Router

from . import start, menu, biography, works, ai_chat, contests, questions, admin


def get_main_router() -> Router:
    """Barcha routerlarni birlashtiradi. Tartib MUHIM!"""
    router = Router()
    # Admin birinchi - admin states bo'lsa, admin handlerlar ushlasin
    router.include_router(admin.router)
    # Asosiy
    router.include_router(start.router)
    router.include_router(menu.router)
    router.include_router(biography.router)
    router.include_router(works.router)
    router.include_router(contests.router)
    router.include_router(questions.router)
    # AI suhbat oxirida — chunki u har qanday matnni ushlaydi state'da
    router.include_router(ai_chat.router)
    return router
