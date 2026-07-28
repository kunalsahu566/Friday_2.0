import importlib.util
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"


def load_plugins(router_registry):
    """Register every plugin that exposes a `register(registry)` function."""
    for plugin_path in PLUGIN_DIR.glob("*.py"):
        if plugin_path.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(router_registry)
                print(f"[PluginLoader] Loaded plugin: {plugin_path.stem}")
        except Exception as error:
            print(f"[PluginLoader] Failed to load {plugin_path.stem}: {error}")
