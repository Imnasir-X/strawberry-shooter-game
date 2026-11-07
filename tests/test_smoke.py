"""Headless smoke tests for the game loop (no display or audio device needed)."""

import pygame
import pytest

import shooter_game as game


class FakeKeys:
    """Stand-in for pygame.key.get_pressed() that holds the fire key down."""

    def __init__(self, pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def test_assets_load():
    assert game.background_img is not None
    assert game.bullet_img is not None
    assert game.enemy_img.get_width() == 60
    assert game.boss_img.get_width() == 160


def test_enemies_actually_fall():
    enemy = game.Enemy(score=0)
    start = enemy.rect.y
    for _ in range(30):
        enemy.update()
    assert enemy.rect.y > start


def test_triple_shot_fires_three_bullets():
    player = game.Player()
    bullets = pygame.sprite.Group()
    player.triple_shot = True
    player.last_shot_time = -10_000
    player.shoot(bullets, pygame.sprite.Group())
    assert len(bullets) == 3


def test_game_loop_runs_headless(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys({pygame.K_SPACE}))
    monkeypatch.setattr(game, "game_over_screen", lambda score, high: (game.MENU, max(score, high)))
    high = game.main_game(0, max_frames=600, autostart=True)
    assert isinstance(high, int)


def test_game_over_restart_starts_fresh_run(monkeypatch):
    player = game.Player()
    group = pygame.sprite.GroupSingle(player)
    monkeypatch.setattr(game, "game_over_screen", lambda score, high: (game.PLAYING, max(score, high)))
    state, high = game.end_run(player, 120, 50)
    assert state == game.PLAYING
    assert high == 120
    assert not group  # the dead player is removed, so the loop resets score and lives


@pytest.fixture(autouse=True, scope="session")
def _quit_pygame():
    yield
    pygame.quit()
