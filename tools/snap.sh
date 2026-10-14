#!/usr/bin/env bash
# usage: tools/snap.sh <scene> <local times comma-separated>  → prints contact sheet path
set -e
cd "$(dirname "$0")/.."
node tools/build.mjs >/dev/null
off=$(python3 -c "import json;d=json.load(open('timeline/timing.json'));print([s['start'] for s in d['sections'] if s['id']=='$1'][0])")
abs=$(python3 -c "print(','.join(str(round($off+float(x),3)) for x in '$2'.split(',')))")
npx hyperframes snapshot --at "$abs" 2>&1 | grep -E "contact-sheet|rror" | sed 's/ (grid.*//'
