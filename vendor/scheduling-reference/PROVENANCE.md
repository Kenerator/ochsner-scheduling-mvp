# Supplied scheduling reference provenance

Recorded: 2026-10-08.

Source: the supplied synthetic patient appointment assignment package at
`/Users/ken/codeRepos/PoC-RFP/patient_appointment_project/`.
This selective copy supports the approved MVP private internal review. It is not a public distribution or deployment grant. No separate upstream license grant is asserted.

The eight files below are byte-for-byte copies. The server remains the supplied independent standard-library HTTP service with in-memory state; restarting its owned process resets bookings. Application logic must use its API rather than inspect fixture-only fields.

Original intake, email, credentials, unrelated attachments and filesystem metadata are excluded. The fixtures are supplied synthetic data. This manifest records source identity, not application or live-AI qualification.

| Source path relative to supplied package / vendored path | SHA-256 |
| --- | --- |
| `openapi/scheduling-api.yaml` | `62e17d269d924d1a3832c16a262cb85f78ebbceb078cdb73e759a91bf40fa735` |
| `mock-api/server.py` | `9597f92fe3ec19c16e08b1491fbac12e1ffed87bd41c137be1e638addac2d1f1` |
| `mock-api/README.md` | `b7d463b52e61cbf63cb0d70ebe661eea67b25332e4af19ff2b86ae239cafde80` |
| `data/patients.json` | `4bc471bef84eccee513b2ae15127cbf532b6aa47f151831ff7c2a6b832889d48` |
| `data/providers.json` | `0745b592a15821474ebee45f868c3ed90d4bf24846903a17e7da0b210a3d92d6` |
| `data/slots.json` | `340bb75c9c737281de2e48b7c299141ce4c27e41001c0172c4e8f0927cf0ce9b` |
| `data/appointments.json` | `02be083e7d1d5841b29a4bb1fb663ba49f6c3d9ed47c236fa67545e8432d0d65` |
| `data/README.md` | `be5b3dc7289a97838316f0f203bc6adae1d63bedce771e68555cfa8c55aab356` |
