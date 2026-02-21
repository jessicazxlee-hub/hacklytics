import { initializeApp, type FirebaseOptions } from 'firebase/app'
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    type User,
} from 'firebase/auth'
import {
    getFirestore,
    doc,
    setDoc,
    getDoc,
    collection,
    getDocs,
    deleteDoc,
} from 'firebase/firestore'
import type { UserProfile } from '../types'

// Load firebase config dynamically
let firebaseConfig: FirebaseOptions | null = null

try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const cfg = require('../firebaseConfig')
    firebaseConfig = cfg?.default ?? cfg
} catch {
    try {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const cfg2 = require('../firebaseConfig.example')
        firebaseConfig = cfg2?.default ?? cfg2
    } catch {
        firebaseConfig = null
    }
}

if (!firebaseConfig) {
    throw new Error(
        'Missing Firebase config. Copy app/firebaseConfig.example.ts to app/firebaseConfig.ts and fill your keys.'
    )
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const db = getFirestore(app)

// ---------- Auth helpers ----------

export async function signupWithEmail(email: string, password: string): Promise<User> {
    const userCred = await createUserWithEmailAndPassword(auth, email, password)
    return userCred.user
}

export async function loginWithEmail(email: string, password: string): Promise<User> {
    const userCred = await signInWithEmailAndPassword(auth, email, password)
    return userCred.user
}

export async function signOutUser(): Promise<void> {
    await signOut(auth)
}

// ---------- Profile helpers ----------

export async function createProfile(uid: string, profile: UserProfile): Promise<void> {
    await setDoc(doc(db, 'users', uid), profile, { merge: true })
}

export async function getProfile(uid: string): Promise<UserProfile | null> {
    const d = await getDoc(doc(db, 'users', uid))
    return d.exists() ? (d.data() as UserProfile) : null
}

export async function getAllUsers(): Promise<Array<{ id: string } & UserProfile>> {
    const snap = await getDocs(collection(db, 'users'))
    return snap.docs.map(d => ({ id: d.id, ...(d.data() as UserProfile) }))
}

export async function getUsersByIds(uids: string[]): Promise<Array<{ id: string } & UserProfile>> {
    // Hackathon-scale: fetch individually (fine for small N)
    const out: Array<{ id: string } & UserProfile> = []
    for (const uid of uids) {
        const p = await getProfile(uid)
        if (p) out.push({ id: uid, ...p })
    }
    return out
}

// ---------- Friends helpers ----------
// Data model: users/{uid}/friends/{friendUid}  (doc id = friendUid)

export async function addFriend(myUid: string, otherUid: string): Promise<void> {
    await setDoc(
        doc(db, 'users', myUid, 'friends', otherUid),
        { createdAt: Date.now() },
        { merge: true }
    )
    await setDoc(
        doc(db, 'users', otherUid, 'friends', myUid),
        { createdAt: Date.now() },
        { merge: true }
    )
}

export async function removeFriend(myUid: string, otherUid: string): Promise<void> {
    await deleteDoc(doc(db, 'users', myUid, 'friends', otherUid))
    await deleteDoc(doc(db, 'users', otherUid, 'friends', myUid))
}

export async function listFriendIds(myUid: string): Promise<string[]> {
    const snap = await getDocs(collection(db, 'users', myUid, 'friends'))
    return snap.docs.map(d => d.id)
}

export default {
    signupWithEmail,
    loginWithEmail,
    createProfile,
    getProfile,
    getAllUsers,
    getUsersByIds,
    addFriend,
    removeFriend,
    listFriendIds,
}