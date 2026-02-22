import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity } from 'react-native'
import { db } from '../../lib/firebase'
import { collection, getDocs } from 'firebase/firestore'
import { useRouter } from 'expo-router'

type Friend = {
    id: string
    name?: string
    hobbies?: string[]
}

export default function Friends() {
    const router = useRouter()
    const [friends, setFriends] = useState<Friend[]>([])

    useEffect(() => {
        async function load() {
            const snap = await getDocs(collection(db, 'users'))
            const users: Friend[] = snap.docs.map(d => ({
                id: d.id,
                ...(d.data() as Omit<Friend, 'id'>),
            }))
            setFriends(users)
        }
        load()
    }, [])

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Friends</Text>
            <FlatList
                data={friends}
                keyExtractor={i => i.id}
                renderItem={({ item }) => (
                    <TouchableOpacity
                        style={{ padding: 12, borderBottomWidth: 1 }}
                        onPress={() => router.push(`/chat/${item.id}`)}
                    >
                        <Text style={{ fontWeight: '600' }}>
                            {item.name ?? 'Unnamed'}
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
