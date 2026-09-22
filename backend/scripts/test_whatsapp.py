#!/usr/bin/env python3
"""
BloodConnect — WhatsApp Meta Cloud API Integration Diagnostic Tool.

Tests WhatsApp Cloud API configuration by sending a pre-approved template message
(e.g., 'hello_world') to a specified recipient without exposing secret tokens.

Usage:
    python scripts/test_whatsapp.py --mobile 9876543210
    python scripts/test_whatsapp.py --mobile 9876543210 --template hello_world --lang en_US
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.whatsapp_service import MetaWhatsAppProvider, normalize_recipient_mobile


def mask_token(token: str) -> str:
    """Mask sensitive token string for safe diagnostic output."""
    if not token or not token.strip():
        return "[NOT SET]"
    t = token.strip()
    if len(t) <= 8:
        return "****"
    return f"{t[:4]}...{t[-4:]} (len={len(t)})"


def mask_id(val: str) -> str:
    """Mask ID string for safe output."""
    if not val or not val.strip():
        return "[NOT SET]"
    v = val.strip()
    if len(v) <= 6:
        return "****"
    return f"{v[:3]}...{v[-3:]} (len={len(v)})"


async def run_diagnostic(recipient: str, template: str, language: str):
    print("=" * 70)
    print("  BLOODCONNECT — WHATSAPP META CLOUD API DIAGNOSTIC TEST")
    print("=" * 70)

    # 1. Environment & Configuration Check
    print("\n[*] CONFIGURATION AUDIT:")
    print(f"  - ENVIRONMENT:                    {settings.ENVIRONMENT}")
    print(f"  - NOTIFICATION_PROVIDER:          {settings.NOTIFICATION_PROVIDER}")
    print(f"  - WHATSAPP_PROVIDER:              {settings.WHATSAPP_PROVIDER}")
    print(f"  - META_GRAPH_API_VERSION:         {settings.META_GRAPH_API_VERSION}")
    print(f"  - META_WA_PHONE_NUMBER_ID:        {mask_id(settings.META_WA_PHONE_NUMBER_ID)}")
    print(f"  - META_WA_BUSINESS_ACCOUNT_ID:    {mask_id(settings.META_WA_BUSINESS_ACCOUNT_ID)}")
    print(f"  - META_WA_ACCESS_TOKEN:           {mask_token(settings.META_WA_ACCESS_TOKEN)}")
    print(f"  - WHATSAPP_WEBHOOK_VERIFY_TOKEN:  {mask_token(settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN)}")

    # 2. Validation
    has_token = bool(settings.META_WA_ACCESS_TOKEN and settings.META_WA_ACCESS_TOKEN.strip())
    has_phone = bool(settings.META_WA_PHONE_NUMBER_ID and settings.META_WA_PHONE_NUMBER_ID.strip())

    if not has_token or not has_phone:
        print("\n[!] ERROR: Missing required Meta Cloud API credentials in environment!")
        if not has_token:
            print("    -> META_WA_ACCESS_TOKEN is not configured.")
        if not has_phone:
            print("    -> META_WA_PHONE_NUMBER_ID is not configured.")
        sys.exit(1)

    # 3. Recipient Normalization
    normalized = normalize_recipient_mobile(recipient)
    masked_recipient = f"+{normalized[:2]} {normalized[2:4]}******{normalized[-2:]}"
    print(f"\n[*] TARGET RECIPIENT:")
    print(f"  - Input Mobile:                   {recipient}")
    print(f"  - Normalized (WhatsApp format):   {normalized} ({masked_recipient})")
    print(f"  - Template:                       {template} ({language})")

    # 4. Dispatch Test via Meta Provider
    print(f"\n[*] DISPATCHING TEMPLATE MESSAGE...")
    components = None
    if template in [settings.WHATSAPP_TEMPLATE_BLOOD_REQUEST, "bloodconnect_blood_request"]:
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "O+"},
                    {"type": "text", "text": "Coimbatore"},
                    {"type": "text", "text": "KG Hospital"},
                    {"type": "text", "text": "Emergency Patient"}
                ]
            },
            {
                "type": "button",
                "sub_type": "quick_reply",
                "index": "0",
                "parameters": [{"type": "payload", "payload": "ACCEPT:test"}]
            },
            {
                "type": "button",
                "sub_type": "quick_reply",
                "index": "1",
                "parameters": [{"type": "payload", "payload": "REJECT:test"}]
            }
        ]
    elif template in [settings.WHATSAPP_TEMPLATE_AUTH_OTP, "bloodconnect_auth_otp"]:
        components = [{"type": "body", "parameters": [{"type": "text", "text": "123456"}]}]
    elif template in [settings.WHATSAPP_TEMPLATE_REQUEST_ACCEPTED, "bloodconnect_request_accepted"]:
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Arun Kumar"},
                    {"type": "text", "text": "O+"},
                    {"type": "text", "text": "+91 9876543201"}
                ]
            }
        ]
    elif template in [settings.WHATSAPP_TEMPLATE_REQUEST_REJECTED, "bloodconnect_request_rejected"]:
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Rahul Sharma"},
                    {"type": "text", "text": "A+"}
                ]
            }
        ]

    provider = MetaWhatsAppProvider()
    result = await provider.send_template(
        to_mobile=recipient,
        template_name=template,
        language_code=language,
        components=components
    )
    if not result.success and components and len(components) > 1 and result.error_message and ("components" in result.error_message.lower() or "button" in result.error_message.lower()):
        retry_res = await provider.send_template(
            to_mobile=recipient,
            template_name=template,
            language_code=language,
            components=[components[0]]
        )
        if retry_res.success:
            result = retry_res

    print("\n" + "=" * 70)
    print("  RESULT SUMMARY")
    print("=" * 70)
    if result.success:
        print(f"  [+] SUCCESS: Template message '{template}' accepted by Meta Cloud API!")
        print(f"  [+] Message ID:  {result.provider_message_id}")
        print(f"  [+] Provider:    {result.provider}")
        if result.details:
            print(f"  [+] Meta Details: {result.details}")
    else:
        print(f"  [-] FAILED: Meta Cloud API returned an error.")
        print(f"  [-] Error Message: {result.error_message}")
        if result.details:
            print(f"  [-] Details: {result.details}")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Test Meta WhatsApp Cloud API integration.")
    parser.add_argument(
        "--mobile",
        required=True,
        help="Recipient mobile number (10 digits Indian, e.g. 9876543210 or +919876543210)"
    )
    parser.add_argument(
        "--template",
        default="hello_world",
        help="Meta template name (default: hello_world)"
    )
    parser.add_argument(
        "--lang",
        default=settings.WHATSAPP_TEMPLATE_LANGUAGE or "en",
        help="Template language code (default: from settings or en)"
    )

    args = parser.parse_args()
    asyncio.run(run_diagnostic(args.mobile, args.template, args.lang))


if __name__ == "__main__":
    main()
