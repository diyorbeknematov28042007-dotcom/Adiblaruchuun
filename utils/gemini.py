"""Gemini API bilan ishlash. Bir nechta API kalitlar orasida rotatsiya qiladi."""
import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types

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

    def _get_client(self, idx: int):
        return genai.Client(api_key=self.api_keys[idx])

    def _next_key(self) -> Optional[int]:
        for _ in range(len(self.api_keys)):
            self.current_idx = (self.current_idx + 1) % len(self.api_keys)
            if self.current_idx not in self.failed_keys:
                return self.current_idx
        return None

    async def generate(self, history: list[dict], user_message: str) -> str:
        if not self.api_keys:
            raise RuntimeError("Hech qanday Gemini API kaliti sozlanmagan.")

        last_error = None
        attempts = len(self.api_keys)

        for _ in range(attempts):
            if self.current_idx in self.failed_keys:
                if self._next_key() is None:
                    self.failed_keys.clear()
                    self.current_idx = 0

            try:
                client = self._get_client(self.current_idx)

                # History'ni yangi formatga o'tkazish
                contents = []
                for msg in history:
                    role = msg.get("role", "user")
                    if role == "model":
                        role = "model"
                    else:
                        role = "user"
                    parts_list = msg.get("parts", [])
                    text = parts_list[0] if parts_list else ""
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=text)]
                        )
                    )

                # Foydalanuvchi xabarini qo'shamiz
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_message)]
                    )
                )

                generate_config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1024,
                    temperature=0.8,
                )

                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=self.model_name,
                    contents=contents,
                    config=generate_config,
                )
                return response.text or ""

            except Exception as e:
                error_str = str(e).lower()
                logger.warning(f"Gemini key {self.current_idx} xato: {e}")
                last_error = e

                if "quota" in error_str or "429" in error_str or "resource" in error_str:
                    self.failed_keys.add(self.current_idx)

                if self._next_key() is None:
                    break

        raise RuntimeError(f"Barcha Gemini kalitlar muvaffaqiyatsiz: {last_error}")


_rotator: Optional[GeminiRotator] = None


def get_rotator() -> GeminiRotator:
    global _rotator
    if _rotator is None:
        _rotator = GeminiRotator(config.GEMINI_API_KEYS, config.GEMINI_MODEL)
    return _rotator
