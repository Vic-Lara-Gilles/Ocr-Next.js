from __future__ import annotations

from PIL import Image
from pdf2image import convert_from_path

import cv2
import numpy as np

from app.logger import get_logger

logger = get_logger("ocr.pdf")


class PDFService:
    def _detect_skew_angle(self, image_bgr: np.ndarray) -> float:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=120,
            minLineLength=max(image_bgr.shape[1] // 4, 100),
            maxLineGap=20,
        )
        if lines is None:
            return 0.0

        angles: list[float] = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if -45 <= angle <= 45:
                angles.append(float(angle))

        if not angles:
            return 0.0
        return float(np.median(angles))

    def _rotate(self, image_bgr: np.ndarray, angle: float) -> np.ndarray:
        if abs(angle) < 0.1:
            return image_bgr
        h, w = image_bgr.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image_bgr,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    def process_pdf(self, file_path: str) -> list[Image.Image]:
        logger.info("Converting PDF to images: %s", file_path)
        pages = convert_from_path(file_path, dpi=300)
        processed_images: list[Image.Image] = []

        for page in pages:
            image_bgr = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            skew_angle = self._detect_skew_angle(image_bgr)
            deskewed = self._rotate(image_bgr, skew_angle)
            gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(
                gray, None, h=10, templateWindowSize=7, searchWindowSize=21
            )
            processed_images.append(Image.fromarray(denoised).convert("RGB"))

        logger.info("PDF processing complete: %d pages", len(processed_images))
        return processed_images
