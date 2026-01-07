import os
import json
import importlib
from typing import Any


SAVE_DIR_NAME = "save"
SAVE_FILE_NAME = "autosave.json"


def _project_root() -> str:
    # package is inside project root; go up one level from this file
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _save_path() -> str:
    root = _project_root()
    save_dir = os.path.join(root, SAVE_DIR_NAME)
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, SAVE_FILE_NAME)


def _is_primitive(v: Any) -> bool:
    return isinstance(v, (int, float, str, bool, type(None)))


def _serialize_obj(o: Any) -> Any:
    # modules, blueprints and other game objects -> dict with class + attrs
    try:
        cls = o.__class__
        data = {
            "__class__": cls.__name__,
            "__module__": cls.__module__,
            "attrs": {},
        }
        for k, v in vars(o).items():
            if _is_primitive(v):
                data["attrs"][k] = v
            elif isinstance(v, (list, tuple)):
                # try to shallow-serialize lists of primitives
                serial = []
                ok = True
                for item in v:
                    if _is_primitive(item):
                        serial.append(item)
                    else:
                        ok = False
                        break
                if ok:
                    data["attrs"][k] = serial
        return data
    except Exception:
        return None


def _deserialize_obj(d: dict) -> Any:
    try:
        mod_name = d.get("__module__")
        cls_name = d.get("__class__")
        attrs = d.get("attrs", {}) or {}
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
        # create instance with no args then set attributes
        inst = None
        try:
            inst = cls()
        except Exception:
            # Try constructing with tier/capacity if available
            try:
                init_kwargs = {}
                if "tier" in attrs:
                    init_kwargs["tier"] = attrs.get("tier")
                if "module_size" in attrs:
                    init_kwargs["module_size"] = attrs.get("module_size")
                if "capacity" in attrs:
                    init_kwargs["module_size"] = attrs.get("capacity")
                inst = cls(**init_kwargs)
            except Exception:
                # give up
                inst = None
        if inst is None:
            return None
        for k, v in attrs.items():
            try:
                setattr(inst, k, v)
            except Exception:
                pass
        return inst
    except Exception:
        return None


def save_game(owner) -> None:
    """Save the main pieces of player state to JSON file next to run.py."""
    try:
        data = {}
        inv = getattr(owner, "inventory_manager", None)
        if inv is not None:
            data["inventory"] = dict(getattr(inv, "inventory", {}))
            # serialize unequipped modules
            mods = []
            for m in getattr(inv, "modules", []) or []:
                ser = _serialize_obj(m)
                mods.append(ser)
            data["unequipped_modules"] = mods
        # installed internal modules: prefer central manager state if available
        try:
            from spacegame.core.modules_manager import manager as modules_manager

            installed = modules_manager.get_internal_sections()
        except Exception:
            installed = getattr(owner, "installed_internal_modules", None)
        if installed is None:
            # Initialize to 3 empty sections if not set yet
            installed = [[], [], []]
        ser_installed = []
        for section in installed:
            sec = []
            for m in section:
                sec.append(_serialize_obj(m))
            ser_installed.append(sec)
        data["installed_internal_modules"] = ser_installed

        # hangar info (if present)
        hangar = getattr(owner, "hangar_system", None) or (getattr(inv, "hangar", None) if inv is not None else None)
        if hangar is not None:
            pool = []
            for e in getattr(hangar, "pool", []) or []:
                try:
                    pool.append({
                        "id": int(getattr(e, "id", -1)),
                        "name": getattr(e, "name", ""),
                        "unit_type": getattr(e, "unit_type", ""),
                        "alive": bool(getattr(e, "alive", True)),
                        "tier": int(getattr(e, "tier", 0)),
                        "rarity": getattr(e, "rarity", ""),
                    })
                except Exception:
                    continue
            data["hangar"] = {
                "assignments": list(getattr(hangar, "assignments", [])),
                "slots": list(getattr(hangar, "slots", [])),
                "pool": pool,
            }

        path = _save_path()
        # Write atomically: write to a temp file then replace
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
                try:
                    fh.flush()
                    os.fsync(fh.fileno())
                except Exception:
                    pass
            # Replace the target file atomically
            try:
                os.replace(tmp_path, path)
            except Exception:
                # fallback to rename on older systems
                try:
                    os.remove(path)
                except Exception:
                    pass
                try:
                    os.rename(tmp_path, path)
                except Exception:
                    # last resort: write directly
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(data, fh, indent=2)
        except Exception:
            # If atomic write failed, try a direct write as fallback
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2)
            except Exception:
                pass
    except Exception:
        # never crash game due to save errors
        return


def load_game(owner) -> bool:
    """Load saved state into `owner`. Returns True if a save was loaded."""
    try:
        path = _save_path()
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        inv = getattr(owner, "inventory_manager", None)
        if inv is not None and "inventory" in data:
            try:
                inv.inventory = dict(data.get("inventory", {}))
            except Exception:
                pass

        if inv is not None and "unequipped_modules" in data:
            inv.modules = []
            for ser in data.get("unequipped_modules", []) or []:
                if ser is None:
                    continue
                obj = _deserialize_obj(ser)
                if obj is not None:
                    inv.modules.append(obj)

        if "installed_internal_modules" in data:
            try:
                inst = []
                for section in data.get("installed_internal_modules", []) or []:
                    sec = []
                    for ser in section:
                        if ser is None:
                            continue
                        obj = _deserialize_obj(ser)
                        if obj is not None:
                            sec.append(obj)
                    inst.append(sec)
                try:
                    setattr(owner, "installed_internal_modules", inst)
                except Exception:
                    pass
                # Also restore central ModulesManager state for runtime use
                try:
                    from spacegame.core.modules_manager import manager as modules_manager

                    modules_manager.set_internal_sections(inst)
                except Exception:
                    pass
            except Exception:
                pass

        if "hangar" in data:
            try:
                hang = getattr(owner, "hangar_system", None) or (inv.hangar if inv is not None else None)
                if hang is not None:
                    pool = []
                    try:
                        from spacegame.core.hangar import HangarEntry
                        for e in data.get("hangar", {}).get("pool", []) or []:
                            try:
                                entry = HangarEntry(
                                    id=int(e.get("id", -1)),
                                    name=e.get("name", ""),
                                    unit_type=e.get("unit_type", ""),
                                    alive=bool(e.get("alive", True)),
                                    tier=int(e.get("tier", 0)),
                                    rarity=e.get("rarity", ""),
                                )
                                pool.append(entry)
                            except Exception:
                                continue
                    except Exception:
                        # fallback: keep dicts
                        for e in data.get("hangar", {}).get("pool", []) or []:
                            pool.append(e)

                    hang.pool = pool
                    # Restore assignments and slots, ensuring they match num_slots
                    saved_assignments = list(data.get("hangar", {}).get("assignments", []))
                    saved_slots = list(data.get("hangar", {}).get("slots", []))
                    
                    # Pad or truncate to match num_slots
                    hang.assignments = (saved_assignments + [None] * hang.num_slots)[:hang.num_slots]
                    hang.slots = (saved_slots + [False] * hang.num_slots)[:hang.num_slots]
                    
                    # Ensure any slot with an assignment is marked as ready in hangar
                    # (ship hasn't been deployed yet after load, so it's in hangar)
                    for i, assignment_id in enumerate(hang.assignments):
                        if i < len(hang.slots) and assignment_id is not None:
                            hang.slots[i] = True
            except Exception:
                pass

        return True
    except Exception:
        return False
