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
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { menuAPI } from '../../services/api';
import Constants from 'expo-constants';
import { colors } from '../../theme';

const API_BASE = Constants.expoConfig?.extra?.apiUrl?.replace('/api/v1', '') || 'https://bluespace-restaurants.onrender.com';
const getImageUri = (url) => (url?.startsWith('http') ? url : url ? `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}` : null);

export default function MenuScreen({ navigation }) {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadMenu();
  }, []);

  const loadMenu = async () => {
    try {
      const rid = user?.restaurant_id || user?.id;
      const response = await menuAPI.getMenuItems(rid);
      if (response.success) {
        setItems(response.items || []);
      }
    } catch (error) {
      console.error('Error loading menu:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadMenu();
  };

  const renderItem = ({ item }) => {
    const imageUri = getImageUri(item.image_url);
    return (
      <TouchableOpacity
        style={styles.itemCard}
        onPress={() => navigation.navigate('MenuItem', { itemId: item.id })}
      >
        {imageUri && (
          <Image source={{ uri: imageUri }} style={styles.itemImage} />
        )}
        <View style={styles.itemContent}>
          <Text style={styles.itemName}>{item.name}</Text>
          {item.description && (
            <Text style={styles.itemDescription} numberOfLines={2}>
              {item.description}
            </Text>
          )}
          <View style={styles.itemFooter}>
            <Text style={styles.itemPrice}>
              {user?.currency || 'USD'} {item.price?.toFixed(2)}
            </Text>
            {item.stock != null && (
              <Text style={styles.itemStock}>Stock: {item.stock}</Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Menu Items</Text>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate('MenuItem', { itemId: null })}
        >
          <Text style={styles.addBtnText}>+ Add Item</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No menu items yet</Text>
            <TouchableOpacity
              style={styles.emptyBtn}
              onPress={() => navigation.navigate('MenuItem', { itemId: null })}
            >
              <Text style={styles.emptyBtnText}>Add your first item</Text>
            </TouchableOpacity>
          </View>
        }
      />
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: colors.text },
  addBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  addBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  list: { padding: 16, paddingBottom: 24 },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
    flexDirection: 'row',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  itemImage: {
    width: 100,
    height: 100,
    backgroundColor: colors.border,
  },
  itemContent: { flex: 1, padding: 16, justifyContent: 'center' },
  itemName: { fontSize: 18, fontWeight: 'bold', color: colors.text, marginBottom: 4 },
  itemDescription: { fontSize: 14, color: colors.textLight, marginBottom: 8 },
  itemFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  itemPrice: { fontSize: 16, fontWeight: 'bold', color: colors.primary },
  itemStock: { fontSize: 12, color: colors.textMuted },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: { fontSize: 18, color: colors.textMuted, marginBottom: 20 },
  emptyBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  emptyBtnText: { color: '#fff', fontWeight: '600' },
});
