import uuid
from datetime import date, datetime, timezone, timedelta
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    AdminActionType,
    BloodGroup,
    NotificationType,
    ReportReason,
    ReportStatus,
    RequestStatus,
    UserRole,
)
from app.models.user import User
from app.models.donor import DonorProfile
from app.models.location import Location
from app.models.otp import OtpVerification
from app.models.blood_request import BloodRequest
from app.models.report import Report
from app.models.admin_action import AdminAction
from app.models.notification import Notification


@pytest.mark.asyncio
async def test_locations_seeded(db_session: AsyncSession):
    """Verify that initial predefined locations are seeded correctly."""
    stmt = select(Location)
    result = await db_session.execute(stmt)
    locations = result.scalars().all()
    assert len(locations) == 11
    names = [loc.name for loc in locations]
    assert "Coimbatore" in names
    assert "Sulur" in names
    assert "Pollachi" in names
    assert "Tiruppur" in names


@pytest.mark.asyncio
async def test_location_unique_constraint(db_session: AsyncSession):
    """Verify unique constraint on location name."""
    duplicate_loc = Location(name="Coimbatore", district="Coimbatore", state="Tamil Nadu")
    db_session.add(duplicate_loc)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_creation_and_unique_mobile(db_session: AsyncSession):
    """Verify User model creation, defaults, and mobile uniqueness."""
    user = User(
        name="John Doe",
        mobile="9876543210",
        role=UserRole.DONOR,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.name == "John Doe"
    assert user.mobile == "9876543210"
    assert user.role == UserRole.DONOR
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None

    # Test unique constraint on mobile
    dup_user = User(
        name="Jane Doe",
        mobile="9876543210",
        role=UserRole.REQUESTER,
    )
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_donor_profile_and_user_relationship(db_session: AsyncSession):
    """Verify 1-to-1 relationship between User and DonorProfile, and search fields."""
    loc_stmt = select(Location).where(Location.name == "Coimbatore")
    loc_result = await db_session.execute(loc_stmt)
    location = loc_result.scalar_one()

    user = User(name="Donor Alice", mobile="9876543211", role=UserRole.DONOR)
    db_session.add(user)
    await db_session.flush()

    donor_profile = DonorProfile(
        user_id=user.id,
        date_of_birth=date(1995, 5, 20),
        blood_group=BloodGroup.O_POS,
        location_id=location.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )
    db_session.add(donor_profile)
    await db_session.commit()
    await db_session.refresh(donor_profile)
    await db_session.refresh(user)

    assert user.donor_profile is not None
    assert user.donor_profile.blood_group == BloodGroup.O_POS
    assert donor_profile.user.name == "Donor Alice"
    assert donor_profile.location.name == "Coimbatore"


@pytest.mark.asyncio
async def test_blood_request_flow(db_session: AsyncSession):
    """Verify blood request creation and status transitions."""
    loc_stmt = select(Location).where(Location.name == "Sulur")
    loc_result = await db_session.execute(loc_stmt)
    location = loc_result.scalar_one()

    requester = User(name="Requester Bob", mobile="9876543212", role=UserRole.REQUESTER)
    donor_user = User(name="Donor Charlie", mobile="9876543213", role=UserRole.DONOR)
    db_session.add_all([requester, donor_user])
    await db_session.flush()

    donor_profile = DonorProfile(
        user_id=donor_user.id,
        date_of_birth=date(1992, 8, 14),
        blood_group=BloodGroup.A_POS,
        location_id=location.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True
    )
    db_session.add(donor_profile)
    await db_session.flush()

    # Create Blood Request
    blood_request = BloodRequest(
        requester_id=requester.id,
        donor_id=donor_profile.id,
        blood_group=BloodGroup.A_POS,
        location_id=location.id,
        message="Urgent requirement for surgery",
        status=RequestStatus.PENDING
    )
    db_session.add(blood_request)
    await db_session.commit()
    await db_session.refresh(blood_request)

    assert blood_request.status == RequestStatus.PENDING
    assert blood_request.requester.name == "Requester Bob"
    assert blood_request.donor.user.name == "Donor Charlie"

    # Accept request
    blood_request.status = RequestStatus.ACCEPTED
    blood_request.responded_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(blood_request)

    assert blood_request.status == RequestStatus.ACCEPTED
    assert blood_request.responded_at is not None


@pytest.mark.asyncio
async def test_otp_verification_lifecycle(db_session: AsyncSession):
    """Verify OtpVerification record creation and expiration."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=5)
    
    otp = OtpVerification(
        mobile="9876543214",
        otp_hash="hashed_otp_value_123456",
        expires_at=expires,
        attempts=0
    )
    db_session.add(otp)
    await db_session.commit()
    await db_session.refresh(otp)

    assert isinstance(otp.id, uuid.UUID)
    assert otp.mobile == "9876543214"
    assert otp.verified_at is None
    assert otp.attempts == 0

    # Simulate verification
    otp.attempts += 1
    otp.verified_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(otp)

    assert otp.attempts == 1
    assert otp.verified_at is not None


@pytest.mark.asyncio
async def test_report_and_admin_action_audit(db_session: AsyncSession):
    """Verify report submission and administrative audit logging."""
    loc_stmt = select(Location).where(Location.name == "Pollachi")
    loc_result = await db_session.execute(loc_stmt)
    location = loc_result.scalar_one()

    admin_user = User(name="Admin Dave", mobile="9876543215", role=UserRole.ADMIN)
    reporter = User(name="Reporter Eve", mobile="9876543216", role=UserRole.REQUESTER)
    donor_user = User(name="Donor Frank", mobile="9876543217", role=UserRole.DONOR)
    db_session.add_all([admin_user, reporter, donor_user])
    await db_session.flush()

    donor_profile = DonorProfile(
        user_id=donor_user.id,
        date_of_birth=date(1990, 1, 1),
        blood_group=BloodGroup.B_POS,
        location_id=location.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True
    )
    db_session.add(donor_profile)
    await db_session.flush()

    # Create Report
    report = Report(
        donor_id=donor_profile.id,
        reporter_id=reporter.id,
        reason=ReportReason.WRONG_BLOOD_GROUP,
        description="Donor stated they are B- not B+",
        status=ReportStatus.OPEN
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)

    assert report.status == ReportStatus.OPEN
    assert report.reason == ReportReason.WRONG_BLOOD_GROUP

    # Admin acts on report
    report.status = ReportStatus.RESOLVED
    report.resolved_at = datetime.now(timezone.utc)
    
    admin_action = AdminAction(
        admin_id=admin_user.id,
        action=AdminActionType.RESOLVE_REPORT.value,
        target_type="report",
        target_id=str(report.id),
        details={"notes": "Verified and corrected donor record"}
    )
    db_session.add(admin_action)
    await db_session.commit()
    await db_session.refresh(admin_action)

    assert admin_action.admin.name == "Admin Dave"
    assert admin_action.action == "RESOLVE_REPORT"
    assert admin_action.target_id == str(report.id)


@pytest.mark.asyncio
async def test_notification_creation(db_session: AsyncSession):
    """Verify notification creation and user association."""
    user = User(name="Recipient Grace", mobile="9876543218", role=UserRole.REQUESTER)
    db_session.add(user)
    await db_session.flush()

    notification = Notification(
        user_id=user.id,
        type=NotificationType.REQUEST_ACCEPTED,
        title="Blood Request Accepted",
        message="A donor has accepted your blood request.",
        is_read=False
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.is_read is False
    assert notification.type == NotificationType.REQUEST_ACCEPTED
    assert notification.user.name == "Recipient Grace"
