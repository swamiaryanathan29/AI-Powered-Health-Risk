#!/usr/bin/env python3
"""
Generate a minimal test PNG image containing a survey form text.
Usage: python sample_inputs/generate_test_image.py
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    text = (
        "Age: 42\n"
        "Smoker: yes\n"
        "Exercise: rarely\n"
        "Diet: high sugar\n"
    )

    img = Image.new("RGB", (400, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.multiline_text((20, 20), text, fill=(0, 0, 0), spacing=8)

    out_path = os.path.join(os.path.dirname(__file__), "survey_form.png")
    img.save(out_path)
    print(f"✅ Saved: {out_path}")

except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
