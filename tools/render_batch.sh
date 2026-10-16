#!/bin/zsh
# Render a list of storyboard shots back to back; resumable (skips shots whose frames all exist).
#   tools/render_batch.sh preview B1_02 B1_03 ...
q=$1; shift
cd "$(dirname $0)/.."
for id in "$@"; do
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/render_storyboard.py -- \
      --shot $id --quality $q > renders/log_$id.txt 2>&1 || echo "FAIL $id"
  echo "$id $(ls renders/shots/$id/$q 2>/dev/null | wc -l | tr -d ' ') frames"
done
