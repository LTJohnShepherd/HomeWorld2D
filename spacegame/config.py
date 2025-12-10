"""Global configuration and core gameplay constants for SpaceGame.

Only important gameplay / tuning values are centralized here.
Visual layout numbers and UI offsets stay close to their code.
"""

IMAGES_DIR = "spacegame/assets/images"
PREVIEWS_DIR = "spacegame/assets/previews"

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
PLAYER_DEFAULT_ARMOR_DAMAGE  = 10.0

# ---- Enemy Pirate Frigate defaults ----
PIRATE_DEFAULT_SPEED         = 140.0
PIRATE_DEFAULT_ROT_SPEED     = 240.0
PIRATE_DEFAULT_FIRE_RANGE    = 260.0
PIRATE_DEFAULT_FIRE_COOLDOWN = 0.8
PIRATE_DEFAULT_BULLET_DAMAGE = 10.0
PIRATE_DEFAULT_ARMOR_DAMAGE  = 9.0

# ---- Expedition ship / hangar ----
HANGAR_SLOT_COUNT      = 3
INTERCEPTOR_POOL_SIZE  = 5
RESOURCE_COLLECTOR_POOL_SIZE = 5  # Number of resource collectors to create at game start
PLASMA_BOMBER_POOL_SIZE = 1  # Number of plasma bombers to create at game start

# ---- Projectile defaults ----
PROJECTILE_SPEED    = 600.0
PROJECTILE_RADIUS   = 4
PROJECTILE_LIFETIME = 2.0

# ---- Gameplay behaviour tuning ----
SEPARATION_ITER = 2  # How many times to push shapes apart when they overlap

# ---- UI Colors ----
UI_BG_COLOR           = (4, 18, 35)
UI_TITLE_COLOR        = (185, 210, 235)
UI_NAV_LINE_COLOR     = (35, 80, 120)
UI_NAV_BG_COLOR       = (10, 40, 70)
UI_TAB_TEXT_COLOR     = (185, 210, 235)
UI_TAB_TEXT_SELECTED  = (255, 255, 255)
UI_TAB_UNDERLINE_COLOR= (255, 170, 60)
UI_SECTION_BASE_COLOR = (15, 45, 85)
UI_SECTION_HOVER_COLOR= (30, 80, 135)
UI_SECTION_TEXT_COLOR = (230, 240, 255)

# ---- UI Layout ----
UI_TOP_BAR_HEIGHT = 96
UI_TAB_HEIGHT     = 38

# ---- Tier flag colors ----
UI_ICON_BLUE  = (70, 130, 220)
UI_ICON_WHITE = (240, 240, 255)