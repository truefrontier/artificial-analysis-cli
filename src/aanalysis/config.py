"""Configuration management."""

from pathlib import Path
import sys


def get_config_dir() -> Path:
    """Get config directory."""
    return Path.home() / ".config" / "artificial-analysis"


def get_api_key_path() -> Path:
    """Get API key file path."""
    return get_config_dir() / "api_key"


def set_api_key(key: str) -> None:
    """Set API key in config file.
    
    Args:
        key: API key to store
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    key_path = get_api_key_path()
    key_path.write_text(key.strip())
    key_path.chmod(0o600)  # Secure permissions
    
    print(f"API key saved to {key_path}")


def read_api_key_from_stdin() -> str:
    """Read API key from stdin."""
    print("Enter API key (input hidden):")
    import getpass
    key = getpass.getpass("")
    return key.strip()


def read_api_key_from_file(path: Path) -> str:
    """Read API key from file."""
    if not path.exists():
        print(f"Error: Key file not found: {path}", file=sys.stderr)
        sys.exit(3)
    return path.read_text().strip()
