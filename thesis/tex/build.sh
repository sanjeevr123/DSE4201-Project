#!/bin/sh
# Build the thesis PDF with tectonic (Homebrew). Usage: sh build.sh   ->  build/main.pdf
export PATH=/opt/homebrew/bin:$PATH
cd "$(dirname "$0")" && mkdir -p build && tectonic -X compile main.tex --outdir build
