import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useCart } from '../../context/CartContext';
import { ordersAPI } from '../../services/api';

export default function CheckoutScreen({ navigation }) {
  const { cart, restaurant, total, clearCart } = useCart();
  const [orderType, setOrderType] = useState('dine_in');
  const [tableNumber, setTableNumber] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePlaceOrder = async () => {
    if (orderType === 'dine_in') {
      if (!tableNumber.trim()) {
        Alert.alert('Error', 'Please enter your table number');
        return;
      }
    } else {
      if (!customerName.trim()) {
        Alert.alert('Error', 'Please enter your name');
        return;
      }
      if (!customerPhone.trim()) {
        Alert.alert('Error', 'Please enter your phone number');
        return;
      }
      if (!deliveryAddress.trim()) {
        Alert.alert('Error', 'Please enter delivery address');
        return;
      }
    }

    setLoading(true);
    try {
      const orderData = {
        restaurant_id: restaurant.id,
        order_type: orderType,
        total: total,
        items: cart.map((item) => ({
          menu_item_id: item.id,
          quantity: item.quantity,
        })),
        table_number: orderType === 'dine_in' ? tableNumber.trim() : null,
        customer_name: orderType === 'delivery' ? customerName.trim() : null,
        customer_phone: orderType === 'delivery' ? customerPhone.trim() : null,
        delivery_address: orderType === 'delivery' ? deliveryAddress.trim() : null,
        special_instructions: specialInstructions.trim() || null,
      };

      const response = await ordersAPI.createGuestOrder(orderData);
      if (response.success) {
        clearCart();
        navigation.replace('OrderTracking', { orderId: response.order.id });
      } else {
        Alert.alert('Error', response.error || 'Failed to place order');
      }
    } catch (error) {
      Alert.alert(
        'Error',
        error.response?.data?.error || error.message || 'Failed to place order. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Checkout</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Order Type</Text>
        <View style={styles.orderTypeRow}>
          <TouchableOpacity
            style={[styles.orderTypeBtn, orderType === 'dine_in' && styles.orderTypeBtnActive]}
            onPress={() => setOrderType('dine_in')}
          >
            <Text style={[styles.orderTypeText, orderType === 'dine_in' && styles.orderTypeTextActive]}>
              Dine In
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.orderTypeBtn, orderType === 'delivery' && styles.orderTypeBtnActive]}
            onPress={() => setOrderType('delivery')}
          >
            <Text style={[styles.orderTypeText, orderType === 'delivery' && styles.orderTypeTextActive]}>
              Delivery
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          {orderType === 'dine_in' ? 'Table Details' : 'Your Details'}
        </Text>
        {orderType === 'dine_in' ? (
          <TextInput
            style={styles.input}
            placeholder="Table number *"
            value={tableNumber}
            onChangeText={setTableNumber}
            keyboardType="number-pad"
          />
        ) : (
          <>
            <TextInput
              style={styles.input}
              placeholder="Your name *"
              value={customerName}
              onChangeText={setCustomerName}
              autoCapitalize="words"
            />
            <TextInput
              style={styles.input}
              placeholder="Phone number *"
              value={customerPhone}
              onChangeText={setCustomerPhone}
              keyboardType="phone-pad"
            />
            <TextInput
              style={styles.input}
              placeholder="Delivery address *"
              value={deliveryAddress}
              onChangeText={setDeliveryAddress}
            />
          </>
        )}
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Special instructions (optional)"
          value={specialInstructions}
          onChangeText={setSpecialInstructions}
          multiline
          numberOfLines={3}
        />
      </View>

      <View style={styles.summary}>
        <Text style={styles.summaryTitle}>Order Summary</Text>
        {cart.map((item) => (
          <View key={item.id} style={styles.summaryRow}>
            <Text style={styles.summaryItem}>{item.name} × {item.quantity}</Text>
            <Text style={styles.summaryPrice}>
              {restaurant?.currency || 'USD'} {(item.price * item.quantity).toFixed(2)}
            </Text>
          </View>
        ))}
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalValue}>
            {restaurant?.currency || 'USD'} {total.toFixed(2)}
          </Text>
        </View>
      </View>

      <TouchableOpacity
        style={styles.placeButton}
        onPress={handlePlaceOrder}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.placeButtonText}>Place Order</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  backText: { color: '#e67e22', fontSize: 16 },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: 'bold', textAlign: 'center', color: '#333' },
  section: { backgroundColor: '#fff', padding: 16, marginTop: 10 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#333', marginBottom: 12 },
  orderTypeRow: { flexDirection: 'row' },
  orderTypeBtn: {
    flex: 1,
    padding: 14,
    marginHorizontal: 6,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
  },
  orderTypeBtnActive: { backgroundColor: '#e67e22' },
  orderTypeText: { fontSize: 16, color: '#666' },
  orderTypeTextActive: { color: '#fff', fontWeight: 'bold' },
  input: {
    backgroundColor: '#f5f5f5',
    padding: 14,
    borderRadius: 8,
    marginBottom: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  summary: {
    backgroundColor: '#fff',
    padding: 16,
    marginTop: 10,
  },
  summaryTitle: { fontSize: 16, fontWeight: 'bold', color: '#333', marginBottom: 12 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  summaryItem: { fontSize: 14, color: '#666' },
  summaryPrice: { fontSize: 14, color: '#333' },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  totalLabel: { fontSize: 18, fontWeight: 'bold', color: '#333' },
  totalValue: { fontSize: 18, fontWeight: 'bold', color: '#e67e22' },
  placeButton: {
    backgroundColor: '#e67e22',
    padding: 18,
    margin: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  placeButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
