import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR


class SpaceStation(SpaceUnit):
    """A stationary space station that serves as a friendly, non-combatant structure.
    
    Properties:
    - Always spawned at a fixed position in a station area
    - Friendly to the player (is_enemy=False)
    - Cannot move or take damage
    - Cannot deal damage
    - Not controllable by the player
    - Serves as a healing/resupply point for player fleet
    """

    def shape_id(self):
        return "space_station"
    
    def get_tier(self) -> int:
        return 0

    def __init__(self, start_pos, **kwargs):
        # Load station sprite
        sprite = pygame.image.load(IMAGES_DIR + "/Higarran_Station.png").convert_alpha()

        # Scale the sprite to an appropriate size (stations should be large and visible)
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 3, sprite.get_height() // 3)
        )

        # Initialize as a non-enemy unit with speed and rotation speed of 0
        super().__init__(
            start_pos,
            ship_size=scaled_sprite.get_size(),
            is_enemy=False,
            speed=0.0,
            rotation_speed=0.0,
            rarity="common",
            **kwargs
        )
        self.base_surf = scaled_sprite
        # Update the image to use the sprite instead of the default yellow rect
        self.image = self.base_surf.copy()
        self.rect = self.image.get_rect(center=(int(self.mover.world_pos.x), int(self.mover.world_pos.y)))

        # Station stats: unkillable, deals no damage
        self.bullet_damage = 0.0
        self.armor_damage = 0.0

        # Station has very high health (effectively unkillable)
        self.max_health = 999999.0
        self.health = self.max_health
        self.max_armor = 999999.0
        self.armor = self.max_armor

    def take_damage(self, amount):
        """Stations cannot take damage."""
        pass

    def take_armor_damage(self, amount):
        """Stations cannot take armor damage."""
        pass

    def heal(self, amount):
        """Stations do not heal (they are not damaged)."""
        pass

    def fire(self, projectiles_group, target_pos=None):
        """Stations cannot fire weapons."""
        pass

    def update(self, dt, **kwargs):
        """Update the station (limited functionality since it's stationary).
        
        The station:
        - Does not move
        - Does not rotate
        - Only updates sprite visuals if needed
        """
        # Update rect position in case it was set at init
        self.rect.center = (int(self.mover.world_pos.x), int(self.mover.world_pos.y))
