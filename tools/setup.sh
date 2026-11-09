#!/bin/bash
# One-time setup per session.
set -e
pip install --break-system-packages -q pymunk pycairo
python3 -c "import cairo, pymunk; print('setup ok')"
