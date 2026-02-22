import React, { useCallback, useState } from 'react'
import { ActivityIndicator, Button, FlatList, Text, View } from 'react-native'
import { useFocusEffect, useRouter } from 'expo-router'

import {
    acceptGroupMatch,
    declineGroupMatch,
    getGroupMatches,
    leaveGroupMatch,
    type GroupMatch,
} from '../../lib/backend'

export default function Matches() {
    const router = useRouter()
    const [groups, setGroups] = useState<GroupMatch[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [actingGroupId, setActingGroupId] = useState<string | null>(null)

    const load = useCallback(async (mode: 'initial' | 'refresh' = 'initial') => {
        if (mode === 'refresh') {
            setRefreshing(true)
        } else {
            setLoading(true)
        }
        try {
            const items = await getGroupMatches()
            setGroups(items)
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
            } else {
                alert('Failed to load group matches')
            }
        } finally {
            if (mode === 'refresh') {
                setRefreshing(false)
            } else {
                setLoading(false)
            }
        }
    }, [])

    useFocusEffect(useCallback(() => {
        void load('initial')
    }, [load]))

    async function handleAction(groupId: string, action: 'accept' | 'decline' | 'leave') {
        if (actingGroupId) return
        setActingGroupId(groupId)
        try {
            const updated =
                action === 'accept'
                    ? await acceptGroupMatch(groupId)
                    : action === 'decline'
                        ? await declineGroupMatch(groupId)
                        : await leaveGroupMatch(groupId)

            if (updated.my_member_status === 'declined' || updated.my_member_status === 'left') {
                setGroups(prev => prev.filter(group => group.id !== groupId))
            } else {
                setGroups(prev => prev.map(group => (group.id === groupId ? updated : group)))
            }
        } catch (err: unknown) {
            if (typeof err === 'object' && err !== null && 'message' in err) {
                alert(String((err as { message: unknown }).message))
            } else {
                alert(`Failed to ${action} group match`)
            }
        } finally {
            setActingGroupId(null)
        }
    }

    function canOpenChat(group: GroupMatch) {
        return ['confirmed', 'scheduled', 'completed'].includes(group.status)
    }

    function memberLine(group: GroupMatch) {
        return group.members
            .map(member => {
                const name = member.user.display_name ?? member.user.id.slice(0, 8)
                return `${name} (${member.status})`
            })
            .join(', ')
    }

    return (
        <View style={{ flex: 1, padding: 12 }}>
            <Text style={{ fontSize: 20, marginBottom: 8 }}>Matches</Text>
            <Text style={{ color: '#666', marginBottom: 8 }}>
                Your group matches and invites.
            </Text>
            {loading ? <ActivityIndicator /> : null}

            <FlatList
                data={groups}
                refreshing={refreshing}
                onRefresh={() => void load('refresh')}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => {
                    const isActing = actingGroupId === item.id
                    const acceptedCount = item.member_counts.accepted ?? 0
                    const invitedCount = item.member_counts.invited ?? 0

                    return (
                        <View style={{ padding: 12, borderBottomWidth: 1, gap: 6 }}>
                            <Text style={{ fontWeight: '600' }}>
                                {item.venue?.name_snapshot ?? (item.group_match_mode === 'chat_only' ? 'Chat-only group' : 'Group match')}
                            </Text>
                            <Text>
                                Status: {item.status} • Mode: {item.group_match_mode}
                            </Text>
                            <Text>
                                You: {item.my_member_status} • Accepted: {acceptedCount} • Invited: {invitedCount}
                            </Text>
                            {item.venue?.neighborhood_snapshot || item.venue?.address_snapshot ? (
                                <Text style={{ color: '#555' }}>
                                    {item.venue.neighborhood_snapshot ?? item.venue.address_snapshot}
                                </Text>
                            ) : null}
                            <Text style={{ color: '#555' }}>
                                Members: {memberLine(item)}
                            </Text>

                            {item.my_member_status === 'invited' ? (
                                <View style={{ flexDirection: 'row', gap: 8 }}>
                                    <Button
                                        title={isActing ? 'Working...' : 'Accept'}
                                        onPress={() => handleAction(item.id, 'accept')}
                                        disabled={isActing}
                                    />
                                    <Button
                                        title="Decline"
                                        onPress={() => handleAction(item.id, 'decline')}
                                        color="#b45309"
                                        disabled={isActing}
                                    />
                                </View>
                            ) : null}

                            {item.my_member_status === 'accepted' ? (
                                <View style={{ flexDirection: 'row', gap: 8 }}>
                                    {canOpenChat(item) ? (
                                        <Button
                                            title="Open Chat"
                                            onPress={() =>
                                                router.push({
                                                    pathname: '/chat/[groupMatchId]',
                                                    params: { groupMatchId: item.id },
                                                })
                                            }
                                            disabled={isActing}
                                        />
                                    ) : null}
                                    <Button
                                        title={isActing ? 'Working...' : 'Leave'}
                                        onPress={() => handleAction(item.id, 'leave')}
                                        color="#c00"
                                        disabled={isActing}
                                    />
                                </View>
                            ) : null}
                        </View>
                    )
                }}
                ListEmptyComponent={
                    !loading ? (
                        <Text style={{ color: '#666' }}>
                            No group matches yet. New group invites will appear here.
                        </Text>
                    ) : null
                }
            />
        </View>
    )
}
