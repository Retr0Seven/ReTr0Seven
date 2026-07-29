#!/usr/bin/env python3
"""Regenerate assets/portrait.txt from a portrait photo.

This helper is optional and is not used by GitHub Actions. It requires Pillow,
NumPy, and OpenCV. The included portrait.txt was generated from Mouad's supplied
photo, so the repository works without shipping the original photo.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError as exc:
    raise SystemExit("Install Pillow, numpy, and opencv-python-headless first") from exc

RAMP = "@%#s*c+=-:. "


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("assets/portrait.txt"))
    parser.add_argument("--cols", type=int, default=88)
    parser.add_argument("--rows", type=int, default=62)
    args = parser.parse_args()

    image = Image.open(args.input).convert("RGB")
    width, height = image.size

    # Defaults tuned for the supplied square portrait. The polygon isolates the
    # head, headphones, scarf, and upper body while clearing the bright scene.
    sx, sy = width / 1244, height / 1244
    points = [
        (610,405),(690,410),(750,450),(795,520),(800,635),(780,695),
        (840,760),(930,820),(980,980),(250,980),(300,850),(400,780),
        (455,720),(430,640),(430,520),(480,445),(540,415),
    ]
    points = [(int(x * sx), int(y * sy)) for x, y in points]
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    draw.ellipse((int(410*sx), int(395*sy), int(820*sx), int(785*sy)), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, int(5 * sx))))

    crop_box = (int(330*sx), int(380*sy), int(910*sx), int(1020*sy))
    crop = np.array(image.crop(crop_box))
    crop_mask = np.array(mask.crop(crop_box)).astype(np.float32) / 255

    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    base = cv2.bilateralFilter(gray, 7, 50, 50)
    base = cv2.createCLAHE(clipLimit=2.7, tileGridSize=(8, 8)).apply(base)
    dx = cv2.Sobel(base, cv2.CV_32F, 1, 0, ksize=3)
    dy = cv2.Sobel(base, cv2.CV_32F, 0, 1, ksize=3)
    edge = np.clip(cv2.magnitude(dx, dy) / 220, 0, 1)
    value = np.power(np.clip(base / 255.0, 0, 1), 1.35)
    value = np.clip(value - edge * 0.23, 0, 1)
    enhanced = (value * 255).astype(np.uint8)
    isolated = (enhanced * crop_mask + 255 * (1 - crop_mask)).astype(np.uint8)
    small = cv2.resize(isolated, (args.cols, args.rows), interpolation=cv2.INTER_AREA)
    indices = (small / 255 * (len(RAMP) - 1)).astype(int)
    lines = ["".join(RAMP[index] for index in row) for row in indices]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
