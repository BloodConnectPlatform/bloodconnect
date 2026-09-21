import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.webhook_service import webhook_service

logger = logging.getLogger("webhooks_api")

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get(
    "/whatsapp",
    summary="Meta WhatsApp Webhook Verification",
    description="Validates the hub.verify_token sent by Meta and returns hub.challenge to complete webhook registration.",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK
)
async def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    # Fallbacks for non-dot parameter passing
    mode: Optional[str] = Query(None),
    verify_token: Optional[str] = Query(None),
    challenge: Optional[str] = Query(None),
):
    selected_mode = hub_mode or mode
    selected_token = hub_verify_token or verify_token
    selected_challenge = hub_challenge or challenge

    challenge_response = webhook_service.verify_challenge(
        mode=selected_mode,
        verify_token=selected_token,
        challenge=selected_challenge
    )
    return PlainTextResponse(content=str(challenge_response), status_code=status.HTTP_200_OK)


@router.post(
    "/whatsapp",
    summary="Meta WhatsApp Webhook Event Receiver",
    description="Receives incoming WhatsApp webhook notifications (messages, interactive button replies, delivery statuses).",
    status_code=status.HTTP_200_OK
)
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db)
):
    raw_body = await request.body()
    
    # 1. Verify HMAC-SHA256 Signature
    webhook_service.verify_signature(raw_body=raw_body, signature_header=x_hub_signature_256)

    # 2. Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception as e:
        logger.warning(f"[WebhooksAPI] Malformed JSON payload received: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON in webhook request body."
        )

    # 3. Process Events
    result = await webhook_service.process_event_payload(db=db, payload=payload)

    return {"status": "EVENT_RECEIVED", "details": result}
