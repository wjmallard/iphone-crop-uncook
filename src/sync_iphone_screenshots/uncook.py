"""Template matching to locate a JPEG crop region within the original PNG."""

import cv2
import numpy as np
from PIL import Image


def find_crop_region(
    original_path: str, edited_path: str, threshold: float = 0.8
) -> tuple[int, int, int, int] | None:
    """Find where the edited crop lives in the original image.

    Returns (x, y, w, h) in original image coordinates, or None if no match.
    """
    original = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
    edited = cv2.imread(edited_path, cv2.IMREAD_GRAYSCALE)

    if original is None or edited is None:
        return None

    orig_h, orig_w = original.shape
    edit_h, edit_w = edited.shape

    # If same dimensions, no crop was applied (just color/exposure edits)
    if orig_h == edit_h and orig_w == edit_w:
        return (0, 0, orig_w, orig_h)

    # Template must be smaller than the source
    if edit_h > orig_h or edit_w > orig_w:
        return None

    result = cv2.matchTemplate(original, edited, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    x, y = max_loc
    return (x, y, edit_w, edit_h)


def lossless_crop(original_path: str, region: tuple[int, int, int, int]) -> Image.Image:
    """Crop the original PNG using Pillow (lossless)."""
    x, y, w, h = region
    img = Image.open(original_path)
    return img.crop((x, y, x + w, y + h))
