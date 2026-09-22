from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional, Tuple
import uuid
from fastapi import HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    generate_whatsapp_login_token,
    hash_whatsapp_token,
)
from app.models.enums import UserRole
from app.models.user import User
from app.models.whatsapp_login_token import WhatsAppLoginToken
from app.schemas.auth import TokenResponse, UserResponse
from app.services.whatsapp_service import ProviderSendResult, get_whatsapp_provider

logger = logging.getLogger("whatsapp_auth_service")


def mask_phone_number(mobile: str) -> str:
    """Mask mobile number for safe audit logging (e.g. '98****3201')."""
    cleaned = mobile.strip()
    if len(cleaned) <= 4:
        return "****"
    return f"{cleaned[:2]}****{cleaned[-4:]}"


def normalize_mobile(mobile: str) -> str:
    """Normalize phone number to 10-digit Indian format (e.g. '919876543210' -> '9876543210')."""
    cleaned = mobile.strip().replace(" ", "").replace("-", "").replace("+", "")
    if len(cleaned) == 12 and cleaned.startswith("91") and cleaned[2] in "6789":
        return cleaned[2:]
    return cleaned


class WhatsAppAuthService:
    def __init__(self):
        # In-memory IP rate limiting tracker for redemption attempts: {ip: [timestamps]}
        self._ip_redemption_attempts: Dict[str, list] = {}

    def _check_ip_rate_limit(self, client_ip: Optional[str], max_attempts: int = 20, window_seconds: int = 60) -> bool:
        """Check if client IP exceeded allowed redemption attempts in window."""
        if not client_ip:
            return True
        now = datetime.now(timezone.utc).timestamp()
        attempts = self._ip_redemption_attempts.get(client_ip, [])
        # Filter timestamps within window
        valid_attempts = [ts for ts in attempts if now - ts < window_seconds]
        if len(valid_attempts) >= max_attempts:
            return False
        valid_attempts.append(now)
        self._ip_redemption_attempts[client_ip] = valid_attempts
        return True

    def clear_ip_rate_limits(self) -> None:
        """Clear recorded IP rate limit timestamps (useful for tests)."""
        self._ip_redemption_attempts.clear()

    def _resolve_public_base_url(self, request: Optional[Request] = None) -> str:
        """
        Determine the public base URL for links sent in WhatsApp.
        Prioritizes explicit config, then incoming tunnel/proxy headers, then FRONTEND_URL.
        """
        if settings.WHATSAPP_MAGIC_LINK_BASE_URL and settings.WHATSAPP_MAGIC_LINK_BASE_URL.strip():
            return settings.WHATSAPP_MAGIC_LINK_BASE_URL.strip().rstrip("/")
        if settings.FRONTEND_URL and "localhost" not in settings.FRONTEND_URL and "127.0.0.1" not in settings.FRONTEND_URL:
            return settings.FRONTEND_URL.strip().rstrip("/")
        if request:
            forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
            forwarded_proto = request.headers.get("x-forwarded-proto") or "https"
            if forwarded_host and "localhost" not in forwarded_host and "127.0.0.1" not in forwarded_host:
                host_val = forwarded_host.split(",")[0].strip()
                if host_val.startswith("api."):
                    host_val = "www." + host_val[4:]
                return f"{forwarded_proto}://{host_val}".rstrip("/")
        return (settings.FRONTEND_URL or settings.PUBLIC_API_URL or "http://localhost:3000").rstrip("/")

    async def handle_login_request(
        self,
        db: AsyncSession,
        sender_mobile: str,
        raw_message: Optional[dict] = None,
        command: str = "LOGIN",
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming 'LOGIN' or 'REGISTER' command from WhatsApp webhook.
        Validates sender, checks rate limits, creates token, and dispatches magic or registration link.
        """
        norm_mobile = normalize_mobile(sender_mobile)
        masked = mask_phone_number(norm_mobile)
        logger.info(f"[WhatsAppAuthService] Processing WhatsApp {command} request for {masked}")

        # 1. Lookup User by phone variants
        phone_variants = {
            norm_mobile,
            sender_mobile,
            f"+91{norm_mobile}",
            f"91{norm_mobile}",
            f"+{sender_mobile}",
            norm_mobile[-10:] if len(norm_mobile) >= 10 else norm_mobile
        }
        stmt = (
            select(User)
            .options(selectinload(User.donor_profile))
            .where(User.mobile.in_(phone_variants))
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # Auto-provision / upgrade admin if mobile is in INITIAL_ADMIN_PHONE_NUMBERS
        initial_admins = settings.INITIAL_ADMIN_PHONE_NUMBERS or []
        if isinstance(initial_admins, str):
            initial_admins = [p.strip() for p in initial_admins.split(",") if p.strip()]

        is_admin_configured = any(
            normalize_mobile(str(admin_p)) == norm_mobile
            or str(admin_p) in phone_variants
            or (len(str(admin_p).replace("+", "")) >= 10 and str(admin_p).replace("+", "")[-10:] == norm_mobile[-10:])
            for admin_p in initial_admins
        )

        if is_admin_configured:
            if not user:
                logger.info(f"[WhatsAppAuthService] Mobile {masked} is configured in INITIAL_ADMIN_PHONE_NUMBERS. Auto-provisioning admin user.")
                user = User(
                    name="System Administrator",
                    mobile=norm_mobile,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            elif user.role != UserRole.ADMIN:
                logger.info(f"[WhatsAppAuthService] Upgrading user {masked} to ADMIN based on INITIAL_ADMIN_PHONE_NUMBERS.")
                user.role = UserRole.ADMIN
                user.is_active = True
                await db.commit()
                await db.refresh(user)

        # 2. Case: Unregistered User -> Provide 1-Click Pre-verified Registration Link
        if not user:
            logger.info(f"[WhatsAppAuthService] No account found for mobile {masked}. Generating pre-verified registration link.")
            verification_token = create_verification_token(norm_mobile, expires_delta=timedelta(hours=1))
            base_url = self._resolve_public_base_url(request)
            reg_url = f"{base_url}/register?mobile={norm_mobile}&token={verification_token}"

            reply_res = await self.send_unregistered_reply(to_mobile=sender_mobile, reg_url=reg_url)
            if not reply_res.success:
                logger.error(f"[WhatsAppAuthService] Failed to send unregistered reply to {masked}: {reply_res.error_message}")
            return {
                "status": "unregistered",
                "message": "User not registered, sent registration link with pre-verified token.",
                "provider_result": reply_res.success,
                "registration_url": reg_url
            }

        # 3. Case: Deactivated User
        if not user.is_active:
            logger.warning(f"[WhatsAppAuthService] Account for mobile {masked} is deactivated.")
            reply_res = await self.send_deactivated_reply(to_mobile=sender_mobile)
            if not reply_res.success:
                logger.error(f"[WhatsAppAuthService] Failed to send deactivated reply to {masked}: {reply_res.error_message}")
            return {
                "status": "deactivated",
                "message": "User deactivated, sent contact support reply.",
                "provider_result": reply_res.success
            }

        # 4. Rate Limiting & Cooldown Protection
        now = datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(seconds=settings.WHATSAPP_LOGIN_COOLDOWN_SECONDS)

        # Check most recent token request
        recent_stmt = (
            select(WhatsAppLoginToken)
            .where(
                WhatsAppLoginToken.whatsapp_phone == norm_mobile,
                WhatsAppLoginToken.created_at >= cooldown_threshold
            )
            .order_by(WhatsAppLoginToken.created_at.desc())
            .limit(1)
        )
        recent_res = await db.execute(recent_stmt)
        recent_token = recent_res.scalar_one_or_none()

        if recent_token:
            logger.info(f"[WhatsAppAuthService] Rate limit hit for {masked}: Cooldown active.")
            reply_res = await self.send_rate_limited_reply(to_mobile=sender_mobile)
            if not reply_res.success:
                logger.error(f"[WhatsAppAuthService] Failed to send rate-limited reply to {masked}: {reply_res.error_message}")
            return {
                "status": "rate_limited",
                "message": "Login request within cooldown window, sent notice.",
                "provider_result": reply_res.success
            }

        # Check window limit (max requests in 15 mins)
        window_threshold = now - timedelta(minutes=15)
        window_stmt = (
            select(WhatsAppLoginToken)
            .where(
                WhatsAppLoginToken.whatsapp_phone == norm_mobile,
                WhatsAppLoginToken.created_at >= window_threshold
            )
        )
        window_res = await db.execute(window_stmt)
        window_count = len(window_res.scalars().all())

        if window_count >= settings.WHATSAPP_LOGIN_MAX_REQUESTS_WINDOW:
            logger.warning(f"[WhatsAppAuthService] Rate limit hit for {masked}: Max window attempts exceeded.")
            reply_res = await self.send_rate_limited_reply(to_mobile=sender_mobile)
            if not reply_res.success:
                logger.error(f"[WhatsAppAuthService] Failed to send rate-limited reply to {masked}: {reply_res.error_message}")
            return {
                "status": "rate_limited",
                "message": "Exceeded maximum login requests in window, sent notice.",
                "provider_result": reply_res.success
            }

        # 5. Generate and store token
        msg_id = raw_message.get("id") if raw_message else None
        req_meta = {
            "webhook_msg_id": msg_id,
            "timestamp": now.isoformat()
        }
        raw_token, token_record = await self.create_whatsapp_login_token(
            db=db,
            user=user,
            whatsapp_phone=norm_mobile,
            request_metadata=req_meta
        )

        # 6. Construct HTTPS Magic Link URL
        base_url = self._resolve_public_base_url(request)
        magic_url = f"{base_url.rstrip('/')}/auth/whatsapp?token={raw_token}"

        # 7. Dispatch message via WhatsApp
        if command == "REGISTER":
            send_result = await self.send_already_registered_reply(
                to_mobile=sender_mobile,
                magic_url=magic_url
            )
        else:
            send_result = await self.send_whatsapp_login_link(
                to_mobile=sender_mobile,
                magic_url=magic_url
            )

        if not send_result.success:
            logger.error(
                f"[WhatsAppAuthService] FAILED to deliver login link to {masked}: "
                f"error='{send_result.error_message}' (provider={send_result.provider})"
            )
            return {
                "status": "delivery_failed",
                "provider_result": False,
                "error_message": send_result.error_message
            }

        logger.info(f"[WhatsAppAuthService] Dispatched magic login link to {masked} (User ID: {user.id})")
        return {
            "status": "login_link_sent",
            "provider_result": True
        }

    async def create_whatsapp_login_token(
        self,
        db: AsyncSession,
        user: User,
        whatsapp_phone: str,
        request_metadata: Optional[dict] = None
    ) -> Tuple[str, WhatsAppLoginToken]:
        """
        Generate a cryptographically secure token, store only its HMAC-SHA256 hash in DB,
        and return the raw token and model record.
        """
        raw_token = generate_whatsapp_login_token()
        token_hash = hash_whatsapp_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.WHATSAPP_LOGIN_TOKEN_EXPIRE_MINUTES)

        token_record = WhatsAppLoginToken(
            id=uuid.uuid4(),
            user_id=user.id,
            whatsapp_phone=whatsapp_phone,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            used_at=None,
            request_metadata=request_metadata
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(token_record)

        return raw_token, token_record

    async def send_whatsapp_login_link(
        self,
        to_mobile: str,
        magic_url: str
    ) -> ProviderSendResult:
        """Send normal reply message with secure magic link over WhatsApp Cloud API."""
        provider = get_whatsapp_provider()
        message = (
            "Blood Connect Login\n\n"
            "We received your login request.\n\n"
            "Click the link below to securely continue to Blood Connect:\n"
            f"{magic_url}\n\n"
            "This link expires in 5 minutes and can only be used once.\n\n"
            "If you did not request this link, you can safely ignore this message."
        )
        return await provider.send_text(to_mobile=to_mobile, text=message)

    async def send_unregistered_reply(
        self,
        to_mobile: str,
        reg_url: Optional[str] = None
    ) -> ProviderSendResult:
        """Reply to unregistered WhatsApp phone number, providing 1-click registration link."""
        provider = get_whatsapp_provider()
        if reg_url:
            message = (
                "Blood Connect Registration\n\n"
                "We couldn't find a Blood Connect account linked to this WhatsApp number. Please register first.\n\n"
                "Your WhatsApp number is already verified! Tap the link below to complete your registration in 30 seconds:\n"
                f"{reg_url}\n\n"
                "This registration link is valid for 1 hour."
            )
        else:
            message = (
                "Blood Connect\n\n"
                "We couldn't find a Blood Connect account linked to this WhatsApp number. Please register first."
            )
        return await provider.send_text(to_mobile=to_mobile, text=message)

    async def send_already_registered_reply(
        self,
        to_mobile: str,
        magic_url: str
    ) -> ProviderSendResult:
        """Reply to registered user who sent REGISTER, providing instant login link."""
        provider = get_whatsapp_provider()
        message = (
            "Blood Connect\n\n"
            "You already have an active Blood Connect account linked to this WhatsApp number!\n\n"
            "Click below to securely sign in to your dashboard:\n"
            f"{magic_url}\n\n"
            "This link expires in 5 minutes."
        )
        return await provider.send_text(to_mobile=to_mobile, text=message)

    async def send_deactivated_reply(self, to_mobile: str) -> ProviderSendResult:
        """Reply to deactivated account."""
        provider = get_whatsapp_provider()
        message = (
            "Blood Connect\n\n"
            "Your Blood Connect account has been deactivated. Please contact support."
        )
        return await provider.send_text(to_mobile=to_mobile, text=message)

    async def send_rate_limited_reply(self, to_mobile: str) -> ProviderSendResult:
        """Reply when repeated login requests are received within cooldown."""
        provider = get_whatsapp_provider()
        message = (
            "Blood Connect Login\n\n"
            "A login link was recently sent to this WhatsApp number. "
            "Please check your previous messages or wait a minute before requesting another."
        )
        return await provider.send_text(to_mobile=to_mobile, text=message)

    async def redeem_whatsapp_login_token(
        self,
        db: AsyncSession,
        raw_token: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[TokenResponse, User]:
        """
        Atomically validate and redeem a WhatsApp magic login token.
        Guarantees single-use and prevents concurrent double-redemptions.
        """
        generic_error = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This login link is invalid or has expired. Please request a new login link through WhatsApp."
        )

        # 1. Basic format validation
        if not raw_token or len(raw_token.strip()) < 16:
            logger.warning("[WhatsAppAuthService] Attempt to redeem malformed or empty token.")
            raise generic_error

        # 2. IP Rate limiting check
        if not self._check_ip_rate_limit(client_ip):
            logger.warning(f"[WhatsAppAuthService] Rate limit exceeded for IP {client_ip} on token redemption.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many redemption attempts. Please wait a moment and try again."
            )

        # 3. Compute deterministic hash
        token_hash = hash_whatsapp_token(raw_token.strip())
        now = datetime.now(timezone.utc)

        # 4. Atomic conditional update: used_at = now WHERE token_hash = hash AND used_at IS NULL AND expires_at > now
        stmt = (
            update(WhatsAppLoginToken)
            .where(
                WhatsAppLoginToken.token_hash == token_hash,
                WhatsAppLoginToken.used_at.is_(None),
                WhatsAppLoginToken.expires_at > now
            )
            .values(
                used_at=now,
                redeemed_ip=client_ip,
                redeemed_user_agent=user_agent
            )
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(stmt)
        await db.commit()

        # If 0 rows updated: Token does not exist, was already used, or is expired.
        if result.rowcount == 0:
            logger.warning("[WhatsAppAuthService] Atomic token redemption failed (invalid, expired, or already used).")
            raise generic_error

        # 5. Fetch associated User
        token_stmt = (
            select(WhatsAppLoginToken)
            .options(selectinload(WhatsAppLoginToken.user).selectinload(User.donor_profile))
            .where(WhatsAppLoginToken.token_hash == token_hash)
        )
        token_res = await db.execute(token_stmt)
        token_record = token_res.scalar_one_or_none()

        if not token_record or not token_record.user:
            logger.error("[WhatsAppAuthService] Token record found but user missing.")
            raise generic_error

        user = token_record.user

        if not user.is_active:
            logger.warning(f"[WhatsAppAuthService] User {user.id} account is deactivated upon token redemption.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support."
            )

        # 6. Issue standard JWT session tokens
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        token_payload = {
            "sub": str(user.id),
            "mobile": user.mobile,
            "role": role_val
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        has_donor = user.donor_profile is not None

        user_response = UserResponse(
            id=user.id,
            name=user.name,
            mobile=user.mobile,
            role=user.role if isinstance(user.role, UserRole) else UserRole(user.role),
            is_active=user.is_active,
            has_donor_profile=has_donor,
            created_at=user.created_at
        )

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response
        )

        logger.info(f"[WhatsAppAuthService] Successfully redeemed WhatsApp login token for user {user.id}")
        return token_response, user


whatsapp_auth_service = WhatsAppAuthService()
