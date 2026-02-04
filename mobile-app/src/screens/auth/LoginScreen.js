import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { colors } from '../../theme';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }

    setLoading(true);
    const result = await login(email, password);
    setLoading(false);

    if (!result.success) {
      Alert.alert('Login Failed', result.error || 'Invalid credentials');
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
          onPress={() => navigation.navigate('Landing')}
          style={styles.backButton}
        >
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>

        <View style={styles.card}>
          <View style={styles.shimmerBar} />
          <View style={styles.brandLogo}>
            <Text style={styles.brandIcon}>🍽️</Text>
          </View>
          <Text style={styles.headerTitle}>Welcome Back</Text>
          <Text style={styles.headerSubtitle}>Sign in to manage your restaurant</Text>

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
              autoComplete="email"
            />

            <Text style={[styles.label, { marginTop: 20 }]}>Password</Text>
            <View style={styles.passwordWrapper}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                placeholder="Password"
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

            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Sign In</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => navigation.navigate('Register')}
              style={styles.linkButton}
            >
              <Text style={styles.linkText}>Don't have an account? Create one now</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2d3748',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
    paddingTop: 60,
  },
  backButton: {
    position: 'absolute',
    top: 48,
    left: 24,
    zIndex: 10,
  },
  backText: {
    color: '#fff',
    fontSize: 16,
  },
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
  brandLogo: {
    alignItems: 'center',
    marginBottom: 20,
  },
  brandIcon: {
    fontSize: 48,
  },
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
    marginBottom: 28,
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
  passwordWrapper: {
    position: 'relative',
  },
  passwordInput: {
    paddingRight: 50,
  },
  eyeButton: {
    position: 'absolute',
    right: 12,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
  },
  eyeIcon: {
    fontSize: 20,
  },
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
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 24,
    alignItems: 'center',
    paddingTop: 24,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  linkText: {
    color: colors.authPrimary,
    fontSize: 15,
    fontWeight: '600',
  },
});
