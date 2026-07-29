# Setup

## 1. Use the correct profile repository

The repository must be public and named exactly like the GitHub username:

```text
Retr0Seven
```

GitHub treats the name case-insensitively, so an existing `ReTr0Seven` profile
repository also works.

## 2. Replace the current repository contents

Copy everything from this package into the root of the profile repository and
push it to the default branch.

```bash
git add .
git commit -m "profile: install self-generated README"
git push
```

## 3. Run the workflow once

Open the repository on GitHub:

```text
Actions → refresh profile graphics → Run workflow
```

The included SVG files contain a preview snapshot. The first workflow run
replaces that snapshot with the current public contribution and repository data.

## 4. Workflow permissions

The workflow declares:

```yaml
permissions:
  contents: write
```

If GitHub still blocks the commit, open:

```text
Repository Settings → Actions → General → Workflow permissions
```

Select **Read and write permissions**.

## Local preview

The statistics generator uses only the Python standard library:

```bash
python scripts/generate_stats.py --demo
```

The static headings and stack graphic can be rebuilt with:

```bash
python scripts/generate_static_assets.py
```

## Portrait regeneration

The repository does not contain the original photo. The generated ASCII artwork
is stored in `assets/ascii-portrait.png` and embedded into `hero.svg` when the
statistics script runs.

To experiment with the text-based portrait generator:

```bash
pip install pillow numpy opencv-python-headless
python scripts/generate_portrait.py path/to/photo.jpg
```

That command rewrites `assets/portrait.txt`. The high-fidelity hero currently
uses `assets/ascii-portrait.png`; replacing it requires an image with the same
transparent-background treatment.
