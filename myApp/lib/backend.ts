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
