import { auth } from './firebase'

export type MeProfile = {
    id: string
    email: string
    display_name: string | null
    neighborhood: string | null
    hobbies: string[]
}

export type MeProfileUpdate = {
    display_name?: string | null
    hobbies?: string[]
}

export type UserPublic = {
    id: string
    display_name: string | null
    neighborhood: string | null
    discoverable: boolean
    open_to_meetups: boolean
    hobbies: string[]
}

export type FriendListItem = {
    user: UserPublic
    friend_since: string
}

export type FriendRequest = {
    id: string
    requester_id: string
    addressee_id: string
    status: string
    responded_at: string | null
    created_at: string
    updated_at: string
}

export type FriendRequestCreateResult = FriendRequest & {
    created: boolean
}

export type MatchItem = {
    user: UserPublic
    score: number
    signals: {
        same_neighborhood: boolean
        hobby_overlap_count: number
        overlap_hobbies: string[]
    }
}

export type GroupChatSummary = {
    id: string
    status: string
    group_match_mode: 'in_person' | 'chat_only'
    chat_room_key: string | null
    member_count: number
    venue_name: string | null
    last_message: {
        id: string
        sender_user_id: string
        body_preview: string
        created_at: string
    } | null
    created_at: string
    updated_at: string
}

export type GroupChatMessage = {
    id: string
    group_match_id: string
    sender: {
        id: string
        display_name: string | null
    }
    body: string
    created_at: string
    updated_at: string
}

function apiBaseUrl(): string {
    return process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000'
}

async function authHeaders(): Promise<Record<string, string>> {
    const user = auth.currentUser
    if (!user) {
        throw new Error('Not authenticated')
    }

    const idToken = await user.getIdToken(true)
    return {
        Authorization: `Bearer ${idToken}`,
        'Content-Type': 'application/json',
    }
}

export async function getMeProfile(): Promise<MeProfile> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/me/profile`, {
        method: 'GET',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load profile: ${response.status} ${body}`)
    }

    return (await response.json()) as MeProfile
}

export async function patchMeProfile(payload: MeProfileUpdate): Promise<MeProfile> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/me/profile`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload),
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to update profile: ${response.status} ${body}`)
    }

    return (await response.json()) as MeProfile
}

export async function getFriends(): Promise<FriendListItem[]> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/friends`, {
        method: 'GET',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load friends: ${response.status} ${body}`)
    }

    return (await response.json()) as FriendListItem[]
}

export async function getMatches(limit = 20, offset = 0): Promise<MatchItem[]> {
    const headers = await authHeaders()
    const response = await fetch(
        `${apiBaseUrl()}/api/v1/matches?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`,
        {
            method: 'GET',
            headers,
        }
    )

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load matches: ${response.status} ${body}`)
    }

    return (await response.json()) as MatchItem[]
}

export async function sendFriendRequest(userId: string): Promise<FriendRequestCreateResult> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/friends/requests/${userId}`, {
        method: 'POST',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to send friend request: ${response.status} ${body}`)
    }

    return (await response.json()) as FriendRequestCreateResult
}

export async function getChats(limit = 20, offset = 0): Promise<GroupChatSummary[]> {
    const headers = await authHeaders()
    const response = await fetch(
        `${apiBaseUrl()}/api/v1/chats?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`,
        {
            method: 'GET',
            headers,
        }
    )

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load chats: ${response.status} ${body}`)
    }

    return (await response.json()) as GroupChatSummary[]
}

export async function getChatMessages(groupMatchId: string, limit = 100): Promise<GroupChatMessage[]> {
    const headers = await authHeaders()
    const response = await fetch(
        `${apiBaseUrl()}/api/v1/chats/${encodeURIComponent(groupMatchId)}/messages?limit=${encodeURIComponent(String(limit))}`,
        {
            method: 'GET',
            headers,
        }
    )

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load chat messages: ${response.status} ${body}`)
    }

    return (await response.json()) as GroupChatMessage[]
}

export async function sendChatMessage(groupMatchId: string, body: string): Promise<GroupChatMessage> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/chats/${encodeURIComponent(groupMatchId)}/messages`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ body }),
    })

    if (!response.ok) {
        const text = await response.text()
        throw new Error(`Failed to send chat message: ${response.status} ${text}`)
    }

    return (await response.json()) as GroupChatMessage
}
