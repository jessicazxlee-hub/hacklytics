import { useFocusEffect, useRouter } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import React, { useCallback, useEffect, useState } from "react";
import {
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import {
  getMeProfile,
  getMyRestaurantRatings,
  patchMeProfile,
  type RestaurantRatingWithRestaurant,
} from "../../lib/backend";
import { auth, signOutUser } from "../../lib/firebase";

type ProfileState = {
  displayName: string;
  hobbies: string[];
};

function getFirebaseDisplayName(): string {
  const u = auth.currentUser;
  return u?.displayName ?? u?.email?.split("@")[0] ?? "";
}

export default function Profile() {
  const router = useRouter();
  const [profile, setProfile] = useState<ProfileState>({
    displayName: "",
    hobbies: [],
  });
  const [loading, setLoading] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [pastRatings, setPastRatings] = useState<RestaurantRatingWithRestaurant[]>([]);
  const [ratingsError, setRatingsError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    const u = auth.currentUser;
    if (!u) return;

    setLoading(true);
    setProfileError(null);
    setRatingsError(null);
    try {
      const [profileResult, ratingsResult] = await Promise.allSettled([
        getMeProfile(),
        getMyRestaurantRatings(),
      ]);

      if (profileResult.status === "fulfilled") {
        const p = profileResult.value;
        setProfile({
          displayName: p.display_name ?? "",
          hobbies: p.hobbies ?? [],
        });
      } else {
        throw profileResult.reason;
      }

      if (ratingsResult.status === "fulfilled") {
        const sorted = [...ratingsResult.value].sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        );
        setPastRatings(sorted.slice(0, 5));
      } else {
        setPastRatings([]);
        setRatingsError("Could not load past ratings");
      }
    } catch (err: unknown) {
      const message =
        typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to load profile";
      setProfileError(message);
      setProfile({
        displayName: getFirebaseDisplayName(),
        hobbies: [],
      });
      setPastRatings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      if (!u) {
        router.replace("/sign-in");
        return;
      }
      loadProfile();
    });

    return unsub;
  }, [router, loadProfile]);

  useFocusEffect(
    useCallback(() => {
      if (auth.currentUser) loadProfile();
    }, [loadProfile]),
  );

  async function save() {
    try {
      const updated = await patchMeProfile({
        display_name: profile.displayName.trim() || null,
        hobbies: profile.hobbies.filter(Boolean),
      });
      setProfile({
        displayName: updated.display_name ?? "",
        hobbies: updated.hobbies ?? [],
      });
      alert("Saved");
    } catch (err: unknown) {
      if (typeof err === "object" && err !== null && "message" in err) {
        alert(String((err as { message: unknown }).message));
      } else {
        alert("Failed to save profile");
      }
    }
  }

  async function handleLogout() {
    await signOutUser();
    router.replace("/sign-in");
  }

  return (
    <View style={styles.container}>
      <View style={styles.topSection}>
        <Text style={styles.name}>
          {profile.displayName || getFirebaseDisplayName() || "Willy Wonka"}
        </Text>

        <View style={styles.imageCircle}>
          <Image
            source={{
              uri: "https://preview.redd.it/xkwvbt1jx0b41.jpg?width=640&crop=smart&auto=webp&s=cc56d07bdfe8cc57563d9efcaf16877fb10b4f63",
            }}
            style={styles.image}
          />
        </View>

        <TouchableOpacity style={styles.logoutPill} onPress={handleLogout}>
          <Text style={styles.logoutPillText}>Log out</Text>
        </TouchableOpacity>
      </View>

      {/* Bottom Card */}
      <View style={styles.card}>
        <Text style={styles.quote}>
          “There is no life I know to compare with pure imagination.”
        </Text>

        {/* Toggle Buttons */}
        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.activeButton}>
            <Text style={styles.activeText}>Hobbies</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.outlineButton}>
            <Text style={styles.outlineText}>Locations</Text>
          </TouchableOpacity>
        </View>

        {/* List Items */}
        {profile.hobbies.length === 0 ? (
          <View style={styles.listItem}>
            <Text>No hobbies yet</Text>
          </View>
        ) : (
          profile.hobbies.map((hobby, index) => (
            <View key={index} style={styles.listItem}>
              <Text>{hobby}</Text>
            </View>
          ))
        )}

        <Text style={styles.sectionHeader}>My past ratings</Text>
        {ratingsError ? (
          <View style={styles.listItem}>
            <Text>{ratingsError}</Text>
          </View>
        ) : pastRatings.length === 0 ? (
          <View style={styles.listItem}>
            <Text>No ratings yet</Text>
            <Text style={styles.subtleText}>
              Rate venues in Discover to improve your group matches.
            </Text>
          </View>
        ) : (
          pastRatings.map((rating) => (
            <View key={rating.id} style={styles.listItem}>
              <Text style={styles.ratingTitle}>
                {rating.restaurant?.name ?? `Restaurant #${rating.restaurant_id}`}
              </Text>
              <Text style={styles.subtleText}>
                {rating.rating}/5
                {rating.restaurant?.cuisine ? ` • ${rating.restaurant.cuisine}` : ""}
              </Text>
            </View>
          ))
        )}

      </View>

      {/* <TextInput
        value={profile.displayName}
        onChangeText={(t) => setProfile((p) => ({ ...p, displayName: t }))}
        placeholder="Display name"
        style={{ borderWidth: 1, marginVertical: 8, padding: 8 }}
      />

      <TextInput
        value={profile.hobbies}
        onChangeText={(t) => setProfile((p) => ({ ...p, hobbies: t }))}
        placeholder="Hobbies (comma separated)"
        style={{ borderWidth: 1, marginVertical: 8, padding: 8 }}
      />

      <Button title="Save" onPress={save} />
      <View style={{ marginTop: 12 }}>
        <Button title="Log out" onPress={handleLogout} color="#c00" />
      </View> */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#9ec1de",
  },

  topSection: {
    height: "50%",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 2,
  },

  name: {
    fontSize: 40,
    fontWeight: "bold",
    color: "white",
    marginBottom: 20,
  },

  imageCircle: {
    width: 250,
    height: 250,
    borderRadius: 125,
    backgroundColor: "white",
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },

  image: {
    width: 230,
    height: 230,
    borderRadius: 115,
  },

  logoutPill: {
    marginTop: 14,
    backgroundColor: "#b93838",
    paddingVertical: 10,
    paddingHorizontal: 25,
    borderRadius: 10,
  },

  logoutPillText: {
    color: "white",
    fontWeight: "600",
  },

  card: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    height: "55%",
    zIndex: 1,
    backgroundColor: "#d9e3ea",
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 24,
  },

  quote: {
    fontStyle: "italic",
    fontSize: 16,
    marginBottom: 20,
  },

  buttonRow: {
    flexDirection: "row",
    marginBottom: 20,
  },

  activeButton: {
    backgroundColor: "#d58d6d",
    paddingVertical: 10,
    paddingHorizontal: 25,
    borderRadius: 10,
    marginRight: 10,
  },

  activeText: {
    color: "white",
    fontWeight: "600",
  },

  outlineButton: {
    borderWidth: 1,
    borderColor: "#d58d6d",
    paddingVertical: 10,
    paddingHorizontal: 25,
    borderRadius: 10,
  },

  outlineText: {
    color: "#d58d6d",
    fontWeight: "600",
  },

  listItem: {
    backgroundColor: "#eee",
    padding: 14,
    borderRadius: 8,
    marginBottom: 10,
  },

  sectionHeader: {
    marginTop: 4,
    marginBottom: 10,
    fontWeight: "700",
    color: "#374151",
  },

  ratingTitle: {
    fontWeight: "600",
  },

  subtleText: {
    marginTop: 2,
    color: "#6b7280",
    fontSize: 12,
  },
});
