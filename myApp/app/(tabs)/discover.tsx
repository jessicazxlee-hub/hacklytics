import React, { useCallback, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";

import {
  getMyRestaurantRatings,
  getRestaurants,
  rateRestaurant,
  type Restaurant,
  type RestaurantRatingWithRestaurant,
} from "../../lib/backend";

type RatingsByRestaurantId = Record<number, RestaurantRatingWithRestaurant>;

export default function Discover() {
  const [query, setQuery] = useState("");
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [ratingsByRestaurantId, setRatingsByRestaurantId] = useState<RatingsByRestaurantId>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [ratingRestaurantId, setRatingRestaurantId] = useState<number | null>(null);

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [restaurantsData, myRatings] = await Promise.all([
        getRestaurants(),
        getMyRestaurantRatings(),
      ]);

      const ratingMap: RatingsByRestaurantId = {};
      for (const rating of myRatings) {
        ratingMap[rating.restaurant_id] = rating;
      }

      setRestaurants(restaurantsData);
      setRatingsByRestaurantId(ratingMap);
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
    if (!normalized) {
      return restaurants;
    }
    return restaurants.filter((restaurant) => {
      const haystack = [
        restaurant.name,
        restaurant.cuisine ?? "",
        restaurant.address ?? "",
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [restaurants, query]);

  async function handleRate(restaurant: Restaurant, rating: number) {
    if (ratingRestaurantId !== null) return;
    setRatingRestaurantId(restaurant.id);
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
      setRatingRestaurantId(null);
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerSection}>
        <Text style={styles.title}>Discover</Text>
        <Text style={styles.subtitle}>
          Search places and rate what you&apos;ve visited.
        </Text>
        <TextInput
          placeholder="Search locations..."
          value={query}
          onChangeText={setQuery}
          style={styles.search}
        />
      </View>

      {loading ? <ActivityIndicator style={{ marginTop: 8 }} /> : null}

      <FlatList
        data={filteredRestaurants}
        refreshing={refreshing}
        onRefresh={() => void load("refresh")}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ gap: 12, paddingBottom: 20 }}
        renderItem={({ item }) => {
          const myRating = ratingsByRestaurantId[item.id];
          const isSaving = ratingRestaurantId === item.id;

          return (
            <View style={styles.card}>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>{item.name}</Text>
                <Text style={styles.metaText}>
                  {item.cuisine ?? "Unknown cuisine"}
                  {item.address ? ` • ${item.address}` : ""}
                </Text>
                <Text style={styles.description}>
                  Rate restaurants you enjoy so Proximity can form better group
                  matches and venue recommendations.
                </Text>

                <Text style={styles.ratingLabel}>
                  Your rating: {myRating ? `${myRating.rating}/5` : "Not rated yet"}
                </Text>
                <View style={styles.ratingRow}>
                  {[1, 2, 3, 4, 5].map((value) => (
                    <Pressable
                      key={value}
                      onPress={() => void handleRate(item, value)}
                      disabled={isSaving}
                      style={[
                        styles.ratingButton,
                        myRating?.rating === value ? styles.ratingButtonActive : null,
                        isSaving ? styles.ratingButtonDisabled : null,
                      ]}
                    >
                      <Text
                        style={[
                          styles.ratingButtonText,
                          myRating?.rating === value ? styles.ratingButtonTextActive : null,
                        ]}
                      >
                        {value}
                      </Text>
                    </Pressable>
                  ))}
                </View>
                {isSaving ? <Text style={styles.savingText}>Saving...</Text> : null}
              </View>
            </View>
          );
        }}
        ListEmptyComponent={
          !loading ? (
            <Text style={styles.emptyText}>
              {query.trim()
                ? "No restaurants match your search yet."
                : "No restaurants available yet. Seed restaurants first."}
            </Text>
          ) : null
        }
      />
    </View>
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
  card: {
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "700",
  },
  metaText: {
    marginTop: 4,
    color: "#555",
  },
  description: {
    marginTop: 8,
    color: "#555",
  },
  ratingLabel: {
    marginTop: 12,
    fontWeight: "600",
  },
  ratingRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 8,
    flexWrap: "wrap",
  },
  ratingButton: {
    minWidth: 36,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    backgroundColor: "#fff",
    alignItems: "center",
  },
  ratingButtonActive: {
    backgroundColor: "#d58d6d",
    borderColor: "#d58d6d",
  },
  ratingButtonDisabled: {
    opacity: 0.7,
  },
  ratingButtonText: {
    fontWeight: "600",
    color: "#334155",
  },
  ratingButtonTextActive: {
    color: "#fff",
  },
  savingText: {
    marginTop: 8,
    color: "#6b7280",
  },
  emptyText: {
    color: "#6b7280",
    paddingVertical: 20,
  },
});
