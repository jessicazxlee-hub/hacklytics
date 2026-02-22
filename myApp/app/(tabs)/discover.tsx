import {
  APIProvider,
  Map,
  MapCameraChangedEvent,
  Marker,
} from "@vis.gl/react-google-maps";
import { useState } from "react";
import {
  Image,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { MaterialCommunityIcons } from "@expo/vector-icons";
const API_KEY = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY;

const locations = [
  {
    id: 1,
    name: "Molly Tea",
    lat: 33.908997155921156,
    lng: -84.28836434883065,
    description:
      "Inspired by the elegance of jasmine, Molly Tea leads the way in Chinese floral tea innovation...",
    image:
      "https://lh3.googleusercontent.com/gps-cs-s/AHVAwernBzc2WqRYy-tz3_5gfKOlLPozI_XjrFPI3y23R845qz4JNa1hkM88xEG1EAkO6bhnKn6LUn84ISS0xO3dA5blWozQT5izRpYHD7I49DNBlxoOmc8j1CM19Hd78Djreb_svrXnXOE-ms_Z=w408-h544-k-no",
  },
  {
    id: 2,
    name: "Ding Tea",
    lat: 33.78226540295082,
    lng: -84.40781292000098,
    description:
      "DINGTEA is Your Gateway to Exceptional Teas that Honor Tradition and Embrace Modern Flavors. At DINGTEA, we believe that tea is more than a beverage-it's a ...",
    image:
      "https://lh3.googleusercontent.com/p/AF1QipM3yDP-Vi2h0RUXhOEEQoPHYjMi1jpp-XAApeiE=w426-h240-k-no",
  },
  {
    id: 3,
    name: "Moge Tea",
    lat: 33.77825464644469,
    lng: -84.38891044698578,
    description:
      "Moge Tee is the best tasting bubble tea. Naturally Delicious!",
    image:
      "https://lh3.googleusercontent.com/gps-cs-s/AHVAwepBom00OcN6Vps3pCqQ2OR2nTfCJRny0Sv1AJ-S90OysN3Po7qGQ1J_x8Uw1tSV_dbw_nac2a5UTHcndJIJOMXBHSEJZSZIPcy8ESK9BTOWLQC70X9OrtQ-ip5N846HW16bsOxTUJC8LhE=w408-h544-k-no",
  },
];

export default function Discover() {
  const [selectedLocation, setSelectedLocation] = useState<
    (typeof locations)[number] | null
  >(null);

  const [rating, setRating] = useState(0);

  return (
    <APIProvider apiKey={API_KEY ?? ""}>
      <View style={styles.container}>
        <View>
          <Text style={{ fontSize: 20 }}>Discover</Text>
          <TextInput placeholder="Search locations..." style={styles.search} />
        </View>

        <Map
          defaultZoom={13}
          defaultCenter={{ lat: 33.77702970249832, lng: -84.39570715625945 }}
          onCameraChanged={(ev: MapCameraChangedEvent) =>
            console.log(
              "camera changed:",
              ev.detail.center,
              "zoom:",
              ev.detail.zoom,
            )
          }
        >
          {locations.map((loc) => (
            <Marker
              key={loc.id}
              position={{ lat: loc.lat, lng: loc.lng }}
              title={loc.name}
              onClick={() => {
                setSelectedLocation(loc);
                setRating(0);
              }}
            />
          ))}
        </Map>

        <View style={styles.card}>
          <Image
            source={{
              uri: selectedLocation?.image,
            }}
            style={styles.image}
          />

          <View style={{ flex: 1 }}>
            <Text style={styles.cardTitle}>{selectedLocation?.name}</Text>
            <View style={{ flexDirection: "row", marginVertical: 6 }}>
              {[...Array(5)].map((_, i) => {
                const heartNumber = i + 1;
                const isFilled = heartNumber <= rating;

                return (
                  <TouchableOpacity
                    key={i}
                    style={{ marginRight: 4 }}
                    onPress={() => setRating(heartNumber)}
                  >
                    <MaterialCommunityIcons
                      name={isFilled ? "heart" : "heart-outline"}
                      size={24}
                      color="#FF5A5F"
                    />
                  </TouchableOpacity>
                );
              })}
            </View>
            <Text style={styles.description}>
              {selectedLocation?.description}
            </Text>
          </View>
        </View>
      </View>
    </APIProvider>
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
