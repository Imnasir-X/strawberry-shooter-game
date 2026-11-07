"""Strawberry Shooter - Birthday Edition.

A small arcade shooter built with pygame: move along the bottom of the screen,
fire strawberries at falling birthday cakes, chain combos, collect power-ups
and take down a boss every few hundred points.
"""

import math
import os
import random
import sys

import pygame

# Initialize Pygame
pygame.init()
try:
    pygame.mixer.init()
except pygame.error as e:  # No audio device (CI, headless servers)
    print(f"Audio unavailable: {e}. Running without sound.")
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Strawberry Shooter - Birthday Edition")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
BLACK = (0, 0, 0)
PINK  = (255, 105, 180)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Base directory for assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")

# Debug logging: set STRAWBERRY_DEBUG=1 to enable.
DEBUG = os.environ.get("STRAWBERRY_DEBUG", "").lower() in ("1", "true", "yes")

# Game states
MENU = 0
PLAYING = 1
PAUSE = 2

# Placeholder for stars (for menu background)
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 2), random.randint(1, 3), WHITE] for _ in range(50)]

# ========== IMAGE LOADING & SCALING ==========
def scale_image(img, target_width):
    aspect = img.get_height() / img.get_width()
    return pygame.transform.smoothscale(img, (target_width, int(target_width * aspect)))

# Load Happy Birthday Background
background_path = os.path.join(ASSET_DIR, "background.png")
if DEBUG:
    print(f"Attempting to load background from: {background_path}")
try:
    background_img = pygame.image.load(background_path).convert_alpha()
    background_img = pygame.transform.smoothscale(background_img, (WIDTH, HEIGHT))
    if DEBUG:
        print("Happy birthday background loaded successfully.")
except (FileNotFoundError, pygame.error) as e:
    print(f"Could not load {background_path}: {e}. Using the star-field background.")
    background_img = None

def make_player_placeholder(size=60):
    """Draw a simple launcher sprite used when no custom player image is supplied."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.polygon(surf, PINK, [(size // 2, 0), (size, size), (0, size)])
    pygame.draw.polygon(surf, WHITE, [(size // 2, 0), (size, size), (0, size)], 3)
    pygame.draw.circle(surf, RED, (size // 2, size * 2 // 3), size // 6)
    return surf


def load_optional_image(filenames, width):
    """Load the first image that exists in assets/, scaled to `width`, or None."""
    for name in filenames:
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            continue
        try:
            img = scale_image(pygame.image.load(path).convert_alpha(), width)
            if DEBUG:
                print(f"Loaded {name}.")
            return img
        except pygame.error as e:
            print(f"Error loading {name}: {e}.")
    return None


def make_strawberry(size=34):
    """Draw a strawberry sprite (berry body, seeds and leafy top)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    w, h = size, size
    body = [(w * 0.5, h * 0.98), (w * 0.08, h * 0.45), (w * 0.2, h * 0.25),
            (w * 0.5, h * 0.3), (w * 0.8, h * 0.25), (w * 0.92, h * 0.45)]
    pygame.draw.polygon(surf, (220, 30, 60), body)
    pygame.draw.circle(surf, (220, 30, 60), (int(w * 0.3), int(h * 0.42)), int(w * 0.22))
    pygame.draw.circle(surf, (220, 30, 60), (int(w * 0.7), int(h * 0.42)), int(w * 0.22))
    for sx, sy in [(0.3, 0.45), (0.5, 0.5), (0.7, 0.45), (0.4, 0.65), (0.6, 0.65), (0.5, 0.8)]:
        pygame.draw.ellipse(surf, (255, 230, 120), (int(w * sx) - 1, int(h * sy) - 2, 3, 4))
    leaves = [(w * 0.5, h * 0.3), (w * 0.2, h * 0.12), (w * 0.4, h * 0.18), (w * 0.5, h * 0.02),
              (w * 0.6, h * 0.18), (w * 0.8, h * 0.12)]
    pygame.draw.polygon(surf, (40, 160, 60), leaves)
    return surf


