// import React, { useEffect, useState } from 'react'
// import {
//     View,
//     Text,
//     FlatList,
//     TextInput,
//     Button,
//     KeyboardAvoidingView,
//     Platform,
//     ActivityIndicator,
// } from 'react-native'
// import { useLocalSearchParams } from 'expo-router'

// import {
//     getChatMessages,
//     sendChatMessage,
//     type GroupChatMessage,
// } from '../../lib/backend'

// export default function GroupChatScreen() {
//     const params = useLocalSearchParams()
//     const groupMatchId =
//         typeof params.groupMatchId === 'string' ? params.groupMatchId : null

//     const [messages, setMessages] = useState<GroupChatMessage[]>([])
//     const [loading, setLoading] = useState(true)
//     const [sending, setSending] = useState(false)
//     const [text, setText] = useState('')

//     useEffect(() => {
//         let mounted = true

//         async function load() {
//             if (!groupMatchId) {
//                 if (mounted) {
//                     setLoading(false)
//                 }
//                 return
//             }

//             try {
//                 const items = await getChatMessages(groupMatchId)
//                 if (mounted) {
//                     setMessages(items)
//                 }
//             } catch (err: unknown) {
//                 if (mounted) {
//                     if (typeof err === 'object' && err !== null && 'message' in err) {
//                         alert(String((err as { message: unknown }).message))
//                     } else {
//                         alert('Failed to load chat messages')
//                     }
//                 }
//             } finally {
//                 if (mounted) {
//                     setLoading(false)
//                 }
//             }
//         }

//         load()
//         return () => {
//             mounted = false
//         }
//     }, [groupMatchId])

//     async function handleSend() {
//         if (!groupMatchId || sending) return
//         if (!text.trim()) return

//         setSending(true)
//         try {
//             const message = await sendChatMessage(groupMatchId, text)
//             setMessages((prev) => [...prev, message])
//             setText('')
//         } catch (err: unknown) {
//             if (typeof err === 'object' && err !== null && 'message' in err) {
//                 alert(String((err as { message: unknown }).message))
//             } else {
//                 alert('Failed to send message')
//             }
//         } finally {
//             setSending(false)
//         }
//     }

//     return (
//         <KeyboardAvoidingView
//             behavior={Platform.OS === 'ios' ? 'padding' : undefined}
//             style={{ flex: 1 }}
//         >
//             <View style={{ flex: 1, padding: 12 }}>
//                 <Text style={{ fontSize: 20, marginBottom: 8 }}>Group Chat</Text>
//                 <Text style={{ color: '#666', marginBottom: 8 }}>
//                     {groupMatchId ? `Group: ${groupMatchId}` : 'Missing group chat id'}
//                 </Text>
//                 {loading ? <ActivityIndicator /> : null}
//                 <FlatList
//                     data={messages}
//                     keyExtractor={(item) => item.id}
//                     renderItem={({ item }) => (
//                         <View
//                             style={{
//                                 padding: 8,
//                                 backgroundColor: '#FFF',
//                                 marginVertical: 4,
//                                 borderRadius: 8,
//                                 borderWidth: 1,
//                                 borderColor: '#ddd',
//                             }}
//                         >
//                             <Text style={{ fontWeight: '600' }}>
//                                 {item.sender.display_name ?? item.sender.id}
//                             </Text>
//                             <Text>{item.body}</Text>
//                         </View>
//                     )}
//                     ListEmptyComponent={
//                         !loading ? (
//                             <Text style={{ color: '#666' }}>
//                                 No messages yet.
//                             </Text>
//                         ) : null
//                     }
//                 />
//             </View>

//             <View style={{ flexDirection: 'row', padding: 8, gap: 8 }}>
//                 <TextInput
//                     value={text}
//                     onChangeText={setText}
//                     placeholder="Message"
//                     style={{
//                         flex: 1,
//                         borderWidth: 1,
//                         padding: 8,
//                         borderRadius: 6,
//                     }}
//                 />
//                 <Button
//                     title={sending ? 'Sending...' : 'Send'}
//                     onPress={handleSend}
//                     disabled={sending || !groupMatchId}
//                 />
//             </View>
//         </KeyboardAvoidingView>
//     )
// }

