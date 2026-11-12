#!/usr/bin/env bash
# ==============================================================================
# Keep a Changelog Helper (`scripts/changelog-add.sh`)
# Usage:
#   bash scripts/changelog-add.sh <Category> "<Entry message>"
#   Valid categories: Added, Changed, Deprecated, Removed, Fixed, Security
# ==============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHANGELOG_FILE="$PROJECT_DIR/CHANGELOG.md"

if [[ $# -lt 2 ]]; then
    echo "Usage: bash scripts/changelog-add.sh <Added|Changed|Deprecated|Removed|Fixed|Security> \"<message>\"" >&2
    exit 1
fi

CATEGORY="$1"
shift
MESSAGE="$*"

case "$CATEGORY" in
    Added|Changed|Deprecated|Removed|Fixed|Security) ;;
    *)
        echo "ERROR: Invalid category '$CATEGORY'. Must be one of: Added, Changed, Deprecated, Removed, Fixed, Security." >&2
        exit 1
        ;;
esac

python3 - "$CHANGELOG_FILE" "$CATEGORY" "$MESSAGE" <<'PY'
import sys
from pathlib import Path

changelog_path = Path(sys.argv[1])
category = sys.argv[2]
message = sys.argv[3].strip()
bullet = f"- {message}"

text = changelog_path.read_text(encoding="utf-8")
lines = text.splitlines()

unreleased_idx = next((i for i, line in enumerate(lines) if line.startswith("## [Unreleased]")), None)
if unreleased_idx is None:
    raise SystemExit("ERROR: '## [Unreleased]' section not found in CHANGELOG.md")

next_release_idx = next(
    (i for i in range(unreleased_idx + 1, len(lines)) if lines[i].startswith("## [")),
    len(lines),
)

section_header = f"### {category}"
cat_idx = next(
    (i for i in range(unreleased_idx + 1, next_release_idx) if lines[i].strip() == section_header),
    None,
)

if cat_idx is not None:
    insert_at = cat_idx + 1
    if bullet not in lines[cat_idx + 1 : next_release_idx]:
        lines.insert(insert_at, bullet)
else:
    insert_at = unreleased_idx + 1
    while insert_at < next_release_idx and lines[insert_at].strip() == "":
        insert_at += 1
    lines[insert_at:insert_at] = [section_header, bullet, ""]

changelog_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(f"Updated CHANGELOG.md under ## [Unreleased] -> ### {category}: {bullet}")
PY

git -C "$PROJECT_DIR" add "$CHANGELOG_FILE"
