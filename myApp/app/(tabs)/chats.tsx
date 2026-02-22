import React, { useEffect, useState } from 'react'
import { View, Text, FlatList, ActivityIndicator, Pressable } from 'react-native'
import { useRouter } from 'expo-router'

import { getChats, type GroupChatSummary } from '../../lib/backend'

export default function ChatsTab() {
    const router = useRouter()
    const [chats, setChats] = useState<GroupChatSummary[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let mounted = true

        async function load() {
            try {
                const items = await getChats()
                if (mounted) {
                    setChats(items)
                }
            } catch (err: unknown) {
                if (mounted) {
                    if (typeof err === 'object' && err !== null && 'message' in err) {
                        alert(String((err as { message: unknown }).message))
                    } else {
                        alert('Failed to load chats')
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
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Chats</Text>
            <Text style={{ color: '#666', marginBottom: 8 }}>
                Group chats only. Chat opens when you are in a confirmed group.
            </Text>
            {loading ? <ActivityIndicator /> : null}
            <FlatList
                data={chats}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                    <Pressable
                        onPress={() =>
                            router.push({
                                pathname: '/chat/[groupMatchId]',
                                params: { groupMatchId: item.id },
                            })
                        }
                        style={{ padding: 12, borderBottomWidth: 1 }}
                    >
                        <Text style={{ fontWeight: '600' }}>
                            {item.venue_name ?? (item.group_match_mode === 'chat_only' ? 'Chat-only group' : 'Group chat')}
                        </Text>
                        <Text>
                            {item.member_count} members • {item.group_match_mode} • {item.status}
                        </Text>
                        <Text style={{ color: '#555', marginTop: 4 }}>
                            {item.last_message?.body_preview ?? 'No messages yet'}
                        </Text>
                    </Pressable>
                )}
                ListEmptyComponent={
                    !loading ? <Text style={{ color: '#666' }}>No group chats yet.</Text> : null
                }
            />
        </View>
    )
}
