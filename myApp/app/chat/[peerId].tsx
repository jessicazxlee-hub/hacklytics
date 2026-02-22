import React, { useEffect, useState, useRef } from 'react'
import {
    View,
    Text,
    FlatList,
    TextInput,
    Button,
    KeyboardAvoidingView,
    Platform,
} from 'react-native'
import { useLocalSearchParams } from 'expo-router'
import { auth, db } from '../../lib/firebase'
import {
    collection,
    addDoc,
    query,
    orderBy,
    onSnapshot,
    serverTimestamp,
} from 'firebase/firestore'
import { io } from 'socket.io-client'

type ChatMessage = {
    id?: string
    from: string
    text: string
    room?: string
    createdAt?: any
}

export default function ChatScreen() {
    const params = useLocalSearchParams()
    const peerId =
        typeof params.peerId === 'string' ? params.peerId : null

    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [text, setText] = useState('')

    const socketRef = useRef<ReturnType<typeof io> | null>(null)
    const roomIdRef = useRef<string | null>(null)

    useEffect(() => {
        if (!peerId) return

        let unsubscribe: () => void = () => { }

        async function init() {
            const user = auth.currentUser
            if (!user) return

            const roomId = [user.uid, peerId].sort().join('_')
            roomIdRef.current = roomId

            const msgsRef = collection(db, 'messages', roomId, 'msgs')
            const q = query(msgsRef, orderBy('createdAt', 'asc'))

            unsubscribe = onSnapshot(q, (snap) => {
                const list: ChatMessage[] = snap.docs.map(d => ({
                    id: d.id,
                    ...(d.data() as Omit<ChatMessage, 'id'>),
                }))
                setMessages(list)
            })

            const token = await user.getIdToken()
            const socket = io('http://localhost:4000', {
                query: { token },
            })

            socketRef.current = socket
            socket.emit('join', roomId)

            socket.on('message', (m: ChatMessage) => {
                if (m.room === roomId) {
                    setMessages(prev => [...prev, m])
                }
            })
        }

        init()

        return () => {
            unsubscribe()
            socketRef.current?.disconnect()
            socketRef.current = null
        }
    }, [peerId])

    async function send() {
        const user = auth.currentUser
        const roomId = roomIdRef.current
        if (!user || !roomId || !text.trim()) return

        socketRef.current?.emit('message', {
            toRoom: roomId,
            text,
        })

        await addDoc(collection(db, 'messages', roomId, 'msgs'), {
            from: user.uid,
            text,
            createdAt: serverTimestamp(),
        })

        setText('')
    }

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={{ flex: 1 }}
        >
            <View style={{ flex: 1, padding: 12 }}>
                <FlatList
                    data={messages}
                    keyExtractor={(i) => i.id ?? Math.random().toString()}
                    renderItem={({ item }) => (
                        <View
                            style={{
                                padding: 8,
                                backgroundColor:
                                    item.from === auth.currentUser?.uid
                                        ? '#DCF8C6'
                                        : '#FFF',
                                marginVertical: 4,
                                borderRadius: 8,
                            }}
                        >
                            <Text>{item.text}</Text>
                        </View>
                    )}
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
                <Button title="Send" onPress={send} />
            </View>
        </KeyboardAvoidingView>
    )
}
