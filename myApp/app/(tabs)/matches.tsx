import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity } from 'react-native'
import { db } from '../lib/firebase'
import { collection, getDocs } from 'firebase/firestore'
import { useRouter } from 'expo-router'

type MatchUser = {
    id: string
    name?: string
    hobbies?: string[]
    location?: {
        lat?: number
        lng?: number
        latitude?: number
        longitude?: number
    }
}

type LatLng = {
    lat: number
    lng: number
}

function distanceKm(a: LatLng, b: LatLng): number {
    const R = 6371
    const toRad = (v: number) => (v * Math.PI) / 180
    const dLat = toRad(b.lat - a.lat)
    const dLon = toRad(b.lng - a.lng)
    const lat1 = toRad(a.lat)
    const lat2 = toRad(b.lat)
    const aa =
        Math.sin(dLat / 2) ** 2 +
        Math.sin(dLon / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2)
    const c = 2 * Math.atan2(Math.sqrt(aa), Math.sqrt(1 - aa))
    return R * c
}

export default function Matches() {
    const router = useRouter()
    const [matches, setMatches] = useState<MatchUser[]>([])

    useEffect(() => {
        async function load() {
            const snap = await getDocs(collection(db, 'users'))
            const users: MatchUser[] = snap.docs.map(d => ({
                id: d.id,
                ...(d.data() as Omit<MatchUser, 'id'>),
            }))
            setMatches(users)
        }
        load()
    }, [])

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Matches</Text>
            <FlatList
                data={matches}
                keyExtractor={i => i.id}
                renderItem={({ item }) => (
                    <TouchableOpacity
                        style={{ padding: 12, borderBottomWidth: 1 }}
                        onPress={() => router.push(`/friends?userId=${item.id}`)}
                    >
                        <Text style={{ fontWeight: '600' }}>
                            {item.name ?? 'No name'}
                        </Text>
                        <Text>
                            {item.hobbies?.join(', ') ?? ''}
                        </Text>
                    </TouchableOpacity>
                )}
            />
        </View>
    )
}