def make_cake(size=60):
    """Draw a small birthday cake sprite with a lit candle."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = size
    pygame.draw.rect(surf, (250, 210, 230), (s * 0.1, s * 0.45, s * 0.8, s * 0.45), border_radius=6)
    pygame.draw.rect(surf, (255, 250, 245), (s * 0.1, s * 0.45, s * 0.8, s * 0.12), border_radius=6)
    for i in range(5):
        pygame.draw.circle(surf, (255, 250, 245), (int(s * (0.18 + i * 0.16)), int(s * 0.57)), int(s * 0.06))
    pygame.draw.rect(surf, (230, 90, 140), (s * 0.1, s * 0.75, s * 0.8, s * 0.06))
    pygame.draw.rect(surf, (120, 190, 255), (s * 0.46, s * 0.22, s * 0.08, s * 0.23))
    pygame.draw.ellipse(surf, (255, 200, 40), (s * 0.43, s * 0.06, s * 0.14, s * 0.18))
    pygame.draw.ellipse(surf, (255, 120, 0), (s * 0.465, s * 0.12, s * 0.07, s * 0.09))
    return surf


# Sprites are drawn in code so the game runs with no image files. To use your
# own art, drop player.png, enemy.png or strawberry.png into assets/.
player_img = load_optional_image(["player.png", "player.jpg"], 60) or make_player_placeholder(60)
enemy_img = load_optional_image(["enemy.png", "enemy.jpg"], 60) or make_cake(60)
boss_img = scale_image(enemy_img, 160)


def load_sprite_sheet(filename, frame_width, frame_height, num_frames):
    sheet = pygame.image.load(filename).convert_alpha()
    frames = []
    for i in range(num_frames):
        frame = sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
        frames.append(scale_image(frame, 40))
    return frames


# Optional animated strawberry: assets/strawberry_sheet.png, 4 frames of 50x50.
bullet_frames = None
try:
    sheet_path = os.path.join(ASSET_DIR, "strawberry_sheet.png")
    if os.path.exists(sheet_path):
        bullet_frames = load_sprite_sheet(sheet_path, frame_width=50, frame_height=50, num_frames=4)
except (pygame.error, ValueError) as e:
    print(f"Sprite sheet error: {e}. Using the static strawberry.")
    bullet_frames = None

bullet_img = load_optional_image(["strawberry.png"], 40) or make_strawberry(34)

# ========== SOUND LOADING ==========
def load_sound(name):
    """Load a sound from assets/, returning None if audio is unavailable."""
    if not pygame.mixer.get_init():
        return None
    try:
        sound = pygame.mixer.Sound(os.path.join(ASSET_DIR, name))
        if DEBUG:
            print(f"{name} loaded successfully.")
        return sound
    except (FileNotFoundError, pygame.error) as e:
        print(f"Error loading {name}: {e}. Continuing without it.")
        return None


shoot_sound = load_sound("shoot.wav")
hit_sound = load_sound("hit.wav")
enemy_die_sound = load_sound("enemy_die.wav")
explosion_sound = None
powerup_sound = None

# Sound cooldown to prevent echo
last_enemy_die_time = 0
SOUND_COOLDOWN = 100  # milliseconds

# ========== PARTICLE EFFECTS ==========
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, color=PINK, radius=3, lifespan=20):
        super().__init__()
        self.pos = list(pos)
        self.radius = radius
        self.lifespan = lifespan
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]

    def update(self):
        self.lifespan -= 1
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.rect.center = self.pos
        if self.lifespan <= 0:
            self.kill()

# ========== SPRITE CLASSES ==========
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.speed = 7
        self.lives = 3
        self.bombs = 1
        self.shield_active = False
        self.triple_shot = False
        self.shield_timer = 0
        self.triple_shot_timer = 0
        self.shield_duration = 600
        self.triple_shot_duration = 600
        self.last_shot_time = 0
        self.shoot_cooldown = 200  # 200ms cooldown between shots

    def update(self, keys_pressed):
        if keys_pressed[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys_pressed[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if self.shield_active:
            self.shield_timer += 1
            if self.shield_timer >= self.shield_duration:
                self.shield_active = False
        if self.triple_shot:
            self.triple_shot_timer += 1
            if self.triple_shot_timer >= self.triple_shot_duration:
                self.triple_shot = False
        current_time = pygame.time.get_ticks()
        if keys_pressed[pygame.K_SPACE] and (current_time - self.last_shot_time >= self.shoot_cooldown):
            return True
        return False

    def shoot(self, bullet_group, all_sprites):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            spreads = (-3, 0, 3) if self.triple_shot else (0,)
            for x_speed in spreads:
                bullet_group.add(Bullet(self.rect.centerx, self.rect.top, x_speed, -10))
            if DEBUG:
                print(f"Shot fired at {current_time}. Bullet count: {len(bullet_group)}")
            self.last_shot_time = current_time
            if shoot_sound:
                shoot_sound.play()

    def take_damage(self):
        if not self.shield_active:
            self.lives -= 1
            return True
        return False

    def use_bomb(self, enemy_group, boss_group, all_sprites):
        global last_enemy_die_time
        if self.bombs > 0:
            self.bombs -= 1
            current_time = pygame.time.get_ticks()
            for enemy in enemy_group:
                enemy.kill()
                for _ in range(10):
                    particle = Particle(enemy.rect.center, PINK, radius=random.randint(2, 5), lifespan=random.randint(20, 40))
                    all_sprites.add(particle)
            if boss_group.sprite:
                boss_group.sprite.health -= 50
                if boss_group.sprite.health <= 0:
                    boss_group.sprite.kill()
            if enemy_die_sound and (current_time - last_enemy_die_time >= SOUND_COOLDOWN):
                if DEBUG:
                    print("Playing enemy_die.wav for bomb use")
                enemy_die_sound.play()
                last_enemy_die_time = current_time
            return True
        return False

    def draw_shield(self, surface):
        if self.shield_active:
            pygame.draw.circle(surface, (0, 255, 255), self.rect.center, 40, 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, score):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect(midbottom=(random.randint(30, WIDTH - 30), 0))
        # Track y as a float: pygame Rects are integers, so sub-pixel speeds
        # added straight to rect.y were truncated and enemies never moved.
        self.y = float(self.rect.y)
        self.speed = random.uniform(0.8, 1.6 + score * 0.005)

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)
        if self.rect.top > HEIGHT:
            self.kill()

    def take_damage(self):
        return True

class Boss(pygame.sprite.Sprite):
    def __init__(self, health):
        super().__init__()
        self.image = boss_img
        self.rect = self.image.get_rect(center=(WIDTH // 2, 130))
        self.health = health
        self.max_health = health

    def shoot(self, bullet_group):
        return None

    def aim_at_player(self, player, bullet_group):
        pass

    def update(self):
        pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, x_speed, y_speed):
        super().__init__()
        if bullet_frames:
            self.frames = bullet_frames
            self.frame_index = 0
            self.image = self.frames[self.frame_index]
        else:
            self.image = bullet_img
        self.rect = self.image.get_rect(center=(x, y))
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.animation_timer = 0

    def update(self):
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed
        if hasattr(self, 'frames'):
            self.animation_timer += 1
            if self.animation_timer % 5 == 0:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.image = self.frames[self.frame_index]
        if self.rect.bottom < 0 or self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, powerup_type, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(YELLOW if powerup_type == 'shield' else PURPLE if powerup_type == 'triple' else RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.type = powerup_type

    def update(self):
        self.rect.y += 1
        if self.rect.top > HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=pos)
        self.lifespan = 20

    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()

class TextSprite(pygame.sprite.Sprite):
    def __init__(self, text, size, color, pos, duration, speed_y=0):
        super().__init__()
        font = pygame.font.Font(None, size)
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect(center=pos)
        self.y = float(self.rect.y)
        self.duration = duration
        self.speed_y = speed_y

    def update(self):
        self.y += self.speed_y
        self.rect.y = int(self.y)
        self.duration -= 1
        if self.duration <= 0:
            self.kill()

# ========== HELPER FUNCTIONS ==========
def spawn_powerup(pos, powerup_group, all_sprites):
    powerup_types = ['shield', 'triple', 'bomb']
    weights = [0.4, 0.4, 0.2]
    powerup_type = random.choices(powerup_types, weights=weights)[0]

    powerup = PowerUp(powerup_type, pos[0], pos[1])
    powerup_group.add(powerup)
    all_sprites.add(powerup)

    for _ in range(10):
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        particle = Particle(
            (pos[0] + offset_x, pos[1] + offset_y),
            color=(255, 255, 0),
            radius=2,
            lifespan=20
        )
        all_sprites.add(particle)

def render_text_with_shadow(text, font, color, shadow_color, pos, shadow_offset=(2, 2)):
    shadow = font.render(text, True, shadow_color)
    main_text = font.render(text, True, color)
    screen.blit(shadow, (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]))
    screen.blit(main_text, pos)

def draw_bar(surface, x, y, width, height, value, max_value, color, bg_color=(50, 50, 50)):
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    if value > 0:
        fill_width = int(width * (value / max_value))
        pygame.draw.rect(surface, color, (x, y, fill_width, height))
    pygame.draw.rect(surface, (200, 200, 200), (x, y, width, height), 1)

def update_stars(stars_list):
    for star in stars_list:
        star[1] += star[2]
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

def draw_stars(surface, stars_list):
    for star in stars_list:
        pygame.draw.circle(surface, star[4], (int(star[0]), int(star[1])), star[3])

def main_menu():
    menu_font = pygame.font.Font(None, 64)
    instruction_font = pygame.font.Font(None, 32)

    title_text = menu_font.render("Strawberry Shooter", True, RED)
    subtitle_text = menu_font.render("Birthday Edition", True, PINK)
    start_text = instruction_font.render("Press ENTER to Start", True, WHITE)
    controls_text = instruction_font.render("Arrow Keys: Move, SPACE: Shoot, B: Bomb", True, WHITE)

    title_y = HEIGHT // 3
    title_direction = 0.5
    rotation = 0

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return PLAYING
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        update_stars(stars)

        title_y += title_direction
        if title_y > HEIGHT // 3 + 10 or title_y < HEIGHT // 3 - 10:
            title_direction *= -1

        rotation = (rotation + 1) % 360

        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill((10, 10, 40))
            draw_stars(screen, stars)

        menu_frames = bullet_frames or [bullet_img]
        if menu_frames:
            strawberry = menu_frames[(rotation // 90) % len(menu_frames)]
            scaled_strawberry = pygame.transform.scale(strawberry, (50, 50))  # Match bullet size in menu
            rotated_strawberry = pygame.transform.rotate(scaled_strawberry, rotation)
            screen.blit(rotated_strawberry, (50, 50))
            screen.blit(rotated_strawberry, (WIDTH - 100, 50))
            screen.blit(rotated_strawberry, (50, HEIGHT - 100))
            screen.blit(rotated_strawberry, (WIDTH - 100, HEIGHT - 100))

        render_text_with_shadow("Strawberry Shooter", menu_font, RED, BLACK,
                               (WIDTH // 2 - title_text.get_width() // 2, title_y))
        render_text_with_shadow("Birthday Edition", menu_font, PINK, BLACK,
                               (WIDTH // 2 - subtitle_text.get_width() // 2, title_y + 70))

        pulse = (pygame.time.get_ticks() % 1000) / 1000
        alpha = int(128 + 127 * math.sin(pulse * 2 * math.pi))
        start_text_copy = start_text.copy()
        start_text_copy.set_alpha(alpha)
        screen.blit(start_text_copy, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT * 2 // 3))

        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT * 2 // 3 + 50))

        pygame.display.flip()

def pause_game():
    pause_font = pygame.font.Font(None, 48)
    instruction_font = pygame.font.Font(None, 36)

    pause_text = pause_font.render("GAME PAUSED", True, WHITE)
    continue_text = instruction_font.render("Press P to Continue", True, WHITE)
    quit_text = instruction_font.render("Press ESC to Quit", True, WHITE)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return PLAYING
                elif event.key == pygame.K_ESCAPE:
                    return MENU

        screen.blit(overlay, (0, 0))

        render_text_with_shadow("GAME PAUSED", pause_font, WHITE, BLACK,
                               (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))
        render_text_with_shadow("Press P to Continue", instruction_font, WHITE, BLACK,
                               (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT // 2 + 20))
        render_text_with_shadow("Press ESC to Quit", instruction_font, WHITE, BLACK,
                               (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 70))

        pygame.display.flip()

def game_over_screen(final_score, high_score):
    font_large = pygame.font.Font(None, 64)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 36)

    game_over_text = font_large.render("GAME OVER", True, RED)
    restart_text = font_medium.render("Press R to Restart", True, WHITE)
    quit_text = font_medium.render("Press Q for Menu", True, WHITE)
    score_text = font_medium.render(f"Final Score: {final_score}", True, WHITE)

    is_new_high_score = final_score > high_score
    if is_new_high_score:
        high_score = final_score
        high_score_text = font_medium.render("NEW HIGH SCORE!", True, YELLOW)
    else:
        high_score_text = font_medium.render(f"High Score: {high_score}", True, WHITE)

    particles = pygame.sprite.Group()
    for _ in range(50):
        pos = (WIDTH // 2, HEIGHT // 2)
        color = (random.randint(150, 255), random.randint(0, 100), random.randint(0, 100))
        particle = Particle(pos, color=color, radius=random.randint(2, 5), lifespan=random.randint(60, 120))
        particles.add(particle)

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return PLAYING, high_score
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    return MENU, high_score

        particles.update()
        if random.random() < 0.1:
            pos = (random.randint(0, WIDTH), random.randint(0, HEIGHT))
            color = (random.randint(150, 255), random.randint(0, 100), random.randint(0, 100))
            particle = Particle(pos, color=color, radius=random.randint(2, 4), lifespan=random.randint(30, 60))
            particles.add(particle)

        if background_img:
            darkened = background_img.copy()
            dark_overlay = pygame.Surface(darkened.get_size(), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 150))
            darkened.blit(dark_overlay, (0, 0))
            screen.blit(darkened, (0, 0))
        else:
            screen.fill((10, 10, 40))
            for star in stars:
                dimmed_color = tuple(max(0, c-100) for c in star[4][:3])
                pygame.draw.circle(screen, dimmed_color, (int(star[0]), int(star[1])), star[3])

        particles.draw(screen)

        if is_new_high_score:
            pulse = (pygame.time.get_ticks() % 1000) / 1000
            scale_factor = 1.0 + 0.1 * math.sin(pulse * 2 * math.pi)
            scaled_text = pygame.transform.scale(
                high_score_text,
                (int(high_score_text.get_width() * scale_factor),
                 int(high_score_text.get_height() * scale_factor))
            )
            screen.blit(scaled_text,
                      (WIDTH // 2 - scaled_text.get_width() // 2, HEIGHT // 2 + 40))
        else:
            screen.blit(high_score_text,
                      (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 40))

        render_text_with_shadow("GAME OVER", font_large, RED, BLACK,
                              (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        render_text_with_shadow(f"Final Score: {final_score}", font_medium, WHITE, BLACK,
                              (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20))
        render_text_with_shadow("Press R to Restart", font_small, WHITE, BLACK,
                              (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT * 3 // 4))
        render_text_with_shadow("Press Q for Menu", font_small, WHITE, BLACK,
                              (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT * 3 // 4 + 50))

        pygame.display.flip()

def create_enemy_wave(enemy_group, all_sprites, count, score):
    for _ in range(count):
        enemy = Enemy(score)
        enemy_group.add(enemy)
        all_sprites.add(enemy)

def end_run(player, score, high_score):
    """Remove the dead player so the next PLAYING frame starts a fresh run."""
    player.kill()
    return game_over_screen(score, high_score)


def main_game(high_score=0, max_frames=None, autostart=False):
    """Run the menu and game loop. Returns the (possibly updated) high score.

    max_frames and autostart exist for headless smoke tests and screenshots.
    """
    global last_enemy_die_time
    game_state = MENU
    score = 0
    level = 1
    boss_level_interval = 500
    next_boss_score = boss_level_interval
    has_boss = False

    all_sprites = pygame.sprite.Group()
    player_group = pygame.sprite.GroupSingle()
    enemy_group = pygame.sprite.Group()
    boss_group = pygame.sprite.GroupSingle()
    player_bullet_group = pygame.sprite.Group()
    enemy_bullet_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()
    text_group = pygame.sprite.Group()

    spawn_timer = 0
    spawn_interval = 90  # Slow initial spawn rate
    combo_count = 0
    combo_timer = 0

    game_state = PLAYING if autostart else main_menu()
    hud_font = pygame.font.Font(None, 36)
    boss_font = pygame.font.Font(None, 30)
    frames = 0

    running = True
    while running:
        frames += 1
        if max_frames is not None and frames > max_frames:
            return high_score
        if game_state == PLAYING:
            if not player_group:
                all_sprites.empty()
                player_group.empty()
                enemy_group.empty()
                boss_group.empty()
                player_bullet_group.empty()
                enemy_bullet_group.empty()
                powerup_group.empty()
                text_group.empty()

                score = 0
                level = 1
                next_boss_score = boss_level_interval
                has_boss = False
                spawn_timer = 0
                spawn_interval = 90
                combo_count = 0
                combo_timer = 0

                player = Player()
                player_group.add(player)
                all_sprites.add(player)

                ready_text = TextSprite("Get Ready!", 72, YELLOW, (WIDTH // 2, HEIGHT // 2), duration=120, speed_y=-0.5)
                text_group.add(ready_text)
                all_sprites.add(ready_text)

                create_enemy_wave(enemy_group, all_sprites, 3, score)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        game_state = PAUSE
                    elif event.key == pygame.K_b:
                        player = player_group.sprite
                        if player and player.use_bomb(enemy_group, boss_group, all_sprites):
                            bomb_text = TextSprite("BOMB USED!", 48, RED,
                                                 (WIDTH // 2, HEIGHT // 2),
                                                 duration=60, speed_y=-1)
                            text_group.add(bomb_text)
                            all_sprites.add(bomb_text)

            keys_pressed = pygame.key.get_pressed()
            player = player_group.sprite
            if player:
                if player.update(keys_pressed):
                    player.shoot(player_bullet_group, all_sprites)
                    all_sprites.add(player_bullet_group.sprites())

            spawn_timer += 1
            if spawn_timer >= spawn_interval:
                spawn_timer = 0
                enemy_count = min(1 + level // 2, 5)
                create_enemy_wave(enemy_group, all_sprites, enemy_count, score)
                spawn_interval = max(30, 90 - level * 2)

            if combo_count > 0:
                combo_timer += 1
                if combo_timer > 60:
                    combo_count = 0
                    combo_timer = 0

            for sprite in all_sprites:
                if sprite != player:
                    sprite.update()

            boss = boss_group.sprite
            if boss:
                result = boss.shoot(enemy_bullet_group)
                if result == "aim_at_player":
                    boss.aim_at_player(player_group.sprite, enemy_bullet_group)
                if result:
                    all_sprites.add(enemy_bullet_group.sprites())

            if score >= next_boss_score and not has_boss:
                boss = Boss(health=100 + level * 20)
                boss_group.add(boss)
                all_sprites.add(boss)
                has_boss = True

                warning_text = TextSprite("BOSS INCOMING!", 64, RED,
                                        (WIDTH // 2, HEIGHT // 2),
                                        duration=120, speed_y=0)
                text_group.add(warning_text)
                all_sprites.add(warning_text)

                next_boss_score += boss_level_interval + (level * 100)

            # Collision detection: Player bullets vs. enemies
            hits = pygame.sprite.groupcollide(player_bullet_group, enemy_group, True, False)
            if hits:
                current_time = pygame.time.get_ticks()
                play_sound = (current_time - last_enemy_die_time >= SOUND_COOLDOWN)
                for enemies in hits.values():
                    for enemy in enemies:
                        if enemy.take_damage():
                            enemy.kill()
                            if enemy_die_sound and play_sound:
                                if DEBUG:
                                    print("Playing enemy_die.wav for bullet-killed enemy")
                                enemy_die_sound.play()
                                last_enemy_die_time = current_time
                                play_sound = False
                            for _ in range(10):
                                particle = Particle(enemy.rect.center, PINK,
                                                  radius=random.randint(2, 5),
                                                  lifespan=random.randint(20, 40))
                                all_sprites.add(particle)

                            combo_count += 1
                            combo_timer = 0
                            score_add = 10 * (1 + min(combo_count // 5, 4))
                            score += score_add

                            score_text = TextSprite(f"+{score_add}", 24, WHITE,
                                                  enemy.rect.center,
                                                  duration=30, speed_y=-1)
                            text_group.add(score_text)
                            all_sprites.add(score_text)

                            if combo_count % 5 == 0 and combo_count > 0:
                                combo_text = TextSprite(f"{combo_count} COMBO!", 36, YELLOW,
                                                      (WIDTH // 2, HEIGHT // 3),
                                                      duration=60, speed_y=-1)
                                text_group.add(combo_text)
                                all_sprites.add(combo_text)

                            if random.random() < 0.1:
                                spawn_powerup(enemy.rect.center, powerup_group, all_sprites)

            # Player bullets vs. boss
            if boss_group:
                boss_hits = pygame.sprite.groupcollide(player_bullet_group, boss_group, True, False)
                if boss_hits:
                    current_time = pygame.time.get_ticks()
                    play_sound = (current_time - last_enemy_die_time >= SOUND_COOLDOWN)
                    for bullet, bosses in boss_hits.items():
                        for boss in bosses:
                            boss.health -= 1
                            hit_x = bullet.rect.centerx
                            hit_y = bullet.rect.centery
                            for _ in range(5):
                                particle = Particle((hit_x, hit_y),
                                                  color=(255, 255, 0),
                                                  radius=random.randint(2, 4),
                                                  lifespan=random.randint(10, 20))
                                all_sprites.add(particle)
                            if boss.health <= 0:
                                boss.kill()
                                if enemy_die_sound and play_sound:
                                    if DEBUG:
                                        print("Playing enemy_die.wav for bullet-killed boss")
                                    enemy_die_sound.play()
                                    last_enemy_die_time = current_time
                                has_boss = False
                                for _ in range(20):
                                    explosion_pos = (
                                        boss.rect.centerx + random.randint(-50, 50),
                                        boss.rect.centery + random.randint(-50, 50)
                                    )
                                    explosion = Explosion(explosion_pos)
                                    all_sprites.add(explosion)
                                boss_score = 200 + (level * 50)
                                score += boss_score
                                victory_text = TextSprite(f"BOSS DEFEATED! +{boss_score}", 48, YELLOW,
                                                        (WIDTH // 2, HEIGHT // 2),
                                                        duration=120, speed_y=-0.5)
                                text_group.add(victory_text)
                                all_sprites.add(victory_text)
                                level += 1
                                level_text = TextSprite(f"LEVEL {level}!", 48, YELLOW,
                                                      (WIDTH // 2, HEIGHT // 2 + 60),
                                                      duration=120, speed_y=-0.5)
                                text_group.add(level_text)
                                all_sprites.add(level_text)
                                for _ in range(3):
                                    spawn_pos = (
                                        random.randint(100, WIDTH - 100),
                                        random.randint(100, HEIGHT // 2)
                                    )
                                    spawn_powerup(spawn_pos, powerup_group, all_sprites)
                                if explosion_sound:
                                    explosion_sound.play()

            # Player vs. enemy collision
            player = player_group.sprite
            if player:
                collided_enemies = pygame.sprite.spritecollide(player, enemy_group, True)
                if collided_enemies:
                    for enemy in collided_enemies:
                        explosion = Explosion(enemy.rect.center)
                        all_sprites.add(explosion)
                    if player.take_damage():
                        for _ in range(15):
                            particle = Particle(player.rect.center,
                                              color=(255, 100, 100),
                                              radius=random.randint(3, 6),
                                              lifespan=random.randint(20, 40))
                            all_sprites.add(particle)
                        if explosion_sound:
                            explosion_sound.play()
                        if player.lives <= 0:
                            game_state, high_score = end_run(player, score, high_score)
                            continue

            # Player vs. enemy bullets
            if player:
                bullet_hits = pygame.sprite.spritecollide(player, enemy_bullet_group, True)
                if bullet_hits:
                    if player.take_damage():
                        for _ in range(8):
                            particle = Particle(player.rect.center,
                                              color=(255, 100, 100),
                                              radius=random.randint(2, 5),
                                              lifespan=random.randint(15, 30))
                            all_sprites.add(particle)
                        if hit_sound:
                            hit_sound.play()
                        if player.lives <= 0:
                            game_state, high_score = end_run(player, score, high_score)
                            continue

            # Player vs. powerups
            if player:
                powerup_hits = pygame.sprite.spritecollide(player, powerup_group, True)
                for powerup in powerup_hits:
                    if powerup.type == 'shield':
                        player.shield_active = True
                        player.shield_timer = 0
                        powerup_text = TextSprite("SHIELD ACTIVATED!", 36, YELLOW,
                                                (WIDTH // 2, HEIGHT // 3),
                                                duration=60, speed_y=-1)
                    elif powerup.type == 'triple':
                        player.triple_shot = True
                        player.triple_shot_timer = 0
                        powerup_text = TextSprite("TRIPLE SHOT ACTIVATED!", 36, PURPLE,
                                                (WIDTH // 2, HEIGHT // 3),
                                                duration=60, speed_y=-1)
                    elif powerup.type == 'bomb':
                        player.bombs += 1
                        powerup_text = TextSprite(f"BOMB ACQUIRED! ({player.bombs})", 36, RED,
                                                (WIDTH // 2, HEIGHT // 3),
                                                duration=60, speed_y=-1)
                    text_group.add(powerup_text)
                    all_sprites.add(powerup_text)
                    for _ in range(15):
                        particle = Particle(player.rect.center,
                                          color=(255, 255, 0),
                                          radius=random.randint(2, 5),
                                          lifespan=random.randint(20, 40))
                        all_sprites.add(particle)
                    if powerup_sound:
                        powerup_sound.play()

            if background_img:
                screen.blit(background_img, (0, 0))
            else:
                screen.fill((10, 10, 40))
                update_stars(stars)
                draw_stars(screen, stars)

            all_sprites.draw(screen)

            if player and player.shield_active:
                player.draw_shield(screen)

            boss = boss_group.sprite
            if boss:
                draw_bar(screen, WIDTH // 4, 10, WIDTH // 2, 20,
                        boss.health, boss.max_health, RED)
                boss_text = boss_font.render("BOSS", True, WHITE)
                screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 35))

            font = hud_font
            render_text_with_shadow(f"Score: {score}", font, WHITE, BLACK, (10, 10))
            render_text_with_shadow(f"Lives: {player.lives if player else 0}", font, WHITE, BLACK, (10, 50))
            render_text_with_shadow(f"Level: {level}", font, WHITE, BLACK, (10, 90))
            render_text_with_shadow(f"Bombs: {player.bombs if player else 0}", font, WHITE, BLACK, (10, 130))

            if combo_count > 0:
                combo_color = YELLOW if combo_count >= 10 else WHITE
                render_text_with_shadow(f"Combo: {combo_count}x", font, combo_color, BLACK,
                                      (WIDTH - 200, 10))

            if player:
                if player.shield_active:
                    shield_time = int((player.shield_duration - player.shield_timer) / 60)
                    render_text_with_shadow(f"Shield: {shield_time}s", font, YELLOW, BLACK,
                                          (WIDTH - 200, 50))
                if player.triple_shot:
                    triple_time = int((player.triple_shot_duration - player.triple_shot_timer) / 60)
                    render_text_with_shadow(f"Triple Shot: {triple_time}s", font, PURPLE, BLACK,
                                          (WIDTH - 200, 90))

        elif game_state == PAUSE:
            game_state = pause_game()

        elif game_state == MENU:
            return high_score

        pygame.display.flip()
        clock.tick(60)

def main():
    high_score = 0
    while True:
        high_score = main_game(high_score)


if __name__ == "__main__":
    main()
