# Animated terminal hero

The profile opens with a terminal-style SVG rather than a portrait or logo.

It displays the quote:

> you are less valuable than the data you produce

The two quote lines are revealed once with SVG clip-path animations. Mouad's
name, title, location, and GitHub handle then fade in below the quote. A small
cursor continues blinking after the entrance animation ends.

The hero is stored in:

```text
hero.svg
```

It uses only inline SVG, SMIL animation, gradients, and system fonts. It makes
no network requests and does not require a build step.
