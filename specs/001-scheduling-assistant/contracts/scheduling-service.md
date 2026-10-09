# Scheduling service adapter contract

Designed 2026-10-08. Wire authority is supplied [OpenAPI](../../../docs/product/RFP/source/openapi/scheduling-api.yaml); inspected behavior is supplied [server](../../../docs/product/RFP/source/mock-api/server.py) and [guide](../../../docs/product/RFP/source/mock-api/README.md). Do not change the upstream contract or implement a replacement backend.

Base URL defaults to `http://127.0.0.1:4010`. For the accepted local mock lane reject non-loopback scheduling endpoints. Use standard-library HTTP with explicit JSON decoding, Content-Type, finite timeout, bounded response size (1 MiB design limit), no automatic retry and no redirect following for consequential POST. Keep configuration and tests injectable. Unexpected statuses/payloads fail closed, and write ambiguity is preserved.

| Operation | Request | Usable response | Errors |
| --- | --- | --- | --- |
| search patients | GET /patients/search?phone=...&dob=... | 200 object with matches array; require patientId/phone/dateOfBirth/zipCode as typed fields | 400 correction; 503 assistance |
| find providers | GET /providers with optional specialty/location | 200 providers array; require providerId/name/specialty/locations/modalities | 400 unsupported/bad request; 503 assistance |
| find availability | GET /availability with patientId/specialty; optional location/startDate/endDate | 200 slots array; require slotId/providerId/specialty/location/startTime/available | 400 correction; 503 assistance |
| book | POST /appointments JSON patientId, slotId, confirmed:true | Exactly201 object with appointment; require appointmentId/patientId/providerId/specialty/location/startTime/status | 400 known rejection;409 conflict;503 supplied pre-effect rejection; other/transport uncertainty blocks retry |

Specialties: primary_care, dermatology. Locations: downtown, uptown, lakeside. GET provider filters are optional; ask useful missing preferences without inventing API requirements. Availability requires resolved patient and specialty. Date filters are ISO dates, range ordered. Validate returned slots against filters and `available:true`. Server does not perform robust calendar/type validation; client must.

Phone/DOB are sent only to patient search, URL-encoded. Compare returned matches privately, never disclose candidate demographics. ZIP is compared locally against returned candidates, not sent to a nonexistent ZIP API. No subsequent patient operation until exactly one match remains.

Booking takes the internal stored proposal, never model/user-supplied patientId. `confirmed` must be literal true after deterministic consent. Appointment result has no slotId: verify exact patientId/providerId/specialty/location/startTime and `status:scheduled`, plus nonempty appointmentId. HTTP200 or malformed/mismatched201 does not establish booking. Never display raw upstream error messages; translate allowlisted codes to reason-specific guidance.

409 clears proposal/consent and requires a fresh API search, new choice and confirmation. The mock's permanent conflict slot may reappear; exclude that rejected ID for this recovery cycle without identifying fixture metadata. Unknown writes cannot be retried, including after reset. Required endpoints provide no idempotency key or automatic unknown-write reconciliation; tell the user to contact clinic scheduling staff to verify before trying again. Valid supplied503 is issued before route effects, but ambiguous/unrecognized upstream write failures remain unknown.

Deferred: GET /patients/{patientId}/appointments, POST /handoffs. Do not call either in MVP; give actual assistance guidance without fabricated staff engagement or receipt. If separately adopted later, receipt validates only queued status, not human delivery.

Test-only scenario header `X-Mock-Scenario: api_failure` is explicit local demo configuration, not a model-controlled tool argument. Supplied audit logs method/static path/status/duration without required-route query/body. Do not enable raw HTTP debug logging. Fixtures are synthetic, server state in memory; restart resets mock bookings but cannot prove what happened in an arbitrary uncertain operation. Relative dates and fixed offset are mock limitations.
