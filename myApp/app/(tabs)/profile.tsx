import { useFocusEffect, useRouter } from "expo-router";
import { onAuthStateChanged } from "firebase/auth";
import React, { useCallback, useEffect, useState } from "react";
import {
  Button,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { getMeProfile, patchMeProfile } from "../../lib/backend";
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

  const loadProfile = useCallback(async () => {
    const u = auth.currentUser;
    if (!u) return;

    setLoading(true);
    setProfileError(null);
    try {
      const p = await getMeProfile();
      setProfile({
        displayName: p.display_name ?? "",
        hobbies: p.hobbies ?? [],
      });
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

        <View style={{ marginTop: 12 }}>
          <Button title="Log out" onPress={handleLogout} color="#c00" />
        </View>
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

  card: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    height: "55%",
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
});
