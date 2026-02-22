import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity } from 'react-native'
import { db } from '../../lib/firebase'
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
