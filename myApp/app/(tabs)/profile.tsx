import React, { useEffect, useState } from 'react'
import { View, Text, TextInput, Button, Alert } from 'react-native'
import { auth, createProfile, getProfile } from '../lib/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import { useRouter } from 'expo-router'
import * as Location from 'expo-location'

type ProfileState = {
    name: string
    hobbies: string
    maxDistanceKm: string
}

export default function Profile() {
    const router = useRouter()
    const [profile, setProfile] = useState<ProfileState>({
        name: '',
        hobbies: '',
        maxDistanceKm: '10',
    })

    useEffect(() => {
        const unsub = onAuthStateChanged(auth, async u => {
            if (!u) {
                router.replace('/create-account')
                return
            }

            const p = await getProfile(u.uid)
            if (p) {
                setProfile({
                    name: p.name ?? '',
                    hobbies: (p.hobbies ?? []).join(', '),
                    maxDistanceKm: String(p.prefs?.maxDistanceKm ?? 10),
                })
            }
        })

        return unsub
    }, [router])

    async function save() {
        const user = auth.currentUser
        if (!user) return

        const maxDistance = Number(profile.maxDistanceKm)
        await createProfile(user.uid, {
            name: profile.name,
            hobbies: profile.hobbies
                .split(',')
                .map(s => s.trim())
                .filter(Boolean),
            prefs: {
                maxDistanceKm: Number.isFinite(maxDistance) ? maxDistance : 10,
            },
        })

        Alert.alert('Saved', 'Profile updated.')
    }

    async function updateMyLocation() {
        const user = auth.currentUser
        if (!user) return

        const { status } = await Location.requestForegroundPermissionsAsync()
        if (status !== 'granted') {
            Alert.alert('Permission denied', 'Location permission is required to update your location.')
            return
        }

        const pos = await Location.getCurrentPositionAsync({})
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude

        await createProfile(user.uid, {
            location: { lat, lng },
        })

        Alert.alert('Updated', 'Location saved.')
    }

    return (
        <View style={{ flex: 1, padding: 12, gap: 10 }}>
            <Text style={{ fontSize: 20, fontWeight: '600' }}>Profile</Text>

            <TextInput
                value={profile.name}
                onChangeText={t => setProfile(p => ({ ...p, name: t }))}
                placeholder="Name"
                style={{ borderWidth: 1, padding: 10, borderRadius: 8 }}
            />

            <TextInput
                value={profile.hobbies}
                onChangeText={t => setProfile(p => ({ ...p, hobbies: t }))}
                placeholder="Hobbies (comma separated)"
                style={{ borderWidth: 1, padding: 10, borderRadius: 8 }}
            />

            <TextInput
                value={profile.maxDistanceKm}
                onChangeText={t => setProfile(p => ({ ...p, maxDistanceKm: t }))}
                placeholder="Max distance (km)"
                keyboardType="numeric"
                style={{ borderWidth: 1, padding: 10, borderRadius: 8 }}
            />

            <Button title="Save" onPress={save} />
            <Button title="Update my location" onPress={updateMyLocation} />
        </View>
    )
}