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

# 18. RECORDS AND COMMITS

RECCORD DB stores information as records and commits.

A commit represents a distinct committed submission/change in the RECCORD DB record system.

A commit is not identified as an append merely because another commit has the same name.

Two commits with the same name are two separate commits unless an explicit append operation is being performed.

Example:

```text
Commit A
Name: Employment Record

Commit B
Name: Employment Record

These are separate commits.
Same name does not mean append.
19. COMMIT BEHAVIOUR TYPES
Every applicable record/commit must have one of the following behaviour types:
APPEND
MUTABLE
IMMUTABLE
AUTO
These behaviours are system rules and must be enforced by the backend.
20. APPEND-ONLY
APPEND means the existing committed content cannot be edited in place.
New information is added as a new append.
The append appears at the bottom of the applicable record/commit history.
The original committed content remains unchanged.
Example:
Original commit

Name: John Doe
Role: Engineer
An append produces:
Original commit

Name: John Doe
Role: Engineer

Append

Role changed to Senior Engineer.
The original content remains intact.
21. INLINE APPEND / COMMENT
An inline append is not an in-place edit.
If a user wants to address a specific piece of text within an existing commit, they may reference the exact text they are addressing and provide their appended statement/comment.
Example:
Existing text:

The delivery occurred on Monday.
The user may append:
[Referenced text]
"The delivery occurred on Monday."

[Append]
The delivery actually occurred on Tuesday according to the attached record.
The referenced text identifies what the user is addressing.
The original text is not modified.
The append is still a new addition to the record history.
If the user does not need to reference a particular section, the user may append directly at the bottom.
22. APPEND TO MUTABLE
For a MUTABLE commit, an append is treated as a new commit.
It is not a special mutation of the existing commit.
Therefore:
MUTABLE commit
        +
append
        ↓
NEW COMMIT
The previous commit remains part of the record history.
23. MUTABLE
MUTABLE means the committed object may be edited.
The latest valid version is stored as the current state while the backend maintains the required record/history information.
A mutable object may be changed according to its permissions.
However:
An append to a mutable commit is a new commit.
Append behaviour must not be silently converted into an edit.
24. IMMUTABLE
IMMUTABLE means the object cannot be edited.
It also cannot be appended to.
Once committed:
IMMUTABLE
    ↓
NO EDIT
NO APPEND
Any attempted mutation must be rejected by the backend.
25. AUTO
AUTO means the system determines the applicable behaviour using RECCORD DB system logic.
AUTO is not a permission for the frontend to decide behaviour.
The backend determines the applicable rule.
The system's default integrity behaviour is append-only.
Therefore, where AUTO resolves to append-only behaviour:
existing content
       ↓
preserve original
       ↓
new append
No frontend implementation may override AUTO behaviour.

26. COMMIT PERMISSIONS
The backend must verify that the requesting account is permitted to perform the requested operation.
The backend must evaluate:
authenticated identity
account type
organisation membership where applicable
ownership
record permissions
commit behaviour
current record state
The frontend's button visibility is not an authorization mechanism.

27. RECORD HISTORY
Where a record supports history, the backend must preserve the relationship between:
original commit
subsequent mutable versions where applicable
appended commits
inline references
author identity
timestamps
applicable behaviour type
History must not be reconstructed from frontend state.


28. AUTHOR IDENTITY
A committed record must identify its author using the authenticated RECCORD DB identity.
The backend must not trust an author ID supplied by an unauthenticated or unauthorized client.
The authenticated session determines the author.
Phone identity/uID remains the authoritative user identity as defined in Split 1.


29. TIMESTAMPS
Server-side timestamps are authoritative for persistent records.
The client may display timestamps according to locale/timezone requirements, but must not be able to falsify the authoritative creation/commit time.


30. RECEIPTS
RECCORD DB includes a receipt system.
Receipts are a first-class backend resource.
Receipt functionality is not a frontend-only document generator.
Receipts must be persistable and retrievable through the API.
Receipt records must have a defined ownership/authorization relationship.
Receipt data must remain associated with its originating account or organisation according to the applicable product context.


31. FREE RECEIPTS
Receipt functionality is free and unlimited.
The backend must not impose a premium usage quota on the agreed free receipt functionality.
The frontend must not display a false premium restriction for free receipts.


32. INVOICES
RECCORD DB includes an invoice system.
Invoices are first-class backend resources.
Invoice records must be persistable, retrievable, and associated with their applicable account/organisation.
Invoice state must be controlled by the backend.
The frontend must not fabricate invoice status.
33. PREMIUM
RECCORD DB includes premium functionality.
Premium is an entitlement system, not merely a frontend visual switch.
The backend must determine:
whether an account has premium
which premium tier applies
which features are entitled
whether an entitlement is active
applicable subscription/billing state
The frontend consumes the entitlement state returned by the backend.


34. INVOICE++
RECCORD DB includes Invoice++ as a distinct premium product/functionality layer.
Invoice++ must not be silently treated as ordinary invoice functionality.
Its exact feature set, pricing rules, limits, and entitlements must be represented explicitly in the commercial contract when those product definitions are finalized.
The backend must remain the authority for Invoice++ entitlement.
35. BILLING
Billing is a backend concern.
The backend must maintain the relationship between:
Account / Organisation
        ↓
Subscription / Entitlement
        ↓
Premium product
        ↓
Feature access
The frontend must not determine whether a user has paid.
Payment-provider integration details must be isolated behind the backend billing layer.


36. ENTITLEMENTS
Premium feature access must be determined by backend entitlements.
An entitlement may depend on:
account
organisation
product
subscription
billing status
applicable plan
The frontend may display an entitlement but cannot grant itself the entitlement.


37. INVOICE / RECEIPT RELATIONSHIP
Where a transaction produces an invoice or receipt, the backend must maintain the appropriate relationship between the commercial records.
The exact financial/accounting relationship must be defined before implementation where it has not already been specified.
The implementation must not invent accounting semantics.


38. COMMERCIAL DATA INTEGRITY
Invoices, receipts, billing records, subscriptions, and entitlements are persistent backend data.
They must not be stored only in browser storage.
They must not be generated from mock data in production.
39. API RESOURCE PRINCIPLE
Every persistent domain object must have a backend representation.
The API must be organized around domain resources rather than frontend screens.
Primary resource domains include:
/auth
/users
/organisations
/workers
/roles
/records
/commits
/receipts
/invoices
/billing
/subscriptions
/entitlements
/settings
These are resource domains, not permission to invent undocumented endpoint names.
The final endpoint paths and request/response schemas must be documented before implementation.
40. REQUEST VALIDATION
Every write endpoint must validate its request on the backend.
Validation includes, where applicable:
required fields
field type
field format
account type
authentication state
authorization
organisation membership
worker state
role validity
commit behaviour
commercial entitlement
Invalid requests must be rejected.
41. RESPONSE CONTRACT
Successful API responses must have predictable structures.
The API must distinguish:
success
validation failure
authentication failure
authorization failure
not found
conflict
business-rule violation
server failure
The frontend must consume these responses rather than infer backend state from button behaviour.


42. DATABASE AUTHORITY
The database is the persistent source of truth.
The backend is the business-rule authority.
The frontend is the presentation/client layer.
The architecture is therefore:
USER
 ↓
FRONTEND
 ↓
API
 ↓
BACKEND BUSINESS LOGIC
 ↓
DATABASE


43. NO FRONTEND DATABASE
The frontend must not use:
localStorage
sessionStorage
hard-coded objects
mock arrays
fake users
fake organisations
fake invoices
fake receipts
as substitutes for backend persistence.
A client-side cache may only exist as an optimization after the authoritative backend implementation exists and must never become the source of truth.


44. NO SILENT FALLBACK
If the backend is unavailable, the frontend must not silently pretend that an operation succeeded.
For example:
Register
must not display successful registration unless the backend has actually accepted the registration.
The same rule applies to:
login
worker approval
role creation
record creation
commit
append
edit
invoice creation
receipt creation
payment
premium activation


45. SECURITY
Authentication credentials must never be stored in plaintext.
Passwords must be securely hashed by the backend.
Sensitive credentials must not be exposed in API responses.
Worker Credentials must be treated as sensitive organisation registration credentials.
The backend must validate and authorize every protected operation.


46. AUTHORIZATION
Authorization must be enforced server-side.
At minimum, authorization decisions must distinguish:
REGULAR USER
ADMIN
WORKER
and must additionally account for:
organisation membership
ownership
worker approval
role
rank
resource permissions
premium entitlement


47. ADMIN-ONLY ORGANISATION CONTROL
The following are organisation-controlled operations:
worker approval
worker rejection
worker role management
worker rank management
organisation role management
other explicitly Admin-controlled organisation settings
Workers must not gain these permissions merely by possessing a valid Worker Credential.


48. WORKER CREDENTIAL SECURITY
The Worker Credential identifies the organisation for first-time worker registration.
Possession of the credential does not equal:
worker approval
organisation administration
role administration
rank administration
The backend must never treat the credential as an Admin credential.


49. COUNTRY AND LANGUAGE DATA
Country and language datasets are backend/application data.
They must be versionable.
The country dataset must support the information required for:
country selection
calling code
phone validation/matching context
The language dataset must support the application's supported languages.
The frontend consumes these datasets.


50. VERSIONING
The application and API must have explicit versions.
The Version displayed in Settings must correspond to an actual application version.
The backend API must be versionable without silently breaking existing clients.


51. DEPLOYMENT TARGET
The intended production architecture is:
GitHub
   ↓
Source control
   ↓
Vercel
   ↓
RECCORD DB deployment
Frontend and backend deployment architecture must be compatible with Vercel.
Environment secrets must not be committed to GitHub.

52. ENVIRONMENT CONFIGURATION
Environment-specific values must be supplied through deployment environment configuration.
Secrets must never be hard-coded into:
HTML
frontend JavaScript
public configuration
GitHub source files


53. TESTING REQUIREMENT
Backend tests must be written against the API contract.
Critical business rules must have tests before frontend integration.
Tests must cover at minimum:
all three account entry points
worker New registration
worker Existing login
Worker Credential organisation matching
organisation role retrieval
Admin role updates without credential regeneration
worker approval
worker rejection
phone identity matching
country/calling-code behaviour
append-only
mutable
immutable
auto
same-name separate commits
premium entitlement
invoice behaviour
receipt behaviour
authorization boundaries


54. CONTRACT-FIRST IMPLEMENTATION
Implementation order is mandatory:
API CONTRACT
      ↓
DATABASE MODEL
      ↓
BACKEND
      ↓
BACKEND TESTS
      ↓
FRONTEND
      ↓
INTEGRATION TESTS
      ↓
DEPLOYMENT
Frontend implementation must not precede the backend contract.

55. CONTRACT INTEGRITY RULE
No implementation may silently change a product rule contained in this contract.
If implementation reveals an ambiguity, the ambiguity must be raised and resolved explicitly.
It must not be resolved by assumption.
If a future product decision changes a rule, the contract must be updated first and the implementation must then follow the updated contract.

56. PROTOTYPE / TEST FIXTURE RULE
Temporary development fixtures may exist only in explicitly isolated test tooling.
They must never be presented as production application behaviour.
They must never become the production persistence layer.
They must never silently replace a real backend operation.

