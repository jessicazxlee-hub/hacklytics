import React, { useEffect, useState } from 'react'
import { View, Text, TextInput, Button } from 'react-native'
import { auth } from '../lib/firebase'
import { getProfile, createProfile, signOutUser } from '../lib/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import { useRouter } from 'expo-router'

type ProfileState = {
    name: string
    hobbies: string
}

export default function Profile() {
    const router = useRouter()
    const [profile, setProfile] = useState<ProfileState>({
        name: '',
        hobbies: '',
    })

    async function handleLogout() {
        await signOutUser()
        router.replace('/create-account')
    }

    useEffect(() => {
        const unsub = onAuthStateChanged(auth, async (u) => {
            if (!u) {
                router.replace('/create-account')
                return
            }

            const p = await getProfile(u.uid)
            if (p) {
                setProfile({
                    name: p.name ?? '',
                    hobbies: (p.hobbies ?? []).join(', '),
                })
            }
        })

        return unsub
    }, [router])

    async function save() {
        const user = auth.currentUser
        if (!user) return

        await createProfile(user.uid, {
            name: profile.name,
            hobbies: profile.hobbies
                .split(',')
                .map(s => s.trim())
                .filter(Boolean),
        })

        alert('Saved')
    }

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20 }}>Profile</Text>

            <TextInput
                value={profile.name}
                onChangeText={(t) =>
                    setProfile(p => ({ ...p, name: t }))
                }
                placeholder="Name"
                style={{ borderWidth: 1, marginVertical: 8, padding: 8 }}
            />

            <TextInput
                value={profile.hobbies}
                onChangeText={(t) =>
                    setProfile(p => ({ ...p, hobbies: t }))
                }
                placeholder="Hobbies (comma separated)"
                style={{ borderWidth: 1, marginVertical: 8, padding: 8 }}
            />

            <Button title="Save" onPress={save} />

            <Button title="Log out" onPress={handleLogout} color="#c00" />
            
        </View>
    )
}