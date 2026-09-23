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

TEMPLATES_CATALOG = {
    "bloodconnect_blood_request": {
        "description": "Urgent Blood Donation Request to Matching Donor",
        "lang": "en",
        "components": [
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
    },
    "bloodconnect_request_accepted": {
        "description": "Donation Accepted Notification to Requester",
        "lang": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Arun Kumar"},
                    {"type": "text", "text": "O+"},
                    {"type": "text", "text": "+91 9876543201"}
                ]
            }
        ]
    },
    "bloodconnect_request_rejected": {
        "description": "Donation Declined Notification to Requester",
        "lang": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Rahul Sharma"},
                    {"type": "text", "text": "A+"}
                ]
            }
        ]
    },
    "bloodconnect_request_cancelled": {
        "description": "Request Cancelled Notification to Donor",
        "lang": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "B+"},
                    {"type": "text", "text": "Ravi Kumar"},
                    {"type": "text", "text": "Priya Sharma"}
                ]
            }
        ]
    },
    "bloodconnect_request_reminder": {
        "description": "Pending Request Reminder Notification to Donor",
        "lang": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "O-"},
                    {"type": "text", "text": "Kavitha"},
                    {"type": "text", "text": "Coimbatore"}
                ]
            }
        ]
    },
    "bloodconnect_auth_otp": {
        "description": "Login/Registration Verification OTP",
        "lang": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "492815"}
                ]
            }
        ]
    },
    "hello_world": {
        "description": "Meta Hello World Sample Template",
        "lang": "en_US",
        "components": None
    }
}


async def execute_template_test(provider: MetaWhatsAppProvider, recipient: str, template: str, language: str) -> bool:
    config = TEMPLATES_CATALOG.get(template, {})
    components = config.get("components")
    lang_code = language or config.get("lang") or settings.WHATSAPP_TEMPLATE_LANGUAGE or "en"
    desc = config.get("description", "WhatsApp Template")

    print(f"\n[*] Dispatching '{template}' ({desc})...")
    result = await provider.send_template(
        to_mobile=recipient,
        template_name=template,
        language_code=lang_code,
        components=components
    )
    if not result.success and components and len(components) > 1 and result.error_message and ("components" in result.error_message.lower() or "button" in result.error_message.lower()):
        retry_res = await provider.send_template(
            to_mobile=recipient,
            template_name=template,
            language_code=lang_code,
            components=[components[0]]
        )
        if retry_res.success:
            result = retry_res

    if result.success:
        print(f"  [+] SUCCESS: Accepted by Meta Cloud API!")
        print(f"  [+] Message ID:  {result.provider_message_id}")
        return True
    else:
        print(f"  [-] FAILED: Meta API Error: {result.error_message}")
        if result.details:
            print(f"  [-] Details: {result.details}")
        return False


async def run_diagnostic(recipient: str, template: str, language: str, test_all: bool = False):
    print("=" * 70)
    print("  BLOODCONNECT — WHATSAPP META CLOUD API DIAGNOSTIC TEST")
    print("=" * 70)

    # 1. Environment & Configuration Check
    print("\n[*] CONFIGURATION AUDIT:")
    print(f"  - ENVIRONMENT:                    {settings.ENVIRONMENT}")
    print(f"  - NOTIFICATION_PROVIDER:          {settings.NOTIFICATION_PROVIDER}")
    print(f"  - WHATSAPP_PROVIDER:              {settings.WHATSAPP_PROVIDER}")
    print(f"  - DEFAULT_TEMPLATE_LANGUAGE:      {settings.WHATSAPP_TEMPLATE_LANGUAGE}")
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
        sys.exit(1)

    # 3. Recipient Normalization
    normalized = normalize_recipient_mobile(recipient)
    masked_recipient = f"+{normalized[:2]} {normalized[2:4]}******{normalized[-2:]}"
    print(f"\n[*] TARGET RECIPIENT:")
    print(f"  - Input Mobile:                   {recipient}")
    print(f"  - Normalized (WhatsApp format):   {normalized} ({masked_recipient})")

    provider = MetaWhatsAppProvider()

    if test_all:
        approved_templates = [
            "bloodconnect_blood_request",
            "bloodconnect_request_accepted",
            "bloodconnect_request_rejected",
            "bloodconnect_request_cancelled",
            "bloodconnect_request_reminder",
        ]
        print(f"\n[*] Testing all {len(approved_templates)} core BloodConnect templates...")
        results = {}
        for t_name in approved_templates:
            ok = await execute_template_test(provider, recipient, t_name, language)
            results[t_name] = ok

        print("\n" + "=" * 70)
        print("  BATCH TEST SUMMARY")
        print("=" * 70)
        for t_name, ok in results.items():
            status_str = "[PASS]" if ok else "[FAIL]"
            print(f"  {status_str} {t_name}")
    else:
        ok = await execute_template_test(provider, recipient, template, language)
        if not ok:
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
        default="bloodconnect_blood_request",
        help="Meta template name (default: bloodconnect_blood_request)"
    )
    parser.add_argument(
        "--lang",
        default="",
        help="Template language code (default: auto from catalog or config)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all 5 approved BloodConnect templates in batch"
    )

    args = parser.parse_args()
    asyncio.run(run_diagnostic(args.mobile, args.template, args.lang, test_all=args.all))


if __name__ == "__main__":
    main()

