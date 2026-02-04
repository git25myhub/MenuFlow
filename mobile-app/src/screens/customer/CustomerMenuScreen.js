import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  Image,
  ScrollView,
} from 'react-native';
import { useCart } from '../../context/CartContext';
import { menuAPI, restaurantsAPI } from '../../services/api';
import Constants from 'expo-constants';
import { colors } from '../../theme';

const API_BASE = Constants.expoConfig?.extra?.apiUrl?.replace('/api/v1', '') || 'https://bluespace-restaurants.onrender.com';

const getImageUri = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
};

const CATEGORY_ICONS = {
  starters: '🥗',
  appetizers: '🥗',
  'main course': '🍖',
  mains: '🍖',
  desserts: '🍰',
  sweets: '🍰',
  beverages: '🥤',
  drinks: '🥤',
  'hot drinks': '☕',
  coffee: '☕',
  tea: '☕',
  sides: '🥔',
  breakfast: '🍳',
  burgers: '🍔',
  sandwiches: '🍔',
  pizza: '🍕',
};

const getCategoryIcon = (name) => CATEGORY_ICONS[name?.toLowerCase()] || '🍽️';

export default function CustomerMenuScreen({ navigation }) {
  const { restaurant, setRestaurant, addToCart, itemCount } = useCart();
  const [restaurants, setRestaurants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectingRestaurant, setSelectingRestaurant] = useState(!restaurant);

  useEffect(() => {
    if (selectingRestaurant) {
      loadRestaurants();
    } else {
      loadMenu();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        menuAPI.getMenuItems(restaurant.id, selectedCategory),
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

  useEffect(() => {
    if (restaurant?.id && !selectingRestaurant) {
      loadMenu();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]);

  const onRefresh = () => {
    setRefreshing(true);
    if (selectingRestaurant) loadRestaurants();
    else loadMenu();
  };

  const selectRestaurant = (r) => {
    setRestaurant(r);
    setSelectingRestaurant(false);
  };

  const filteredItems = selectedCategory
    ? items.filter((i) => i.category_id === selectedCategory)
    : items;

  const renderRestaurant = ({ item }) => (
    <TouchableOpacity
      style={styles.restaurantCard}
      onPress={() => selectRestaurant(item)}
    >
      {item.logo_url && (
        <Image
          source={{ uri: getImageUri(item.logo_url) }}
          style={styles.restaurantLogo}
        />
      )}
      <Text style={styles.restaurantName}>{item.name}</Text>
      {item.description && (
        <Text style={styles.restaurantDesc} numberOfLines={2}>
          {item.description}
        </Text>
      )}
    </TouchableOpacity>
  );

  const renderMenuItem = ({ item }) => {
    const soldOut = item.stock === 0;
    const imageUri = getImageUri(item.image_url);
    return (
      <View style={styles.menuCard}>
        {imageUri && (
          <View style={styles.menuImageWrap}>
            <Image source={{ uri: imageUri }} style={styles.menuImage} />
            {soldOut && (
              <View style={styles.soldOutBadge}>
                <Text style={styles.soldOutText}>Sold Out</Text>
              </View>
            )}
          </View>
        )}
        <View style={styles.menuContent}>
          <Text style={styles.menuTitle}>{item.name}</Text>
          {item.description && (
            <Text style={styles.menuDesc} numberOfLines={2}>
              {item.description}
            </Text>
          )}
          <View style={styles.menuFooter}>
            <Text style={styles.menuPrice}>
              {restaurant?.currency || 'USD'} {item.price?.toFixed(2)}
            </Text>
            <View style={[styles.stockBadge, soldOut ? styles.stockOut : styles.stockIn]}>
              <Text style={styles.stockText}>
                {soldOut ? 'Out of Stock' : 'In Stock'}
              </Text>
            </View>
          </View>
          {!soldOut && (
            <TouchableOpacity
              style={styles.addBtn}
              onPress={() => addToCart(item)}
            >
              <Text style={styles.addBtnText}>Add to Cart</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (selectingRestaurant) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Landing')}>
            <Text style={styles.backText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Select Restaurant</Text>
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
      {/* Hero */}
      <View style={styles.hero}>
        <View style={styles.heroOverlay}>
          {restaurant?.logo_url && (
            <Image
              source={{ uri: getImageUri(restaurant.logo_url) }}
              style={styles.heroLogo}
            />
          )}
          <Text style={styles.heroTitle}>
            Welcome to {restaurant?.name}
          </Text>
          <Text style={styles.heroSubtitle}>✨ We are delighted to serve you today! ✨</Text>
        </View>
      </View>

      {/* Header */}
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

      {/* Categories */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.categoryScroll}
        contentContainerStyle={styles.categoryScrollContent}
      >
        <TouchableOpacity
          style={[styles.categoryBtn, !selectedCategory && styles.categoryBtnActive]}
          onPress={() => setSelectedCategory(null)}
        >
          <Text style={styles.categoryIcon}>🍽️</Text>
          <Text style={styles.categoryText}>All</Text>
        </TouchableOpacity>
        {categories.map((cat) => (
          <TouchableOpacity
            key={cat.id}
            style={[
              styles.categoryBtn,
              selectedCategory === cat.id && styles.categoryBtnActive,
            ]}
            onPress={() => setSelectedCategory(cat.id)}
          >
            <Text style={styles.categoryIcon}>{getCategoryIcon(cat.name)}</Text>
            <Text style={styles.categoryText}>{cat.name}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Menu items */}
      <FlatList
        data={filteredItems}
        renderItem={renderMenuItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.menuList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No menu items available</Text>
          </View>
        }
      />

      {/* Floating Place Order */}
      <TouchableOpacity
        style={styles.placeOrderBtn}
        onPress={() => navigation.navigate('Cart')}
      >
        <Text style={styles.placeOrderBtnText}>Place Order</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  hero: {
    minHeight: 180,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  heroLogo: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginBottom: 12,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { fontSize: 18, fontWeight: 'bold', color: colors.text },
  backText: { color: colors.primary, fontSize: 16 },
  cartBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  cartBadgeText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  categoryScroll: { maxHeight: 56, backgroundColor: '#fff' },
  categoryScrollContent: {
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    marginRight: 8,
  },
  categoryBtnActive: {
    backgroundColor: colors.primary,
  },
  categoryIcon: { fontSize: 18, marginRight: 6 },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textLight,
  },
  menuList: { padding: 16, paddingBottom: 100 },
  menuCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  menuImageWrap: { position: 'relative', height: 180 },
  menuImage: { width: '100%', height: '100%', resizeMode: 'cover' },
  soldOutBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'rgba(231,76,60,0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  soldOutText: { color: '#fff', fontWeight: '600', fontSize: 12 },
  menuContent: { padding: 16 },
  menuTitle: { fontSize: 18, fontWeight: 'bold', color: colors.text, marginBottom: 6 },
  menuDesc: { fontSize: 14, color: colors.textLight, marginBottom: 12 },
  menuFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  menuPrice: { fontSize: 18, fontWeight: '600', color: colors.primary },
  stockBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  stockIn: { backgroundColor: 'rgba(75,183,27,0.15)' },
  stockOut: { backgroundColor: 'rgba(231,76,60,0.15)' },
  stockText: { fontSize: 12, fontWeight: '500' },
  addBtn: {
    backgroundColor: colors.primary,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  addBtnText: { color: '#fff', fontWeight: '600' },
  restaurantCard: {
    backgroundColor: '#fff',
    padding: 20,
    margin: 10,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  restaurantLogo: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginBottom: 12,
  },
  restaurantName: { fontSize: 20, fontWeight: 'bold', color: colors.text, marginBottom: 8 },
  restaurantDesc: { fontSize: 14, color: colors.textLight },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: { fontSize: 18, color: colors.textMuted },
  placeOrderBtn: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    backgroundColor: colors.success,
    paddingVertical: 16,
    paddingHorizontal: 28,
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
  placeOrderBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
