import React, { useEffect } from 'react'
import { useRouter } from 'expo-router'
import { auth } from '../lib/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import { View, ActivityIndicator } from 'react-native'

export default function Index() {
    const router = useRouter()

    useEffect(() => {
        const unsub = onAuthStateChanged(auth, (user) => {
            if (user) router.replace('/(tabs)')
            else router.replace('/sign-in')
        })
        return unsub
    }, [router])

    return (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator />
        </View>
    )
}
