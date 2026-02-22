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
import { Link, useRouter } from 'expo-router'

export default function CreateAccount() {
    const router = useRouter()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [age, setAge] = useState('')
    const [gender, setGender] = useState<'unspecified' | 'female' | 'male' | 'nonbinary'>('unspecified')
    const [hobbies, setHobbies] = useState('')

    async function handleSignup() {
        const user = await signupWithEmail(email, password)

        router.replace('/(tabs)')
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
            <Link href="/sign-in" style={{ width: '100%', textAlign: 'center', margin: 10, padding: 10, color: 'white', backgroundColor: 'green' }}>Sign in</Link>
        </ScrollView>
    )
}