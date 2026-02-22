import React, { useState } from 'react'
import {
    Text,
    TextInput,
    Button,
    ScrollView,
} from 'react-native'
import { loginWithEmail } from '../lib/firebase'
import { Link, useRouter } from 'expo-router'

export default function SignIn() {
    const router = useRouter()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')

    async function handleSignIn() {
        const normalizedEmail = email.trim().toLowerCase()
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailPattern.test(normalizedEmail)) {
            alert(`Invalid email: "${normalizedEmail}"`)
            return
        }

        try {
            await loginWithEmail(normalizedEmail, password)
            router.replace('/(tabs)')
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'code' in err) {
                alert(String((err as { code: unknown }).code))
                return
            }
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
                return
            }
            alert('Sign in failed')
        }
    }

    return (
        <ScrollView contentContainerStyle={{ padding: 16 }}>
            <Text style={{ fontSize: 24, marginBottom: 8 }}>
                Sign in
            </Text>

            <TextInput
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                style={{ borderWidth: 1, marginBottom: 8, padding: 8 }}
            />

            <TextInput
                placeholder="Password"
                value={password}
                secureTextEntry
                onChangeText={setPassword}
                style={{ borderWidth: 1, marginBottom: 8, padding: 8 }}
            />

            <Button title="Sign In" onPress={handleSignIn} />
            <Link href="/create-account" style={{ width: '100%', textAlign: 'center', margin: 10, padding: 10, color: 'white', backgroundColor: 'green' }}>Create account</Link>
        </ScrollView>
    )
} 
