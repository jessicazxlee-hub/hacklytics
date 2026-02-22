import React, { useEffect, useState } from 'react'
import { View, Text, TextInput, Button } from 'react-native'
import { auth, signOutUser } from '../../lib/firebase'
import { getMeProfile, patchMeProfile } from '../../lib/backend'
import { onAuthStateChanged } from 'firebase/auth'
import { useRouter } from 'expo-router'

type ProfileState = {
    displayName: string
    hobbies: string
}

export default function Profile() {
    const router = useRouter()
    const [profile, setProfile] = useState<ProfileState>({
        displayName: '',
        hobbies: '',
    })

    useEffect(() => {
        const unsub = onAuthStateChanged(auth, async (u) => {
            if (!u) {
                router.replace('/sign-in')
                return
            }

            try {
                const p = await getMeProfile()
                setProfile({
                    displayName: p.display_name ?? '',
                    hobbies: (p.hobbies ?? []).join(', '),
                })
            } catch (err: unknown) {
                if (typeof err === 'object' && err !== null && 'message' in err) {
                    alert(String((err as { message: unknown }).message))
                } else {
                    alert('Failed to load profile')
                }
            }
        })

        return unsub
    }, [router])

    async function save() {
        try {
            const updated = await patchMeProfile({
                display_name: profile.displayName.trim() || null,
                hobbies: profile.hobbies
                    .split(',')
                    .map(s => s.trim().toLowerCase())
                    .filter(Boolean),
            })
            setProfile({
                displayName: updated.display_name ?? '',
                hobbies: (updated.hobbies ?? []).join(', '),
            })
            alert('Saved')
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
            } else {
                alert('Failed to save profile')
            }
        }
    }

    async function handleLogout() {
        await signOutUser()
        router.replace('/sign-in')
    }

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20 }}>Profile</Text>

            <TextInput
                value={profile.displayName}
                onChangeText={(t) =>
                    setProfile(p => ({ ...p, displayName: t }))
                }
                placeholder="Display name"
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
            <View style={{ marginTop: 12 }}>
                <Button title="Log out" onPress={handleLogout} color="#c00" />
            </View>
        </View>
    )
}
