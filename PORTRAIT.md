# ASCII avatar

This version uses the Retr0Seven logo rather than a personal portrait.

The source image is stored at:

```text
assets/avatar-source.jpg
```

The generator converts the bright logo strokes into a compact character ramp:

```text
space · + @
```

Each row is revealed from left to right through an animated SVG clip path. The
animation runs once and freezes, while the terminal cursor continues blinking.

Regenerate it with:

```bash
python -m pip install Pillow
python scripts/generate_ascii.py assets/avatar-source.jpg ascii.svg
```

The generated SVG has no external image or font dependency.
