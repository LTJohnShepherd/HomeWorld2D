"""Global configuration and core gameplay constants for SpaceGame.

Only important gameplay / tuning values are centralized here.
Visual layout numbers and UI offsets stay close to their code.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
PREVIEWS_DIR = ASSETS_DIR / "previews"

# ---- Window / timing ----
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

# Target frames per second for the main game loop and menus.
FPS = 60

# ---- Player ship (SpaceUnit defaults) ----
PLAYER_DEFAULT_SPEED         = 300.0
PLAYER_DEFAULT_ROT_SPEED     = 360.0
PLAYER_DEFAULT_FIRE_RANGE    = 230.0
PLAYER_DEFAULT_FIRE_COOLDOWN = 0.55
PLAYER_DEFAULT_BULLET_DAMAGE = 12.0

# ---- Enemy Pirate Frigate defaults ----
PIRATE_DEFAULT_SPEED         = 140.0
PIRATE_DEFAULT_ROT_SPEED     = 240.0
PIRATE_DEFAULT_FIRE_RANGE    = 260.0
PIRATE_DEFAULT_FIRE_COOLDOWN = 0.8
PIRATE_DEFAULT_BULLET_DAMAGE = 10.0

# ---- Expedition ship / hangar ----
EXPEDITION_MAX_HEALTH  = 500.0
HANGAR_SLOT_COUNT      = 3
INTERCEPTOR_POOL_SIZE  = 5

# ---- Projectile defaults ----
PROJECTILE_SPEED    = 600.0
PROJECTILE_RADIUS   = 4
PROJECTILE_LIFETIME = 2.0

# ---- Gameplay behaviour tuning ----
SEPARATION_ITER = 2  # How many times to push shapes apart when they overlap
