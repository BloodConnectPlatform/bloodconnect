#!/usr/bin/env python3
"""
Blood Connect — Database Seeding Script.

Seeds predefined locations and a rich dataset of sample users, donor profiles,
blood requests, notifications, reports, and admin logs.
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.database.base import Base
from app.database.session import AsyncSessionLocal, engine
from app.seeds.locations import seed_locations
from app.seeds.users import (
    SAMPLE_DONORS,
    SAMPLE_REQUESTERS,
    seed_users,
)


async def main():
    print("=" * 70)
    print(f"[*] Blood Connect -- Database Seeder ({settings.ENVIRONMENT} mode)")
    print(f"[*] Database: {settings.DATABASE_URL}")
    print("=" * 70)

    # 1. Initialize schema if using SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[+] Database tables verified.")

    # 2. Run Seeding inside an active session
    async with AsyncSessionLocal() as session:
        print("\n[1/2] Seeding Predefined Locations...")
        loc_count = await seed_locations(session)
        if loc_count > 0:
            print(f"  [+] Added {loc_count} new locations.")
        else:
            print("  [+] Predefined locations already exist.")

        print("\n[2/2] Seeding Sample Users & Domain Entities...")
        stats = await seed_users(session)

    print("\n" + "=" * 70)
    print("[*] SEEDING SUMMARY")
    print("=" * 70)
    print(f"  - Admins created:        {stats['admins']}")
    print(f"  - Requesters created:    {stats['requesters']}")
    print(f"  - Donors created:        {stats['donors']}")
    print(f"  - Requests created:      {stats['requests']}")
    print(f"  - Reports created:       {stats['reports']}")
    print(f"  - Notifications created: {stats['notifications']}")
    print(f"  - Admin Actions logged:  {stats['admin_actions']}")
    print("=" * 70)

    print("\n[*] SAMPLE TEST ACCOUNTS (Login via Mobile OTP)")
    print("-" * 70)
    print(f"{'Role':<12} | {'Name':<22} | {'Mobile':<12} | {'Details'}")
    print("-" * 70)

    initial_admins = settings.INITIAL_ADMIN_PHONE_NUMBERS
    if isinstance(initial_admins, str):
        initial_admins = [p.strip() for p in initial_admins.split(",") if p.strip()]
    for admin_phone in initial_admins:
        print(f"{'ADMIN':<12} | {'System Administrator':<22} | {admin_phone:<12} | System Administration")


    for req in SAMPLE_REQUESTERS:
        print(f"{'REQUESTER':<12} | {req['name']:<22} | {req['mobile']:<12} | Active Requester")

    for donor in SAMPLE_DONORS[:8]:  # Display first 8 donors as highlight
        status_note = f"{donor['blood_group'].value} ({donor['location']})"
        if not donor.get("is_available", True):
            status_note += " [Unavailable]"
        if not donor.get("is_otp_verified", True):
            status_note += " [Unverified]"
        print(f"{'DONOR':<12} | {donor['name']:<22} | {donor['mobile']:<12} | {status_note}")

    if len(SAMPLE_DONORS) > 8:
        print(f"... and {len(SAMPLE_DONORS) - 8} more donor profiles seeded across all blood groups.")

    print("-" * 70)
    print("[i] In development mode, the OTP is returned in the API response as 'debug_otp'.")
    print("[+] Seeding completed successfully.\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
