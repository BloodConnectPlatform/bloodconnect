import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.core.security import create_verification_token
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RequesterAuthRequest,
    SendOTPRequest,
    SendOTPResponse,
    TokenResponse,
    UserResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    WhatsAppTokenRedeemRequest,
)
from app.services.auth_service import auth_service
from app.services.otp_service import otp_service
from app.services.whatsapp_auth_service import whatsapp_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP to mobile number",
    description="Generates, hashes, and dispatches an OTP to the given mobile number. Enforces cooldown and rate limits.",
    status_code=status.HTTP_200_OK
)
async def send_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await otp_service.send_otp(
        db=db,
        mobile=request.mobile,
        purpose=request.purpose or "LOGIN"
    )
    return result


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Verify OTP",
    description="Validates a submitted OTP for a mobile number and issues a verification token for registration.",
    status_code=status.HTTP_200_OK
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    success, message, _ = await otp_service.verify_otp(
        db=db,
        mobile=request.mobile,
        otp=request.otp
    )

    # Check if this mobile is already registered
    stmt = select(User).where(User.mobile == request.mobile)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    verification_token = create_verification_token(request.mobile)

    return VerifyOTPResponse(
        success=True,
        message=message,
        verification_token=verification_token,
        is_registered=existing_user is not None,
        role=existing_user.role if existing_user else None
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with mobile OTP",
    description="Authenticates an existing user using their verified mobile number and OTP, returning JWT tokens.",
    status_code=status.HTTP_200_OK
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.login_with_otp(
        db=db,
        mobile=request.mobile,
        otp=request.otp
    )


@router.post(
    "/requester-auth",
    response_model=TokenResponse,
    summary="Requester Login or Sign-Up with Name and OTP",
    description="Authenticates or registers a requester using their Full Name and verified Mobile OTP.",
    status_code=status.HTTP_200_OK
)
async def requester_auth(
    request: RequesterAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.authenticate_requester(
        db=db,
        name=request.name,
        mobile=request.mobile,
        otp=request.otp
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generates a new access token and refresh token using a valid refresh token.",
    status_code=status.HTTP_200_OK
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh_tokens(
        db=db,
        refresh_token_str=request.refresh_token
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns identity and role information for the currently authenticated user.",
    status_code=status.HTTP_200_OK
)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        mobile=current_user.mobile,
        role=current_user.role,
        is_active=current_user.is_active,
        has_donor_profile=current_user.donor_profile is not None,
        created_at=current_user.created_at
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Logs out the currently authenticated user session.",
    status_code=status.HTTP_200_OK
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    return LogoutResponse(
        success=True,
        message="User logged out successfully."
    )


@router.get(
    "/whatsapp",
    summary="Redeem WhatsApp Magic Login Token (Browser / API)",
    description="Validates the single-use WhatsApp magic token, creates session, and redirects to dashboard (or returns JSON).",
    response_model=TokenResponse,
    responses={
        200: {"description": "Authenticated session tokens or HTML auto-login redirect."},
        400: {"description": "Invalid or expired login link."},
        429: {"description": "Rate limit exceeded."}
    }
)
async def redeem_whatsapp_token_get(
    request: Request,
    token: str = Query(..., description="WhatsApp single-use login token"),
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    accept_header = request.headers.get("accept", "")
    is_browser_request = "text/html" in accept_header or not ("application/json" in accept_header)

    try:
        token_response, user = await whatsapp_auth_service.redeem_whatsapp_login_token(
            db=db,
            raw_token=token,
            client_ip=client_ip,
            user_agent=user_agent
        )
    except HTTPException as e:
        if not is_browser_request:
            raise e
        # Render clean branded error page for browser clicks
        error_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blood Connect - Login Link Invalid</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
    .card {{ background: white; max-width: 440px; width: 100%; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #e2e8f0; text-align: center; }}
    .header {{ background: #e11d48; color: white; padding: 28px 24px; }}
    .content {{ padding: 32px 24px; }}
    .icon {{ width: 56px; height: 56px; background: #fee2e2; color: #dc2626; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 16px; margin-left: auto; margin-right: auto; }}
    h1 {{ font-size: 20px; font-weight: 800; margin: 0 0 10px; color: #0f172a; }}
    p {{ font-size: 14px; color: #64748b; line-height: 1.6; margin: 0 0 24px; }}
    .btn {{ display: inline-block; background: #dc2626; color: white; text-decoration: none; font-weight: 700; font-size: 14px; padding: 12px 24px; border-radius: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2 style="margin:0; font-size: 20px;">Blood Connect</h2>
    </div>
    <div class="content">
      <div class="icon">&#9888;</div>
      <h1>Login Link Invalid or Expired</h1>
      <p>This login link is invalid or has expired. Please request a new login link through WhatsApp.</p>
      <a href="/" class="btn">Return to Home</a>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=error_html, status_code=e.status_code)

    if not is_browser_request:
        return token_response

    # Determine destination dashboard
    target_path = "/requester/dashboard"
    if user.role == UserRole.ADMIN:
        target_path = "/admin"
    elif user.role == UserRole.DONOR:
        target_path = "/donor/dashboard"

    frontend_base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")

    # Check if backend and frontend are on the same origin
    import urllib.parse
    backend_origin = urllib.parse.urlparse(str(request.url)).netloc
    frontend_origin = urllib.parse.urlparse(frontend_base).netloc
    same_origin = backend_origin == frontend_origin

    if same_origin:
        # Same origin: safe to set localStorage directly and redirect
        target_url = f"{frontend_base}{target_path}"
        user_dict_json = json.dumps(token_response.user.model_dump(mode="json"))
        access_token_json = json.dumps(token_response.access_token)
        refresh_token_json = json.dumps(token_response.refresh_token)
        target_url_json = json.dumps(target_url)

        auto_login_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blood Connect - Signing in...</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
    .card {{ background: white; max-width: 440px; width: 100%; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 40px 24px; text-align: center; border: 1px solid #e2e8f0; }}
    .spinner {{ border: 4px solid #f3f4f6; border-top: 4px solid #dc2626; border-radius: 50%; width: 44px; height: 44px; animation: spin 0.8s linear infinite; margin: 0 auto 20px; }}
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    h1 {{ font-size: 20px; font-weight: 800; color: #0f172a; margin: 0 0 8px; }}
    p {{ font-size: 14px; color: #64748b; margin: 0; }}
  </style>
  <script>
    try {{
      localStorage.setItem('access_token', {access_token_json});
      localStorage.setItem('refresh_token', {refresh_token_json});
      localStorage.setItem('bloodconnect_user', {user_dict_json});
    }} catch (e) {{
      console.error("Storage error:", e);
    }}
    window.location.replace({target_url_json});
  </script>
</head>
<body>
  <div class="card">
    <div class="spinner"></div>
    <h1>Signing in to Blood Connect...</h1>
    <p>Redirecting you to your dashboard.</p>
    <p style="margin-top: 16px; font-size: 12px;"><a href="{target_url}" style="color: #dc2626; font-weight: bold; text-decoration: none;">Click here if not redirected automatically &rarr;</a></p>
  </div>
</body>
</html>"""
        return HTMLResponse(content=auto_login_html, status_code=status.HTTP_200_OK)
    else:
        # Cross-origin: pass tokens via URL hash fragment to the frontend callback page
        # Hash fragments are never sent to the server, keeping tokens secure
        import base64
        auth_payload = json.dumps({
            "access_token": token_response.access_token,
            "refresh_token": token_response.refresh_token,
            "user": token_response.user.model_dump(mode="json"),
            "redirect": target_path,
        })
        encoded_payload = base64.urlsafe_b64encode(auth_payload.encode()).decode()
        callback_url = f"{frontend_base}/auth/whatsapp/callback#{encoded_payload}"

        redirect_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blood Connect - Signing in...</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
    .card {{ background: white; max-width: 440px; width: 100%; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 40px 24px; text-align: center; border: 1px solid #e2e8f0; }}
    .spinner {{ border: 4px solid #f3f4f6; border-top: 4px solid #dc2626; border-radius: 50%; width: 44px; height: 44px; animation: spin 0.8s linear infinite; margin: 0 auto 20px; }}
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    h1 {{ font-size: 20px; font-weight: 800; color: #0f172a; margin: 0 0 8px; }}
    p {{ font-size: 14px; color: #64748b; margin: 0; }}
  </style>
  <script>
    window.location.replace("{callback_url}");
  </script>
</head>
<body>
  <div class="card">
    <div class="spinner"></div>
    <h1>Signing in to Blood Connect...</h1>
    <p>Redirecting you securely...</p>
    <p style="margin-top: 16px; font-size: 12px;"><a href="{callback_url}" style="color: #dc2626; font-weight: bold; text-decoration: none;">Click here if not redirected automatically &rarr;</a></p>
  </div>
</body>
</html>"""
        return HTMLResponse(content=redirect_html, status_code=status.HTTP_200_OK)


@router.post(
    "/whatsapp/redeem",
    response_model=TokenResponse,
    summary="Redeem WhatsApp Magic Login Token (JSON POST)",
    description="Redeems a single-use WhatsApp magic token programmatically, returning JWT tokens and user payload.",
    status_code=status.HTTP_200_OK
)
async def redeem_whatsapp_token_post(
    request: Request,
    payload: WhatsAppTokenRedeemRequest,
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    token_response, _ = await whatsapp_auth_service.redeem_whatsapp_login_token(
        db=db,
        raw_token=payload.token,
        client_ip=client_ip,
        user_agent=user_agent
    )
    return token_response


@router.get(
    "/whatsapp/config",
    summary="Get WhatsApp fast login configuration",
    description="Returns the configured WhatsApp Business phone number and wa.me redirect URL."
)
async def get_whatsapp_config():
    phone = (settings.WHATSAPP_NUMBER or settings.WHATSAPP_BUSINESS_PHONE_NUMBER or "919843883304").strip().replace(" ", "").replace("-", "").replace("+", "")
    return {
        "whatsapp_phone_number": phone,
        "login_url": f"https://wa.me/{phone}?text=LOGIN"
    }

