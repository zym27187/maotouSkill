#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image, ImageSequence
from rapidocr_onnxruntime import RapidOCR


VALID_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def load_image_for_ocr(path: Path) -> Image.Image:
    image = Image.open(path)
    if getattr(image, "is_animated", False):
        try:
            image = next(ImageSequence.Iterator(image)).copy()
        except StopIteration:
            image = image.copy()
    else:
        image = image.copy()

    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    return image


def normalize_lines(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        clean = " ".join(line.split())
        if clean:
            normalized.append(clean)
    return normalized


def classify(char_count: int, line_count: int) -> str:
    if char_count == 0:
        return "no_text"
    if char_count < 8:
        return "tiny_text"
    if char_count < 30 or line_count <= 1:
        return "short_text"
    return "rich_text"


def scan_images(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "ocr_raw.jsonl"
    summary_path = output_dir / "ocr_summary.tsv"
    buckets_path = output_dir / "ocr_buckets.json"

    engine = RapidOCR()
    image_paths = sorted(
        path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in VALID_SUFFIXES
    )

    buckets: dict[str, list[str]] = {
        "no_text": [],
        "tiny_text": [],
        "short_text": [],
        "rich_text": [],
    }

    with raw_path.open("w", encoding="utf-8") as raw_file, summary_path.open(
        "w", encoding="utf-8", newline=""
    ) as summary_file:
        writer = csv.writer(summary_file, delimiter="\t")
        writer.writerow(
            [
                "filename",
                "relative_path",
                "category",
                "char_count",
                "line_count",
                "avg_confidence",
                "text_preview",
            ]
        )

        for idx, image_path in enumerate(image_paths, start=1):
            image = load_image_for_ocr(image_path)
            result, elapsed = engine(image)

            text_lines: list[str] = []
            confidences: list[float] = []
            raw_items: list[dict[str, Any]] = []

            for item in result or []:
                box, text, confidence = item
                text_str = str(text)
                text_lines.append(text_str)
                confidences.append(float(confidence))
                raw_items.append(
                    {
                        "box": box,
                        "text": text_str,
                        "confidence": float(confidence),
                    }
                )

            clean_lines = normalize_lines(text_lines)
            joined = "\n".join(clean_lines)
            char_count = len(joined.replace("\n", ""))
            category = classify(char_count, len(clean_lines))
            avg_confidence = round(mean(confidences), 6) if confidences else 0.0
            preview = joined.replace("\n", " / ")[:180]

            record = {
                "index": idx,
                "filename": image_path.name,
                "relative_path": str(image_path.relative_to(input_dir)),
                "category": category,
                "char_count": char_count,
                "line_count": len(clean_lines),
                "avg_confidence": avg_confidence,
                "elapsed": elapsed,
                "text_lines": clean_lines,
                "raw_items": raw_items,
            }

            raw_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            writer.writerow(
                [
                    image_path.name,
                    record["relative_path"],
                    category,
                    char_count,
                    len(clean_lines),
                    avg_confidence,
                    preview,
                ]
            )
            buckets[category].append(image_path.name)

    with buckets_path.open("w", encoding="utf-8") as buckets_file:
        json.dump(buckets, buckets_file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch OCR images and bucket them by text density.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    scan_images(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
