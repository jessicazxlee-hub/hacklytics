import { useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import {
    FlatList,
    Image,
    Pressable,
    StyleSheet,
    Text,
    View,
} from "react-native";

import { getChats, type GroupChatSummary } from "../../lib/backend";

const dummyChats = [
  {
    id: "1",
    groupName: "Cracked Hackers",
    lastMessage: "It was so awesome!",
    timestamp: "Just Now",
    unread: true,
    members: [
      "https://randomuser.me/api/portraits/women/65.jpg",
      "https://randomuser.me/api/portraits/men/45.jpg",
      "https://randomuser.me/api/portraits/women/12.jpg",
    ],
  },
  {
    id: "2",
    groupName: "SHAP Volunteers",
    lastMessage: "Deb: Make sure to avoid the snow!",
    timestamp: "5:27AM",
    unread: true,
    members: [
      "https://randomuser.me/api/portraits/women/36.jpg",
      "https://randomuser.me/api/portraits/men/22.jpg",
      "https://randomuser.me/api/portraits/women/11.jpg",
    ],
  },
  {
    id: "3",
    groupName: "Hacklytics 2026",
    lastMessage: "You loved: You all worked really hard!",
    timestamp: "2:00AM",
    unread: false,
    members: [
      "https://randomuser.me/api/portraits/women/12.jpg",
      "https://randomuser.me/api/portraits/men/22.jpg",
      "https://randomuser.me/api/portraits/women/36.jpg",
    ],
  },
];

export default function ChatsTab() {
  const router = useRouter();
  const [chats, setChats] = useState<GroupChatSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const items = await getChats();
        if (mounted) {
          setChats(items);
        }
      } catch (err: unknown) {
        if (mounted) {
          if (typeof err === "object" && err !== null && "message" in err) {
            alert(String((err as { message: unknown }).message));
          } else {
            alert("Failed to load chats");
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  function renderProfilePics(urls: string[]) {
    return urls.map((url, i) => (
      <Image
        key={i}
        source={{ uri: url }}
        style={[
          styles.profilePic,
          { marginLeft: i === 0 ? 0 : -12, zIndex: 3 - i },
        ]}
      />
    ));
  }

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Text style={{ fontSize: 20, marginBottom: 8 }}>Chats</Text>
      <Text style={{ color: "#666", marginBottom: 8 }}>
        Group chats only. Chat opens when you are in a confirmed group.
      </Text>
      {/* {loading ? <ActivityIndicator /> : null} */}
      <FlatList
        data={dummyChats}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          //   <Pressable
          //     onPress={() =>
          //       router.push({
          //         pathname: "/chat/[groupMatchId]",
          //         params: { groupMatchId: item.id },
          //       })
          //     }
          //     style={{ padding: 12, borderBottomWidth: 1 }}
          //   >
          //     <Text style={{ fontWeight: "600" }}>
          //       {item.venue_name ??
          //         (item.group_match_mode === "chat_only"
          //           ? "Chat-only group"
          //           : "Group chat")}
          //     </Text>
          //     <Text>
          //       {item.member_count} members • {item.group_match_mode} •{" "}
          //       {item.status}
          //     </Text>
          //     <Text style={{ color: "#555", marginTop: 4 }}>
          //       {item.last_message?.body_preview ?? "No messages yet"}
          //     </Text>
          //   </Pressable>
          <Pressable
            style={[styles.card, item.unread && styles.unreadCard]}
            onPress={() =>
              router.push({
                pathname: "/chat/[groupMatchId]",
                params: { groupMatchId: item.id },
              })
            }
          >
            {" "}
            <View style={styles.profilePicsContainer}>
              {renderProfilePics(item.members)}
            </View>
            <View style={styles.textContainer}>
              <Text
                style={[styles.groupName, item.unread && styles.unreadText]}
              >
                {item.groupName}
              </Text>
              <Text
                style={[styles.message, item.unread && styles.unreadText]}
                numberOfLines={1}
              >
                {item.lastMessage}
              </Text>
            </View>
            <View style={styles.rightContainer}>
              <Text
                style={[styles.timestamp, item.unread && styles.unreadText]}
              >
                {item.timestamp}
              </Text>
              {item.unread && <View style={styles.unreadDot} />}
            </View>
          </Pressable>
        )}
        // ListEmptyComponent={
        //   !loading ? (
        //     <Text style={{ color: "#666" }}>No group chats yet.</Text>
        //   ) : null
        // }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "white",
    padding: 12,
    borderRadius: 16,
    marginVertical: 6,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  unreadCard: {
    backgroundColor: "#e6f0ff",
  },
  profilePicsContainer: {
    flexDirection: "row",
    width: 100,
  },
  profilePic: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: "white",
  },
  textContainer: {
    flex: 1,
    marginLeft: 12,
  },
  groupName: {
    fontWeight: "bold",
    fontSize: 16,
    marginBottom: 2,
  },
  message: {
    color: "#555",
    fontSize: 14,
  },
  rightContainer: {
    alignItems: "flex-end",
    marginLeft: 8,
    minWidth: 60,
  },
  timestamp: {
    fontSize: 12,
    color: "#999",
  },
  unreadDot: {
    marginTop: 4,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#3478f6",
  },
  unreadText: {
    fontWeight: "bold",
    color: "#222",
  },
});
