from fastapi import APIRouter
from app.schemas.legal import LegalDocumentResponse, LegalSection

router = APIRouter(tags=["Legal & Compliance"])

PRIVACY_POLICY_DATA = LegalDocumentResponse(
    title="Privacy Policy",
    last_updated="September 2026",
    platform_name="BloodConnect",
    summary=(
        "BloodConnect is a non-profit, community-driven voluntary blood donor discovery platform operating across Coimbatore and surrounding regions. "
        "We are committed to strict personal privacy: donor phone numbers are never published in public search directories, and contact numbers are exchanged "
        "only when a donor explicitly accepts an emergency blood request."
    ),
    sections=[
        LegalSection(
            title="1. Scope & Core Privacy Commitment",
            content=(
                "This Privacy Policy describes how BloodConnect collects, uses, and safeguards personal data when voluntary donors and requesters use our platform. "
                "BloodConnect operates strictly as an intermediary communication directory to connect voluntary blood donors with patients in medical emergencies. "
                "We respect individual privacy, enforce role-based data isolation, and never monetize, sell, or rent personal information to any third party."
            ),
            points=[
                "Applicable to all users across covered regions including Coimbatore, Sulur, Tiruppur, Pollachi, Mettupalayam, Avinashi, Palladam, Udumalpet, Annur, Madukkarai, and Perur.",
                "Designed with privacy-by-design principles: data is collected solely for facilitating voluntary blood donations."
            ]
        ),
        LegalSection(
            title="2. Information We Collect",
            content=(
                "We collect only the minimal data strictly necessary to facilitate verified emergency blood donation connections."
            ),
            points=[
                "Voluntary Donors: Full name, 10-digit Indian mobile number, blood group (A+, A-, B+, B-, AB+, AB-, O+, O-), date of birth (to verify legal eligibility between 18 and 65 years old), location (predefined district/locality), availability status, and contact consent.",
                "Blood Requesters: Full name, 10-digit mobile number, patient name, hospital name, required blood group, urgency level, location, and optional medical requirement details.",
                "Authentication Data: Hashed One-Time Passwords (OTPs) and cryptographically signed session tokens (JWT). Plaintext OTPs and passwords are never stored in our database.",
                "Audit & Security Logs: Administrative action records and dispute/report submissions for platform moderation and safety."
            ]
        ),
        LegalSection(
            title="3. Public Directory vs. Contact Privacy Protection",
            content=(
                "BloodConnect enforces strict data segregation between public search results and private contact information."
            ),
            points=[
                "Concealed Public Search: Public donor search results display ONLY the donor's name, blood group, general location, age, and availability status. Donor mobile numbers are strictly hidden from public searches and unauthenticated API queries.",
                "Pending Requests: When a requester submits a donation request, the requester's mobile number is concealed from the donor while the request remains in PENDING status.",
                "Two-Way Contact Disclosure Upon Acceptance: Contact phone numbers of the donor and requester are revealed to each other ONLY after the donor explicitly accepts (ACCEPTED) the emergency blood request.",
                "Rejected or Inactive Requests: If a request is declined or cancelled, phone numbers remain permanently hidden between the parties."
            ]
        ),
        LegalSection(
            title="4. OTP Verification & Passwordless Authentication",
            content=(
                "BloodConnect utilizes a passwordless authentication model using 6-digit One-Time Passwords (OTPs) delivered via WhatsApp or SMS."
            ),
            points=[
                "Server-Side Hashing: OTPs are hashed using SHA-256 before being stored in the database. Plaintext OTPs are never stored or logged.",
                "Time-Limited Expiry: Each OTP is valid for a maximum of 5 minutes.",
                "Brute-Force Protection: A maximum of 3 failed verification attempts is allowed before the OTP is invalidated. Resend requests enforce a 60-second cooldown."
            ]
        ),
        LegalSection(
            title="5. Third-Party Messaging Services (Meta WhatsApp & SMS)",
            content=(
                "To deliver critical, time-sensitive alerts during medical emergencies, BloodConnect integrates with the Meta WhatsApp Cloud API and transactional SMS gateways."
            ),
            points=[
                "Transactional Messages Only: WhatsApp notifications are strictly restricted to authentication OTPs, magic login verification links, and urgent blood request notifications.",
                "No Marketing or Advertising: We do not send promotional broadcasts, advertisements, or unsolicited messages.",
                "Meta Cloud API: Messages sent through WhatsApp adhere to Meta's Cloud API platform policies. We share only the recipient's phone number and the necessary transactional message parameters."
            ]
        ),
        LegalSection(
            title="6. User Rights & Data Management",
            content=(
                "Users maintain control over their data and availability on BloodConnect."
            ),
            points=[
                "Availability Toggle: Donors can toggle their availability status to 'Unavailable' at any moment via their dashboard to stop receiving donation requests.",
                "Profile Updates: Donors can update their name, location, and contact consent directly from their account settings.",
                "Reporting & Moderation: Users can report incorrect profiles, misuse, or spam through the built-in reporting system for administrative investigation."
            ]
        ),
        LegalSection(
            title="7. Data Security & Storage",
            content=(
                "We implement robust technical and operational measures to protect your personal information against unauthorized access, alteration, or disclosure. "
                "Data is stored in secured databases with role-based access control, parameterized queries, and administrative audit logging."
            )
        ),
        LegalSection(
            title="8. Contact Information",
            content=(
                "If you have questions, feedback, or concerns regarding this Privacy Policy or your data on BloodConnect, you may contact the platform administrators through the official community channels."
            )
        )
    ]
)

