import React, { useEffect } from 'react'
import { Stack } from 'expo-router'
import { auth } from './lib/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import { useRouter } from 'expo-router'
import { View, ActivityIndicator } from 'react-native'

export default function Index() {
    const router = useRouter()

    useEffect(() => {
        const unsub = onAuthStateChanged(auth, (user) => {
            if (user) router.replace('(tabs)')
            else router.replace('/create-account')
        })
        return unsub
    }, [])

    return (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator />
        </View>
    )
}
