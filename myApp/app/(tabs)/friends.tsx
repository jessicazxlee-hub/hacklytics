import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native'
import { useRouter } from 'expo-router'
import { auth, listFriendIds, getUsersByIds } from '../lib/firebase'
import type { UserProfile } from '../types'

type FriendRow = { id: string } & UserProfile

export default function Friends() {
    const router = useRouter()
    const [friends, setFriends] = useState<FriendRow[]>([])
    const [refreshing, setRefreshing] = useState(false)

    async function load() {
        const me = auth.currentUser
        if (!me) return
        const ids = await listFriendIds(me.uid)
        const users = await getUsersByIds(ids)
        setFriends(users)
    }

    useEffect(() => {
        load()
    }, [])

    async function onRefresh() {
        setRefreshing(true)
        try {
            await load()
        } finally {
            setRefreshing(false)
        }
    }

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Friends</Text>
            <FlatList
                data={friends}
                keyExtractor={i => i.id}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
                renderItem={({ item }) => (
                    <TouchableOpacity
                        style={{ padding: 12, borderBottomWidth: 1 }}
                        onPress={() => router.push(`/chat/${item.id}`)}
                    >
                        <Text style={{ fontWeight: '600' }}>{item.name ?? 'Unnamed'}</Text>
                        <Text>{item.hobbies?.join(', ') ?? ''}</Text>
                    </TouchableOpacity>
                )}
                ListEmptyComponent={
                    <Text style={{ padding: 12, opacity: 0.7 }}>
                        No friends yet. Go to Matches and “Like/Add Friend”.
                    </Text>
                }
            />
        </View>
    )
}