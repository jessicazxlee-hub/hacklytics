import React, { useState } from 'react'
import {
    View,
    Text,
    TextInput,
    Button,
    ScrollView,
} from 'react-native'
import { Picker } from '@react-native-picker/picker'
import { signupWithEmail } from './lib/firebase'
import { useRouter } from 'expo-router'

export default function CreateAccount() {
    const router = useRouter()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [age, setAge] = useState('')
    const [gender, setGender] = useState<'unspecified' | 'female' | 'male' | 'nonbinary'>('unspecified')
    const [hobbies, setHobbies] = useState('')

    async function handleSignup() {
        const normalizedEmail = email.trim().toLowerCase()
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailPattern.test(normalizedEmail)) {
            alert(`Invalid email: "${normalizedEmail}"`)
            return
        }

        try {
            await signupWithEmail(normalizedEmail, password)

            alert('Signup succeeded')
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
            alert('Signup failed')
        }
    }

    return (
        <ScrollView contentContainerStyle={{ padding: 16 }}>
            <Text style={{ fontSize: 24, marginBottom: 8 }}>
                Create account
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

            <TextInput
                placeholder="Full name"
                value={name}
                onChangeText={setName}
                style={{ borderWidth: 1, marginBottom: 8, padding: 8 }}
            />

            <TextInput
                placeholder="Age"
                value={age}
                onChangeText={setAge}
                keyboardType="numeric"
                style={{ borderWidth: 1, marginBottom: 8, padding: 8 }}
            />

            <Text>Gender</Text>
            <Picker
                selectedValue={gender}
                onValueChange={(v) => setGender(v)}
            >
                <Picker.Item label="Unspecified" value="unspecified" />
                <Picker.Item label="Female" value="female" />
                <Picker.Item label="Male" value="male" />
                <Picker.Item label="Non-binary" value="nonbinary" />
            </Picker>

            <TextInput
                placeholder="Hobbies (comma separated)"
                value={hobbies}
                onChangeText={setHobbies}
                style={{ borderWidth: 1, marginBottom: 8, padding: 8 }}
            />

            <Button title="Create Account" onPress={handleSignup} />
        </ScrollView>
    )
}
