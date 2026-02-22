import { Image, StyleSheet, Text, TextInput, View } from "react-native";

export default function Discover() {
  return (
    <View style={styles.container}>
      <View>
        <Text style={{ fontSize: 20 }}>Discover</Text>
        <TextInput placeholder="Search locations..." style={styles.search} />
      </View>

      <View style={styles.card}>
        <Image
          source={{
            uri: "https://lh3.googleusercontent.com/gps-cs-s/AHVAwernBzc2WqRYy-tz3_5gfKOlLPozI_XjrFPI3y23R845qz4JNa1hkM88xEG1EAkO6bhnKn6LUn84ISS0xO3dA5blWozQT5izRpYHD7I49DNBlxoOmc8j1CM19Hd78Djreb_svrXnXOE-ms_Z=w408-h544-k-no",
          }}
          style={styles.image}
        />

        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>Molly Tea</Text>
          <Text style={styles.description}>
            Inspired by the elegance of jasmine, Molly Tea leads the way in
            Chinese floral tea innovation...
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: "space-between",
    backgroundColor: "#DEF5FF",
  },
  title: {
    fontSize: 26,
    fontWeight: "bold",
  },
  subtitle: {
    marginTop: 4,
    marginBottom: 16,
    color: "#555",
  },
  search: {
    backgroundColor: "#FFFFFF",
    padding: 12,
    borderRadius: 25,
  },
  card: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  image: {
    width: 100,
    height: 100,
    borderRadius: 12,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: "bold",
  },
  description: {
    marginTop: 6,
    color: "#555",
  },
});
