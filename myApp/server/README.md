# hacklytics-server

Simple Node server for real-time messaging and presence using Socket.IO and Firebase Admin.

Setup

1. Install deps:

```bash
cd server
npm install
```

2. Provide Firebase service account credentials. Either set `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file, or set `SERVICE_ACCOUNT_JSON` to the file contents (careful with env length).

3. Start server:

```bash
npm start
```

Socket.IO authentication

Clients must pass a valid Firebase ID token when connecting: `io('https://server', { query: { token: ID_TOKEN } })`.

Events

- `join` - join a room
- `message` - send message { toRoom, text, meta }
- `locationUpdate` - send { lat, lng } to update Firestore `users/{uid}.location`
