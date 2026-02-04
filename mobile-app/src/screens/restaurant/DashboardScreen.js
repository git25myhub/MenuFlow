import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Image,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { analyticsAPI } from '../../services/api';
import Constants from 'expo-constants';
import { colors } from '../../theme';

const API_BASE = Constants.expoConfig?.extra?.apiUrl?.replace('/api/v1', '') || 'https://bluespace-restaurants.onrender.com';
const getImageUri = (url) => (url?.startsWith('http') ? url : url ? `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}` : null);

export default function DashboardScreen() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await analyticsAPI.getDashboardStats(7);
      if (response.success) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
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
      <View style={styles.hero}>
        {user?.logo_url && (
          <Image
            source={{ uri: getImageUri(user.logo_url) }}
            style={styles.logo}
          />
        )}
        <Text style={styles.welcomeText}>Welcome, {user?.restaurant_name}!</Text>
        <Text style={styles.heroSubtitle}>Manage your menu and track orders from here.</Text>
      </View>

      {stats && (
        <View style={styles.statsContainer}>
          <View style={[styles.statCard, styles.statPrimary]}>
            <Text style={styles.statValue}>{stats.total_orders}</Text>
            <Text style={styles.statLabel}>Total Orders</Text>
          </View>
          <View style={[styles.statCard, styles.statSuccess]}>
            <Text style={styles.statValue}>
              {stats.currency} {stats.total_revenue?.toFixed(2) || '0.00'}
            </Text>
            <Text style={styles.statLabel}>Total Revenue</Text>
          </View>
          <View style={[styles.statCard, styles.statInfo]}>
            <Text style={styles.statValue}>{stats.recent_orders}</Text>
            <Text style={styles.statLabel}>Recent (7d)</Text>
          </View>
          <View style={[styles.statCard, styles.statSecondary]}>
            <Text style={styles.statValue}>
              {stats.currency} {stats.recent_revenue?.toFixed(2) || '0.00'}
            </Text>
            <Text style={styles.statLabel}>Revenue (7d)</Text>
          </View>
        </View>
      )}

      {stats?.orders_by_status && Object.keys(stats.orders_by_status).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Orders by Status</Text>
          {Object.entries(stats.orders_by_status).map(([status, count]) => (
            <View key={status} style={styles.statusRow}>
              <Text style={styles.statusLabel}>{status.replace(/_/g, ' ')}</Text>
              <Text style={styles.statusCount}>{count}</Text>
            </View>
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
  hero: {
    padding: 24,
    backgroundColor: colors.primary,
    marginBottom: 16,
  },
  logo: {
    width: 64,
    height: 64,
    borderRadius: 32,
    marginBottom: 12,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  heroSubtitle: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 6,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 12,
  },
  statCard: {
    width: '48%',
    padding: 20,
    borderRadius: 16,
    margin: '1%',
    alignItems: 'center',
  },
  statPrimary: { backgroundColor: colors.primary },
  statSuccess: { backgroundColor: colors.success },
  statInfo: { backgroundColor: colors.info },
  statSecondary: { backgroundColor: '#6c757d' },
  statValue: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 6,
  },
  statLabel: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
  },
  section: {
    backgroundColor: '#fff',
    padding: 20,
    margin: 12,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    color: colors.text,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  statusLabel: {
    fontSize: 15,
    color: colors.text,
    textTransform: 'capitalize',
  },
  statusCount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.primary,
  },
});

