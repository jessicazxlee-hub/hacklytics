import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

type GroupChatCardProps = {
  groupName: string;
  message: string;
  timestamp: string; // e.g., "Just Now", "2h ago"
  profilePics: string[]; // array of image URLs
  isUnread?: boolean;
};

export function GroupChatCard({
  groupName,
  message,
  timestamp,
  profilePics,
  isUnread = false,
}: GroupChatCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.profilePicsContainer}>
        {profilePics.slice(0, 3).map((uri, i) => (
          <Image
            key={i}
            source={{ uri }}
            style={[
              styles.profilePic,
              { marginLeft: i === 0 ? 0 : -12 }, // overlap by 12px
              { zIndex: profilePics.length - i }, // keep leftmost on top
            ]}
          />
        ))}
      </View>

      <View style={styles.textContainer}>
        <Text style={styles.groupName}>{groupName}</Text>
        <Text style={styles.message} numberOfLines={1}>
          {message}
        </Text>
      </View>

      <View style={styles.rightContainer}>
        <Text style={styles.timestamp}>{timestamp}</Text>
        {isUnread && <View style={styles.unreadDot} />}
      </View>
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
  profilePicsContainer: {
    flexDirection: "row",
    width: 70,
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
    backgroundColor: "#3478f6", // blue dot
  },
});
