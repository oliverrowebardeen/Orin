#!/bin/bash
# Quick launcher for Orin

cd "$(dirname "$0")"
python3 -m src.main "$@"
