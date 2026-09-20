import asyncio
from datetime import date
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.models.admin_action import AdminAction
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, UserRole
from app.models.location import Location
from app.models.user import User
from app.seeds.users import seed_users


@pytest_asyncio.fixture(scope="function")
async def admin_mgmt_fixture(client: AsyncClient, db_session: AsyncSession):
    """Fixture providing initialized admins, requesters, donors, and tokens."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # Admin 1
    admin1_mobile = "9876543301"
    admin1_user = User(name="Admin One", mobile=admin1_mobile, role=UserRole.ADMIN, is_active=True)
    db_session.add(admin1_user)

    # Admin 2
    admin2_mobile = "9876543302"
    admin2_user = User(name="Admin Two", mobile=admin2_mobile, role=UserRole.ADMIN, is_active=True)
    db_session.add(admin2_user)

    # Regular Requester
    req_mobile = "9876543303"
    req_user = User(name="Requester User", mobile=req_mobile, role=UserRole.REQUESTER, is_active=True)
    db_session.add(req_user)

    await db_session.commit()

    # Tokens
    s1 = await client.post("/api/v1/auth/send-otp", json={"mobile": admin1_mobile})
    l1 = await client.post("/api/v1/auth/login", json={"mobile": admin1_mobile, "otp": s1.json()["debug_otp"]})
    admin1_token = l1.json()["access_token"]

    s2 = await client.post("/api/v1/auth/send-otp", json={"mobile": admin2_mobile})
    l2 = await client.post("/api/v1/auth/login", json={"mobile": admin2_mobile, "otp": s2.json()["debug_otp"]})
    admin2_token = l2.json()["access_token"]

    s3 = await client.post("/api/v1/auth/send-otp", json={"mobile": req_mobile})
    l3 = await client.post("/api/v1/auth/login", json={"mobile": req_mobile, "otp": s3.json()["debug_otp"]})
    req_token = l3.json()["access_token"]

    # Register a Donor User
    donor_mobile = "9876543304"
    s4 = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_mobile})
    r4 = await client.post(
        "/api/v1/donors",
        json={
            "name": "Donor User",
            "mobile": donor_mobile,
            "otp": s4.json()["debug_otp"],
            "date_of_birth": "1994-05-15",
            "blood_group": "O+",
            "location_id": loc.id,
            "contact_consent": True,
        }
    )
    donor_token = r4.json()["access_token"]
    donor_user = (await db_session.execute(select(User).where(User.mobile == donor_mobile))).scalar_one()

    return {
        "admin1_user": admin1_user,
        "admin1_token": admin1_token,
        "admin2_user": admin2_user,
        "admin2_token": admin2_token,
        "req_user": req_user,
        "req_token": req_token,
        "donor_user": donor_user,
        "donor_token": donor_token,
        "bootstrap_secret": settings.ADMIN_BOOTSTRAP_SECRET,
    }


# ============================================================================
# 1. BOOTSTRAP PROVISIONING TESTS
# ============================================================================

def test_settings_initial_admin_phone_numbers_normalization():
    """Verify Settings parses comma-separated, list, whitespace, and duplicate inputs."""
    # Comma-separated with spaces and prefixes
    phones1 = Settings.assemble_initial_admin_phones(" 9876543210 , +919876543211, 9876543210 ")
    assert phones1 == ["9876543210", "9876543211"]

    # JSON-like string
    phones2 = Settings.assemble_initial_admin_phones('["9876543210", "9876543212"]')
    assert phones2 == ["9876543210", "9876543212"]

    # List of mixed strings
    phones3 = Settings.assemble_initial_admin_phones(["09876543210", "919876543211", "9876543210"])
    assert phones3 == ["9876543210", "9876543211"]

    # Empty values
    assert Settings.assemble_initial_admin_phones("") == []
    assert Settings.assemble_initial_admin_phones(None) == []


@pytest.mark.asyncio
async def test_seed_users_provisions_configured_admins(db_session: AsyncSession, monkeypatch):
    """Verify configured phone numbers are provisioned as ADMIN during seed."""
    test_phones = ["9876543310", "9876543311"]
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PHONE_NUMBERS", test_phones)

    stats = await seed_users(db_session)
    assert stats["admins"] == 2

    # Check both users exist with ADMIN role
    for p in test_phones:
        user = (await db_session.execute(select(User).where(User.mobile == p))).scalar_one_or_none()
        assert user is not None
        assert user.role == UserRole.ADMIN
        assert user.name == "System Administrator"


@pytest.mark.asyncio
async def test_seed_users_preserves_existing_admins_not_in_bootstrap(db_session: AsyncSession, monkeypatch):
    """Verify existing admins are NOT demoted even if absent from INITIAL_ADMIN_PHONE_NUMBERS."""
    # Pre-create an admin not in bootstrap
    existing_admin = User(name="Existing Leader", mobile="9876543320", role=UserRole.ADMIN, is_active=True)
    db_session.add(existing_admin)
    await db_session.commit()

    # Configure bootstrap with only a different admin
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PHONE_NUMBERS", ["9876543321"])
    await seed_users(db_session)

    # Verify both admins exist with ADMIN role
    admin1 = (await db_session.execute(select(User).where(User.mobile == "9876543320"))).scalar_one()
    admin2 = (await db_session.execute(select(User).where(User.mobile == "9876543321"))).scalar_one()
    assert admin1.role == UserRole.ADMIN
    assert admin2.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_seed_users_empty_bootstrap_creates_no_admins(db_session: AsyncSession, monkeypatch):
    """Verify empty INITIAL_ADMIN_PHONE_NUMBERS does not create any admins."""
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PHONE_NUMBERS", [])
    stats = await seed_users(db_session)
    assert stats["admins"] == 0

    admin_count = (await db_session.execute(select(func.count(User.id)).where(User.role == UserRole.ADMIN))).scalar()
    assert admin_count == 0


# ============================================================================
# 2. PROMOTE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_promote_user_with_admin_jwt(client: AsyncClient, admin_mgmt_fixture, db_session: AsyncSession):
    """Test authenticated administrator can promote a requester to admin."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    payload = {"action": "PROMOTE", "mobile": fixture["req_user"].mobile}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["action"] == "PROMOTE"
    assert data["user"]["mobile"] == fixture["req_user"].mobile
    assert data["user"]["role"] == "ADMIN"

    # Verify DB role
    db_user = (await db_session.execute(select(User).where(User.mobile == fixture["req_user"].mobile))).scalar_one()
    assert db_user.role == UserRole.ADMIN

    # Verify audit log
    audit_res = await db_session.execute(
        select(AdminAction).where(AdminAction.action == "PROMOTE", AdminAction.target_id == str(db_user.id))
    )
    audit = audit_res.scalar_one_or_none()
    assert audit is not None
    assert audit.admin_id == fixture["admin1_user"].id
    assert audit.details["actor_type"] == "admin_user"


