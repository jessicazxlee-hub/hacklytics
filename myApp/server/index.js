const express = require('express')
const http = require('http')
const cors = require('cors')
const { Server } = require('socket.io')
const admin = require('firebase-admin')

// Initialize Firebase Admin
if (!process.env.GOOGLE_APPLICATION_CREDENTIALS && !process.env.SERVICE_ACCOUNT_JSON) {
    console.warn('Set GOOGLE_APPLICATION_CREDENTIALS or SERVICE_ACCOUNT_JSON env var to a service account JSON path or content')
}

try {
    if (process.env.SERVICE_ACCOUNT_JSON) {
        const serviceAccount = JSON.parse(process.env.SERVICE_ACCOUNT_JSON)
        admin.initializeApp({ credential: admin.credential.cert(serviceAccount) })
    } else {
        admin.initializeApp()
    }
} catch (err) {
    console.error('Firebase admin init error', err.message)
}

const app = express()
app.use(cors())
app.use(express.json())

const server = http.createServer(app)
const io = new Server(server, { cors: { origin: '*' } })

// Simple health
app.get('/health', (req, res) => res.json({ ok: true }))

io.use(async (socket, next) => {
    // Expect client to send token in query: ?token=ID_TOKEN
    const token = socket.handshake.query && socket.handshake.query.token
    if (!token) return next(new Error('Authentication error: missing token'))
    try {
        const decoded = await admin.auth().verifyIdToken(token)
        socket.user = { uid: decoded.uid }
        return next()
    } catch (err) {
        return next(new Error('Authentication error'))
    }
})

io.on('connection', (socket) => {
    const uid = socket.user && socket.user.uid
    console.log('socket connected', uid)

    socket.on('join', (room) => {
        socket.join(room)
    })

    socket.on('message', async (payload) => {
        // payload: { toRoom, text, meta }
        try {
            const msg = {
                from: uid,
                text: payload.text || '',
                meta: payload.meta || {},
                createdAt: admin.firestore.FieldValue.serverTimestamp()
            }
            // save to Firestore `messages/{room}/msgs`
            if (payload.toRoom) {
                const roomRef = admin.firestore().collection('messages').doc(payload.toRoom)
                await roomRef.collection('msgs').add(msg)
                io.to(payload.toRoom).emit('message', { room: payload.toRoom, ...msg })
            }
        } catch (err) {
            console.error('message error', err.message)
        }
    })

    socket.on('locationUpdate', async (data) => {
        // data: { lat, lng }
        try {
            await admin.firestore().collection('users').doc(uid).set({ location: new admin.firestore.GeoPoint(data.lat, data.lng), updatedAt: admin.firestore.FieldValue.serverTimestamp() }, { merge: true })
        } catch (err) {
            console.error('locationUpdate error', err.message)
        }
    })

    socket.on('disconnect', () => {
        console.log('disconnect', uid)
    })
})

const PORT = process.env.PORT || 4000
server.listen(PORT, () => console.log(`Server listening on ${PORT}`))
