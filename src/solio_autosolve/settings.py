"""Settings management for Solio solver configuration."""

from pathlib import Path
from typing import Any

import yaml

from .config import PROJECT_ROOT


def load_solver_settings() -> dict[str, Any]:
    """
    Load solver settings from solver_settings.yaml.
    
    Returns:
        Dictionary containing solver configuration.
        Returns default settings if file doesn't exist.
    """
    settings_file = PROJECT_ROOT / "solver_settings.yaml"
    
    if not settings_file.exists():
        print(f"Settings file not found: {settings_file}")
        print("Using default settings")
        return get_default_settings()
    
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f)
        
        print(f"Loaded settings from: {settings_file}")
        return settings or get_default_settings()
    
    except Exception as e:
        print(f"Error loading settings: {e}")
        print("Using default settings")
        return get_default_settings()


def get_default_settings() -> dict[str, Any]:
    """Return default solver settings."""
    return {
        "timeout": 300,
        "horizon_weeks": 10,
    }


def save_default_settings() -> None:
    """Save default settings to solver_settings.yaml if it doesn't exist."""
    settings_file = PROJECT_ROOT / "solver_settings.yaml"
    
    if settings_file.exists():
        print(f"Settings file already exists: {settings_file}")
        return
    
    default_settings = get_default_settings()
    
    # Add comments manually since PyYAML doesn't preserve comments well
    content = """# Solio Solver Settings Configuration
# 
# This file defines solver parameters that will be applied before running optimization.
# Only includes settings that have been tested and confirmed to work with Solio's UI.

# Solver timeout in seconds (how long to wait for optimization to complete)
# Default: 300 (5 minutes)
# Note: This is a local timeout for our script, not sent to Solio
timeout: {timeout}

# Horizon: Number of gameweeks to optimize ahead (1-10)
# Lower values = faster solves, less forward planning
# Higher values = slower solves, better long-term planning
# Default: 10 gameweeks
horizon_weeks: {horizon_weeks}
""".format(
        timeout=default_settings["timeout"],
        horizon_weeks=default_settings["horizon_weeks"],
    )
    
    with open(settings_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Created default settings file: {settings_file}")


def main():
    """Main entry point for settings command."""
    # When run directly, create default settings file
    save_default_settings()
    
    # Load and display settings
    settings = load_solver_settings()
    print("\nCurrent Settings:")
    print(yaml.dump(settings, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
