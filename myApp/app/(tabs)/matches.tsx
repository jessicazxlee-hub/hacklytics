import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, Button, ActivityIndicator } from 'react-native'
import { getMatches, sendFriendRequest, type MatchItem } from '../../lib/backend'

export default function Matches() {
    const [matches, setMatches] = useState<MatchItem[]>([])
    const [loading, setLoading] = useState(true)
    const [sendingUserId, setSendingUserId] = useState<string | null>(null)

    useEffect(() => {
        let mounted = true

        async function load() {
            try {
                const items = await getMatches()
                if (mounted) {
                    setMatches(items)
                }
            } catch (err: unknown) {
                if (mounted) {
                    if (typeof err === 'object' && err !== null && 'message' in err) {
                        alert(String((err as { message: unknown }).message))
                    } else {
                        alert('Failed to load matches')
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

    async function handleSendRequest(userId: string) {
        if (sendingUserId) return
        setSendingUserId(userId)
        try {
            const result = await sendFriendRequest(userId)
            alert(result.created ? 'Friend request sent' : 'Friend request already pending')
            setMatches(prev => prev.filter(match => match.user.id !== userId))
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
            } else {
                alert('Failed to send friend request')
            }
        } finally {
            setSendingUserId(null)
        }
    }

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Matches</Text>
            {loading ? <ActivityIndicator /> : null}
            <FlatList
                data={matches}
                keyExtractor={i => i.user.id}
                renderItem={({ item }) => (
                    <View style={{ padding: 12, borderBottomWidth: 1 }}>
                        <Text style={{ fontWeight: '600' }}>
                            {item.user.display_name ?? 'No name'}
                        </Text>
                        <Text>{item.user.neighborhood ?? ''}</Text>
                        <Text>
                            {item.user.hobbies.join(', ')}
                        </Text>
                        <Text style={{ color: '#555', marginTop: 4 }}>
                            Score: {item.score} | Same neighborhood: {item.signals.same_neighborhood ? 'yes' : 'no'}
                        </Text>
                        <Text style={{ color: '#555', marginBottom: 8 }}>
                            Overlap: {item.signals.overlap_hobbies.join(', ') || 'none'}
                        </Text>
                        <Button
                            title={sendingUserId === item.user.id ? 'Sending...' : 'Send Friend Request'}
                            onPress={() => handleSendRequest(item.user.id)}
                            disabled={sendingUserId !== null}
                        />
                    </View>
                )}
                ListEmptyComponent={
                    !loading ? <Text style={{ color: '#666' }}>No matches yet.</Text> : null
                }
            />
        </View>
    )
}
