import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function CustomerMenuScreen() {
  return (
    <View style={styles.container}>
      <Text>Customer Menu</Text>
      {/* Add customer menu browsing */}
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

