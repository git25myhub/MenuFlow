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
import { useAuth } from '../../context/AuthContext';
import { ordersAPI } from '../../services/api';
import { colors } from '../../theme';

const STATUS_COLORS = {
  new: '#3498db',
  pending: '#f39c12',
  paid: '#2ecc71',
  preparing: '#9b59b6',
  ready: '#1abc9c',
  delivered: '#27ae60',
  cancelled: '#e74c3c',
};

export default function OrdersScreen({ navigation }) {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('dine_in');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await ordersAPI.getOrders();
      if (response.success) {
        setOrders(response.orders || []);
      }
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadOrders();
  };

  const filteredOrders = orders.filter((o) => o.order_type === activeTab);
  const dineInCount = orders.filter((o) => o.order_type === 'dine_in').length;
  const deliveryCount = orders.filter((o) => o.order_type === 'delivery').length;

  const renderOrder = ({ item }) => (
    <TouchableOpacity
      style={styles.orderCard}
      onPress={() => navigation.navigate('OrderDetail', { orderId: item.id })}
    >
      <View style={styles.orderHeader}>
        <Text style={styles.orderId}>Order #{item.id}</Text>
        <View
          style={[
            styles.statusBadge,
            { backgroundColor: STATUS_COLORS[item.status] || '#95a5a6' },
          ]}
        >
          <Text style={styles.statusText}>{item.status.toUpperCase()}</Text>
        </View>
      </View>
      <Text style={styles.orderType}>
        {item.order_type === 'dine_in' && item.table_number
          ? `Table ${item.table_number}`
          : item.order_type}
      </Text>
      <Text style={styles.orderTotal}>
        {user?.currency || 'USD'} {item.total?.toFixed(2)}
      </Text>
      <Text style={styles.orderTime}>
        {new Date(item.created_at).toLocaleString()}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'dine_in' && styles.tabActive]}
          onPress={() => setActiveTab('dine_in')}
        >
          <Text style={[styles.tabText, activeTab === 'dine_in' && styles.tabTextActive]}>
            Dine-in
          </Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{dineInCount}</Text>
          </View>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'delivery' && styles.tabActive]}
          onPress={() => setActiveTab('delivery')}
        >
          <Text style={[styles.tabText, activeTab === 'delivery' && styles.tabTextActive]}>
            Delivery
          </Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{deliveryCount}</Text>
          </View>
        </TouchableOpacity>
      </View>
      <FlatList
        data={filteredOrders}
        renderItem={renderOrder}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No {activeTab.replace('_', '-')} orders yet</Text>
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
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 2,
    borderBottomColor: colors.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    gap: 8,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: colors.primary,
    marginBottom: -2,
  },
  tabText: { fontSize: 15, color: colors.textLight, fontWeight: '500' },
  tabTextActive: { color: colors.text, fontWeight: '600' },
  badge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  list: { padding: 16 },
  orderCard: {
    backgroundColor: '#fff',
    padding: 18,
    marginBottom: 14,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  orderId: { fontSize: 18, fontWeight: 'bold', color: colors.text },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  orderType: {
    fontSize: 14,
    color: colors.textLight,
    marginBottom: 6,
    textTransform: 'capitalize',
  },
  orderTotal: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.primary,
    marginBottom: 6,
  },
  orderTime: { fontSize: 12, color: colors.textMuted },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: { fontSize: 18, color: colors.textMuted },
});
