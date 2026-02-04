import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { menuAPI } from '../../services/api';
import { colors } from '../../theme';

export default function MenuItemScreen({ route, navigation }) {
  const { itemId } = route?.params || {};
  const isEdit = !!itemId;
  const { user } = useAuth();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [categoryId, setCategoryId] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [stock, setStock] = useState('');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCategories();
    if (isEdit) {
      loadItem();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId]);

  const loadCategories = async () => {
    try {
      const rid = user?.restaurant_id || user?.id;
      const res = await menuAPI.getCategories(rid);
      if (res.success && res.categories?.length > 0) {
        setCategories(res.categories);
        if (!isEdit && res.categories[0]) {
          setCategoryId(res.categories[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadItem = async () => {
    try {
      const res = await menuAPI.getMenuItem(itemId);
      if (res.success && res.item) {
        const item = res.item;
        setName(item.name || '');
        setDescription(item.description || '');
        setPrice(item.price?.toString() || '');
        setCategoryId(item.category_id);
        setImageUrl(item.image_url || '');
        setStock(item.stock?.toString() ?? '');
      }
    } catch (error) {
      console.error('Error loading item:', error);
      Alert.alert('Error', 'Failed to load menu item');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter item name');
      return;
    }
    const priceNum = parseFloat(price);
    if (isNaN(priceNum) || priceNum < 0) {
      Alert.alert('Error', 'Please enter a valid price');
      return;
    }
    if (!categoryId) {
      Alert.alert('Error', 'Please select a category');
      return;
    }

    setSaving(true);
    try {
      const data = {
        name: name.trim(),
        description: description.trim() || null,
        price: priceNum,
        category_id: categoryId,
        image_url: imageUrl.trim() || null,
        stock: stock !== '' ? parseInt(stock, 10) : 0,
      };

      if (isEdit) {
        const res = await menuAPI.updateMenuItem(itemId, data);
        if (res.success) {
          Alert.alert('Success', 'Menu item updated');
          navigation.goBack();
        } else {
          Alert.alert('Error', res.error || 'Update failed');
        }
      } else {
        const res = await menuAPI.createMenuItem(data);
        if (res.success) {
          Alert.alert('Success', 'Menu item added');
          navigation.goBack();
        } else {
          Alert.alert('Error', res.error || 'Create failed');
        }
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || error.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {isEdit ? 'Edit Menu Item' : 'Add Menu Item'}
        </Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Name *</Text>
        <TextInput
          style={styles.input}
          placeholder="Item name"
          value={name}
          onChangeText={setName}
        />

        <Text style={styles.label}>Description</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Describe your dish"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={3}
        />

        <Text style={styles.label}>Price *</Text>
        <TextInput
          style={styles.input}
          placeholder="0.00"
          value={price}
          onChangeText={setPrice}
          keyboardType="decimal-pad"
        />

        <Text style={styles.label}>Category *</Text>
        <View style={styles.categoryRow}>
          {categories.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={[
                styles.categoryChip,
                categoryId === cat.id && styles.categoryChipActive,
              ]}
              onPress={() => setCategoryId(cat.id)}
            >
              <Text
                style={[
                  styles.categoryChipText,
                  categoryId === cat.id && styles.categoryChipTextActive,
                ]}
              >
                {cat.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Image URL</Text>
        <TextInput
          style={styles.input}
          placeholder="https://example.com/image.jpg"
          value={imageUrl}
          onChangeText={setImageUrl}
          autoCapitalize="none"
        />
        {imageUrl.trim() && (
          <Image
            source={{ uri: imageUrl.trim() }}
            style={styles.previewImage}
            resizeMode="cover"
          />
        )}

        <Text style={styles.label}>Stock (optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="0"
          value={stock}
          onChangeText={setStock}
          keyboardType="number-pad"
        />

        <TouchableOpacity
          style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.saveBtnText}>
              {isEdit ? 'Update Item' : 'Add Menu Item'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
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
  form: { padding: 20 },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#fff',
    padding: 14,
    borderRadius: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  categoryRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    marginRight: 8,
    marginBottom: 8,
  },
  categoryChipActive: { backgroundColor: colors.primary },
  categoryChipText: { fontSize: 14, color: colors.text },
  categoryChipTextActive: { color: '#fff', fontWeight: '600' },
  previewImage: {
    width: '100%',
    height: 150,
    borderRadius: 8,
    marginTop: 12,
    backgroundColor: colors.border,
  },
  saveBtn: {
    backgroundColor: colors.primary,
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 32,
  },
  saveBtnDisabled: { opacity: 0.7 },
  saveBtnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