@pytest.mark.asyncio
async def test_promote_user_with_bootstrap_secret(client: AsyncClient, admin_mgmt_fixture, db_session: AsyncSession):
    """Test break-glass X-Admin-Secret can promote a user without admin JWT."""
    fixture = admin_mgmt_fixture
    headers = {"X-Admin-Secret": fixture["bootstrap_secret"]}

    payload = {"action": "PROMOTE", "mobile": fixture["req_user"].mobile}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["action"] == "PROMOTE"
    assert data["user"]["role"] == "ADMIN"

    # Verify audit log has admin_id=None (System/Bootstrap actor)
    db_user = (await db_session.execute(select(User).where(User.mobile == fixture["req_user"].mobile))).scalar_one()
    audit_res = await db_session.execute(
        select(AdminAction).where(AdminAction.action == "PROMOTE", AdminAction.target_id == str(db_user.id))
    )
    audit = audit_res.scalar_one_or_none()
    assert audit is not None
    assert audit.admin_id is None
    assert audit.details["actor_type"] == "bootstrap_secret"


@pytest.mark.asyncio
async def test_promote_nonexistent_user_returns_404(client: AsyncClient, admin_mgmt_fixture):
    """Test promoting a nonexistent phone number returns 404."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    payload = {"action": "PROMOTE", "mobile": "9999999999"}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_promote_already_admin_is_idempotent(client: AsyncClient, admin_mgmt_fixture):
    """Test promoting an already-admin user returns safe idempotent response."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    payload = {"action": "PROMOTE", "mobile": fixture["admin1_user"].mobile}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "already an administrator" in data["message"]


