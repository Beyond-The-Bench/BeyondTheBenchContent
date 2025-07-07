#!/bin/bash

# Union sync for Adventures and Projects from Obsidian and Server to Content
# Removes files from content if missing from BOTH sources

set -e

# Ensure we're in the correct directory (repository root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "=== Starting Blog Content Update ==="
echo "Working directory: $(pwd)"
echo "Script directory: $SCRIPT_DIR"
echo "Repository root: $REPO_ROOT"

# Paths
OBSIDIAN_ADVENTURES="/home/ollie/Documents/Obsidian Vaults/HiveMind/Blog Posts/Adventures"
OBSIDIAN_PROJECTS="/home/ollie/Documents/Obsidian Vaults/HiveMind/Blog Posts/Projects"
SERVER_ADVENTURES="/home/ollie/Github/BeyondTheBenchServer/posts/Adventures"
SERVER_PROJECTS="/home/ollie/Github/BeyondTheBenchServer/posts/Projects"
CONTENT_ADVENTURES="$REPO_ROOT/Adventures"
CONTENT_PROJECTS="$REPO_ROOT/Projects"

echo "=== Checking source directories ==="
echo "Obsidian Adventures: $([ -d "$OBSIDIAN_ADVENTURES" ] && echo "✓ Found" || echo "✗ Missing")"
echo "Obsidian Projects: $([ -d "$OBSIDIAN_PROJECTS" ] && echo "✓ Found" || echo "✗ Missing")"
echo "Server Adventures: $([ -d "$SERVER_ADVENTURES" ] && echo "✓ Found" || echo "✗ Missing")"
echo "Server Projects: $([ -d "$SERVER_PROJECTS" ] && echo "✓ Found" || echo "✗ Missing")"

sync_union() {
  SRC1="$1"
  SRC2="$2"
  DEST="$3"
  mkdir -p "$DEST"

  echo "=== Syncing $(basename "$DEST") ==="
  
  # Always copy from both sources (source of truth)
  FILES_COPIED=0
  for SRC in "$SRC1" "$SRC2"; do
    if [ -d "$SRC" ]; then
      for FILE in "$SRC"/*.md; do
        [ -e "$FILE" ] || continue
        BASENAME="$(basename "$FILE")"
        DEST_FILE="$DEST/$BASENAME"
        
        # Always copy - sources are source of truth
        echo "✓ Copying $BASENAME from $(basename "$SRC")"
        cp "$FILE" "$DEST_FILE"
        FILES_COPIED=$((FILES_COPIED + 1))
      done
    fi
  done

  # Remove files from DEST not present in either source
  FILES_REMOVED=0
  for FILE in "$DEST"/*.md; do
    [ -e "$FILE" ] || continue
    BASENAME="$(basename "$FILE")"
    IN_SRC1=0
    IN_SRC2=0
    [ -f "$SRC1/$BASENAME" ] && IN_SRC1=1
    [ -f "$SRC2/$BASENAME" ] && IN_SRC2=1
    if [ $IN_SRC1 -eq 0 ] && [ $IN_SRC2 -eq 0 ]; then
      echo "✗ Removing $BASENAME (not found in either source)"
      rm "$FILE"
      FILES_REMOVED=$((FILES_REMOVED + 1))
    fi
  done
  
  echo "$(basename "$DEST"): $FILES_COPIED files copied, $FILES_REMOVED files removed"
}

# Sync Adventures
sync_union "$OBSIDIAN_ADVENTURES" "$SERVER_ADVENTURES" "$CONTENT_ADVENTURES"
# Sync Projects
sync_union "$OBSIDIAN_PROJECTS" "$SERVER_PROJECTS" "$CONTENT_PROJECTS"

echo "=== Blog post sync complete ==="

echo "=== Processing images ==="
python3 "$SCRIPT_DIR/images.py"
echo "=== Image processing complete ==="

echo "=== Committing changes ==="
echo "Current git status:"
git status --porcelain

git add . 
# Only commit if there are changes
if ! git diff --staged --quiet; then
    echo "✓ Changes detected, committing and pushing..."
    git commit -m "chore: Automated update of blog posts and images"
    git push origin master
    echo "✓ Changes successfully pushed to repository"
else
    echo "ℹ No changes to commit"
fi

echo "=== Blog content update complete ==="
exit 0