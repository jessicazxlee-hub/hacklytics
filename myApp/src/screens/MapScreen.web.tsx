import React, { useEffect, useMemo, useState } from 'react'
import { View, Text, TextInput, Button, Alert, Linking, ScrollView } from 'react-native'
import { auth, getProfile, getUsersByIds, listFriendIds } from '../lib/firebase'
import type { POI, UserProfile } from '../types'

let mapConfig: { MAPBOX_TOKEN?: string } = {}
try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const cfg = require('../mapConfig')
    mapConfig = cfg?.default ?? cfg
} catch {
    try {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const cfg2 = require('../mapConfig.example')
        mapConfig = cfg2?.default ?? cfg2
    } catch {
        mapConfig = {}
    }
}

function normalizeLatLng(loc?: any): { latitude: number; longitude: number } | null {
    if (!loc) return null
    const lat = loc.lat ?? loc.latitude
    const lng = loc.lng ?? loc.longitude
    if (typeof lat !== 'number' || typeof lng !== 'number') return null
    return { latitude: lat, longitude: lng }
}

async function fetchMapboxPOIs(queryText: string, center: { latitude: number; longitude: number }): Promise<POI[]> {
    const token = mapConfig?.MAPBOX_TOKEN
    if (!token || token === 'YOUR_MAPBOX_TOKEN') return []

    const q = encodeURIComponent(queryText)
    const url =
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${q}.json` +
        `?limit=10&proximity=${center.longitude},${center.latitude}&access_token=${token}`

    const res = await fetch(url)
    if (!res.ok) throw new Error(`Mapbox error: ${res.status}`)
    const data = await res.json()

    const features = Array.isArray(data?.features) ? data.features : []
    return features
        .map((f: any, idx: number) => {
            const name = f?.text ?? f?.place_name ?? 'POI'
            const centerArr = f?.center
            if (!Array.isArray(centerArr) || centerArr.length < 2) return null
            const [lng, lat] = centerArr
            if (typeof lat !== 'number' || typeof lng !== 'number') return null
            return {
                id: f?.id ?? `${idx}`,
                name,
                coords: { latitude: lat, longitude: lng },
            } as POI
        })
        .filter(Boolean)
}

export default function MapScreenWeb() {
    const [me, setMe] = useState<(UserProfile & { id: string }) | null>(null)
    const [friends, setFriends] = useState<Array<UserProfile & { id: string }>>([])
    const [poiQuery, setPoiQuery] = useState('rock climbing gym')
    const [pois, setPois] = useState<POI[]>([])
    const [poiLoading, setPoiLoading] = useState(false)

    useEffect(() => {
        async function load() {
            const u = auth.currentUser
            if (!u) return
            const profile = await getProfile(u.uid)
            setMe({ id: u.uid, ...(profile ?? {}) })

            const ids = await listFriendIds(u.uid)
            const f = await getUsersByIds(ids)
            setFriends(f)
        }
        load()
    }, [])

    const myCenter = useMemo(() => normalizeLatLng(me?.location), [me?.location])

    async function searchPOIs() {
        if (!myCenter) {
            Alert.alert('Add location', 'Update your location in Profile first.')
            return
        }
        setPoiLoading(true)
        try {
            const results = await fetchMapboxPOIs(poiQuery.trim(), myCenter)
            setPois(results)
            if (results.length === 0 && (!mapConfig?.MAPBOX_TOKEN || mapConfig.MAPBOX_TOKEN === 'YOUR_MAPBOX_TOKEN')) {
                Alert.alert('Mapbox token missing', 'Add MAPBOX_TOKEN in app/mapConfig.ts to enable POI search.')
            }
        } catch (e: any) {
            Alert.alert('Map error', e?.message ?? 'Failed to load POIs.')
        } finally {
            setPoiLoading(false)
        }
    }

    return (
        <ScrollView contentContainerStyle={{ padding: 16, gap: 10 }}>
            <Text style={{ fontSize: 18, fontWeight: '600' }}>Map (Web)</Text>
            <Text style={{ opacity: 0.8 }}>
                Native maps aren’t supported on Expo Web. This fallback shows friends + POIs and opens them in Google Maps.
            </Text>

            <Text style={{ fontWeight: '600' }}>Friends</Text>
            {friends.length === 0 ? (
                <Text style={{ opacity: 0.7 }}>No friends yet.</Text>
            ) : (
                friends.map(f => {
                    const loc = normalizeLatLng(f.location)
                    return (
                        <View key={f.id} style={{ paddingVertical: 6 }}>
                            <Text>{f.name ?? 'Friend'}</Text>
                            <Text style={{ opacity: 0.8 }}>{(f.hobbies ?? []).join(', ')}</Text>
                            {loc ? (
                                <Button
                                    title="Open location"
                                    onPress={() =>
                                        Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${loc.latitude},${loc.longitude}`)
                                    }
                                />
                            ) : (
                                <Text style={{ opacity: 0.6 }}>No location saved</Text>
                            )}
                        </View>
                    )
                })
            )}

            <Text style={{ fontWeight: '600', marginTop: 10 }}>POIs</Text>
            <TextInput
                value={poiQuery}
                onChangeText={setPoiQuery}
                placeholder="Search POIs (e.g., rock climbing gym)"
                style={{ borderWidth: 1, padding: 10, borderRadius: 8 }}
            />
            <Button title={poiLoading ? 'Searching…' : 'Search POIs'} onPress={searchPOIs} disabled={poiLoading} />

            {pois.length === 0 ? (
                <Text style={{ opacity: 0.7 }}>No POIs yet.</Text>
            ) : (
                pois.map(p => (
                    <View key={p.id} style={{ paddingVertical: 6 }}>
                        <Text>{p.name}</Text>
                        <Button
                            title="Open in Google Maps"
                            onPress={() =>
                                Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${p.coords.latitude},${p.coords.longitude}`)
                            }
                        />
                    </View>
                ))
            )}
        </ScrollView>
    )
}