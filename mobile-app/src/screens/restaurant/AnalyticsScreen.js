import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { analyticsAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { colors } from '../../theme';

export default function AnalyticsScreen() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [revenueStats, setRevenueStats] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [days]);

  const loadAnalytics = async () => {
    try {
      const [dashboardRes, revenueRes] = await Promise.all([
        analyticsAPI.getDashboardStats(days),
        analyticsAPI.getRevenueStats(days),
      ]);
      if (dashboardRes.success) setStats(dashboardRes.stats);
      if (revenueRes.success) setRevenueStats(revenueRes.stats);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAnalytics();
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
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <View style={styles.daySelector}>
          {[7, 30].map((d) => (
            <TouchableOpacity
              key={d}
              style={[styles.dayBtn, days === d && styles.dayBtnActive]}
              onPress={() => setDays(d)}
            >
              <Text style={[styles.dayBtnText, days === d && styles.dayBtnTextActive]}>
                {d}d
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {stats && (
        <View style={styles.statsGrid}>
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
            <Text style={styles.statLabel}>Orders ({days}d)</Text>
          </View>
          <View style={[styles.statCard, styles.statSecondary]}>
            <Text style={styles.statValue}>
              {stats.currency} {stats.recent_revenue?.toFixed(2) || '0.00'}
            </Text>
            <Text style={styles.statLabel}>Revenue ({days}d)</Text>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: { fontSize: 24, fontWeight: 'bold', color: colors.text },
  daySelector: { flexDirection: 'row', gap: 8 },
  dayBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  dayBtnActive: { backgroundColor: colors.primary },
  dayBtnText: { fontSize: 14, color: colors.textLight, fontWeight: '600' },
  dayBtnTextActive: { color: '#fff' },
  statsGrid: {
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
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 6,
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
  },
  section: {
    backgroundColor: '#fff',
    margin: 12,
    padding: 20,
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
    color: colors.text,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  statusLabel: { fontSize: 15, color: colors.text, textTransform: 'capitalize' },
  statusCount: { fontSize: 16, fontWeight: 'bold', color: colors.primary },
});
