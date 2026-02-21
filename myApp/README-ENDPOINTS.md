# Hacklytics — Backend & Integration Notes

This file explains how the backend and frontend pieces connect and where to add API keys.

Firebase
- Create a Firebase project and enable Authentication (Email/Password) and Firestore.
- In the frontend, copy `app/firebaseConfig.example.ts` to `app/firebaseConfig.ts` and fill the values from the Firebase console.
- Install Firebase client SDK in the app:

```bash
cd myApp
yarn add firebase
```

Backend (real-time messaging)
- The server is in `server/`. It uses `firebase-admin` to verify ID tokens and to write messages/locations to Firestore.
- Install server deps:

```bash
cd server
npm install
```

- Provide Firebase credentials:
  - Preferred: set `GOOGLE_APPLICATION_CREDENTIALS` to the path of a service account JSON (from Firebase Console > Service Accounts).
  - Alternative: set `SERVICE_ACCOUNT_JSON` env var to the JSON contents (useful for deployment platforms that accept env vars).

- Start server:

```bash
cd server
npm start
```

Map API
- For POI (e.g., gyms) and improved basemap use Mapbox or Google Places.
- Set `MAPBOX_TOKEN` or `GOOGLE_MAPS_API_KEY` in your environment. In the frontend, call their REST APIs to request POIs near the matched user's approximate location and display them as extra pins.

Socket usage (frontend)
- Install `socket.io-client` in the app and connect with the Firebase ID token for authentication:

```js
import io from 'socket.io-client'
const token = await auth.currentUser.getIdToken()
const socket = io('https://your-server.com', { query: { token } })
socket.emit('join', roomId)
socket.emit('message', { toRoom: roomId, text: 'hello' })
```

Security
- Use Firestore security rules to restrict reads/writes to authorized users. Example rules:

```
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId;
    }
    match /messages/{roomId}/msgs/{msgId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

Notes & Next steps
- The included front-end screens are minimal skeletons. For production, add:
  - Proper navigation guards for auth state
  - Geohash indexing or GeoFirestore-style queries for efficient proximity search
  - Map POI integration (Mapbox or Google Places) to show relevant meetup locations
  - Message UI and typing/read receipts
