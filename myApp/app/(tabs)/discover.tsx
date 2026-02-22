import {
  APIProvider,
  Map,
  type MapCameraChangedEvent,
  Marker,
} from "@vis.gl/react-google-maps";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useFocusEffect } from "expo-router";
import React, { useCallback, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import {
  getMyRestaurantRatings,
  getRestaurants,
  rateRestaurant,
  type Restaurant,
  type RestaurantRatingWithRestaurant,
} from "../../lib/backend";

const API_KEY = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY;

type RatingsByRestaurantId = Record<number, RestaurantRatingWithRestaurant>;
type PendingRatingsByRestaurantId = Record<number, number>;

const DEFAULT_MAP_CENTER = { lat: 33.77702970249832, lng: -84.39570715625945 };

function restaurantDescription(restaurant: Restaurant): string {
  const parts = [
    restaurant.cuisine ? `${restaurant.cuisine} cuisine` : null,
    restaurant.address ? `Located at ${restaurant.address}` : null,
  ].filter(Boolean);
  if (parts.length === 0) {
    return "Rate places you enjoy so Proximity can build better group matches and venue suggestions.";
  }
  return `${parts.join(". ")}.`;
}

export default function Discover() {
  const [query, setQuery] = useState("");
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [ratingsByRestaurantId, setRatingsByRestaurantId] = useState<RatingsByRestaurantId>({});
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [ratingRestaurantId, setRatingRestaurantId] = useState<number | null>(null);
  const [pendingRatingsByRestaurantId, setPendingRatingsByRestaurantId] =
    useState<PendingRatingsByRestaurantId>({});

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [restaurantsResult, ratingsResult] = await Promise.allSettled([
        getRestaurants(),
        getMyRestaurantRatings(),
      ]);

      if (restaurantsResult.status !== "fulfilled") {
        throw restaurantsResult.reason;
      }

      const restaurantsData = restaurantsResult.value;
      const myRatings = ratingsResult.status === "fulfilled" ? ratingsResult.value : [];

      const ratingMap: RatingsByRestaurantId = {};
      for (const rating of myRatings) {
        ratingMap[rating.restaurant_id] = rating;
      }

      setRestaurants(restaurantsData);
      setRatingsByRestaurantId(ratingMap);

      if (restaurantsData.length > 0) {
        setSelectedRestaurantId((prev) =>
          prev && restaurantsData.some((r) => r.id === prev) ? prev : restaurantsData[0].id,
        );
      } else {
        setSelectedRestaurantId(null);
      }

      if (ratingsResult.status !== "fulfilled") {
        console.warn("Discover ratings load failed; showing restaurants without saved ratings.", ratingsResult.reason);
      }
    } catch (err: unknown) {
      if (typeof err === "object" && err !== null && "message" in err) {
        alert(String((err as { message: unknown }).message));
      } else {
        alert("Failed to load Discover data");
      }
    } finally {
      if (mode === "refresh") {
        setRefreshing(false);
      } else {
        setLoading(false);
      }
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load("initial");
    }, [load]),
  );

  const filteredRestaurants = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return restaurants;
    return restaurants.filter((restaurant) => {
      const haystack = [restaurant.name, restaurant.cuisine ?? "", restaurant.address ?? ""]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [restaurants, query]);

  const markerRestaurants = useMemo(
    () =>
      filteredRestaurants.filter(
        (restaurant) =>
          typeof restaurant.latitude === "number" && typeof restaurant.longitude === "number",
      ),
    [filteredRestaurants],
  );

  const selectedRestaurant =
    filteredRestaurants.find((restaurant) => restaurant.id === selectedRestaurantId) ??
    restaurants.find((restaurant) => restaurant.id === selectedRestaurantId) ??
    filteredRestaurants[0] ??
    restaurants[0] ??
    null;

  async function handleRate(restaurant: Restaurant, rating: number) {
    if (ratingRestaurantId !== null) return;
    setRatingRestaurantId(restaurant.id);
    setPendingRatingsByRestaurantId((prev) => ({
      ...prev,
      [restaurant.id]: rating,
    }));
    try {
      const saved = await rateRestaurant(restaurant.id, {
        rating,
        visited: true,
        would_return: rating >= 4 ? true : rating <= 2 ? false : null,
      });

      setRatingsByRestaurantId((prev) => ({
        ...prev,
        [restaurant.id]: {
          ...saved,
          restaurant,
        },
      }));
    } catch (err: unknown) {
      if (typeof err === "object" && err !== null && "message" in err) {
        alert(String((err as { message: unknown }).message));
      } else {
        alert("Failed to save rating");
      }
    } finally {
      setPendingRatingsByRestaurantId((prev) => {
        const next = { ...prev };
        delete next[restaurant.id];
        return next;
      });
      setRatingRestaurantId(null);
    }
  }

  const selectedRating = selectedRestaurant
    ? pendingRatingsByRestaurantId[selectedRestaurant.id] ??
      ratingsByRestaurantId[selectedRestaurant.id]?.rating ??
      0
    : 0;
  const selectedMapCenter =
    selectedRestaurant &&
    typeof selectedRestaurant.latitude === "number" &&
    typeof selectedRestaurant.longitude === "number"
      ? { lat: selectedRestaurant.latitude, lng: selectedRestaurant.longitude }
      : DEFAULT_MAP_CENTER;

  return (
    <APIProvider apiKey={API_KEY ?? ""}>
      <View style={styles.container}>
        <View style={styles.headerSection}>
          <Text style={styles.title}>Discover</Text>
          <Text style={styles.subtitle}>
            Search venues and rate what you&apos;ve tried to improve group matching.
          </Text>
          <TextInput
            placeholder="Search locations..."
            value={query}
            onChangeText={setQuery}
            style={styles.search}
          />
        </View>

        {loading ? <ActivityIndicator style={{ marginTop: 8 }} /> : null}

        <View style={styles.mapWrap}>
          <Map
            key={selectedRestaurant?.id ?? "discover-map-default"}
            defaultZoom={13}
            defaultCenter={selectedMapCenter}
            style={{ width: "100%", height: "100%" }}
            onCameraChanged={(ev: MapCameraChangedEvent) =>
              console.log("camera changed:", ev.detail.center, "zoom:", ev.detail.zoom)
            }
          >
            {markerRestaurants.map((restaurant) => (
              <Marker
                key={restaurant.id}
                position={{
                  lat: restaurant.latitude as number,
                  lng: restaurant.longitude as number,
                }}
                title={restaurant.name}
                onClick={() => setSelectedRestaurantId(restaurant.id)}
              />
            ))}
          </Map>
        </View>

        <View style={styles.card}>
          <View style={styles.imagePlaceholder}>
            <Image
              source={{
                uri: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&q=80&auto=format&fit=crop",
              }}
              style={styles.image}
            />
          </View>

          <View style={{ flex: 1 }}>
            <Text style={styles.cardTitle}>
              {selectedRestaurant?.name ?? "Select a place"}
            </Text>
            <Text style={styles.metaText}>
              {selectedRestaurant
                ? `${selectedRestaurant.cuisine ?? "Unknown cuisine"}${selectedRestaurant.address ? ` • ${selectedRestaurant.address}` : ""}`
                : "Search or tap a marker to choose a venue"}
            </Text>

            <View style={{ flexDirection: "row", marginVertical: 8 }}>
              {[...Array(5)].map((_, i) => {
                const heartNumber = i + 1;
                const isFilled = heartNumber <= selectedRating;
                const disabled = !selectedRestaurant || ratingRestaurantId === selectedRestaurant.id;

                return (
                  <TouchableOpacity
                    key={heartNumber}
                    style={{ marginRight: 6 }}
                    onPress={() => selectedRestaurant && void handleRate(selectedRestaurant, heartNumber)}
                    disabled={disabled}
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

            <Text style={styles.ratingLabel}>
              {selectedRestaurant
                ? `Your rating: ${selectedRating ? `${selectedRating}/5` : "Not rated yet"}`
                : "Choose a venue to rate"}
            </Text>
            <Text style={styles.description}>
              {selectedRestaurant
                ? restaurantDescription(selectedRestaurant)
                : "Ratings from Discover feed your preference signals for better group formation."}
            </Text>
            {selectedRestaurant && ratingRestaurantId === selectedRestaurant.id ? (
              <Text style={styles.savingText}>Saving...</Text>
            ) : null}
          </View>
        </View>

        <FlatList
          data={filteredRestaurants}
          horizontal
          refreshing={refreshing}
          onRefresh={() => void load("refresh")}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={{ gap: 8, paddingBottom: 8 }}
          renderItem={({ item }) => {
            const selected = item.id === selectedRestaurant?.id;
            const myRating =
              pendingRatingsByRestaurantId[item.id] ??
              ratingsByRestaurantId[item.id]?.rating ??
              null;
            return (
              <Pressable
                onPress={() => setSelectedRestaurantId(item.id)}
                style={[styles.venueChip, selected ? styles.venueChipSelected : null]}
              >
                <Text style={[styles.venueChipText, selected ? styles.venueChipTextSelected : null]}>
                  {item.name}
                </Text>
                <Text style={[styles.venueChipMeta, selected ? styles.venueChipMetaSelected : null]}>
                  {myRating ? `${myRating}/5` : "Rate"}
                </Text>
              </Pressable>
            );
          }}
          ListEmptyComponent={
            !loading ? (
              <Text style={styles.emptyText}>
                {query.trim() ? "No restaurants match your search yet." : "No restaurants available yet. Seed restaurants first."}
              </Text>
            ) : null
          }
        />
      </View>
    </APIProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#DEF5FF",
    gap: 12,
  },
  headerSection: {
    gap: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
  },
  subtitle: {
    color: "#4b5563",
  },
  search: {
    backgroundColor: "#FFFFFF",
    padding: 12,
    borderRadius: 25,
  },
  mapWrap: {
    height: 260,
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#dbe3ea",
  },
  card: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  imagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 12,
    overflow: "hidden",
    marginRight: 12,
    backgroundColor: "#e5e7eb",
  },
  image: {
    width: 100,
    height: 100,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: "bold",
  },
  metaText: {
    marginTop: 4,
    color: "#555",
  },
  ratingLabel: {
    marginTop: 2,
    fontWeight: "600",
  },
  description: {
    marginTop: 6,
    color: "#555",
  },
  savingText: {
    marginTop: 6,
    color: "#6b7280",
  },
  venueChip: {
    backgroundColor: "#fff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#d1d5db",
    paddingHorizontal: 12,
    paddingVertical: 8,
    minWidth: 110,
  },
  venueChipSelected: {
    borderColor: "#d58d6d",
    backgroundColor: "#fff4ef",
  },
  venueChipText: {
    fontWeight: "600",
    color: "#111827",
  },
  venueChipTextSelected: {
    color: "#9a3412",
  },
  venueChipMeta: {
    marginTop: 2,
    fontSize: 12,
    color: "#6b7280",
  },
  venueChipMetaSelected: {
    color: "#9a3412",
  },
  emptyText: {
    color: "#6b7280",
    paddingVertical: 8,
  },
});
