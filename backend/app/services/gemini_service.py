from __future__ import annotations

import abc
import json
import re
from typing import Any

import google.generativeai as genai
from PIL import Image

from app.config import settings


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
		genai.configure(api_key=settings.GEMINI_API_KEY)
		self.model = genai.GenerativeModel("gemini-2.0-flash")

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
		response = self.model.generate_content([PROMPT, image])
		if not response or not getattr(response, "text", None):
			raise ValueError("Empty response from Gemini OCR")
		return self._extract_json(response.text)
