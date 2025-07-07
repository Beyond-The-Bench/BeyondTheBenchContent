#!/bin/bash

# Union sync for Adventures and Projects from Obsidian and Server to Content
# Removes files from content if missing from BOTH sources

set -e

# Paths
OBSIDIAN_ADVENTURES="/home/ollie/Documents/Obsidian Vaults/HiveMind/Blog Posts/Adventures"
OBSIDIAN_PROJECTS="/home/ollie/Documents/Obsidian Vaults/HiveMind/Blog Posts/Projects"
SERVER_ADVENTURES="/home/ollie/Github/BeyondTheBenchServer/posts/Adventures"
SERVER_PROJECTS="/home/ollie/Github/BeyondTheBenchServer/posts/Projects"
CONTENT_ADVENTURES="/home/ollie/Github/BeyondTheBenchContent/Adventures"
CONTENT_PROJECTS="/home/ollie/Github/BeyondTheBenchContent/Projects"

sync_union() {
  SRC1="$1"
  SRC2="$2"
  DEST="$3"
  mkdir -p "$DEST"

  # Always copy from both sources (source of truth)
  for SRC in "$SRC1" "$SRC2"; do
    if [ -d "$SRC" ]; then
      for FILE in "$SRC"/*.md; do
        [ -e "$FILE" ] || continue
        BASENAME="$(basename "$FILE")"
        DEST_FILE="$DEST/$BASENAME"
        
        # Always copy - sources are source of truth
        echo "Copying $BASENAME from $(basename "$SRC")"
        cp "$FILE" "$DEST_FILE"
      done
    fi
  done

  # Remove files from DEST not present in either source
  for FILE in "$DEST"/*.md; do
    [ -e "$FILE" ] || continue
    BASENAME="$(basename "$FILE")"
    IN_SRC1=0
    IN_SRC2=0
    [ -f "$SRC1/$BASENAME" ] && IN_SRC1=1
    [ -f "$SRC2/$BASENAME" ] && IN_SRC2=1
    if [ $IN_SRC1 -eq 0 ] && [ $IN_SRC2 -eq 0 ]; then
      echo "Removing $BASENAME (not found in either source)"
      rm "$FILE"
    fi
  done
}

# Sync Adventures
sync_union "$OBSIDIAN_ADVENTURES" "$SERVER_ADVENTURES" "$CONTENT_ADVENTURES"
# Sync Projects
sync_union "$OBSIDIAN_PROJECTS" "$SERVER_PROJECTS" "$CONTENT_PROJECTS"

echo "Union sync complete."

python3 /home/ollie/Github/BeyondTheBenchContent/scripts/images.py

git add . 
# Only commit if there are changes
if ! git diff --staged --quiet; then
    git commit -m "chore: Automated update of blog posts and images"
    git push origin master
else
    echo "No changes to commit"
fi
exit 0