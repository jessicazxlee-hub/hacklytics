import React, { useEffect, useMemo, useState } from 'react'
import { View, Text, ActivityIndicator, TextInput, Button, Alert } from 'react-native'
import MapView, { Marker, Callout } from 'react-native-maps'
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

export default function MapScreen() {
    const [loading, setLoading] = useState(true)
    const [me, setMe] = useState<(UserProfile & { id: string }) | null>(null)
    const [friends, setFriends] = useState<Array<UserProfile & { id: string }>>([])
    const [poiQuery, setPoiQuery] = useState('rock climbing gym')
    const [pois, setPois] = useState<POI[]>([])
    const [poiLoading, setPoiLoading] = useState(false)

    useEffect(() => {
        async function load() {
            try {
                const u = auth.currentUser
                if (!u) return

                const profile = await getProfile(u.uid)
                setMe({ id: u.uid, ...(profile ?? {}) })

                const ids = await listFriendIds(u.uid)
                const f = await getUsersByIds(ids)
                setFriends(f)
            } finally {
                setLoading(false)
            }
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
            if (results.length === 0) {
                Alert.alert(
                    'No POIs returned',
                    mapConfig?.MAPBOX_TOKEN ? 'Try a different query.' : 'Add a Mapbox token in app/mapConfig.ts to enable POIs.'
                )
            }
        } catch (e: any) {
            Alert.alert('Map error', e?.message ?? 'Failed to load POIs.')
        } finally {
            setPoiLoading(false)
        }
    }

    if (loading) {
        return (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                <ActivityIndicator />
            </View>
        )
    }

    return (
        <View style={{ flex: 1 }}>
            <View style={{ padding: 10, gap: 8 }}>
                <Text style={{ fontSize: 18, fontWeight: '600' }}>Map</Text>

                <TextInput
                    value={poiQuery}
                    onChangeText={setPoiQuery}
                    placeholder="Search POIs (e.g., rock climbing gym)"
                    style={{ borderWidth: 1, padding: 10, borderRadius: 8 }}
                />

                <Button title={poiLoading ? 'Searching…' : 'Search POIs'} onPress={searchPOIs} disabled={poiLoading} />

                {!myCenter && (
                    <Text style={{ color: '#a00' }}>
                        Your location is missing. Go to Profile → “Update my location”.
                    </Text>
                )}
            </View>

            <MapView
                style={{ flex: 1 }}
                initialRegion={{
                    latitude: myCenter?.latitude ?? 33.7756,
                    longitude: myCenter?.longitude ?? -84.3963,
                    latitudeDelta: 0.08,
                    longitudeDelta: 0.08,
                }}
            >
                {myCenter && (
                    <Marker coordinate={myCenter} pinColor="blue">
                        <Callout>
                            <Text>Me</Text>
                        </Callout>
                    </Marker>
                )}

                {friends
                    .map(f => ({ id: f.id, name: f.name, loc: normalizeLatLng(f.location), hobbies: f.hobbies }))
                    .filter(x => x.loc)
                    .map(f => (
                        <Marker key={f.id} coordinate={f.loc as any}>
                            <Callout>
                                <Text style={{ fontWeight: '600' }}>{f.name ?? 'Friend'}</Text>
                                <Text>{(f.hobbies ?? []).join(', ')}</Text>
                            </Callout>
                        </Marker>
                    ))}

                {pois.map(p => (
                    <Marker key={p.id} coordinate={p.coords} pinColor="gold">
                        <Callout>
                            <Text>{p.name}</Text>
                        </Callout>
                    </Marker>
                ))}
            </MapView>
        </View>
    )
}