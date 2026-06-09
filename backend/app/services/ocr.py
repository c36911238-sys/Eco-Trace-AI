"""
OCR Service — Driver-based abstraction layer.

Production: swap MockOCRDriver for GoogleVisionOCRDriver or TesseractOCRDriver.
Testing: MockOCRDriver returns deterministic, seeded results.
"""
import os
import random
from abc import ABC, abstractmethod

from app.db.models import CategoryEnum


class OCRDriver(ABC):
    """Abstract interface for all OCR receipt extraction backends."""

    @abstractmethod
    def extract_receipt(self, image_bytes: bytes) -> dict:
        """
        Parse a receipt image and return structured carbon emission data.

        Args:
            image_bytes: Raw bytes of the uploaded image file.

        Returns:
            A dict with keys:
              - success (bool): Whether extraction succeeded.
              - extracted_data (dict | None): Carbon log fields if successful.
        """
        raise NotImplementedError


class MockOCRDriver(OCRDriver):
    """
    Deterministic mock OCR driver for local development and testing.
    Uses a seeded random source so tests are reproducible.
    """

    _RECEIPT_SCENARIOS = [
        {
            "category": CategoryEnum.food,
            "amount_range": (5.0, 25.0),
            "description": "Grocery Store Purchase",
        },
        {
            "category": CategoryEnum.transportation,
            "amount_range": (15.0, 45.0),
            "description": "Fuel Station Receipt",
        },
        {
            "category": CategoryEnum.electricity,
            "amount_range": (30.0, 100.0),
            "description": "Utility Bill",
        },
    ]

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def extract_receipt(self, image_bytes: bytes) -> dict:
        scenario = self._rng.choice(self._RECEIPT_SCENARIOS)
        low, high = scenario["amount_range"]
        amount = round(self._rng.uniform(low, high), 2)

        return {
            "success": True,
            "extracted_data": {
                "category": scenario["category"],
                "emission_amount": amount,
                "description": scenario["description"],
                "source": "ocr",
            },
        }


class GoogleVisionOCRDriver(OCRDriver):
    """
    Production OCR driver backed by Google Cloud Vision API.

    Requires GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS
    environment variables to be configured.
    """

    def extract_receipt(self, image_bytes: bytes) -> dict:
        # TODO: Implement Google Cloud Vision API call here.
        # Example:
        #   from google.cloud import vision
        #   client = vision.ImageAnnotatorClient()
        #   image = vision.Image(content=image_bytes)
        #   response = client.text_detection(image=image)
        #   texts = response.text_annotations
        #   ... parse texts into category + emission_amount ...
        raise NotImplementedError(
            "GoogleVisionOCRDriver is not yet implemented. "
            "Set OCR_DRIVER=mock in your .env to use the mock driver."
        )


_DRIVER_MAP: dict[str, type[OCRDriver]] = {
    "mock": MockOCRDriver,
    "google_vision": GoogleVisionOCRDriver,
}

_ocr_driver_instance: OCRDriver | None = None


def get_ocr_driver() -> OCRDriver:
    """
    Return the configured OCR driver singleton.

    The driver is selected via the OCR_DRIVER environment variable.
    Defaults to 'mock' if not set.

    Returns:
        An OCRDriver instance.
    """
    global _ocr_driver_instance
    if _ocr_driver_instance is None:
        driver_name = os.getenv("OCR_DRIVER", "mock").lower()
        driver_class = _DRIVER_MAP.get(driver_name)
        if driver_class is None:
            raise ValueError(
                f"Unknown OCR_DRIVER '{driver_name}'. "
                f"Valid options: {list(_DRIVER_MAP.keys())}"
            )
        _ocr_driver_instance = driver_class()
    return _ocr_driver_instance
