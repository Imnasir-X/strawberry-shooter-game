"""Play a few seconds headlessly and save a frame to docs/preview.png.

Usage: SDL_VIDEODRIVER=dummy python scripts/render_preview.py
"""

import math
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import shooter_game as game  # noqa: E402

FRAMES = 420


class AutoPilot:
    """Holds fire and sweeps left and right so the frame shows some action."""

    def __init__(self):
        self.frame = 0

    def __call__(self):
        self.frame += 1
        direction = pygame.K_LEFT if math.sin(self.frame / 40) < 0 else pygame.K_RIGHT
        pressed = {pygame.K_SPACE, direction}
        return type("Keys", (), {"__getitem__": lambda _self, k: k in pressed})()


def main():
    random.seed(4)
    pygame.key.get_pressed = AutoPilot()
    game.game_over_screen = lambda score, high: (game.MENU, max(score, high))
    original_flip = pygame.display.flip
    count = {"n": 0}

    def flip():
        count["n"] += 1
        if count["n"] == FRAMES:
            out = ROOT / "docs" / "preview.png"
            out.parent.mkdir(exist_ok=True)
            pygame.image.save(game.screen, str(out))
            print(f"Saved {out}")
        original_flip()

    pygame.display.flip = flip
    game.main_game(0, max_frames=FRAMES + 1, autostart=True)
    pygame.quit()


if __name__ == "__main__":
    main()
