import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { ordersAPI } from '../../services/api';

const STATUS_LABELS = {
  new: 'Order Received',
  pending: 'Payment Pending',
  paid: 'Paid',
  preparing: 'Preparing',
  ready: 'Ready for Pickup',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

export default function OrderTrackingScreen({ route, navigation }) {
  const { orderId } = route?.params || {};
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadOrder = async () => {
    if (!orderId) return;
    try {
      const response = await ordersAPI.trackOrder(orderId);
      if (response.success) {
        setOrder(response.order);
      }
    } catch (error) {
      console.error('Error loading order:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadOrder();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId]);

  const onRefresh = () => {
    setRefreshing(true);
    loadOrder();
  };

  if (loading && !order) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e67e22" />
      </View>
    );
  }

  if (!order) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Order not found</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('Landing')}
        >
          <Text style={styles.buttonText}>Back to Home</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.card}>
        <Text style={styles.orderId}>Order #{order.id}</Text>
        <View
          style={[
            styles.statusBadge,
            { backgroundColor: getStatusColor(order.status) },
          ]}
        >
          <Text style={styles.statusText}>
            {STATUS_LABELS[order.status] || order.status}
          </Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Total</Text>
        <Text style={styles.total}>USD {order.total?.toFixed(2)}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Placed at</Text>
        <Text style={styles.value}>
          {order.created_at
            ? new Date(order.created_at).toLocaleString()
            : '—'}
        </Text>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('CustomerMenu')}
      >
        <Text style={styles.buttonText}>Order Again</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.linkButton}
        onPress={() => navigation.navigate('Landing')}
      >
        <Text style={styles.linkText}>Back to Home</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function getStatusColor(status) {
  const colors = {
    new: '#3498db',
    pending: '#f39c12',
    paid: '#2ecc71',
    preparing: '#9b59b6',
    ready: '#1abc9c',
    delivered: '#27ae60',
    cancelled: '#e74c3c',
  };
  return colors[status] || '#95a5a6';
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 16 },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  card: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 8,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  orderId: { fontSize: 24, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  statusText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  label: { fontSize: 14, color: '#666', marginBottom: 4 },
  total: { fontSize: 20, fontWeight: 'bold', color: '#e67e22' },
  value: { fontSize: 16, color: '#333' },
  errorText: { fontSize: 18, color: '#666', textAlign: 'center', marginBottom: 24 },
  button: {
    backgroundColor: '#e67e22',
    padding: 18,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  linkButton: { alignItems: 'center', marginTop: 16 },
  linkText: { color: '#e67e22', fontSize: 16 },
});
