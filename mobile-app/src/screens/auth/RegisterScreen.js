import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { colors } from '../../theme';

const CURRENCIES = [
  { value: 'USD', label: 'US Dollar ($)' },
  { value: 'KES', label: 'Kenyan Shilling (KSh)' },
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'GBP', label: 'British Pound (£)' },
  { value: 'INR', label: 'Indian Rupee (₹)' },
  { value: 'AUD', label: 'Australian Dollar (A$)' },
  { value: 'CAD', label: 'Canadian Dollar (C$)' },
  { value: 'JPY', label: 'Japanese Yen (¥)' },
];

export default function RegisterScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [restaurantName, setRestaurantName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleRegister = async () => {
    if (!email || !password || !restaurantName) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }
    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    setLoading(true);
    const result = await register({
      email,
      password,
      restaurant_name: restaurantName,
      currency,
    });
    setLoading(false);

    if (!result.success) {
      Alert.alert('Registration Failed', result.error || 'Registration failed');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <TouchableOpacity
          onPress={() => navigation.navigate('Login')}
          style={styles.backButton}
        >
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>

        <View style={styles.card}>
          <View style={styles.shimmerBar} />
          <View style={styles.brandLogo}>
            <Text style={styles.brandIcon}>🍽️</Text>
          </View>
          <Text style={styles.headerTitle}>Create Your Account</Text>
          <Text style={styles.headerSubtitle}>Start your digital menu journey today</Text>

          <View style={styles.form}>
            <Text style={styles.label}>Email address</Text>
            <TextInput
              style={styles.input}
              placeholder="name@example.com"
              placeholderTextColor="#a0aec0"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <Text style={[styles.label, { marginTop: 16 }]}>Password</Text>
            <View style={styles.passwordWrapper}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                placeholder="Min 6 characters"
                placeholderTextColor="#a0aec0"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
              />
              <TouchableOpacity
                style={styles.eyeButton}
                onPress={() => setShowPassword(!showPassword)}
              >
                <Text style={styles.eyeIcon}>{showPassword ? '🙈' : '👁️'}</Text>
              </TouchableOpacity>
            </View>

            <Text style={[styles.label, { marginTop: 16 }]}>Confirm Password</Text>
            <TextInput
              style={styles.input}
              placeholder="Confirm password"
              placeholderTextColor="#a0aec0"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
            />
            {confirmPassword.length > 0 && (
              <Text
                style={[
                  styles.matchText,
                  password === confirmPassword ? styles.matchOk : styles.matchErr,
                ]}
              >
                {password === confirmPassword ? '✓ Passwords match' : '✗ Passwords do not match'}
              </Text>
            )}

            <Text style={[styles.label, { marginTop: 16 }]}>Restaurant Name</Text>
            <TextInput
              style={styles.input}
              placeholder="Your restaurant name"
              placeholderTextColor="#a0aec0"
              value={restaurantName}
              onChangeText={setRestaurantName}
              autoCapitalize="words"
            />

            <Text style={[styles.label, { marginTop: 16 }]}>Currency</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.currencyRow}
            >
              {CURRENCIES.map((c) => (
                <TouchableOpacity
                  key={c.value}
                  style={[styles.currencyChip, currency === c.value && styles.currencyChipActive]}
                  onPress={() => setCurrency(c.value)}
                >
                  <Text
                    style={[
                      styles.currencyChipText,
                      currency === c.value && styles.currencyChipTextActive,
                    ]}
                  >
                    {c.value}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleRegister}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Create Account</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => navigation.navigate('Login')}
              style={styles.linkButton}
            >
              <Text style={styles.linkText}>Already have an account? Sign in here</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#2d3748' },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
    paddingTop: 60,
    paddingBottom: 40,
  },
  backButton: { position: 'absolute', top: 48, left: 24, zIndex: 10 },
  backText: { color: '#fff', fontSize: 16 },
  card: {
    backgroundColor: 'rgba(255,255,255,0.98)',
    borderRadius: 24,
    padding: 28,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.3,
    shadowRadius: 60,
    elevation: 20,
  },
  shimmerBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    backgroundColor: colors.authPrimary,
  },
  brandLogo: { alignItems: 'center', marginBottom: 20 },
  brandIcon: { fontSize: 48 },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#2d3748',
    textAlign: 'center',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 15,
    color: '#718096',
    textAlign: 'center',
    marginBottom: 24,
  },
  form: {},
  label: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    height: 54,
    paddingHorizontal: 16,
    paddingLeft: 44,
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    backgroundColor: colors.inputBg,
    fontSize: 16,
    color: '#2d3748',
  },
  passwordWrapper: { position: 'relative' },
  passwordInput: { paddingRight: 50 },
  eyeButton: {
    position: 'absolute',
    right: 12,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
  },
  eyeIcon: { fontSize: 20 },
  matchText: { fontSize: 13, marginTop: 6 },
  matchOk: { color: '#48bb78' },
  matchErr: { color: '#f56565' },
  currencyRow: { marginTop: 8, marginBottom: 8, maxHeight: 44 },
  currencyChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    marginRight: 8,
  },
  currencyChipActive: {
    backgroundColor: colors.authPrimary,
  },
  currencyChipText: { fontSize: 14, color: '#4a5568', fontWeight: '500' },
  currencyChipTextActive: { color: '#fff' },
  button: {
    backgroundColor: colors.authPrimary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
    shadowColor: colors.authPrimary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 15,
    elevation: 8,
  },
  buttonDisabled: { opacity: 0.7 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  linkButton: {
    marginTop: 24,
    alignItems: 'center',
    paddingTop: 24,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  linkText: { color: colors.authPrimary, fontSize: 15, fontWeight: '600' },
});
