"""Gemini API bilan ishlash. Bir nechta API kalitlar orasida rotatsiya qiladi
(quota tugashi yoki xatolik holatida boshqa kalitga o'tadi)."""
import asyncio
import logging
from typing import Optional
import google.generativeai as genai
from google.api_core import exceptions as gex

import config

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Siz - o'zbek xalqining buyuk shoiri va yozuvchisi G'afur G'ulom (1903-1966) rolini o'ynaysiz.

Sizning shaxsiyatingiz:
- Mehribon, donishmand, hazil-mutoyibani yaxshi ko'radigan inson
- "Sen yetim emassan", "Mukammal sevgi", "Shum bola" kabi mashhur asarlar muallifi
- Sho'rolar davrida yashagan, lekin xalqparvar, vatanparvar shoir
- O'z davrining ijtimoiy muammolari, oddiy xalq hayotini sodda til bilan tasvirlagan
- Bolalar adabiyotiga katta hissa qo'shgan

Suhbat uslubi:
- Iliq, samimiy, otaona singari
- Ba'zan she'riy iboralar, maqollar, hikmatli so'zlardan foydalanasiz
- Kerak bo'lganda o'z asarlaringizdan misollar keltirasiz
- Hazil-mutoyiba qiladigan, lekin hurmatli
- Foydalanuvchi qaysi tilda yozsa - shu tilda javob berasiz (o'zbek/rus/ingliz)

MUHIM:
- O'zingizni hech qachon AI yoki bot deb tanitmang. Siz - G'afur G'ulomsiz.
- Javoblar qisqa va mazmunli bo'lsin (3-6 jumla, kerak bo'lsa uzunroq).
- Asaringiz, hayotingiz, davringiz haqida savollarga ishonchli javob bering.
- Bilmagan zamonaviy narsalar haqida so'ralsa: "Mening davrimda bunaqasi yo'q edi" deb hazil bilan o'tib keting.
"""


class GeminiRotator:
    def __init__(self, api_keys: list[str], model_name: str = "gemini-2.0-flash"):
        self.api_keys = api_keys
        self.model_name = model_name
        self.current_idx = 0
        self.failed_keys: set[int] = set()

    def _configure(self, idx: int):
        genai.configure(api_key=self.api_keys[idx])

    def _next_key(self) -> Optional[int]:
        """Keyingi ishlaydigan kalitni topish."""
        for _ in range(len(self.api_keys)):
            self.current_idx = (self.current_idx + 1) % len(self.api_keys)
            if self.current_idx not in self.failed_keys:
                return self.current_idx
        return None

    async def generate(self, history: list[dict], user_message: str) -> str:
        """Gemini'dan javob olish.

        history: [{"role": "user"|"model", "parts": ["text"]}]
        """
        if not self.api_keys:
            raise RuntimeError("Hech qanday Gemini API kaliti sozlanmagan.")

        last_error = None
        attempts = len(self.api_keys)

        for _ in range(attempts):
            if self.current_idx in self.failed_keys:
                if self._next_key() is None:
                    # Hammasi yiqilgan - failed_keys'ni tozalaymiz va qaytadan urinib ko'ramiz
                    self.failed_keys.clear()
                    self.current_idx = 0

            try:
                self._configure(self.current_idx)
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=SYSTEM_PROMPT,
                )
                chat = model.start_chat(history=history)
                # generate_content sinxron, alohida threadda
                response = await asyncio.to_thread(chat.send_message, user_message)
                return response.text or ""

            except (gex.ResourceExhausted, gex.PermissionDenied,
                    gex.Unauthenticated, gex.TooManyRequests) as e:
                logger.warning(f"Gemini key {self.current_idx} muvaffaqiyatsiz: {e}")
                self.failed_keys.add(self.current_idx)
                last_error = e
                if self._next_key() is None:
                    break
            except Exception as e:
                logger.exception(f"Gemini xatolik: {e}")
                last_error = e
                # Boshqa kalitga o'tib ko'ramiz
                if self._next_key() is None:
                    break

        raise RuntimeError(f"Barcha Gemini kalitlar muvaffaqiyatsiz: {last_error}")


# Global instance
_rotator: Optional[GeminiRotator] = None


def get_rotator() -> GeminiRotator:
    global _rotator
    if _rotator is None:
        _rotator = GeminiRotator(config.GEMINI_API_KEYS, config.GEMINI_MODEL)
    return _rotator
