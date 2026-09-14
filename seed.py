#!/usr/bin/env python3
"""
Blood Connect — Root Database Seeding Wrapper.
Proxies to backend/seed.py.
"""

import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import asyncio
from backend.seed import main

if __name__ == "__main__":
    asyncio.run(main())
