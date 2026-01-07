"""Sound Manager for Space Game.

Manages all game audio using pygame mixer functions.
Ensures only one sound plays at a time (mutual exclusivity).
Maps game events to appropriate sound effects.
"""

import pygame
import random
import os
from pathlib import Path
from typing import Optional, Dict, List


class SoundManager:
    """Centralized sound management system."""

    def __init__(self, sounds_dir: str = None):
        """Initialize the sound manager.

        Args:
            sounds_dir: Path to the sounds directory. If None, uses default asset path.
        """
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Set up sounds directory
        if sounds_dir is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent.parent
            sounds_dir = str(base_dir / "assets" / "sounds")

        self.sounds_dir = sounds_dir
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self.current_sound_channel = pygame.mixer.Channel(0)
        self.is_playing = False

        # Load all sounds on initialization
        self._load_all_sounds()

        # Sound event groups for logical mapping
        self.sound_groups = {
            # Command sounds - unit movement orders
            "MOVE_COMMAND": [
                "COMMAND_MOVE_1", "COMMAND_MOVE_2", "COMMAND_MOVE_3",
                "COMMAND_MOVE_4", "COMMAND_MOVE_5", "COMMAND_MOVE_6",
                "COMMAND_MOVE_7", "COMMAND_MOVE_9", "COMMAND_MOVE_10",
                "COMMAND_MOVE_11", "COMMAND_MOVE_12", "COMMAND_MOVE_13",
                "COMMAND_MOVE_14", "COMMAND_MOVE_15"
            ],
            # Dock commands
            "DOCK_COMMAND": [
                "COMMAND_ANYSHIPGENERICDOCKCARRIER_1",
                "COMMAND_ANYSHIPGENERICDOCKCARRIER_2",
                "COMMAND_ANYSHIPGENERICDOCKCARRIER_3",
                "COMMAND_ANYSHIPGENERICDOCKCARRIER_4"
            ],
            # Harvest/collect resources
            "HARVEST_COMMAND": [
                "COMMAND_RESOURCECOLLECTORHARVEST_1",
                "COMMAND_RESOURCECOLLECTORHARVEST_2",
                "COMMAND_RESOURCECOLLECTORHARVEST_3",
                "COMMAND_RESOURCECOLLECTORHARVEST_4",
                "COMMAND_RESOURCECOLLECTORHARVEST_5"
            ],
            # Repair commands
            "REPAIR_COMMAND": [
                "COMMAND_STARTEDREPAIRS_1",
                "COMMAND_STARTEDREPAIRS_2",
                "COMMAND_STARTEDREPAIRS_3",
                "COMMAND_STARTEDREPAIRS_4"
            ],
            # Hyperspace jump start
            "HYPERSPACE_LAUNCH": ["STATUS_LAUNCH_HYPERSPACE_1"],
            # Hyperspace jump complete
            "HYPERSPACE_COMPLETE": ["STATUS_COMPLETE_HYPERSPACE_1"],
            # Refining/processing complete
            "REFINING_COMPLETE": ["STATUS_COMPLETE_REFINING_1"],
            # Fabrication/construction complete
            "FABRICATION_COMPLETE": ["STATUS_COMPLETE_CONSTRUCTION_1"],
            # Docking/arrival chatter
            "SHIP_DOCKING": [
                "CHATTER_ANYSHIPDOCKING_1", "CHATTER_ANYSHIPDOCKING_2",
                "CHATTER_ANYSHIPDOCKING_3", "CHATTER_ANYSHIPDOCKING_4",
                "CHATTER_ANYSHIPDOCKING_5", "CHATTER_ANYSHIPDOCKING_6",
                "CHATTER_ANYSHIPDOCKING_7"
            ],
            # Resource collector full notifications
            "RESOURCE_COLLECTOR_FULL": [
                "CHATTER_RESOURCECOLLECTOR_FULL_1",
                "CHATTER_RESOURCECOLLECTOR_FULL_2",
                "CHATTER_RESOURCECOLLECTOR_FULL_3",
                "CHATTER_RESOURCECOLLECTOR_FULL_4",
                "CHATTER_RESOURCECOLLECTOR_FULL_5",
                "CHATTER_RESOURCECOLLECTOR_FULL_6",
                "CHATTER_RESOURCECOLLECTOR_FULL_7"
            ],
            # Resource transfer chatter
            "RESOURCE_TRANSFER": [
                "CHATTER_RESOURCECOLLECTOR_RESOURCESTRANSFERRED_1",
                "CHATTER_RESOURCECOLLECTOR_RESOURCESTRANSFERRED_2",
                "CHATTER_RESOURCECOLLECTOR_RESOURCESTRANSFERRED_3",
                "CHATTER_RESOURCECOLLECTOR_RESOURCESTRANSFERRED_4",
                "CHATTER_RESOURCECOLLECTOR_RESOURCESTRANSFERRED_5"
            ],
            # Unit destroyed alerts
            "UNIT_DESTROYED_FRIGATE": ["STATUS_REPORT_DESTROYED_FRIGATE_1"],
            "UNIT_DESTROYED_COLLECTOR": ["STATUS_REPORT_DESTROYED_RESOURCECOLLECTOR_1"],
            "UNIT_DESTROYED_STRIKEGROUP": ["STATUS_REPORT_DESTROYED_STRIKEGROUP_1"]
        }

    def _load_all_sounds(self) -> None:
        """Load all sound files from the sounds directory."""
        if not os.path.isdir(self.sounds_dir):
            print(f"Warning: Sounds directory not found at {self.sounds_dir}")
            return

        for filename in os.listdir(self.sounds_dir):
            if filename.endswith(('.ogg', '.wav', '.mp3')):
                sound_name = filename.rsplit('.', 1)[0]
                sound_path = os.path.join(self.sounds_dir, filename)
                try:
                    sound = pygame.mixer.Sound(sound_path)
                    self.sound_cache[sound_name] = sound
                except pygame.error as e:
                    print(f"Error loading sound {sound_name}: {e}")

    def _is_sound_playing(self) -> bool:
        """Check if any sound is currently playing."""
        return pygame.mixer.get_busy()

    def _play_sound(self, sound: pygame.mixer.Sound) -> bool:
        """Play a sound using the current channel.

        Args:
            sound: The pygame Sound object to play.

        Returns:
            True if sound was played, False if a sound was already playing.
        """
        if self._is_sound_playing():
            return False

        try:
            self.current_sound_channel.play(sound)
            return True
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False

    def play_sound_by_name(self, sound_name: str) -> bool:
        """Play a specific sound by its name.

        Args:
            sound_name: The name of the sound file (without extension).

        Returns:
            True if sound was played, False otherwise.
        """
        if sound_name not in self.sound_cache:
            print(f"Sound '{sound_name}' not found in cache.")
            return False

        return self._play_sound(self.sound_cache[sound_name])

    def play_random_from_group(self, group_name: str) -> bool:
        """Play a random sound from a named sound group.

        Args:
            group_name: The name of the sound group (e.g., "MOVE_COMMAND").

        Returns:
            True if sound was played, False otherwise.
        """
        if group_name not in self.sound_groups:
            print(f"Sound group '{group_name}' not found.")
            return False

        sound_names = self.sound_groups[group_name]
        if not sound_names:
            print(f"Sound group '{group_name}' is empty.")
            return False

        # Filter to only available sounds
        available_sounds = [name for name in sound_names if name in self.sound_cache]
        if not available_sounds:
            print(f"No available sounds in group '{group_name}'.")
            return False

        sound_name = random.choice(available_sounds)
        return self._play_sound(self.sound_cache[sound_name])

    def stop_current_sound(self) -> None:
        """Stop the currently playing sound."""
        self.current_sound_channel.stop()

    # ==================== Event-based sound triggers ====================

    def on_move_command(self) -> bool:
        """Play sound when a unit receives a move command."""
        return self.play_random_from_group("MOVE_COMMAND")

    def on_dock_command(self) -> bool:
        """Play sound when a unit receives a dock command."""
        return self.play_random_from_group("DOCK_COMMAND")

    def on_harvest_command(self) -> bool:
        """Play sound when a unit receives a harvest/collect command."""
        return self.play_random_from_group("HARVEST_COMMAND")

    def on_repair_command(self) -> bool:
        """Play sound when repairs are started."""
        return self.play_random_from_group("REPAIR_COMMAND")

    def on_hyperspace_launch(self) -> bool:
        """Play sound when hyperspace jump begins."""
        return self.play_random_from_group("HYPERSPACE_LAUNCH")

    def on_hyperspace_complete(self) -> bool:
        """Play sound when hyperspace jump completes and asteroids/station are drawn."""
        return self.play_random_from_group("HYPERSPACE_COMPLETE")

    def on_refining_complete(self) -> bool:
        """Play sound when a refinement process completes."""
        return self.play_random_from_group("REFINING_COMPLETE")

    def on_fabrication_complete(self) -> bool:
        """Play sound when a construction/fabrication process completes."""
        return self.play_random_from_group("FABRICATION_COMPLETE")

    def on_ship_docking(self) -> bool:
        """Play sound when a ship docks or arrives at station."""
        return self.play_random_from_group("SHIP_DOCKING")

    def on_resource_collector_full(self) -> bool:
        """Play sound when a resource collector's inventory is full."""
        return self.play_random_from_group("RESOURCE_COLLECTOR_FULL")

    def on_resource_transfer(self) -> bool:
        """Play sound when resources are transferred between units."""
        return self.play_random_from_group("RESOURCE_TRANSFER")

    def on_unit_destroyed_frigate(self) -> bool:
        """Play sound when a frigate is destroyed."""
        return self.play_random_from_group("UNIT_DESTROYED_FRIGATE")

    def on_unit_destroyed_collector(self) -> bool:
        """Play sound when a resource collector is destroyed."""
        return self.play_random_from_group("UNIT_DESTROYED_COLLECTOR")

    def on_unit_destroyed_strikegroup(self) -> bool:
        """Play sound when a strike group is destroyed."""
        return self.play_random_from_group("UNIT_DESTROYED_STRIKEGROUP")

    # ==================== Utility methods ====================

    def get_sound_groups(self) -> List[str]:
        """Get a list of all available sound group names."""
        return list(self.sound_groups.keys())

    def get_cached_sounds(self) -> List[str]:
        """Get a list of all currently cached sound names."""
        return list(self.sound_cache.keys())

    def set_volume(self, volume: float) -> None:
        """Set the volume for the current channel.

        Args:
            volume: Volume level from 0.0 (silent) to 1.0 (full).
        """
        volume = max(0.0, min(1.0, volume))
        self.current_sound_channel.set_volume(volume)

    def get_volume(self) -> float:
        """Get the current channel volume."""
        return self.current_sound_channel.get_volume()


# Global singleton instance
_instance: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    """Get or create the global sound manager instance."""
    global _instance
    if _instance is None:
        _instance = SoundManager()
    return _instance


def init_sound_manager(sounds_dir: str = None) -> SoundManager:
    """Initialize the global sound manager with optional custom sounds directory.

    Args:
        sounds_dir: Optional path to sounds directory.

    Returns:
        The initialized SoundManager instance.
    """
    global _instance
    _instance = SoundManager(sounds_dir)
    return _instance
