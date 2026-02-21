import React, { useState } from 'react'
import { View, Text, TextInput, Button, ScrollView, Alert } from 'react-native'
import { Picker } from '@react-native-picker/picker'
import { signupWithEmail, loginWithEmail, createProfile } from './lib/firebase'
import { useRouter } from 'expo-router'

function friendlyAuthError(e: any) {
    const code = e?.code ?? ''
    if (code.includes('auth/email-already-in-use')) return 'That email is already in use.'
    if (code.includes('auth/invalid-email')) return 'That email address looks invalid.'
    if (code.includes('auth/weak-password')) return 'Password is too weak (try 6+ characters).'
    if (code.includes('auth/wrong-password')) return 'Incorrect password.'
    if (code.includes('auth/user-not-found')) return 'No account found with that email.'
    return e?.message ?? 'Something went wrong.'
}

export default function CreateAccount() {
    const router = useRouter()

    const [mode, setMode] = useState<'signup' | 'signin'>('signup')

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [age, setAge] = useState('')
    const [gender, setGender] = useState<'unspecified' | 'female' | 'male' | 'nonbinary'>('unspecified')
    const [hobbies, setHobbies] = useState('')

    async function handleSubmit() {
        try {
            if (mode === 'signin') {
                await loginWithEmail(email, password)
                router.replace('/(tabs)')
                return
            }

            const user = await signupWithEmail(email, password)

            await createProfile(user.uid, {
                name,
                age: Number(age),
                gender,
                hobbies: hobbies.split(',').map(s => s.trim()).filter(Boolean),
                // placeholder preferences (we’ll expand these later)
                prefs: { maxDistanceKm: 10 },
            })

            router.replace('/(tabs)')
        } catch (e: any) {
            Alert.alert('Error', friendlyAuthError(e))
        }
    }

    return (
        <ScrollView contentContainerStyle={{ padding: 16, gap: 10 }}>
            <Text style={{ fontSize: 24 }}>
                {mode === 'signup' ? 'Create account' : 'Sign in'}
            </Text>

            <TextInput placeholder="Email" value={email} onChangeText={setEmail}
                autoCapitalize="none" style={{ borderWidth: 1, padding: 8 }} />

            <TextInput placeholder="Password" value={password} onChangeText={setPassword}
                secureTextEntry style={{ borderWidth: 1, padding: 8 }} />

            {mode === 'signup' && (
                <>
                    <TextInput placeholder="Full name" value={name} onChangeText={setName}
                        style={{ borderWidth: 1, padding: 8 }} />

                    <TextInput placeholder="Age" value={age} onChangeText={setAge}
                        keyboardType="numeric" style={{ borderWidth: 1, padding: 8 }} />

                    <Text>Gender</Text>
                    <Picker selectedValue={gender} onValueChange={(v) => setGender(v)}>
                        <Picker.Item label="Unspecified" value="unspecified" />
                        <Picker.Item label="Female" value="female" />
                        <Picker.Item label="Male" value="male" />
                        <Picker.Item label="Non-binary" value="nonbinary" />
                    </Picker>

                    <TextInput placeholder="Hobbies (comma separated)" value={hobbies} onChangeText={setHobbies}
                        style={{ borderWidth: 1, padding: 8 }} />
                </>
            )}

            <Button title={mode === 'signup' ? 'Create Account' : 'Sign In'} onPress={handleSubmit} />

            <Button
                title={mode === 'signup' ? 'Already have an account? Sign in' : 'Need an account? Create one'}
                onPress={() => setMode(m => (m === 'signup' ? 'signin' : 'signup'))}
            />
        </ScrollView>
    )
}