TERMS_OF_SERVICE_DATA = LegalDocumentResponse(
    title="Terms of Service",
    last_updated="September 2026",
    platform_name="BloodConnect",
    summary=(
        "BloodConnect is a non-profit, community-driven emergency communication intermediary connecting voluntary blood donors with patients across Coimbatore. "
        "BloodConnect is NOT a blood bank and does not collect, test, process, or deliver blood. All medical verifications and donations must take place at licensed hospitals. "
        "Any commercial buying, selling, or charging of fees for blood is strictly illegal and prohibited."
    ),
    sections=[
        LegalSection(
            title="1. Acceptance of Terms",
            content=(
                "By accessing, registering, or using the BloodConnect platform (the 'Platform'), you acknowledge that you have read, understood, and agreed to be bound by these Terms of Service. "
                "If you do not agree with any part of these terms, you must discontinue use of the platform immediately."
            )
        ),
        LegalSection(
            title="2. Nature of Platform: Emergency Intermediary Communication Tool Only",
            content=(
                "BloodConnect is strictly a voluntary intermediary communication directory designed to connect voluntary blood donors with individuals in urgent medical need."
            ),
            points=[
                "NOT A BLOOD BANK: BloodConnect is NOT a blood bank, hospital, clinical laboratory, or medical establishment.",
                "No Blood Handling: BloodConnect does not collect, draw, screen, test, cross-match, process, store, transport, or administer blood or blood components.",
                "Communication Facilitation Only: The platform's sole function is to facilitate direct communication between willing voluntary donors and blood requesters during emergencies."
            ]
        ),
        LegalSection(
            title="3. Mandatory Hospital Clinical Screening & Medical Disclaimer",
            content=(
                "All medical procedures, eligibility evaluations, and blood transfusions must be conducted strictly at authorized hospitals or licensed clinical blood banks."
            ),
            points=[
                "No Medical Advice: BloodConnect does not provide medical diagnoses, treatment advice, or medical clearance of donors.",
                "Mandatory Clinical Verification: Hospitals and certified blood banks are solely responsible for conducting required medical donor screenings, infectious disease testing (e.g., HIV, Hepatitis B/C, Malaria, Syphilis), hemoglobin testing, blood group confirmation, and cross-matching.",
                "Clinical Discretion: The hospital or attending medical officer has full discretion to determine donor eligibility in accordance with National Blood Transfusion Council (NBTC) guidelines."
            ]
        ),
        LegalSection(
            title="4. Strictly Voluntary & Non-Commercial: Absolute Ban on Sale of Blood",
            content=(
                "Blood donation facilitated through BloodConnect is strictly voluntary, altruistic, and unpaid."
            ),
            points=[
                "No Monetary Exchange: Buying, selling, demanding remuneration, offering cash, or charging any fees for blood donation is strictly illegal under the Drugs and Cosmetics Act, 1940 and Indian Penal laws.",
                "Zero-Tolerance Policy: Any user attempting to buy, sell, or solicit money or goods for blood donation will face immediate permanent account termination, blacklisting, and reporting to legal law enforcement authorities."
            ]
        ),
        LegalSection(
            title="5. Donor Eligibility & Account Responsibilities",
            content=(
                "To maintain platform safety and medical integrity, donors and requesters agree to strict eligibility and conduct standards."
            ),
            points=[
                "Age Limit: Voluntary donors must be between 18 and 65 years of age.",
                "Truthful Information: Users must provide accurate, current, and genuine details including their real name, actual blood group, and active mobile number.",
                "No Impersonation: Creating fake profiles, posting bogus emergency requests, or impersonating medical personnel is strictly prohibited.",
                "Contact Respect: Contact details obtained upon request acceptance must be used solely for coordinating the specific blood donation request. Harassment, verbal abuse, spam, or unsolicited outreach is strictly prohibited."
            ]
        ),
        LegalSection(
            title="6. Limitation of Liability",
            content=(
                "BloodConnect is provided on an 'AS IS' and 'AS AVAILABLE' basis to support the community in good faith during medical emergencies."
            ),
            points=[
                "No Guarantee of Availability: BloodConnect does not guarantee that a registered donor will be available, will respond, will arrive at the hospital, or will be deemed medically eligible by hospital staff.",
                "No Liability for Transfusion Outcomes: BloodConnect and its maintainers assume no responsibility or liability for medical complications, adverse transfusion reactions, hospital delays, or disputes between donors and requesters.",
                "Platform Availability: We strive to maintain continuous platform availability but do not guarantee uninterrupted or error-free operation during network or technical disruptions."
            ]
        ),
        LegalSection(
            title="7. Platform Moderation, Auditing & Account Termination",
            content=(
                "Platform administrators reserve the right to review reported profiles, monitor emergency requests, deactivate inactive or offending accounts, and cooperate with law enforcement authorities in cases of platform misuse, fraud, or violations of applicable laws."
            )
        ),
        LegalSection(
            title="8. Changes to Terms",
            content=(
                "We may update these Terms of Service periodically to reflect platform enhancements or regulatory requirements. Continued use of BloodConnect after updates constitute acceptance of the revised terms."
            )
        )
    ]
)

