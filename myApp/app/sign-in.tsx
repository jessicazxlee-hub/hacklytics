import React, { useState } from 'react'
import {
    View,
    Text,
    TextInput,
    Button,
    ScrollView,
} from 'react-native'
import { Picker } from '@react-native-picker/picker'
import { loginWithEmail } from './lib/firebase'
import { Link, useRouter } from 'expo-router'
import { router } from 'expo-router'

export default function SignIn() {
    const router = useRouter()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [age, setAge] = useState('')
    const [gender, setGender] = useState<'unspecified' | 'female' | 'male' | 'nonbinary'>('unspecified')
    const [hobbies, setHobbies] = useState('')

    async function handleSignIn() {
        const user = await loginWithEmail(email, password);
        if (user) {
            router.replace('/(tabs)')
        } else {
            alert('Invalid email or password')
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