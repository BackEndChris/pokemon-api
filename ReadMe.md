# Pokémon API

A backend portfolio project built with FastAPI and PostgreSQL.

The API allows users to register, log in, create Pokémon-style creatures, automatically calculate stats and moves, upload images, and manage only the Pokémon they own.

## Features

- User registration and login
- Password hashing with bcrypt
- JWT authentication
- Pokémon CRUD operations
- Ownership-based authorization
- Validated inputs and case-insensitive usernames
- Bounded pagination
- Verified, size-limited image uploads
- Configurable rate limits
- Automatic stat calculation
- Automatic move assignment
- Image uploads
- PostgreSQL database
- Alembic database migrations
- Swagger/OpenAPI documentation

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Alembic
- JWT
- bcrypt

## Project Structure

```text
Pokemon API/
├── alembic/
│   └── versions/
├── uploads/
├── auth.py
├── auth_routes.py
├── database.py
├── main.py
├── moves.py
├── pokemon_routes.py
├── routes.py
├── schemas.py
├── stats.py
├── requirements.txt
├── alembic.ini
├── .gitignore
└── README.md
```

## Pokemon stats

All 18 types are supported: Normal, Fire, Water, Electric, Grass, Ice,
Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon,
Dark, Steel, and Fairy. Type names are case-sensitive.

Each type has a custom six-stat archetype totaling 360 base points:
HP, attack, defense, special attack, special defense, and speed.
These are simplified rules for this project, rather than official species stats.

On creation, each stat independently receives a random integer from -4 to +4:

```text
hp = type base + variation + level * 3
other stats = type base + variation + level * 2
```

The resulting stats are stored in PostgreSQL. Reading or renaming a Pokemon
does not reroll them. Level increases add the corresponding growth,
preserving its original variation. Levels cannot be lowered.
A Pokemon's type cannot be changed;
PUT requests must still include its current type.

## Learning moves

Each of the 18 types has eight moves defined in `moves.py` (144 moves total):

| Move | Available from | Chance per gained level |
| --- | --- | --- |
| Starter | Level 1 | Guaranteed |
| Additional move | Level 5 | 20% |
| Second move | Level 10 | 20% |
| Additional move | Level 15 | 15% |
| Third move | Level 25 | 10% |
| Additional move | Level 35 | 10% |
| Additional move | Level 50 | 8% |
| Additional move | Level 65 | 5% |

These learning levels and probabilities are custom rules for this project.
A missed move gets another independent chance on the next gained level.
Eligible moves roll independently, so multiple moves can be learned together.
There is no learned-move limit, and a move cannot be learned twice.
Pokemon learn only moves of their own type: Water Pokemon cannot learn Fire
or Electric moves. Both the learning pool and database lookup enforce this.

Creating a Pokemon at a higher level processes learning from level 1 through
that level. Updating from level 10 to 15 processes all five gained levels.
Reading a Pokemon or editing its name at the same level never rerolls moves.
Levels cannot be lowered, which prevents replaying earlier learning chances.

Move records live in `moves`; learned moves are saved in `pokemon_moves`.
`GET /pokemon/{pokemon_id}` returns a `moves` list containing names and powers.
Creation, update, and list responses retain their existing stat-only shape.
Move powers are stored for future use; no battle mechanics are implemented.

## Database migrations

Apply migrations before starting the updated API:

```powershell
python -m alembic upgrade head
```

The special-stats migration adds `special_attack` and `special_defense`.
For existing Pokemon, it fills these using the type base plus `level * 2`,
without randomness, and preserves the four existing stats.

The following move-catalogue migration seeds all 54 moves, preserving existing
move records and learned assignments. Existing Pokemon receive any missing
starter move, without rerolling their past levels. Their next level increase
begins rolling for eligible, unlearned moves.

The next migration adds five more moves per type (90 additional records),
bringing the catalogue to 144. It preserves existing Pokemon and learned moves;
the new moves become eligible on future level gains without rerolling past levels.

## Configuration and running locally

Use Python 3.13 and install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create an ignored `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pokemon_api
SECRET_KEY=YOUR_RANDOM_SECRET
```

Both values must be explicitly configured and nonblank. `DATABASE_URL` must
parse as a PostgreSQL URL with a database name. Startup fails early with the
configuration field name, without printing its value. Existing nonblank JWT
keys remain compatible; use a random secret with at least 32 bytes for new
installations. Changing the key invalidates previously issued tokens.
Percent-encode special characters in database URL credentials.

Apply migrations, then run the app directly without trusting proxy headers:

```powershell
python -m alembic upgrade head
python -m uvicorn main:app --reload --no-proxy-headers
```