DATA_DELETION_DATA = LegalDocumentResponse(
    title="User Data Deletion Instructions",
    last_updated="September 2026",
    platform_name="BloodConnect",
    summary=(
        "BloodConnect values your privacy and personal data rights. Users may request complete deletion or deactivation of their donor profile, "
        "account details, and personal information at any time. Follow the instructions below to submit a deletion request or manage your data."
    ),
    sections=[
        LegalSection(
            title="1. Scope & Rights to Data Deletion",
            content=(
                "In compliance with applicable privacy regulations and Meta Platform Policies, BloodConnect provides voluntary donors and requesters with the right to have their personal data completely erased from our active database. "
                "You may request data deletion at any time without incurring any penalty or cost."
            )
        ),
        LegalSection(
            title="2. What Data Is Deleted Upon Request",
            content=(
                "When a data deletion request is processed, the following information is permanently removed or scrubbed:"
            ),
            points=[
                "Donor Profile Information: Full name, 10-digit mobile number, blood group, date of birth, location, and contact consent records.",
                "User Account & Credentials: User identifier, mobile number associations, active session tokens, and authentication records.",
                "Notification Logs: Personal notification history and emergency request participant linkages.",
                "Database Removal: The personal account record is permanently expunged from active operational databases."
            ]
        ),
        LegalSection(
            title="3. Step-by-Step Instructions to Request Deletion",
            content=(
                "Users can choose between temporary availability deactivation or permanent account erasure:"
            ),
            points=[
                "Option A (Instant Availability Pause): If you wish to stop appearing in public donor searches and stop receiving emergency blood requests immediately, log in to BloodConnect, navigate to your Donor Dashboard (/donor/dashboard), and toggle your availability status to 'Unavailable'.",
                "Option B (Permanent Account & Data Erasure): To permanently delete your entire profile and data, submit a data deletion request by emailing or contacting platform support with the subject 'Data Deletion Request' and providing your registered 10-digit mobile number.",
                "Identity Verification: For security and to prevent fraudulent requests, a one-time verification code (OTP) will be sent to your registered phone number to confirm your identity before data deletion is executed.",
                "Confirmation: Upon successful OTP confirmation, your personal data will be purged from the platform."
            ]
        ),
        LegalSection(
            title="4. Processing Timeline",
            content=(
                "Data deletion requests are reviewed and fulfilled within 48 to 72 hours following phone verification. Once executed, deletion is permanent and cannot be undone."
            )
        ),
        LegalSection(
            title="5. Third-Party Messaging & Meta WhatsApp Data",
            content=(
                "BloodConnect does not retain copies of your messages on external advertising platforms. Once your account is deleted from BloodConnect, our servers will never trigger any future WhatsApp or SMS messages to your phone number. Any chat history remaining inside your personal WhatsApp app is stored locally on your device and can be cleared using your WhatsApp device settings."
            )
        ),
        LegalSection(
            title="6. Support & Inquiries",
            content=(
                "For assistance with data deletion, contact platform support through the official BloodConnect portal."
            )
        )
    ]
)


@router.api_route("/privacy-policy", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, summary="Platform Privacy Policy")
@router.api_route("/privarcy-policy", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, include_in_schema=False)
async def get_privacy_policy():
    """Retrieve the official privacy policy for BloodConnect."""
    return PRIVACY_POLICY_DATA


@router.api_route("/terms", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, summary="Platform Terms of Service")
@router.api_route("/terms-of-service", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, include_in_schema=False)
async def get_terms_of_service():
    """Retrieve the official terms of service for BloodConnect."""
    return TERMS_OF_SERVICE_DATA


@router.api_route("/data-deletion", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, summary="User Data Deletion Instructions")
@router.api_route("/user-data-deletion", methods=["GET", "HEAD"], response_model=LegalDocumentResponse, include_in_schema=False)
async def get_data_deletion_instructions():
    """Retrieve user data deletion instructions for BloodConnect."""
    return DATA_DELETION_DATA


@router.post("/data-deletion", summary="Meta Data Deletion Callback", include_in_schema=False)
async def meta_data_deletion_callback():
    """Meta Data Deletion Callback endpoint returning confirmation code and status URL."""
    import uuid
    confirmation_code = str(uuid.uuid4())
    return {
        "url": "/data-deletion",
        "confirmation_code": confirmation_code
    }

