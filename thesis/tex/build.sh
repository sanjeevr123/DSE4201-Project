#!/bin/sh
# Build the thesis PDF with tectonic (Homebrew). Usage: sh build.sh   ->  build/main.pdf
command -v tectonic >/dev/null 2>&1 || export PATH=/opt/homebrew/bin:$PATH
command -v tectonic >/dev/null 2>&1 || { echo "tectonic not found: install it (https://tectonic-typesetting.github.io/)" >&2; exit 1; }
cd "$(dirname "$0")" && mkdir -p build && tectonic -X compile main.tex --outdir build
