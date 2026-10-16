#!/bin/zsh
# Render a list of storyboard shots back to back (current episode, see shared/tools/paths.py).
#   shared/tools/render_batch.sh preview B1_02 B1_03 ...
#   DREAMFORGE_EPISODE=E2-xxx shared/tools/render_batch.sh preview A0_01
q=$1; shift
cd "$(dirname $0)/../.."
renders=$(python3 -c "import sys; sys.path.insert(0,'shared/tools'); import paths; print(paths.RENDERS)")
mkdir -p "$renders"
for id in "$@"; do
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P shared/tools/render_storyboard.py -- \
      --shot $id --quality $q > "$renders/log_$id.txt" 2>&1 || echo "FAIL $id"
  echo "$id $(ls "$renders/shots/$id/$q" 2>/dev/null | wc -l | tr -d ' ') frames"
done
