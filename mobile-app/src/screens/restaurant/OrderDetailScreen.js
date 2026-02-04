import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { ordersAPI } from '../../services/api';
import { colors } from '../../theme';

const STATUS_ACTIONS = {
  new: [
    { status: 'paid', label: 'Mark as Paid', color: colors.success },
    { status: 'cancelled', label: 'Cancel', color: colors.danger },
  ],
  pending: [
    { status: 'paid', label: 'Mark as Paid', color: colors.success },
    { status: 'cancelled', label: 'Cancel', color: colors.danger },
  ],
  paid: [
    { status: 'preparing', label: 'Preparing', color: '#9b59b6' },
    { status: 'cancelled', label: 'Cancel', color: colors.danger },
  ],
  preparing: [
    { status: 'ready', label: 'Ready', color: '#1abc9c' },
    { status: 'cancelled', label: 'Cancel', color: colors.danger },
  ],
  ready: [
    { status: 'delivered', label: 'Delivered', color: colors.success },
    { status: 'cancelled', label: 'Cancel', color: colors.danger },
  ],
};

export default function OrderDetailScreen({ route, navigation }) {
  const { orderId } = route?.params || {};
  const { user } = useAuth();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadOrder();
  }, [orderId]);

  const loadOrder = async () => {
    try {
      const response = await ordersAPI.getOrder(orderId);
      if (response.success) {
        setOrder(response.order);
      }
    } catch (error) {
      console.error('Error loading order:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (status) => {
    if (status === 'cancelled') {
      Alert.alert(
        'Cancel Order',
        'Are you sure you want to cancel this order?',
        [
          { text: 'No', style: 'cancel' },
          { text: 'Yes, Cancel', style: 'destructive', onPress: () => doUpdate(status) },
        ]
      );
    } else {
      doUpdate(status);
    }
  };

  const doUpdate = async (status) => {
    setUpdating(true);
    try {
      await ordersAPI.updateOrderStatus(orderId, status);
      await loadOrder();
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!order) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Order not found</Text>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backBtnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const actions = STATUS_ACTIONS[order.status] || [];
  const items = order.items || [];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Order #{order.id}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.label}>Status</Text>
          <View style={[styles.statusBadge, { backgroundColor: colors.primary }]}>
            <Text style={styles.statusText}>{order.status.toUpperCase()}</Text>
          </View>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Type</Text>
          <Text style={styles.value}>{order.order_type?.replace('_', '-')}</Text>
        </View>
        {order.table_number && (
          <View style={styles.row}>
            <Text style={styles.label}>Table</Text>
            <Text style={styles.value}>{order.table_number}</Text>
          </View>
        )}
        {order.customer_name && (
          <View style={styles.row}>
            <Text style={styles.label}>Customer</Text>
            <Text style={styles.value}>{order.customer_name}</Text>
          </View>
        )}
        {order.customer_phone && (
          <View style={styles.row}>
            <Text style={styles.label}>Phone</Text>
            <Text style={styles.value}>{order.customer_phone}</Text>
          </View>
        )}
        {order.delivery_address && (
          <View style={styles.row}>
            <Text style={styles.label}>Address</Text>
            <Text style={styles.value}>{order.delivery_address}</Text>
          </View>
        )}
        <View style={styles.row}>
          <Text style={styles.label}>Time</Text>
          <Text style={styles.value}>
            {new Date(order.created_at).toLocaleString()}
          </Text>
        </View>
        {order.special_instructions && (
          <View style={styles.row}>
            <Text style={styles.label}>Instructions</Text>
            <Text style={styles.value}>{order.special_instructions}</Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Items</Text>
        {items.map((item) => (
          <View key={item.id} style={styles.itemRow}>
            <Text style={styles.itemName}>
              {item.quantity}x {item.item_name || item.name}
            </Text>
            <Text style={styles.itemPrice}>
              {user?.currency || 'USD'} {(item.price * item.quantity).toFixed(2)}
            </Text>
          </View>
        ))}
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalValue}>
            {user?.currency || 'USD'} {order.total?.toFixed(2)}
          </Text>
        </View>
      </View>

      {actions.length > 0 && (
        <View style={styles.actions}>
          {actions.map((a) => (
            <TouchableOpacity
              key={a.status}
              style={[styles.actionBtn, { backgroundColor: a.color }]}
              onPress={() => updateStatus(a.status)}
              disabled={updating}
            >
              <Text style={styles.actionBtnText}>{a.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </ScrollView>
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
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backText: { color: colors.primary, fontSize: 16 },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    color: colors.text,
  },
  card: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  row: { marginBottom: 14 },
  label: { fontSize: 12, color: colors.textMuted, marginBottom: 4 },
  value: { fontSize: 16, color: colors.text, fontWeight: '500' },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  section: {
    backgroundColor: '#fff',
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 16,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  itemName: { fontSize: 15, color: colors.text },
  itemPrice: { fontSize: 15, fontWeight: '600', color: colors.primary },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 2,
    borderTopColor: colors.border,
  },
  totalLabel: { fontSize: 18, fontWeight: 'bold', color: colors.text },
  totalValue: { fontSize: 18, fontWeight: 'bold', color: colors.primary },
  actions: { padding: 16, gap: 12 },
  actionBtn: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  actionBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  errorText: { fontSize: 18, color: colors.textMuted, marginBottom: 20 },
  backBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backBtnText: { color: '#fff', fontWeight: '600' },
});
