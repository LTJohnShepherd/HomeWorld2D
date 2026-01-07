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
# Maximum push distance applied per separation call (to avoid large jumps)
SEPARATION_MAX_PUSH = 2.0

# Maximum allowed frame delta (seconds) before treating as a paused frame
MAX_DT = 0.3

# Projectile default damages (fallbacks)
PROJECTILE_DEFAULT_HULL = 10.0
PROJECTILE_DEFAULT_ARMOR = 10.0

# Cinematic / UI tuning
JUMP_CINEMATIC_BAR_FACTOR = 0.12  # fraction of screen height for cinematic bars
JUMP_CINEMATIC_CLOSE_SPEED = 160.0  # pixels per second used to close cinematic bars

# Station healing rate (HP/sec) applied while at a station
STATION_HEALING_RATE = 15.0

# Minimum selection drag size (in pixels) to count as a selection rectangle
SELECTION_MIN_PIXELS = 5

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

# ---- Enemy spawning ----
# Seconds between spawn waves (float). Set to 0 to disable automatic spawns.
ENEMY_SPAWN_INTERVAL = 8.0
# How many enemies to spawn each interval
ENEMY_SPAWN_COUNT = 2