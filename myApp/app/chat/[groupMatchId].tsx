import React, { useEffect, useState } from 'react'
import {
    View,
    Text,
    FlatList,
    TextInput,
    Button,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
} from 'react-native'
import { useLocalSearchParams } from 'expo-router'

import {
    getChatMessages,
    sendChatMessage,
    type GroupChatMessage,
} from '../../lib/backend'

export default function GroupChatScreen() {
    const params = useLocalSearchParams()
    const groupMatchId =
        typeof params.groupMatchId === 'string' ? params.groupMatchId : null

    const [messages, setMessages] = useState<GroupChatMessage[]>([])
    const [loading, setLoading] = useState(true)
    const [sending, setSending] = useState(false)
    const [text, setText] = useState('')

    useEffect(() => {
        let mounted = true

        async function load() {
            if (!groupMatchId) {
                if (mounted) {
                    setLoading(false)
                }
                return
            }

            try {
                const items = await getChatMessages(groupMatchId)
                if (mounted) {
                    setMessages(items)
                }
            } catch (err: unknown) {
                if (mounted) {
                    if (typeof err === 'object' && err !== null && 'message' in err) {
                        alert(String((err as { message: unknown }).message))
                    } else {
                        alert('Failed to load chat messages')
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
    }, [groupMatchId])

    async function handleSend() {
        if (!groupMatchId || sending) return
        if (!text.trim()) return

        setSending(true)
        try {
            const message = await sendChatMessage(groupMatchId, text)
            setMessages((prev) => [...prev, message])
            setText('')
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
            } else {
                alert('Failed to send message')
            }
        } finally {
            setSending(false)
        }
    }

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={{ flex: 1 }}
        >
            <View style={{ flex: 1, padding: 12 }}>
                <Text style={{ fontSize: 20, marginBottom: 8 }}>Group Chat</Text>
                <Text style={{ color: '#666', marginBottom: 8 }}>
                    {groupMatchId ? `Group: ${groupMatchId}` : 'Missing group chat id'}
                </Text>
                {loading ? <ActivityIndicator /> : null}
                <FlatList
                    data={messages}
                    keyExtractor={(item) => item.id}
                    renderItem={({ item }) => (
                        <View
                            style={{
                                padding: 8,
                                backgroundColor: '#FFF',
                                marginVertical: 4,
                                borderRadius: 8,
                                borderWidth: 1,
                                borderColor: '#ddd',
                            }}
                        >
                            <Text style={{ fontWeight: '600' }}>
                                {item.sender.display_name ?? item.sender.id}
                            </Text>
                            <Text>{item.body}</Text>
                        </View>
                    )}
                    ListEmptyComponent={
                        !loading ? (
                            <Text style={{ color: '#666' }}>
                                No messages yet.
                            </Text>
                        ) : null
                    }
                />
            </View>

            <View style={{ flexDirection: 'row', padding: 8, gap: 8 }}>
                <TextInput
                    value={text}
                    onChangeText={setText}
                    placeholder="Message"
                    style={{
                        flex: 1,
                        borderWidth: 1,
                        padding: 8,
                        borderRadius: 6,
                    }}
                />
                <Button
                    title={sending ? 'Sending...' : 'Send'}
                    onPress={handleSend}
                    disabled={sending || !groupMatchId}
                />
            </View>
        </KeyboardAvoidingView>
    )
}
