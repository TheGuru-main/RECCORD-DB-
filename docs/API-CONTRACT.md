# RECCORD DB — API CONTRACT

**Version:** 1.0  
**Status:** Contract Draft — implementation must follow this contract  
**Repository:** RECCORD DB

---

# 1. PURPOSE

RECCORD DB is a structured record, accountability, identity, organisation, transaction, and document system.

The backend is the authoritative source of:

- identity
- authentication
- organisations
- workers
- roles
- permissions
- records
- commits
- append behaviour
- invoices
- receipts
- premium entitlements
- settings
- application configuration
- persistent data

The frontend is a client of the backend.

The frontend must never substitute local storage, mock objects, or fabricated responses for backend persistence.

---

# 2. THREE ENTRY POINTS

RECCORD DB has exactly three primary account entry points:

## 2.1 Regular User

A personal RECCORD DB account.

A Regular User:

- has an individual RECCORD DB identity
- can create and manage their permitted personal records
- can use permitted settings
- receives the Regular User badge
- can use the free receipt functionality
- can access premium functionality when entitled

---

## 2.2 Organisation / Admin

An Admin creates and controls an organisation.

An Admin:

- creates the organisation
- owns/administers the organisation
- manages organisation settings permitted to Admin
- creates and updates organisation roles
- manages workers
- approves or rejects worker registrations
- assigns worker roles
- assigns worker rank
- controls organisation-level worker configuration
- receives the Admin badge

Updating organisation roles must **not** require generating a new Worker Credential.

---

## 2.3 Worker

A Worker belongs to an organisation.

Worker registration has two states/paths:

### New Worker

A person who has not yet completed their worker registration.

The Admin provides the organisation's Worker Credential.

The New Worker:

1. enters the Worker Credential
2. the backend identifies the organisation
3. the backend returns the current roles belonging to that organisation
4. the worker selects their specific role
5. the worker supplies their registration details
6. registration is submitted
7. worker remains pending
8. Admin approves or rejects the registration

### Existing Worker

A worker who has already registered and is returning to access RECCORD DB.

Existing Worker login uses:

- phone number
- username
- password

The Worker Credential is **not** required for normal worker login.

The worker remains associated with the organisation established during initial registration.

---

# 3. WORKER CREDENTIAL

The Worker Credential is an organisation-level registration credential.

It is:

- created for the organisation
- shared by workers for first-time registration
- used to identify the organisation during New Worker registration
- not an individual worker credential
- not a role credential
- not regenerated merely because an Admin adds or changes roles

The Worker Credential does not itself approve a worker.

A worker using the credential enters a pending registration state until Admin approval.

---

# 4. ORGANISATION ROLES

Roles belong to the organisation.

Admin controls the organisation's available worker roles.

Admin may:

- create a role
- update a role
- manage the available role set

Adding or changing roles must not invalidate the existing Worker Credential.

When a New Worker enters a valid Worker Credential, the backend must return the current roles associated with that organisation.

The worker selects their specific role during registration.

The frontend must never maintain its own independent list of organisation roles.

---

# 5. WORKER RANK

Worker badge/rank is controlled by Admin.

There are exactly four Worker ranks.

The rank is separate from the organisation role.

The Worker badge is displayed as:

- Worker — Rank 1
- Worker — Rank 2
- Worker — Rank 3
- Worker — Rank 4

The exact names/labels of the four ranks are an Admin-controlled product definition and must not be invented by the frontend.

A worker cannot independently promote or demote themselves.

---

# 6. IDENTITY

Every account has a RECCORD DB identity.

The user's `uID` is their phone-number identity.

The stored identity must preserve the international phone representation.

For example:

```text
+2348012345678

PHONE NUMBER MATCHING
RECCORD DB must recognize phone numbers that appear in different representations.
The internal matching layer may encounter:
+2348012345678
2348012345678
08012345678
080 1234 5678
National-format numbers such as:
080...
081...
090...
are normalized internally for matching against the corresponding international phone identity.
The normalization exists only for recognition/matching.
It does not replace the user's stored uID.
If a contact already stores:
+2348012345678
it must match directly.
The future contact/messaging integration may use this matching layer to recognize RECCORD identities.

8. COUNTRY → PHONE CASCADE
Country selection occurs before phone-number entry.
The country selection determines the phone-number calling-code context.
The registration flow must therefore operate as:
Country
   ↓
Country calling code
   ↓
Phone number
   ↓
Full international phone identity
The backend/data layer supplies the supported countries and calling codes.
The frontend must not contain an incomplete manually maintained country list.
The selected country must be retained as part of the registration data where required by the data model.

9. LANGUAGE
Language options are data-driven.
The language dropdown must be populated from the application's supported language data.
The frontend must not display an empty dropdown or rely on a single hard-coded language as a substitute for the application language dataset.

10. REGISTRATION DATA
The registration contract must distinguish the fields belonging to each account path.
Fields must not be duplicated merely because another account type happens to use a similar value.
The backend validates each account type according to its own registration contract.
The frontend must submit exactly the fields required by that account type.
No unrequested registration field may be invented.

11. AUTHENTICATION
Authentication is backend controlled.
The backend provides:
registration
login
identity verification
session/authentication state
password handling
authorization
account status
worker approval state
The frontend must not authenticate users locally.
The frontend must not fabricate authentication responses.

12. WORKER APPROVAL
New Worker registration creates a pending worker.
The initial worker state is:
PENDING
Admin may:
PENDING → APPROVED
PENDING → REJECTED
Only an approved worker receives normal organisation access.
Worker approval is controlled by the backend.
The frontend cannot bypass approval.

13. ADMIN CONTROL
Admin is the authority for organisation-controlled worker configuration.
Admin controls:
organisation roles
worker role assignment
worker rank
worker approval
permitted organisation settings
Workers cannot modify these Admin-controlled values.

14. SETTINGS
The settings system includes:
About
Version
Badge
Badge types include:
Regular User
Admin
Worker
Worker badge includes the Admin-controlled four-rank system.
Settings permissions depend on account type.
Regular Users and Admins may modify settings available to their account.
Workers cannot independently modify Admin-controlled organisation settings.

15. API AUTHORITY
All business rules are enforced by the backend.
The frontend must not be trusted for:
account permissions
organisation ownership
worker approval
role ownership
rank assignment
record integrity
invoice state
payment state
premium entitlement
append/mutation rules
Every protected API endpoint must authenticate and authorize the request.

16. ERROR CONTRACT
Backend errors must be structured.
Errors must identify:
error code
human-readable message
relevant validation information where applicable
The frontend must render backend errors rather than guessing what happened.
17. NO MOCK DATA
The production architecture must not depend on:
mock authentication
mock users
mock organisations
mock workers
mock invoices
mock receipts
fake OTPs
localStorage as a database
frontend-generated persistent IDs
Temporary development fixtures may exist only in explicitly isolated test tooling and must never be presented as production application behaviour.