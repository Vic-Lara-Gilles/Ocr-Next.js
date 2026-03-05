from __future__ import annotations

import abc
import concurrent.futures
import json
import re
from typing import Any

from google import genai
from PIL import Image

from app.config import settings
from app.logger import get_logger

# Max simultaneous Gemini requests — stays within 10 RPM free-tier limit
GEMINI_CONCURRENCY = 5

logger = get_logger("ocr.gemini")


PROMPT = (
    "Extract all text and tables from this document image. Return only a valid JSON object "
    "with three fields: texto containing the full plain text as a string, tablas containing "
    "an array of objects each with headers as array of strings and rows as array of arrays of "
    "strings, and campos containing a flat object with key-value pairs for any dates amounts IDs "
    "names or relevant structured data found. Do not return anything outside the JSON object."
)


class OCRService(abc.ABC):
    @abc.abstractmethod
    def process_image(self, image: Image.Image) -> dict[str, Any]:
        raise NotImplementedError


class GeminiOCRService(OCRService):
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _extract_json(self, response_text: str) -> dict[str, Any]:
        cleaned = response_text.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1)

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Gemini response is not a JSON object")

        data.setdefault("texto", "")
        data.setdefault("tablas", [])
        data.setdefault("campos", {})
        return data

    def process_image(self, image: Image.Image) -> dict[str, Any]:
        logger.info("Calling Gemini OCR (image size=%dx%d)", image.width, image.height)
        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[PROMPT, image],
        )
        if not response or not getattr(response, "text", None):
            logger.error("Empty response from Gemini")
            raise ValueError("Empty response from Gemini OCR")
        try:
            result = self._extract_json(response.text)
            logger.info(
                "Gemini OCR success: %d chars, %d tables, %d campos",
                len(result.get("texto", "")),
                len(result.get("tablas", [])),
                len(result.get("campos", {})),
            )
            return result
        except Exception as exc:
            logger.error(
                "JSON parse error: %s | raw=%.200s", exc, response.text, exc_info=True
            )
            raise

    def process_images_parallel(
        self, images: list[Image.Image]
    ) -> list[dict[str, Any]]:
        """Process all pages concurrently, preserving page order."""
        logger.info(
            "Processing %d pages in parallel (max_workers=%d)",
            len(images),
            GEMINI_CONCURRENCY,
        )
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=GEMINI_CONCURRENCY
        ) as executor:
            results = list(executor.map(self.process_image, images))
        logger.info("Parallel OCR complete: %d pages", len(results))
        return results
