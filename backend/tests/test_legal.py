import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_privacy_policy_endpoint(client: AsyncClient):
    """Test GET /api/v1/privacy-policy and top-level /privacy-policy return valid document structure."""
    # Test api/v1 route
    res = await client.get("/api/v1/privacy-policy")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Privacy Policy"
    assert data["platform_name"] == "BloodConnect"
    assert "summary" in data
    assert len(data["sections"]) > 0
    # Check key privacy commitments
    titles = [s["title"] for s in data["sections"]]
    assert any("Public Directory" in t or "Privacy" in t for t in titles)
    assert any("OTP" in t for t in titles)

    # Test top-level route
    top_res = await client.get("/privacy-policy")
    assert top_res.status_code == 200
    assert top_res.json()["title"] == "Privacy Policy"

    # Test typo alias /privarcy-policy
    alias_res = await client.get("/privarcy-policy")
    assert alias_res.status_code == 200
    assert alias_res.json()["title"] == "Privacy Policy"

    # Test HEAD method
    head_res = await client.head("/privacy-policy")
    assert head_res.status_code == 200


@pytest.mark.asyncio
async def test_terms_of_service_endpoint(client: AsyncClient):
    """Test GET /api/v1/terms and top-level /terms return valid document structure."""
    # Test api/v1 route
    res = await client.get("/api/v1/terms")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Terms of Service"
    assert data["platform_name"] == "BloodConnect"
    assert "summary" in data
    assert len(data["sections"]) > 0
    # Check key terms
    titles = [s["title"] for s in data["sections"]]
    assert any("NOT A BLOOD BANK" in s["content"] or "NOT A BLOOD BANK" in str(s.get("points")) for s in data["sections"])
    assert any("Voluntary" in t or "Ban on Sale" in t for t in titles)

    # Test top-level route
    top_res = await client.get("/terms")
    assert top_res.status_code == 200
    assert top_res.json()["title"] == "Terms of Service"

    # Test HEAD method
    head_res = await client.head("/terms")
    assert head_res.status_code == 200


@pytest.mark.asyncio
async def test_data_deletion_endpoint(client: AsyncClient):
    """Test GET /api/v1/data-deletion and top-level /data-deletion return valid instructions and POST callback works."""
    # Test api/v1 route
    res = await client.get("/api/v1/data-deletion")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "User Data Deletion Instructions"
    assert data["platform_name"] == "BloodConnect"
    assert "summary" in data
    assert len(data["sections"]) > 0

    # Test top-level route
    top_res = await client.get("/data-deletion")
    assert top_res.status_code == 200
    assert top_res.json()["title"] == "User Data Deletion Instructions"

    # Test HEAD method
    head_res = await client.head("/data-deletion")
    assert head_res.status_code == 200

    # Test alias /user-data-deletion
    alias_res = await client.get("/user-data-deletion")
    assert alias_res.status_code == 200

    # Test POST Meta callback
    post_res = await client.post("/data-deletion")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert "url" in post_data
    assert "confirmation_code" in post_data

