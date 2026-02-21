// app/types.ts

export type UserProfile = {
    name?: string
    hobbies?: string[]
    age?: number
    gender?: string
    location?: {
        latitude?: number
        longitude?: number
        lat?: number
        lng?: number
    }
}

export type ChatMessage = {
    id?: string
    from: string
    text: string
    room?: string
    createdAt?: any
}

// app/types.ts
export type UserWithLocation = {
    id: string
    name?: string
    hobbies?: string[]
    location?: {
        latitude?: number
        longitude?: number
        lat?: number
        lng?: number
    }
}

export type POI = {
    id: string
    name: string
    coords: {
        latitude: number
        longitude: number
    }
}