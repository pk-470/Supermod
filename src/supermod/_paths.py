from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

# Local-dev paths live at the project root — i.e. the directory the bot is
# launched from. Anchor to the CWD rather than the package, since with a
# src-layout install PACKAGE_DIR no longer sits inside the repo. (Only used in
# local mode; deployment reads credentials from environment variables.)
REPO_ROOT = Path.cwd()

TOKENS_PATH = REPO_ROOT / ".secrets"
LOCAL_MARKER = REPO_ROOT / ".local"  # presence => local-dev mode (gitignored)
FEATURES_DIR = PACKAGE_DIR / "features"
FEATURES_PACKAGE = "supermod.features"
