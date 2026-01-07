import pygame
from typing import List
from spacegame.models.modules.refinerymodule import RefineryModule
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.core.sound_manager import get_sound_manager


class RefiningManager:
    """Manage refinery modules and refinement timers for a player/ship.

    Mirrors FabricationManager but performs resource transformations
    (input -> output) and exposes the same minimal management API used
    by the UI (get_modules, get_selected_index, set_selected_index, get_status).
    """

    def __init__(self):
        # RefiningManager no longer owns module persistence; modules are provided
        # by the central ModulesManager.
        self.selected_index: int = 0
        self.player = None

    def get_modules(self) -> List[RefineryModule]:
        return modules_manager.get_refineries()

    def get_module(self, index: int) -> RefineryModule:
        mods = self.get_modules() or []
        if 0 <= index < len(mods):
            return mods[index]
        return None

    def start_refinement(self, index: int, ore_letter_or_recipe, output_amount: int = None, player=None) -> bool:
        """Start refining using either a recipe object or an ore letter.

        Call patterns supported:
        - start_refinement(index, recipe_obj, player)
        - start_refinement(index, ore_letter, output_amount, player)

        If an ore letter is provided we synthesize a simple recipe using a
        standard conversion (default 2:1 input->output, e.g. 200 -> 100) and
        a default base_refinement_time.
        """
        module = self.get_module(index)
        if ore_letter_or_recipe is None:
            return False

        # If caller passed a recipe-like object, use it directly. Otherwise build one.
        recipe = None
        if isinstance(ore_letter_or_recipe, str):
            ore_letter = ore_letter_or_recipe
            out_amt = int(output_amount) if output_amount is not None else 100
            # default conversion: 2 ore -> 1 refined (so input = out_amt * 2)
            in_amt = out_amt * 2

            out_letter_map = {'A': 'RA', 'B': 'RB', 'C': 'RC', 'M': 'RA'}
            out_letter = out_letter_map.get(ore_letter, None)

            preview_map = {'A': 'RUIngotAT1.png', 'B': 'RUIngotBT1.png', 'C': 'RUIngotCT1.png', 'M': 'RUIngotAT1.png'}

            # synthesize lightweight recipe object
            class _R:
                pass

            recipe = _R()
            recipe.required_ore_letter = ore_letter
            recipe.required_ore_amount = in_amt
            recipe.output_ore_letter = out_letter
            recipe.output_ore_amount = out_amt
            recipe.base_refinement_time = getattr(module, 'base_refinement_time', 10)
            recipe.preview_filename = preview_map.get(ore_letter, None)
        else:
            # assume recipe-like object
            recipe = ore_letter_or_recipe

        ore_letter = getattr(recipe, "required_ore_letter", None)
        ore_amount = int(getattr(recipe, "required_ore_amount", 0))

        inv_mgr = getattr(player, 'inventory_manager', None)
        if inv_mgr is None and ore_letter is not None:
            return False
        available = inv_mgr.get_amount(ore_letter) if ore_letter is not None else 0

        if available < ore_amount:
            return False

        # Get ore tier from ore class to factor into refinement time
        ore_tier = 1
        try:
            ore_classes = {
                'M': None, 'A': None, 'B': None, 'C': None,
            }
            if ore_letter in ore_classes:
                from spacegame.models.ores.orem import RUOreM
                from spacegame.models.ores.orea import RUOreA
                from spacegame.models.ores.oreb import RUOreB
                from spacegame.models.ores.orec import RUOreC
                ore_classes = {'M': RUOreM, 'A': RUOreA, 'B': RUOreB, 'C': RUOreC}
                ore_class = ore_classes.get(ore_letter, RUOreM)
                ore_obj = ore_class(quantity=1)
                ore_tier = int(getattr(ore_obj, 'tier', 1) or 1)
        except Exception:
            ore_tier = 1

        # Use standard_refinement_time_s (in seconds) and apply module factor and ore tier
        if module is None:
            return False

        module_standard_s = float(getattr(module, 'standard_refinement_time_s', 75.0))
        module_factor = float(getattr(module, "base_refinement_time", 1.0))
        total_seconds = int(module_standard_s * module_factor * ore_tier)
        total_ms = max(1, int(total_seconds * 1000))
        module.refinement_total_ms = int(total_ms)
        module.refinement_start_ticks = int(pygame.time.get_ticks())
        module.refinement_recipe = recipe
        module.refinement_progress = 0.0

        if ore_letter is not None:
            if inv_mgr is None:
                raise RuntimeError("InventoryManager required to consume refinement resources")
            # consume the input ore amount
            inv_mgr.consume_resource(ore_letter, ore_amount)

        try:
            self.player = player
        except Exception:
            pass

        return True

    def cancel_refinement(self, index: int) -> None:
        module = self.get_module(index)
        if module is None:
            return
        module.refinement_total_ms = 0
        module.refinement_start_ticks = 0
        module.refinement_progress = 0.0
        module.refinement_recipe = None

    def speed_up(self, index: int) -> None:
        module = self.get_module(index)
        if module is None:
            return
        total_ms = int(getattr(module, "refinement_total_ms", 0))
        if total_ms > 0:
            module.refinement_start_ticks = int(pygame.time.get_ticks()) - int(total_ms)

    def get_status(self, index: int):
        """Return status dict for refinement slot `index`.

        Keys: total_ms, start_ticks, progress (0..1), remaining_s, is_refining, recipe
        """
        module = self.get_module(index)
        recipe = getattr(module, "refinement_recipe", None) if module is not None else None
        if recipe is None:
            progress = 0.0
            remaining_s = 0
            if module is not None:
                module.refinement_progress = progress
                module.refinement_remaining_s = remaining_s
            return {
                "total_ms": 0,
                "start_ticks": 0,
                "progress": progress,
                "remaining_s": remaining_s,
                "is_refining": False,
                "recipe": None,
            }

        total_ms = int(getattr(module, "refinement_total_ms", 0)) if module is not None else 0
        start_ticks = int(getattr(module, "refinement_start_ticks", 0)) if module is not None else 0
        now_ticks = int(pygame.time.get_ticks())

        if total_ms > 0 and start_ticks > 0:
            elapsed = max(0, now_ticks - start_ticks)
            progress = min(1.0, elapsed / float(total_ms))
            remaining_ms = max(0, total_ms - elapsed)
            remaining_s = remaining_ms // 1000
            is_refining = progress < 1.0
            if progress >= 1.0:
                try:
                    self._finalize_refinement(index)
                except Exception:
                    pass
        else:
            progress = 0.0
            remaining_s = int(getattr(module, "base_refinement_time", 0)) if module is not None else 0
            is_refining = False

        if module is not None:
            module.refinement_progress = progress
            module.refinement_remaining_s = remaining_s

        return {
            "total_ms": total_ms,
            "start_ticks": start_ticks,
            "progress": progress,
            "remaining_s": remaining_s,
            "is_refining": is_refining,
            "recipe": getattr(module, "refinement_recipe", None),
        }

    def _finalize_refinement(self, index: int) -> None:
        """Finalize a completed refinement.

        Produces output resources defined by the recipe and adds them to the
        player's InventoryManager using `add_resource`.
        """
        module = self.get_module(index)
        recipe = getattr(module, "refinement_recipe", None)
        if recipe is None:
            return

        player = getattr(self, "player", None)
        if player is None:
            # nothing to do without an owner
            return

        inv_mgr = getattr(player, 'inventory_manager', None)
        if inv_mgr is None:
            # can't add resources without inventory manager
            return

        out_letter = getattr(recipe, "output_ore_letter", None)
        out_amount = int(getattr(recipe, "output_ore_amount", 0))
        preview = getattr(recipe, 'preview_filename', None)

        if out_letter is not None and out_amount > 0:
            try:
                inv_mgr.add_resource(out_letter, out_amount, preview=preview)
            except Exception:
                pass

        # Play refinement complete sound
        try:
            sound_manager = get_sound_manager()
            sound_manager.on_refining_complete()
        except Exception:
            pass

        # Clear module refinement state
        module.refinement_total_ms = 0
        module.refinement_start_ticks = 0
        module.refinement_progress = 0.0
        module.refinement_recipe = None
        module.refinement_remaining_s = 0

    def get_selected_index(self) -> int:
        mods = self.get_modules() or []
        if not mods:
            return 0
        return max(0, min(self.selected_index, len(mods) - 1))

    def set_selected_index(self, index: int) -> None:
        mods = self.get_modules() or []
        if not mods:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(int(index), len(mods) - 1))

    def update(self) -> None:
        try:
            mods = self.get_modules() or []
            for i in range(len(mods)):
                self.get_status(i)
        except Exception:
            pass


def get_refinery_manager(player) -> RefiningManager:
    if player is None:
        if not hasattr(get_refinery_manager, "_global"):
            get_refinery_manager._global = RefiningManager()
        return get_refinery_manager._global

    if not hasattr(player, "_refinery_manager"):
        player._refinery_manager = RefiningManager()
    return player._refinery_manager
