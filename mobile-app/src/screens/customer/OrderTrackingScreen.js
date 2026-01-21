import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function OrderTrackingScreen() {
  return (
    <View style={styles.container}>
      <Text>Order Tracking</Text>
      {/* Add order tracking functionality */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
});

