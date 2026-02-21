import React, { useEffect, useMemo, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity, TextInput } from 'react-native'
import { useRouter } from 'expo-router'
import { auth, getAllUsers, getProfile, listFriendIds } from '../lib/firebase'
import type { UserProfile } from '../types'

type MatchUser = { id: string } & UserProfile

type LatLng = { lat: number; lng: number }

function normalizeLatLng(loc?: any): LatLng | null {
    if (!loc) return null
    const lat = loc.lat ?? loc.latitude
    const lng = loc.lng ?? loc.longitude
    if (typeof lat !== 'number' || typeof lng !== 'number') return null
    return { lat, lng }
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

function hobbyOverlapScore(a?: string[], b?: string[]) {
    const A = new Set((a ?? []).map(x => x.toLowerCase().trim()).filter(Boolean))
    const B = new Set((b ?? []).map(x => x.toLowerCase().trim()).filter(Boolean))
    let count = 0
    for (const x of A) if (B.has(x)) count++
    return count
}

export default function Matches() {
    const router = useRouter()

    const [me, setMe] = useState<(UserProfile & { id: string }) | null>(null)
    const [allUsers, setAllUsers] = useState<MatchUser[]>([])
    const [friendIds, setFriendIds] = useState<Set<string>>(new Set())
    const [hobbyQuery, setHobbyQuery] = useState('') // optional filter
    const [maxDistanceKm, setMaxDistanceKm] = useState<number>(10)

    useEffect(() => {
        async function load() {
            const u = auth.currentUser
            if (!u) return

            const [profile, users, fids] = await Promise.all([
                getProfile(u.uid),
                getAllUsers(),
                listFriendIds(u.uid),
            ])

            setMe({ id: u.uid, ...(profile ?? {}) })
            setAllUsers(users)

            setFriendIds(new Set(fids))

            const pref = profile?.prefs?.maxDistanceKm
            if (typeof pref === 'number' && Number.isFinite(pref)) setMaxDistanceKm(pref)
        }
        load()
    }, [])

    const filtered = useMemo(() => {
        const u = auth.currentUser
        if (!u || !me) return []

        const meLoc = normalizeLatLng(me.location)
        const q = hobbyQuery.trim().toLowerCase()

        const candidates = allUsers
            .filter(x => x.id !== u.uid) // not me
            .filter(x => !friendIds.has(x.id)) // not already friend
            .map(x => {
                const overlap = hobbyOverlapScore(me.hobbies, x.hobbies)
                const dist =
                    meLoc && normalizeLatLng(x.location)
                        ? distanceKm(meLoc, normalizeLatLng(x.location) as LatLng)
                        : null

                return { user: x, overlap, dist }
            })
            .filter(x => x.overlap > 0) // must share at least 1 hobby
            .filter(x => {
                // optional text hobby filter (e.g. "climbing")
                if (!q) return true
                const hobbies = (x.user.hobbies ?? []).join(',').toLowerCase()
                return hobbies.includes(q)
            })
            .filter(x => {
                // distance filter only applies if both have locations
                if (x.dist === null) return true
                return x.dist <= maxDistanceKm
            })
            .sort((a, b) => {
                // sort by overlap desc, then distance asc (nulls last)
                if (b.overlap !== a.overlap) return b.overlap - a.overlap
                if (a.dist === null && b.dist === null) return 0
                if (a.dist === null) return 1
                if (b.dist === null) return -1
                return a.dist - b.dist
            })

        return candidates
    }, [allUsers, friendIds, hobbyQuery, maxDistanceKm, me])

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Matches</Text>

            <TextInput
                value={hobbyQuery}
                onChangeText={setHobbyQuery}
                placeholder="Filter hobby (optional)"
                style={{ borderWidth: 1, padding: 10, borderRadius: 8, marginBottom: 10 }}
            />

            <Text style={{ marginBottom: 10, opacity: 0.8 }}>
                Max distance: {maxDistanceKm} km (edit in Profile prefs)
            </Text>

            <FlatList
                data={filtered}
                keyExtractor={i => i.user.id}
                renderItem={({ item }) => {
                    const u = item.user
                    return (
                        <TouchableOpacity
                            style={{ padding: 12, borderBottomWidth: 1 }}
                            onPress={() => router.push(`/user/${u.id}`)}
                        >
                            <Text style={{ fontWeight: '600' }}>{u.name ?? 'No name'}</Text>
                            <Text>{u.hobbies?.join(', ') ?? ''}</Text>
                            <Text style={{ opacity: 0.8 }}>
                                Shared hobbies: {item.overlap}
                                {item.dist === null ? '' : ` • ~${item.dist.toFixed(1)} km away`}
                            </Text>
                        </TouchableOpacity>
                    )
                }}
                ListEmptyComponent={
                    <Text style={{ padding: 12, opacity: 0.7 }}>
                        No matches yet. Add hobbies + location in Profile.
                    </Text>
                }
            />
        </View>
    )
}