Swagger documentation is available at `/docs`.

## Input validation and authentication

| Input | Rules |
| --- | --- |
| Pokemon name | Surrounding whitespace is trimmed; 1-50 characters after trimming; blank and entirely numeric names rejected. `Pikachu123` and `Porygon2` are valid. |
| New username | Trimmed and stored lowercase; 3-32 ASCII characters; letters, digits, underscore, dot, and hyphen; first character must be a letter, digit, or underscore. |
| Username lookup | Case-insensitive during registration and login; `Ash` and `ash` refer to one account. |
| Email | Pydantic `EmailStr` with `email-validator`; format validation only, with no ownership verification. |
| New password | At least 8 characters, at most 72 UTF-8 bytes; no blank-only passwords or null characters. |
| Login password | Nonempty and at most 72 UTF-8 bytes, with no null characters; shorter legacy passwords remain accepted. |

Passwords are never trimmed, normalized, or truncated. The byte limit matters
for Unicode: 36 copies of `é` or 18 four-byte emoji reach 72 bytes. Existing
bcrypt hashes are retained, and hashing also explicitly rejects truncation.
If an old account was originally created with an over-72-byte password,
bcrypt did not retain its full value: over-limit login is now rejected rather
than silently reproducing truncation. Such an account needs an explicit
password reset; no automatic reset endpoint is included in this change.

The username migration creates a unique index on `lower(username)` and does
not rewrite existing usernames or password hashes. It blocks writes while
checking for case conflicts. If conflicts exist, migration stops without
deleting or merging accounts. Review the conflicting account IDs and choose
explicit renames, then rerun the migration. New registration rules do not
retroactively reject legacy usernames at login.

Bearer tokens require a valid signature, expiration, and positive integer
user subject within the PostgreSQL integer range. Missing, malformed,
invalid, and expired tokens receive 401 with `WWW-Authenticate: Bearer`.
Every authenticated request checks that the user still exists. Unknown users
and incorrect passwords share `Invalid username or password`; unknown users
also perform a dummy bcrypt verification.

## Pagination

`GET /pokemon` and `GET /my-pokemon` accept `limit` and `offset`:

```text
/pokemon?limit=20&offset=0
/my-pokemon?limit=10&offset=20
```

The response remains a JSON list. Defaults are `limit=20`, `offset=0`;
`limit` must be 1-100 and `offset` 0-100000. Both lists use ascending Pokemon
ID ordering, and `/my-pokemon` applies the ownership filter before pagination.
Offsets past the end return an empty list. Offset pages can shift when rows
are inserted or deleted between requests; no snapshot/cursor API is provided.

## Image uploads and cleanup

`POST /pokemon/{id}/image` requires authentication and ownership. By default:

- Maximum file size: **5 MiB** (5,242,880 bytes), configurable with `MAX_UPLOAD_BYTES`.
- Maximum decoded image size: **20 million pixels**, configurable with `MAX_IMAGE_PIXELS`.
- Supported formats: single-frame JPEG, PNG, WEBP.
- A filename is required, but its extension and supplied MIME type are not trusted.
- Pillow verifies and fully decodes the image, then re-encodes its pixels,
  dropping metadata and trailing data. The verified format determines `.jpg`,
  `.png`, or `.webp`; filenames remain generated UUIDs.
- The sanitized result must also fit the byte limit. Empty, malformed,
  oversized, unsupported, and animated images are rejected.

Uploads are written using exclusive creation. Failed writes and rolled-back
updates clean up the new file; the previous image stays referenced until the
new database transaction commits. Replaced images and deleted Pokemon images
are removed after a successful commit. Cleanup refuses traversal paths and
symlinks outside the upload directory. Missing old files are harmless.

Filesystem storage and database transactions are not a single atomic system.
If deletion fails because storage is unavailable or permissions deny it, the
committed API result is preserved and a safe error is logged for maintenance.
There is no durable cleanup queue: permission failures, process crashes, or
an ambiguous database commit outcome can require manual reconciliation of
unreferenced files. Existing files are not retroactively re-encoded.

The request stream is bounded before JSON/multipart parsing: authentication
requests allow 16 KiB; image requests allow the configured file limit plus
64 KiB for multipart overhead, including requests without Content-Length.
Use an upstream body-size limit and timeouts as well for a public deployment.

## Rate limiting

Rate limiting is a portfolio feature implemented as thread-safe sliding windows
using a monotonic clock. All limits below are configurable positive integers;
the default window is 60 seconds (`RATE_WINDOW_SECONDS`).