import { MaterialIcons } from "@expo/vector-icons"; // Using Expo vector icons for send icon
import React, { useState } from "react";
import {
    Image,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from "react-native";

const group = {
  name: "SHAP Lovers",
  status: "Debolina is online",
  members: [
    "https://randomuser.me/api/portraits/women/36.jpg",
    "https://randomuser.me/api/portraits/men/22.jpg",
    "https://randomuser.me/api/portraits/women/65.jpg",
  ],
};

const messages = [
  {
    id: "1",
    sender: "self",
    text: "I think I’m coming to outreach!",
    profilePic: "https://randomuser.me/api/portraits/men/65.jpg",
  },
  {
    id: "2",
    sender: "other",
    senderName: "Kripamove",
    text: "That’s great, woohoo!!",
    profilePic: "https://randomuser.me/api/portraits/women/36.jpg",
  },
  {
    id: "3",
    sender: "other",
    senderName: "Isidro",
    text: "Took you long enough.",
    profilePic: "https://randomuser.me/api/portraits/men/22.jpg",
  },
  {
    id: "4",
    sender: "other",
    senderName: "Debolina",
    text: "Make sure to avoid the snow!",
    profilePic: "https://randomuser.me/api/portraits/women/65.jpg",
  },
];

export default function ChatScreen() {
  const [inputText, setInputText] = useState("");

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: "#f0f6fc" }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.groupInfo}>
          <View style={styles.profilePicsContainer}>
            {group.members.map((uri, i) => (
              <Image
                key={i}
                source={{ uri }}
                style={[
                  styles.profilePic,
                  {
                    marginLeft: i === 0 ? 0 : -16,
                    zIndex: group.members.length - i,
                  },
                ]}
              />
            ))}
          </View>
          <View style={{ marginLeft: 12 }}>
            <Text style={styles.groupName}>{group.name}</Text>
            <Text style={styles.groupStatus}>{group.status}</Text>
          </View>
        </View>
      </View>

      {/* Messages */}
      <ScrollView
        style={{ flex: 1, paddingHorizontal: 12, paddingTop: 20 }}
        contentContainerStyle={{ paddingBottom: 12 }}
        keyboardShouldPersistTaps="handled"
      >
        {messages.map((msg) => {
          const isSelf = msg.sender === "self";
          return (
            <View
              key={msg.id}
              style={[
                styles.messageContainer,
                isSelf ? styles.messageRight : styles.messageLeft,
              ]}
            >
              {!isSelf && (
                <Image
                  source={{ uri: msg.profilePic }}
                  style={styles.messagePic}
                />
              )}
              <View
                style={[
                  styles.bubble,
                  isSelf ? styles.bubbleSelf : styles.bubbleOther,
                ]}
              >
                {!isSelf && (
                  <Text style={styles.senderName}>{msg.senderName}</Text>
                )}
                <Text
                  style={[styles.messageText, isSelf && { color: "white" }]}
                >
                  {msg.text}
                </Text>
              </View>
              {isSelf && (
                <Image
                  source={{ uri: msg.profilePic }}
                  style={styles.messagePic}
                />
              )}
            </View>
          );
        })}
      </ScrollView>

      {/* Message Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Type a message"
          value={inputText}
          onChangeText={setInputText}
          multiline
          placeholderTextColor="#999"
        />
        <TouchableOpacity style={styles.sendIcon}>
          <MaterialIcons name="send" size={24} color="#2a9df4" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
    backgroundColor: "white",
  },
  backButton: {
    paddingRight: 12,
  },
  groupInfo: {
    flexDirection: "row",
    alignItems: "center",
  },
  profilePicsContainer: {
    flexDirection: "row",
    width: 90,
  },
  profilePic: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: "white",
  },
  groupName: {
    fontWeight: "bold",
    fontSize: 16,
  },
  groupStatus: {
    color: "#555",
    fontSize: 13,
  },
  messageContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    marginBottom: 16,
  },
  messageLeft: {
    justifyContent: "flex-start",
  },
  messageRight: {
    justifyContent: "flex-end",
  },
  messagePic: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
  bubble: {
    maxWidth: "70%",
    padding: 10,
    borderRadius: 16,
    marginHorizontal: 8,
  },
  bubbleSelf: {
    backgroundColor: "#2a9df4",
    borderBottomRightRadius: 0,
  },
  bubbleOther: {
    backgroundColor: "white",
    borderBottomLeftRadius: 0,
    borderWidth: 1,
    borderColor: "#ddd",
  },
  senderName: {
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 2,
    color: "#555",
  },
  messageText: {
    fontSize: 14,
    color: "#333",
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "white",
    borderTopWidth: 1,
    borderTopColor: "#ddd",
  },
  input: {
    flex: 1,
    backgroundColor: "#e6ecf8",
    borderRadius: 25,
    paddingVertical: 10,
    paddingHorizontal: 20,
    fontSize: 16,
    color: "#333",
  },
  sendIcon: {
    margin: 12,
  },
});
