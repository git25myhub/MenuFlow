import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useCart } from '../../context/CartContext';
import { menuAPI, restaurantsAPI } from '../../services/api';

export default function CustomerMenuScreen({ navigation }) {
  const { restaurant, setRestaurant, addToCart, itemCount } = useCart();
  const [restaurants, setRestaurants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectingRestaurant, setSelectingRestaurant] = useState(!restaurant);

  useEffect(() => {
    if (selectingRestaurant) {
      loadRestaurants();
    } else {
      loadMenu();
    }
  }, [selectingRestaurant, restaurant?.id]);

  const loadRestaurants = async () => {
    try {
      const response = await restaurantsAPI.listRestaurants();
      if (response.success && response.restaurants?.length > 0) {
        setRestaurants(response.restaurants);
        if (response.restaurants.length === 1) {
          setRestaurant(response.restaurants[0]);
          setSelectingRestaurant(false);
        }
      } else {
        setRestaurants([]);
      }
    } catch (error) {
      console.error('Error loading restaurants:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadMenu = async () => {
    if (!restaurant?.id) return;
    setLoading(true);
    try {
      const [itemsRes, categoriesRes] = await Promise.all([
        menuAPI.getMenuItems(restaurant.id),
        menuAPI.getCategories(restaurant.id),
      ]);
      if (itemsRes.success) setItems(itemsRes.items || []);
      if (categoriesRes.success) setCategories(categoriesRes.categories || []);
    } catch (error) {
      console.error('Error loading menu:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    if (selectingRestaurant) loadRestaurants();
    else loadMenu();
  };

  const selectRestaurant = (r) => {
    setRestaurant(r);
    setSelectingRestaurant(false);
  };

  const renderRestaurant = ({ item }) => (
    <TouchableOpacity
      style={styles.restaurantCard}
      onPress={() => selectRestaurant(item)}
    >
      <Text style={styles.restaurantName}>{item.name}</Text>
      {item.description && (
        <Text style={styles.restaurantDesc} numberOfLines={2}>
          {item.description}
        </Text>
      )}
    </TouchableOpacity>
  );

  const renderMenuItem = ({ item }) => (
    <View style={styles.itemCard}>
      <View style={styles.itemInfo}>
        <Text style={styles.itemName}>{item.name}</Text>
        {item.description && (
          <Text style={styles.itemDescription} numberOfLines={2}>
            {item.description}
          </Text>
        )}
        <Text style={styles.itemPrice}>
          {restaurant?.currency || 'USD'} {item.price?.toFixed(2)}
        </Text>
      </View>
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => addToCart(item)}
      >
        <Text style={styles.addButtonText}>Add</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e67e22" />
      </View>
    );
  }

  if (selectingRestaurant) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Select Restaurant</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Landing')}>
            <Text style={styles.backText}>Back</Text>
          </TouchableOpacity>
        </View>
        <FlatList
          data={restaurants}
          renderItem={renderRestaurant}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No restaurants available</Text>
            </View>
          }
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => setSelectingRestaurant(true)}>
          <Text style={styles.backText}>Change</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{restaurant?.name}</Text>
        <TouchableOpacity
          onPress={() => navigation.navigate('Cart')}
          style={styles.cartBadge}
        >
          <Text style={styles.cartBadgeText}>Cart ({itemCount})</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={items}
        renderItem={renderMenuItem}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No menu items available</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
  backText: { color: '#e67e22', fontSize: 16 },
  cartBadge: { backgroundColor: '#e67e22', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  cartBadgeText: { color: '#fff', fontWeight: 'bold' },
  restaurantCard: {
    backgroundColor: '#fff',
    padding: 20,
    margin: 10,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  restaurantName: { fontSize: 20, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  restaurantDesc: { fontSize: 14, color: '#666' },
  itemCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    margin: 10,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemInfo: { flex: 1 },
  itemName: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 4 },
  itemDescription: { fontSize: 14, color: '#666', marginBottom: 8 },
  itemPrice: { fontSize: 16, fontWeight: 'bold', color: '#e67e22' },
  addButton: {
    backgroundColor: '#e67e22',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  addButtonText: { color: '#fff', fontWeight: 'bold' },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: { fontSize: 18, color: '#999' },
});