| Operation | Environment variable | Default per window | Identity |
| --- | --- | --- | --- |
| Registration | `REGISTER_LIMIT` | 5 | Request source |
| Login | `LOGIN_SOURCE_LIMIT` | 30 | Request source across accounts |
| Login | `LOGIN_ACCOUNT_LIMIT` | 10 | Normalized account **and** request source |
| Image upload | `UPLOAD_LIMIT` | 10 | Both authenticated user and request source |

Login protection considers both account and source without a global account
lockout: an attacker from one address cannot permanently lock another user
out everywhere. Distributed attacks and users behind shared addresses are
limitations. Attempts count regardless of successful credentials; registration
and login source checks also count well-formed JSON with invalid fields.
Malformed JSON is rejected before endpoint dependencies run.

A blocked request receives 429 and a `Retry-After` header in seconds. Rejected
attempts do not extend their window. Successful and failed uploads consume the
same upload budget after authentication. Username keys are hashed in memory.

Client identity is `request.client.host`; application code ignores supplied
`X-Forwarded-For`. The documented direct-server command disables Uvicorn proxy
header processing. Behind a reverse proxy, configure a specific trusted proxy
allowlist in Uvicorn and prevent direct access to the backend. Do not trust
forwarded headers from arbitrary clients; otherwise source limits can be bypassed.

Storage is bounded to 10,000 active identity buckets per process; capacity
exhaustion also returns a temporary 429. Expired buckets are reclaimed.
State resets on restart and is **not shared across workers or servers**.
Use a shared limiter such as Redis and suitable edge protection before scaling
or relying on these limits against distributed abuse. No persistent account
bans or lockouts are stored.

## Error responses and logging

Expected errors use a JSON `detail` field. Validation errors contain a list
of location, message, and type entries, with submitted values and validator
contexts removed so passwords are not echoed.

| Status | Meaning |
| --- | --- |
| 400 | Invalid image, forbidden type change, or level decrease |
| 401 | Invalid login or missing/invalid authentication |
| 404 | Missing Pokemon or Pokemon not owned by the authenticated user |
| 409 | Duplicate username or email |
| 413 | File, decoded image, or request exceeds its limit |
| 415 | Unsupported image format |
| 422 | Invalid fields, pagination, or missing multipart file |
| 429 | Request limit exceeded; inspect `Retry-After` |
| 503 | Database/storage unavailable or missing/inconsistent move catalogue |
| 500 | Unexpected programming/server error |

Database transaction context managers still roll back on errors. Missing or
duplicate matching move records fail safely rather than silently skipping
moves or partially committing a Pokemon/level update. SQL stays parameterized.
Database errors and storage errors log operation categories and exception
class names, without SQL parameters, credentials, tokens, password values,
or raw exception messages. SQLAlchemy parameter rendering is disabled.
Unexpected failures remain server errors; they are not converted into 400s.

## Safe database testing

Tests **truncate users, Pokemon, and learned assignments**. They require a
separate disposable database. Prefer a dedicated database role that has no
write access to the application database.

Create `pokemon_api_test` separately and an ignored `.env.test` file:

```dotenv
DATABASE_URL=postgresql://TEST_USER:TEST_PASSWORD@localhost:5432/pokemon_api_test
SECRET_KEY=AN_INDEPENDENT_TEST_SECRET
```

Both settings must be explicitly present in that file. Missing or incomplete
`.env.test` is an error; inherited variables and `.env` cannot fill the gaps.
The URL must be PostgreSQL, its database name must end in `_test`, and its name
must differ from the normal `.env` database name, even if credentials differ.
No variable interpolation is used for this safety-critical file.

From the repository root, verify the target and migrate it safely:

```powershell
python test_safety.py --migrate
```

Only after verification succeeds, run the tests:

```powershell
python -m pytest -q
```

Pytest repeats the configuration check before importing the app. Immediately
before each TRUNCATE, it verifies both the engine URL and PostgreSQL's actual
`current_database()` against the explicitly approved test configuration.
Image tests use temporary directories; rate-limit tests reset state and move
a fake clock forward rather than sleeping. Tests are intended to run serially
against their own test database; parallel workers need separate databases.
The naming/identity guard is an accident-prevention measure, not a substitute
for isolated database permissions.

The suite covers stats, move learning/type isolation, migrations and account
conflicts, input/password boundaries, authentication and ownership, upload
validation and cleanup failures, transaction rollback, pagination, rate limits,
and test-database safeguards.

Technical references: [Pydantic email validation](https://docs.pydantic.dev/latest/api/networks/#pydantic.networks.EmailStr),
[Pillow image verification](https://pillow.readthedocs.io/en/stable/reference/Image.html),
and [PostgreSQL expression indexes](https://www.postgresql.org/docs/current/indexes-expressional.html).
