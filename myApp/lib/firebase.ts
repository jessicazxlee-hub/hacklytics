import { initializeApp, type FirebaseOptions } from 'firebase/app'
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    type User,
} from 'firebase/auth'

// Load firebase config dynamically
let firebaseConfig: FirebaseOptions | null = null

try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const cfg = require('../app/firebaseConfig')
    firebaseConfig = cfg?.default ?? cfg
} catch {
    try {
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const cfg2 = require('../app/firebaseConfig.example')
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

// ---------- Auth helpers ----------

export async function signupWithEmail(
    email: string,
    password: string
): Promise<User> {
    const userCred = await createUserWithEmailAndPassword(
        auth,
        email,
        password
    )
    return userCred.user
}

export async function loginWithEmail(
    email: string,
    password: string
): Promise<User> {
    const userCred = await signInWithEmailAndPassword(
        auth,
        email,
        password
    )
    return userCred.user
}

export async function signOutUser(): Promise<void> {
    await signOut(auth)
}

export default {
    signupWithEmail,
    loginWithEmail,
    signOutUser,
}
