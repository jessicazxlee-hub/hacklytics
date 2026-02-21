// app/types.ts

export type GeoPointLike = {
    // canonical
    lat?: number
    lng?: number
    // legacy keys (keep for backward compat)
    latitude?: number
    longitude?: number
}

export type UserProfile = {
    name?: string
    hobbies?: string[]
    age?: number
    gender?: string
    location?: GeoPointLike
    prefs?: {
        maxDistanceKm?: number
    }
}

export type ChatMessage = {
    id?: string
    from: string
    text: string
    createdAt?: any
}

export type UserWithLocation = {
    id: string
    name?: string
    hobbies?: string[]
    location?: GeoPointLike
}

export type POI = {
    id: string
    name: string
    coords: {
        latitude: number
        longitude: number
    }
}