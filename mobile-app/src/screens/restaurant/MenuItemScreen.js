import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function MenuItemScreen({ route }) {
  const { itemId } = route.params;

  return (
    <View style={styles.container}>
      <Text>Menu Item {itemId}</Text>
      {/* Add menu item details and edit functionality */}
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