# ============================================================================
# 3. DEMOTE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_demote_admin_with_admin_jwt(client: AsyncClient, admin_mgmt_fixture, db_session: AsyncSession):
    """Test admin can demote another admin when >1 admins exist."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    payload = {"action": "DEMOTE", "mobile": fixture["admin2_user"].mobile}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["action"] == "DEMOTE"
    assert data["user"]["role"] == "REQUESTER"

    # Verify DB role
    db_user = (await db_session.execute(select(User).where(User.mobile == fixture["admin2_user"].mobile))).scalar_one()
    assert db_user.role == UserRole.REQUESTER

    # Verify audit log
    audit_res = await db_session.execute(
        select(AdminAction).where(AdminAction.action == "DEMOTE", AdminAction.target_id == str(db_user.id))
    )
    audit = audit_res.scalar_one_or_none()
    assert audit is not None
    assert audit.admin_id == fixture["admin1_user"].id


@pytest.mark.asyncio
async def test_demote_admin_with_donor_profile_restores_donor_role(client: AsyncClient, admin_mgmt_fixture, db_session: AsyncSession):
    """Test demoting an admin who has a DonorProfile restores DONOR role."""
    fixture = admin_mgmt_fixture
    headers = {"X-Admin-Secret": fixture["bootstrap_secret"]}

    # First promote the donor
    await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "PROMOTE", "mobile": fixture["donor_user"].mobile})

    # Now demote the donor
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "DEMOTE", "mobile": fixture["donor_user"].mobile})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "DONOR"


@pytest.mark.asyncio
async def test_last_admin_lockout_protection(client: AsyncClient, admin_mgmt_fixture, db_session: AsyncSession):
    """Test that the last remaining administrator cannot be demoted."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    # Demote admin2 so only admin1 remains
    r1 = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "DEMOTE", "mobile": fixture["admin2_user"].mobile})
    assert r1.status_code == 200

    # Attempt to demote admin1 (last admin) -> must be rejected
    r2 = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "DEMOTE", "mobile": fixture["admin1_user"].mobile})
    assert r2.status_code in (400, 403, 409)
    assert "Cannot demote the last remaining administrator" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_demote_non_admin_is_idempotent(client: AsyncClient, admin_mgmt_fixture):
    """Test demoting a user who is not an admin returns safe idempotent response."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    payload = {"action": "DEMOTE", "mobile": fixture["req_user"].mobile}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "is not an administrator" in data["message"]


# ============================================================================
# 4. LIST TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_admins_with_jwt_and_secret(client: AsyncClient, admin_mgmt_fixture):
    """Test LIST action returns active administrators with safe fields."""
    fixture = admin_mgmt_fixture

    # 1. Via Admin JWT
    headers_jwt = {"Authorization": f"Bearer {fixture['admin1_token']}"}
    r1 = await client.post("/api/v1/admin/manage-admins", headers=headers_jwt, json={"action": "LIST"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["action"] == "LIST"
    assert len(d1["admins"]) >= 2
    admin_mobiles = [a["mobile"] for a in d1["admins"]]
    assert fixture["admin1_user"].mobile in admin_mobiles
    assert fixture["admin2_user"].mobile in admin_mobiles

    # Ensure no sensitive fields like password/hash/secret
    for a in d1["admins"]:
        assert "password" not in a
        assert "hash" not in a
        assert "secret" not in a

    # 2. Via Bootstrap Secret
    headers_secret = {"X-Admin-Secret": fixture["bootstrap_secret"]}
    r2 = await client.post("/api/v1/admin/manage-admins", headers=headers_secret, json={"action": "LIST"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert len(d2["admins"]) >= 2


# ============================================================================
# 5. SECURITY & AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_missing_credentials_rejected(client: AsyncClient):
    """Test manage-admins rejects unauthenticated requests with 401."""
    response = await client.post("/api/v1/admin/manage-admins", json={"action": "LIST"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_bootstrap_secret_rejected(client: AsyncClient):
    """Test manage-admins rejects incorrect X-Admin-Secret with 401."""
    headers = {"X-Admin-Secret": "invalid_random_secret_string"}
    response = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "LIST"})
    assert response.status_code == 401
    assert "Invalid admin bootstrap secret" in response.json()["detail"]


@pytest.mark.asyncio
async def test_non_admin_jwt_rejected(client: AsyncClient, admin_mgmt_fixture):
    """Test non-admin users (Requester / Donor) receive 403 Forbidden."""
    fixture = admin_mgmt_fixture

    # Requester JWT
    r_req = await client.post(
        "/api/v1/admin/manage-admins",
        headers={"Authorization": f"Bearer {fixture['req_token']}"},
        json={"action": "LIST"}
    )
    assert r_req.status_code == 403

    # Donor JWT
    r_donor = await client.post(
        "/api/v1/admin/manage-admins",
        headers={"Authorization": f"Bearer {fixture['donor_token']}"},
        json={"action": "LIST"}
    )
    assert r_donor.status_code == 403


@pytest.mark.asyncio
async def test_bootstrap_secret_cannot_access_general_admin_apis(client: AsyncClient, admin_mgmt_fixture):
    """Test X-Admin-Secret is restricted to manage-admins and cannot access /admin/donors, /admin/statistics."""
    fixture = admin_mgmt_fixture
    headers = {"X-Admin-Secret": fixture["bootstrap_secret"]}

    # /admin/donors
    r1 = await client.get("/api/v1/admin/donors", headers=headers)
    assert r1.status_code in (401, 403)

    # /admin/statistics
    r2 = await client.get("/api/v1/admin/statistics", headers=headers)
    assert r2.status_code in (401, 403)


@pytest.mark.asyncio
async def test_demoted_admin_immediately_blocked_from_admin_apis(client: AsyncClient, admin_mgmt_fixture):
    """Test that a demoted admin's previously issued JWT is immediately rejected for admin operations."""
    fixture = admin_mgmt_fixture

    # Admin 2 can initially access admin stats
    r_before = await client.get("/api/v1/admin/statistics", headers={"Authorization": f"Bearer {fixture['admin2_token']}"})
    assert r_before.status_code == 200

    # Admin 1 demotes Admin 2
    r_demote = await client.post(
        "/api/v1/admin/manage-admins",
        headers={"Authorization": f"Bearer {fixture['admin1_token']}"},
        json={"action": "DEMOTE", "mobile": fixture["admin2_user"].mobile}
    )
    assert r_demote.status_code == 200

    # Admin 2 attempts to use their old token -> must be 403 Forbidden because database role is now checked in real-time
    r_after = await client.get("/api/v1/admin/statistics", headers={"Authorization": f"Bearer {fixture['admin2_token']}"})
    assert r_after.status_code == 403
    assert "Access forbidden" in r_after.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_action_rejected_with_422(client: AsyncClient, admin_mgmt_fixture):
    """Test that invalid action strings are rejected by Pydantic validation."""
    fixture = admin_mgmt_fixture
    headers = {"Authorization": f"Bearer {fixture['admin1_token']}"}

    # Invalid action name
    r1 = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "SUPERADMIN"})
    assert r1.status_code == 422

    # Missing mobile for PROMOTE
    r2 = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "PROMOTE"})
    assert r2.status_code == 422


# ============================================================================
# 6. CONCURRENCY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_demotions_cannot_demote_last_admin(client: AsyncClient, admin_mgmt_fixture):
    """Verify concurrent demotion requests cannot reduce admin count below 1."""
    from app.database.session import get_db
    from app.main import app
    from tests.conftest import TestSessionLocal

    async def per_request_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_db

    fixture = admin_mgmt_fixture
    headers = {"X-Admin-Secret": fixture["bootstrap_secret"]}

    try:
        # Two admins exist: admin1 and admin2
        # Fire simultaneous demote requests for both
        results = await asyncio.gather(
            client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "DEMOTE", "mobile": fixture["admin1_user"].mobile}),
            client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "DEMOTE", "mobile": fixture["admin2_user"].mobile}),
            return_exceptions=True
        )

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        # Exactly one demotion must succeed (200), and the other must fail (400/403/409)
        assert 200 in statuses
        assert any(s in (400, 403, 409) for s in statuses)

        # Check remaining admin count via LIST
        list_res = await client.post("/api/v1/admin/manage-admins", headers=headers, json={"action": "LIST"})
        assert len(list_res.json()["admins"]) == 1
    finally:
        app.dependency_overrides.clear()

