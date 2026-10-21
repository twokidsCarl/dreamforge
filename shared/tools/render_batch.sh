#!/usr/bin/env bash
# Render a list of storyboard shots back to back (current episode, see shared/tools/paths.py).
#   shared/tools/render_batch.sh preview B1_02 B1_03 ...
#   DREAMFORGE_EPISODE=E2-xxx shared/tools/render_batch.sh preview A0_01
#   FRAMES=1,mid,last shared/tools/render_batch.sh preview A_06a B_08a   # 只渲这几帧（单帧试渲）
# 每镜日志写到 <渲染根>/log_<id>.txt。有镜头失败时打印 FAIL <id>，最后退出码为 1。
q=$1; shift
cd "$(dirname $0)/../.."
# Blender 可执行文件：环境变量 BLENDER > PATH 里的 blender > mac 应用路径
BLENDER_BIN=${BLENDER:-$(command -v blender || echo /Applications/Blender.app/Contents/MacOS/Blender)}
renders=$(python3 -c "import sys; sys.path.insert(0,'shared/tools'); import paths; print(paths.RENDERS)")
mkdir -p "$renders"
frames_arg=()
[ -n "$FRAMES" ] && frames_arg=(--frames "$FRAMES")
failed=0
for id in "$@"; do
  "$BLENDER_BIN" -b --factory-startup -P shared/tools/render_storyboard.py -- \
      --shot $id --quality $q "${frames_arg[@]}" > "$renders/log_$id.txt" 2>&1 || { echo "FAIL $id"; failed=1; }
  # raw: true 的镜头写在 <quality>_raw/
  for d in "$q" "${q}_raw"; do
    [ -d "$renders/shots/$id/$d" ] && echo "$id $d $(ls "$renders/shots/$id/$d" | wc -l | tr -d ' ') frames"
  done
done
exit $failed
