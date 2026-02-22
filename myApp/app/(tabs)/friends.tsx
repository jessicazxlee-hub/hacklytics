import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, ActivityIndicator } from 'react-native'
import { getFriends, type FriendListItem } from '../../lib/backend'

export default function Friends() {
    const [friends, setFriends] = useState<FriendListItem[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let mounted = true

        async function load() {
            try {
                const items = await getFriends()
                if (mounted) {
                    setFriends(items)
                }
            } catch (err: unknown) {
                if (mounted) {
                    if (typeof err === 'object' && err !== null && 'message' in err) {
                        alert(String((err as { message: unknown }).message))
                    } else {
                        alert('Failed to load friends')
                    }
                }
            } finally {
                if (mounted) {
                    setLoading(false)
                }
            }
        }
        load()

        return () => {
            mounted = false
        }
    }, [])

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Friends</Text>
            <Text style={{ color: '#666', marginBottom: 8 }}>
                Friend list now loads from the backend. Chat migration comes next.
            </Text>
            {loading ? (
                <ActivityIndicator />
            ) : null}
            <FlatList
                data={friends}
                keyExtractor={i => i.user.id}
                renderItem={({ item }) => (
                    <View style={{ padding: 12, borderBottomWidth: 1 }}>
                        <Text style={{ fontWeight: '600' }}>
                            {item.user.display_name ?? 'Unnamed'}
                        </Text>
                        <Text>{item.user.neighborhood ?? ''}</Text>
                        <Text>
                            {item.user.hobbies.join(', ')}
                        </Text>
                    </View>
                )}
                ListEmptyComponent={
                    !loading ? <Text style={{ color: '#666' }}>No friends yet.</Text> : null
                }
            />
        </View>
    )
}
