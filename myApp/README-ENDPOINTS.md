# Proximity — Backend And Integration Notes

This file documents the current architecture and endpoint contract.

## Architecture
- Firebase is used for identity only (signup/signin + ID tokens).
- Backend (FastAPI + Postgres) is the source of truth for app state and profiles.
- Canonical API user identifier is `id` (UUID). Treat `firebase_uid` as internal.

## Current Status
- Active backend lives in `backend/`.
- Frontend calls backend profile endpoints via Firebase Bearer token.
- Local password login on backend is disabled.
- Firestore + `server/` Socket.IO service are legacy/optional paths still referenced by some UI screens.

## Frontend Setup (Required)
Create Firebase web config:

```bash
cd /home/jlaco/hacklytics/myApp
cp app/firebaseConfig.example.ts app/firebaseConfig.ts
```

Fill `app/firebaseConfig.ts` with your Firebase project web config values.

## Backend Setup (Required)
Backend verifies Firebase ID tokens with Firebase Admin credentials.

```bash
cd /home/jlaco/hacklytics/myApp/backend
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/proximity/firebase-service-account.json"
uv run uvicorn app.main:app --reload --port 8000
```

## Frontend Run (Web)
```bash
cd /home/jlaco/hacklytics/myApp
export EXPO_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npx expo start --web --port 8081
```

## Auth And Profile Flow (Primary)
1. User signs up/signs in with Firebase SDK in frontend.
2. Frontend gets Firebase ID token and sends `Authorization: Bearer <token>` to backend.
3. Backend verifies token with Firebase Admin SDK.
4. Backend loads/bootstraps Postgres profile for that Firebase user via `/api/v1/me/profile`.
5. Backend returns profile used by the app.

Important:
- Frontend auth is Firebase-based. Frontend does not use `/api/v1/auth/login`.
- Frontend profile bootstrap/read/update uses `/api/v1/me/profile`.
- `/api/v1/auth/register` exists as a transitional backend route and is not the primary frontend auth flow.

## Core Backend Endpoints (Current)
Versioned API base path: `/api/v1` (except health endpoint)

- `GET /healthz`
  - Liveness probe.
- `POST /auth/register`
  - Creates a user profile row (legacy transitional route; not used by primary frontend auth flow).
- `POST /auth/login`
  - Disabled (`410 Gone`), local password login is not supported.
- `GET /me`
  - Returns auth subject from validated token.
- `GET /me/profile`
  - Returns current user profile from Postgres.
  - If no profile exists for a valid Firebase token, backend bootstraps one.
- `PATCH /me/profile`
  - Updates profile fields (including controlled hobby codes).
  - Primary frontend write path for profile state.
- `GET /admin/hobbies`
  - Admin list endpoint (requires `X-Admin-Key`).
- `POST /admin/hobbies`
  - Admin create endpoint (requires `X-Admin-Key`).
- `POST /admin/hobbies/seed`
  - Seeds default hobby catalog (requires `X-Admin-Key`).

## Legacy / Optional Components
These are still present in repo but are not the target architecture:
- `server/` (Node + Socket.IO + Firebase Admin).
- Firestore-backed reads/writes in:
  - `app/(tabs)/friends.tsx`
  - `app/(tabs)/matches.tsx`
  - `app/chat/[peerId].tsx`

If you do not run `server/` and Firestore, auth/profile flows still work; chat/friends/matches legacy screens may not.

## Notes and possible future direction
- Keeping Firebase for identity only.
- Move friends/matches/chat to backend APIs + Postgres (and backend realtime if needed).
- Keep Firestore optional until migration is complete.
