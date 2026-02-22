import { auth } from "./firebase";

export type MeProfile = {
  id: string;
  email: string;
  display_name: string | null;
  neighborhood: string | null;
  hobbies: string[];
};

export type MeProfileUpdate = {
  display_name?: string | null;
  hobbies?: string[];
};

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

export type GroupMatchVenue = {
    id: string
    venue_kind: string
    source: string
    restaurant_id: number | null
    external_place_id: string | null
    name_snapshot: string
    address_snapshot: string | null
    neighborhood_snapshot: string | null
    price_level: number | null
}

export type GroupMatchMember = {
    id: string
    user_id: string
    status: 'invited' | 'accepted' | 'declined' | 'left' | 'removed' | 'replaced'
    slot_number: number | null
    invited_at: string
    responded_at: string | null
    joined_at: string | null
    left_at: string | null
    user: {
        id: string
        display_name: string | null
        neighborhood: string | null
    }
}

export type GroupMatch = {
    id: string
    status: 'forming' | 'confirmed' | 'scheduled' | 'completed' | 'cancelled' | 'expired'
    group_match_mode: 'in_person' | 'chat_only'
    created_source: 'system' | 'user' | 'admin'
    created_by_user_id: string | null
    chat_room_key: string | null
    scheduled_for: string | null
    expires_at: string | null
    member_counts: Record<string, number>
    my_member_status: GroupMatchMember['status']
    members: GroupMatchMember[]
    venue: GroupMatchVenue | null
    created_at: string
    updated_at: string
}

export type Restaurant = {
    id: number
    name: string
    cuisine: string | null
    address: string | null
    latitude: number | null
    longitude: number | null
    created_at: string
}

export type RestaurantRating = {
    id: string
    user_id: string
    restaurant_id: number
    rating: number
    visited: boolean
    would_return: boolean | null
    notes: string | null
    created_at: string
    updated_at: string
}

export type RestaurantRatingWithRestaurant = RestaurantRating & {
    restaurant: Restaurant
}

export type RestaurantRatingUpsert = {
    rating: number
    visited?: boolean
    would_return?: boolean | null
    notes?: string | null
}

function apiBaseUrl(): string {
  return process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

async function authHeaders(): Promise<Record<string, string>> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("Not authenticated");
  }

  const idToken = await user.getIdToken(true);
  return {
    Authorization: `Bearer ${idToken}`,
    "Content-Type": "application/json",
  };
}

export async function getMeProfile(): Promise<MeProfile> {
  const headers = await authHeaders();
  const response = await fetch(`${apiBaseUrl()}/api/v1/me/profile`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to load profile: ${response.status} ${body}`);
  }

  return (await response.json()) as MeProfile;
}

export async function patchMeProfile(
  payload: MeProfileUpdate,
): Promise<MeProfile> {
  const headers = await authHeaders();
  const response = await fetch(`${apiBaseUrl()}/api/v1/me/profile`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to update profile: ${response.status} ${body}`);
  }

  return (await response.json()) as MeProfile;
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

export async function getGroupMatches(
    limit = 20,
    offset = 0,
    includeInactiveMemberships = false
): Promise<GroupMatch[]> {
    const headers = await authHeaders()
    const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
        include_inactive_memberships: String(includeInactiveMemberships),
    })
    const response = await fetch(`${apiBaseUrl()}/api/v1/group-matches?${params.toString()}`, {
        method: 'GET',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load group matches: ${response.status} ${body}`)
    }

    return (await response.json()) as GroupMatch[]
}

async function postGroupMatchAction(
    groupMatchId: string,
    action: 'accept' | 'decline' | 'leave'
): Promise<GroupMatch> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/group-matches/${encodeURIComponent(groupMatchId)}/${action}`, {
        method: 'POST',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to ${action} group match: ${response.status} ${body}`)
    }

    return (await response.json()) as GroupMatch
}

export function acceptGroupMatch(groupMatchId: string): Promise<GroupMatch> {
    return postGroupMatchAction(groupMatchId, 'accept')
}

export function declineGroupMatch(groupMatchId: string): Promise<GroupMatch> {
    return postGroupMatchAction(groupMatchId, 'decline')
}

export function leaveGroupMatch(groupMatchId: string): Promise<GroupMatch> {
    return postGroupMatchAction(groupMatchId, 'leave')
}

export async function getRestaurants(): Promise<Restaurant[]> {
    const response = await fetch(`${apiBaseUrl()}/api/v1/restaurants`, {
        method: 'GET',
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load restaurants: ${response.status} ${body}`)
    }

    return (await response.json()) as Restaurant[]
}

export async function rateRestaurant(
    restaurantId: number,
    payload: RestaurantRatingUpsert
): Promise<RestaurantRating> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/restaurants/${restaurantId}/rating`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to rate restaurant: ${response.status} ${body}`)
    }

    return (await response.json()) as RestaurantRating
}

export async function getMyRestaurantRatings(): Promise<RestaurantRatingWithRestaurant[]> {
    const headers = await authHeaders()
    const response = await fetch(`${apiBaseUrl()}/api/v1/me/restaurant-ratings`, {
        method: 'GET',
        headers,
    })

    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to load my restaurant ratings: ${response.status} ${body}`)
    }

    return (await response.json()) as RestaurantRatingWithRestaurant[]
}
