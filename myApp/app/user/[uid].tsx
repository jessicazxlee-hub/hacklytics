import React, { useEffect, useState } from 'react'
import { View, Text, Button, ActivityIndicator, Alert } from 'react-native'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { auth, addFriend, getProfile, listFriendIds } from '../lib/firebase'

export default function UserProfileScreen() {
    const { uid } = useLocalSearchParams()
    const otherUid = typeof uid === 'string' ? uid : null
    const router = useRouter()

    const [loading, setLoading] = useState(true)
    const [profile, setProfile] = useState<any>(null)
    const [isFriend, setIsFriend] = useState(false)

    useEffect(() => {
        async function load() {
            try {
                const me = auth.currentUser
                if (!me || !otherUid) return

                const p = await getProfile(otherUid)
                setProfile(p)

                const fids = await listFriendIds(me.uid)
                setIsFriend(fids.includes(otherUid))
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [otherUid])

    async function onLike() {
        const me = auth.currentUser
        if (!me || !otherUid) return
        await addFriend(me.uid, otherUid)
        setIsFriend(true)
        Alert.alert('Added', 'You are now friends!')
    }

    if (loading) return <ActivityIndicator style={{ flex: 1 }} />

    return (
        <View style={{ flex: 1, padding: 16, gap: 10 }}>
            <Text style={{ fontSize: 22, fontWeight: '600' }}>{profile?.name ?? 'User'}</Text>
            <Text>Hobbies: {(profile?.hobbies ?? []).join(', ')}</Text>
            <Text>Age: {profile?.age ?? '—'}</Text>
            <Text>Gender: {profile?.gender ?? '—'}</Text>

            {!isFriend ? (
                <Button title="Like / Add Friend" onPress={onLike} />
            ) : (
                <Button title="Open chat" onPress={() => router.push(`/chat/${otherUid}`)} />
            )}
        </View>
    )
}