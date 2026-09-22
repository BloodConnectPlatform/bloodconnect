import asyncio
from datetime import date, datetime, timedelta, timezone
import logging
from typing import Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.admin_action import AdminAction
from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import (
    AdminActionType,
    BloodGroup,
    NotificationType,
    ReportReason,
    ReportStatus,
    RequestStatus,
    UserRole,
)
from app.models.location import Location
from app.models.notification import Notification
from app.models.report import Report
from app.models.user import User
from app.core.config import settings
from app.seeds.locations import seed_locations

logger = logging.getLogger("blood_connect.seed")

# Sample Users and Donors Data Definition
SAMPLE_REQUESTERS = [
    {
        "name": "Priya Sharma",
        "mobile": "9876543220",
        "role": UserRole.REQUESTER,
        "is_active": True,
    },
    {
        "name": "Rahul Verma",
        "mobile": "9876543221",
        "role": UserRole.REQUESTER,
        "is_active": True,
    },
    {
        "name": "Karthik Subramanian",
        "mobile": "9876543222",
        "role": UserRole.REQUESTER,
        "is_active": True,
    },
    {
        "name": "Ananya Iyer",
        "mobile": "9876543223",
        "role": UserRole.REQUESTER,
        "is_active": True,
    },
]

SAMPLE_DONORS = [
    # O+ Donors
    {
        "name": "Arun Kumar",
        "mobile": "9876543201",
        "role": UserRole.DONOR,
        "dob": date(1992, 4, 15),
        "blood_group": BloodGroup.O_POS,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Deepak Raj",
        "mobile": "9876543202",
        "role": UserRole.DONOR,
        "dob": date(1995, 8, 22),
        "blood_group": BloodGroup.O_POS,
        "location": "Sulur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Siddharth Menon",
        "mobile": "9876543203",
        "role": UserRole.DONOR,
        "dob": date(1989, 11, 5),
        "blood_group": BloodGroup.O_POS,
        "location": "Tiruppur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Vijay Shankar",
        "mobile": "9876543204",
        "role": UserRole.DONOR,
        "dob": date(1996, 2, 18),
        "blood_group": BloodGroup.O_POS,
        "location": "Pollachi",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # O- Donors (Universal Donors)
    {
        "name": "Sanjay Krishnan",
        "mobile": "9876543205",
        "role": UserRole.DONOR,
        "dob": date(1991, 7, 30),
        "blood_group": BloodGroup.O_NEG,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Ganesh Prabhu",
        "mobile": "9876543206",
        "role": UserRole.DONOR,
        "dob": date(1994, 9, 12),
        "blood_group": BloodGroup.O_NEG,
        "location": "Mettupalayam",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # A+ Donors
    {
        "name": "Meera Nair",
        "mobile": "9876543207",
        "role": UserRole.DONOR,
        "dob": date(1997, 3, 25),
        "blood_group": BloodGroup.A_POS,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Rajesh Kannan",
        "mobile": "9876543208",
        "role": UserRole.DONOR,
        "dob": date(1990, 6, 14),
        "blood_group": BloodGroup.A_POS,
        "location": "Tiruppur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Kavitha Sundaram",
        "mobile": "9876543209",
        "role": UserRole.DONOR,
        "dob": date(1993, 12, 8),
        "blood_group": BloodGroup.A_POS,
        "location": "Avinashi",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # A- Donors
    {
        "name": "Vikramaditya",
        "mobile": "9876543211",
        "role": UserRole.DONOR,
        "dob": date(1988, 10, 19),
        "blood_group": BloodGroup.A_NEG,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Swathi Narayanan",
        "mobile": "9876543212",
        "role": UserRole.DONOR,
        "dob": date(1998, 5, 3),
        "blood_group": BloodGroup.A_NEG,
        "location": "Palladam",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # B+ Donors
    {
        "name": "Gokul Prasad",
        "mobile": "9876543213",
        "role": UserRole.DONOR,
        "dob": date(1995, 1, 17),
        "blood_group": BloodGroup.B_POS,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Nandhini Mohan",
        "mobile": "9876543214",
        "role": UserRole.DONOR,
        "dob": date(1996, 8, 29),
        "blood_group": BloodGroup.B_POS,
        "location": "Sulur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Manoj Kumar",
        "mobile": "9876543215",
        "role": UserRole.DONOR,
        "dob": date(1992, 10, 10),
        "blood_group": BloodGroup.B_POS,
        "location": "Pollachi",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # B- Donors
    {
        "name": "Dinesh Chandran",
        "mobile": "9876543216",
        "role": UserRole.DONOR,
        "dob": date(1991, 4, 4),
        "blood_group": BloodGroup.B_NEG,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Preethi Venkatesh",
        "mobile": "9876543217",
        "role": UserRole.DONOR,
        "dob": date(1994, 7, 21),
        "blood_group": BloodGroup.B_NEG,
        "location": "Udumalpet",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # AB+ Donors (Universal Recipient)
    {
        "name": "Ashwin Ram",
        "mobile": "9876543218",
        "role": UserRole.DONOR,
        "dob": date(1990, 2, 14),
        "blood_group": BloodGroup.AB_POS,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Divya Balaji",
        "mobile": "9876543219",
        "role": UserRole.DONOR,
        "dob": date(1997, 9, 9),
        "blood_group": BloodGroup.AB_POS,
        "location": "Tiruppur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # AB- Donors (Rarest)
    {
        "name": "Harish Raghavan",
        "mobile": "9876543224",
        "role": UserRole.DONOR,
        "dob": date(1989, 5, 12),
        "blood_group": BloodGroup.AB_NEG,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Sneha Suresh",
        "mobile": "9876543225",
        "role": UserRole.DONOR,
        "dob": date(1999, 11, 27),
        "blood_group": BloodGroup.AB_NEG,
        "location": "Annur",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    # Edge Case Scenarios for testing UI & API filtering
    {
        "name": "Kishore Kumar (Unavailable)",
        "mobile": "9876543226",
        "role": UserRole.DONOR,
        "dob": date(1993, 6, 15),
        "blood_group": BloodGroup.O_POS,
        "location": "Coimbatore",
        "is_otp_verified": True,
        "is_available": False,  # Temporarily unavailable
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Aravind Swamy (Unverified)",
        "mobile": "9876543227",
        "role": UserRole.DONOR,
        "dob": date(1995, 3, 20),
        "blood_group": BloodGroup.A_POS,
        "location": "Coimbatore",
        "is_otp_verified": False,  # Not OTP verified yet
        "is_available": True,
        "is_active": True,
        "contact_consent": True,
    },
    {
        "name": "Naveen Patnaik (Deactivated)",
        "mobile": "9876543228",
        "role": UserRole.DONOR,
        "dob": date(1991, 12, 1),
        "blood_group": BloodGroup.B_POS,
        "location": "Madukkarai",
        "is_otp_verified": True,
        "is_available": True,
        "is_active": False,  # Deactivated profile
        "user_is_active": False,
        "contact_consent": True,
    },
]


async def seed_users(session: AsyncSession) -> Dict[str, int]:
    """
    Seed sample users, donor profiles, requests, notifications, and moderation reports.
    Idempotent: safely handles already-existing records.
    """
    # 1. Ensure locations exist
    await seed_locations(session)
    loc_stmt = select(Location)
    loc_res = await session.execute(loc_stmt)
    locations_map: Dict[str, Location] = {loc.name: loc for loc in loc_res.scalars().all()}

    stats = {
        "admins": 0,
        "requesters": 0,
        "donors": 0,
        "requests": 0,
        "reports": 0,
        "notifications": 0,
        "admin_actions": 0,
    }

    user_lookup: Dict[str, User] = {}
    donor_lookup: Dict[str, DonorProfile] = {}

    # 2. Seed Initial Admins from settings
    initial_admins = settings.INITIAL_ADMIN_PHONE_NUMBERS
    if isinstance(initial_admins, str):
        initial_admins = [p.strip() for p in initial_admins.split(",") if p.strip()]

    for phone in initial_admins:
        stmt = select(User).where(User.mobile == phone)
        res = await session.execute(stmt)
        user = res.scalars().first()
        if not user:
            user = User(
                name="System Administrator",
                mobile=phone,
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            stats["admins"] += 1
        else:
            if user.role != UserRole.ADMIN:
                user.role = UserRole.ADMIN
                await session.flush()
        user_lookup[phone] = user

    # 3. Seed Requesters
    for req_data in SAMPLE_REQUESTERS:
        stmt = select(User).where(User.mobile == req_data["mobile"])
        res = await session.execute(stmt)
        user = res.scalars().first()
        if not user:
            user = User(
                name=req_data["name"],
                mobile=req_data["mobile"],
                role=req_data["role"],
                is_active=req_data["is_active"],
            )
            session.add(user)
            await session.flush()
            stats["requesters"] += 1
        user_lookup[req_data["mobile"]] = user

    # 4. Seed Donors
    for donor_data in SAMPLE_DONORS:
        stmt = select(User).where(User.mobile == donor_data["mobile"])
        res = await session.execute(stmt)
        user = res.scalars().first()

        loc = locations_map.get(donor_data["location"])
        if not loc:
            logger.warning(f"Location {donor_data['location']} not found. Skipping donor {donor_data['name']}.")
            continue

        if not user:
            user_active = donor_data.get("user_is_active", True)
            user = User(
                name=donor_data["name"],
                mobile=donor_data["mobile"],
                role=donor_data["role"],
                is_active=user_active,
            )
            session.add(user)
            await session.flush()

        user_lookup[donor_data["mobile"]] = user

        # Check donor profile
        dp_stmt = select(DonorProfile).where(DonorProfile.user_id == user.id)
        dp_res = await session.execute(dp_stmt)
        donor_profile = dp_res.scalars().first()

        if not donor_profile:
            donor_profile = DonorProfile(
                user_id=user.id,
                date_of_birth=donor_data["dob"],
                blood_group=donor_data["blood_group"],
                location_id=loc.id,
                is_otp_verified=donor_data["is_otp_verified"],
                is_available=donor_data["is_available"],
                is_active=donor_data["is_active"],
                contact_consent=donor_data.get("contact_consent", True),
            )
            session.add(donor_profile)
            await session.flush()
            stats["donors"] += 1

        donor_lookup[donor_data["mobile"]] = donor_profile

    # 5. Seed Sample Blood Requests
    now = datetime.now(timezone.utc)
    priya = user_lookup.get("9876543220")
    rahul = user_lookup.get("9876543221")
    karthik = user_lookup.get("9876543222")

    arun_donor = donor_lookup.get("9876543201")
    sanjay_donor = donor_lookup.get("9876543205")
    meera_donor = donor_lookup.get("9876543207")

    cbe_loc = locations_map.get("Coimbatore")

    if priya and arun_donor and cbe_loc:
        req_check = (
            await session.execute(
                select(BloodRequest).where(
                    BloodRequest.requester_id == priya.id,
                    BloodRequest.donor_id == arun_donor.id,
                )
            )
        ).scalars().first()
        if not req_check:
            req1 = BloodRequest(
                requester_id=priya.id,
                donor_id=arun_donor.id,
                blood_group=BloodGroup.O_POS,
                location_id=cbe_loc.id,
                message="Urgent: Required O+ blood for surgery at KG Hospital Coimbatore tomorrow morning.",
                status=RequestStatus.PENDING,
                created_at=now - timedelta(hours=2),
            )
            session.add(req1)
            stats["requests"] += 1

    if rahul and sanjay_donor and cbe_loc:
        req_check = (
            await session.execute(
                select(BloodRequest).where(
                    BloodRequest.requester_id == rahul.id,
                    BloodRequest.donor_id == sanjay_donor.id,
                )
            )
        ).scalars().first()
        if not req_check:
            req2 = BloodRequest(
                requester_id=rahul.id,
                donor_id=sanjay_donor.id,
                blood_group=BloodGroup.O_NEG,
                location_id=cbe_loc.id,
                message="Emergency: O- blood needed for accident patient at PSG Hospital.",
                status=RequestStatus.ACCEPTED,
                created_at=now - timedelta(days=1),
                responded_at=now - timedelta(hours=22),
            )
            session.add(req2)
            stats["requests"] += 1

    if karthik and meera_donor and cbe_loc:
        req_check = (
            await session.execute(
                select(BloodRequest).where(
                    BloodRequest.requester_id == karthik.id,
                    BloodRequest.donor_id == meera_donor.id,
                )
            )
        ).scalars().first()
        if not req_check:
            req3 = BloodRequest(
                requester_id=karthik.id,
                donor_id=meera_donor.id,
                blood_group=BloodGroup.A_POS,
                location_id=cbe_loc.id,
                message="Scheduled dialysis blood requirement for weekend.",
                status=RequestStatus.REJECTED,
                created_at=now - timedelta(days=2),
                responded_at=now - timedelta(days=1, hours=20),
            )
            session.add(req3)
            stats["requests"] += 1

    # 6. Seed Sample Reports
    ananya = user_lookup.get("9876543223")
    kishore_donor = donor_lookup.get("9876543226")
    if ananya and kishore_donor:
        rep_check = (
            await session.execute(
                select(Report).where(
                    Report.reporter_id == ananya.id,
                    Report.donor_id == kishore_donor.id,
                )
            )
        ).scalars().first()
        if not rep_check:
            rep = Report(
                reporter_id=ananya.id,
                donor_id=kishore_donor.id,
                reason=ReportReason.INCORRECT_INFORMATION,
                description="Donor mentioned being available on call but profile marked as unavailable.",
                status=ReportStatus.OPEN,
                created_at=now - timedelta(days=1),
            )
            session.add(rep)
            stats["reports"] += 1

    # Find any available admin user for sample system notifications and audit trail
    admin_user = next((u for u in user_lookup.values() if u.role == UserRole.ADMIN), None)
    if not admin_user:
        admin_stmt = select(User).where(User.role == UserRole.ADMIN).limit(1)
        admin_user = (await session.execute(admin_stmt)).scalars().first()

    # 7. Seed Sample Notifications
    sample_notifs = [
        (
            user_lookup.get("9876543201"),
            NotificationType.REQUEST_RECEIVED,
            "New Blood Request Received",
            "Priya Sharma has sent you a blood request for O+ blood in Coimbatore.",
            False,
        ),
        (
            user_lookup.get("9876543221"),
            NotificationType.REQUEST_ACCEPTED,
            "Blood Request Accepted",
            "Sanjay Krishnan has accepted your blood request! You may now view contact details to coordinate.",
            False,
        ),
        (
            admin_user,
            NotificationType.SYSTEM,
            "Platform Maintenance Notice",
            "System database verified and sample entities active.",
            True,
        ),
    ]

    for user_obj, n_type, title, message, is_read in sample_notifs:
        if user_obj:
            notif_check = (
                await session.execute(
                    select(Notification).where(
                        Notification.user_id == user_obj.id,
                        Notification.title == title,
                    )
                )
            ).scalars().first()
            if not notif_check:
                notif = Notification(
                    user_id=user_obj.id,
                    type=n_type,
                    title=title,
                    message=message,
                    is_read=is_read,
                    created_at=now - timedelta(hours=1),
                )
                session.add(notif)
                stats["notifications"] += 1

    # 8. Seed Admin Actions Audit Log
    if admin_user and kishore_donor:
        action_check = (
            await session.execute(
                select(AdminAction).where(
                    AdminAction.admin_id == admin_user.id,
                    AdminAction.target_id == str(kishore_donor.id),
                )
            )
        ).scalars().first()
        if not action_check:
            action = AdminAction(
                admin_id=admin_user.id,
                action=AdminActionType.UPDATE_AVAILABILITY.value,
                target_type="donor_profile",
                target_id=str(kishore_donor.id),
                details={"reason": "Sample admin availability check", "status": "UNAVAILABLE"},
                created_at=now - timedelta(days=2),
            )
            session.add(action)
            stats["admin_actions"] += 1

    await session.commit()
    return stats


async def ensure_initial_admins(session: AsyncSession) -> int:
    """Ensure all phone numbers in INITIAL_ADMIN_PHONE_NUMBERS exist as active ADMIN users."""
    initial_admins = settings.INITIAL_ADMIN_PHONE_NUMBERS or []
    if isinstance(initial_admins, str):
        initial_admins = [p.strip() for p in initial_admins.split(",") if p.strip()]

    count = 0
    for raw_phone in initial_admins:
        phone = str(raw_phone).strip().replace(" ", "").replace("-", "")
        if not phone:
            continue
        std_phone = phone[-10:] if len(phone) >= 10 else phone
        phone_variants = {
            phone,
            phone.replace("+", ""),
            f"+91{std_phone}",
            f"91{std_phone}",
            std_phone,
        }
        stmt = select(User).where(User.mobile.in_(phone_variants))
        res = await session.execute(stmt)
        user = res.scalars().first()

        if not user:
            user = User(
                name="System Administrator",
                mobile=std_phone,
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            count += 1
            logger.info(f"Provisioned initial admin user for mobile: {std_phone}")
        else:
            if user.role != UserRole.ADMIN or not user.is_active:
                user.role = UserRole.ADMIN
                user.is_active = True
                await session.flush()
                count += 1
                logger.info(f"Promoted existing user to ADMIN for mobile: {user.mobile}")
    await session.commit()
    return count

