"""Centralised Modules manager.

This module exposes a single `manager` instance that holds the currently
installed internal modules (three sections) and provides helpers to query
fabricator/refinery modules. It is intended to be the single source of
truth for equipped modules across the codebase.
"""
from typing import List
from spacegame.models.modules.module import ShipModule


class ModulesManager:
    def __init__(self):
        # internal sections: 0 = left, 1 = middle, 2 = right
        self.installed_internal_modules: List[List[ShipModule]] = [[], [], []]

        # Ensure a reasonable default when the game starts with no save:
        # install one Fabricator and one Refinery in the middle section so
        # the FABRICATION and REFINING tabs are available by default.
        try:
            if sum(len(s) for s in self.installed_internal_modules) == 0:
                from spacegame.models.modules.fabricatormodule import FabricatorModule
                from spacegame.models.modules.refinerymodule import RefineryModule

                # Create default instances (tier defaults apply)
                self.installed_internal_modules[1] = [FabricatorModule(), RefineryModule()]
        except Exception:
            # Do not raise if imports or instantiation fails
            pass

    # --- Internal sections ---
    def get_internal_sections(self) -> List[List[ShipModule]]:
        return self.installed_internal_modules

    def set_internal_sections(self, sections: List[List[ShipModule]]) -> None:
        # Expect a list of lists; do a shallow copy to keep ownership clear
        self.installed_internal_modules = [list(s or []) for s in sections][:3]
        # ensure exactly three sections
        while len(self.installed_internal_modules) < 3:
            self.installed_internal_modules.append([])

    def install_module(self, section_index: int, module: ShipModule) -> None:
        if 0 <= section_index < 3 and module is not None:
            sec = self.installed_internal_modules[section_index]
            sec.append(module)

    def remove_module(self, section_index: int, module: ShipModule) -> None:
        try:
            if 0 <= section_index < 3:
                sec = self.installed_internal_modules[section_index]
                if module in sec:
                    sec.remove(module)
        except Exception:
            pass

    # --- Helpers for specific module types ---
    def get_fabricators(self) -> List[ShipModule]:
        out: List[ShipModule] = []
        try:
            for sec in self.installed_internal_modules:
                for m in sec:
                    # avoid importing module types here; callers can isinstance
                    # against concrete classes if needed
                    try:
                        if getattr(m, "allowed_sections", None) is not None and getattr(m, "base_fabrication_time", None) is not None:
                            out.append(m)
                    except Exception:
                        continue
        except Exception:
            pass
        return out

    def get_refineries(self) -> List[ShipModule]:
        out: List[ShipModule] = []
        try:
            for sec in self.installed_internal_modules:
                for m in sec:
                    try:
                        if getattr(m, "standard_refinement_time_s", None) is not None or getattr(m, "base_refinement_time", None) is not None:
                            out.append(m)
                    except Exception:
                        continue
        except Exception:
            pass
        return out


# single global manager instance used across the package
manager = ModulesManager()
