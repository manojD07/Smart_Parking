import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from './base-api.service';

// Revenue Analytics Interfaces
export interface RevenueMetrics {
  total_revenue: number;
  today_revenue: number;
  week_revenue: number;
  month_revenue: number;
  year_revenue: number;
  revenue_growth_daily: number;
  revenue_growth_weekly: number;
  revenue_growth_monthly: number;
  average_revenue_per_booking: number;
  total_bookings: number;
}

export interface HourlyRevenue {
  hour: number;
  revenue: number;
  bookings: number;
}

export interface DailyRevenue {
  date: string;
  revenue: number;
  bookings: number;
  average_per_booking: number;
}

export interface LotRevenue {
  lot_id: string;
  lot_name: string;
  total_revenue: number;
  total_bookings: number;
  average_revenue_per_booking: number;
  occupancy_rate: number;
  revenue_per_slot: number;
}

export interface VehicleRevenue {
  car: {
    revenue: number;
    bookings: number;
    average_per_booking: number;
    percentage: number;
  };
  bike: {
    revenue: number;
    bookings: number;
    average_per_booking: number;
    percentage: number;
  };
}

export interface PricingRuleEffectiveness {
  rule_id: string;
  rule_name: string;
  rule_type: string;
  vehicle_type: string;
  bookings_affected: number;
  revenue_generated: number;
  average_multiplier_impact: number;
  effectiveness_score: number;
}

export interface RevenueAnalytics {
  metrics: RevenueMetrics;
  hourly_revenue: HourlyRevenue[];
  daily_revenue: DailyRevenue[];
  lot_revenue: LotRevenue[];
  vehicle_revenue: VehicleRevenue;
  pricing_effectiveness: PricingRuleEffectiveness[];
}

export interface RevenueForecast {
  next_7_days: DailyRevenue[];
  next_30_days: DailyRevenue[];
  projected_monthly: number;
  confidence_level: number;
}

// Booking Analytics Interfaces
export interface BookingTrend {
  date: string;
  total_bookings: number;
  confirmed: number;
  active: number;
  completed: number;
  cancelled: number;
}

export interface BookingPatterns {
  peak_hours: number[];
  peak_days: string[];
  average_duration: number;
  most_popular_vehicle: 'car' | 'bike';
  busiest_lots: string[];
}

export interface BookingAnalytics {
  total_bookings: number;
  booking_growth: number;
  success_rate: number;
  cancellation_rate: number;
  average_duration: number;
  trends: BookingTrend[];
  patterns: BookingPatterns;
  status_breakdown: Record<string, number>;
  vehicle_breakdown: Record<string, number>;
}

// System Overview Interfaces
export interface SystemOverview {
  total_users: number;
  total_parking_lots: number;
  total_slots: number;
  active_bookings: number;
  today_bookings: number;
  today_revenue: number;
  user_growth: number;
  lot_utilization: number;
  system_health: 'excellent' | 'good' | 'fair' | 'poor';
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Get comprehensive revenue analytics
   */
  async getRevenueAnalytics(startDate: string, endDate: string, lotId?: string): Promise<RevenueAnalytics> {
    try {
      // Get dashboard data for overview
      const dashboardData = await this.get<any>('/admin/dashboard').toPromise();
      
      // Get detailed booking data for the date range
      const params: any = {
        start_date: startDate,
        end_date: endDate,
        limit: 1000 // Maximum allowed by backend
      };
      
      if (lotId) {
        params.lot_id = lotId;
      }
      
      const bookingsData = await this.get<any[]>('/admin/bookings', params).toPromise();
      
      // Process revenue analytics from the data
      const analytics = this.processRevenueAnalytics(dashboardData, bookingsData || [], startDate, endDate);
      
      return analytics;
    } catch (error) {
      console.error('Error fetching revenue analytics:', error);
      throw error;
    }
  }

  /**
   * Get revenue by parking lot
   */
  async getRevenueByLot(startDate: string, endDate: string): Promise<LotRevenue[]> {
    try {
      // Get all parking lots
      const lotsData = await this.get<any[]>('/parking/lots').toPromise();
      const lots = lotsData || [];
      
      // Get revenue data for each lot
      const lotRevenuePromises = lots.map(async (lot) => {
        try {
          const lotStats = await this.get<any>(`/parking/admin/lots/${lot.id}/statistics`).toPromise();
          const bookingsData = await this.get<any[]>('/admin/bookings', {
            lot_id: lot.id,
            start_date: startDate,
            end_date: endDate,
            limit: 1000
          }).toPromise();
          
          const totalRevenue = (bookingsData || []).reduce((sum, booking) => sum + (booking.total_amount || 0), 0);
          const totalBookings = (bookingsData || []).length;
          
          return {
            lot_id: lot.id,
            lot_name: lot.name,
            total_revenue: totalRevenue,
            total_bookings: totalBookings,
            average_revenue_per_booking: totalBookings > 0 ? totalRevenue / totalBookings : 0,
            occupancy_rate: lotStats?.booking_statistics?.active_bookings || 0,
            revenue_per_slot: (lot.total_car_slots + lot.total_bike_slots) > 0 ? 
              totalRevenue / (lot.total_car_slots + lot.total_bike_slots) : 0
          };
        } catch (error) {
          console.warn(`Failed to get revenue for lot ${lot.name}:`, error);
          return {
            lot_id: lot.id,
            lot_name: lot.name,
            total_revenue: 0,
            total_bookings: 0,
            average_revenue_per_booking: 0,
            occupancy_rate: 0,
            revenue_per_slot: 0
          };
        }
      });
      
      return Promise.all(lotRevenuePromises);
    } catch (error) {
      console.error('Error fetching revenue by lot:', error);
      throw error;
    }
  }

  /**
   * Get system overview data
   */
  async getSystemOverview(): Promise<SystemOverview> {
    try {
      const dashboardData = await this.get<any>('/admin/dashboard').toPromise();
      
      if (!dashboardData) {
        throw new Error('No dashboard data available');
      }
      
      return {
        total_users: dashboardData.overview?.total_users || 0,
        total_parking_lots: dashboardData.overview?.total_parking_lots || 0,
        total_slots: 0, // Would need to calculate from lots
        active_bookings: dashboardData.today_statistics?.status_breakdown?.active || 0,
        today_bookings: dashboardData.overview?.today_bookings || 0,
        today_revenue: dashboardData.overview?.today_revenue || 0,
        user_growth: 0, // Would need historical data
        lot_utilization: 0, // Would need to calculate
        system_health: this.calculateSystemHealth(dashboardData)
      };
    } catch (error) {
      console.error('Error fetching system overview:', error);
      throw error;
    }
  }

  /**
   * Process raw booking data into revenue analytics
   */
  private processRevenueAnalytics(dashboardData: any, bookingsData: any[], startDate: string, endDate: string): RevenueAnalytics {
    const totalRevenue = bookingsData.reduce((sum, booking) => sum + (booking.total_amount || 0), 0);
    const totalBookings = bookingsData.length;
    
    // Group by date for daily revenue
    const dailyRevenueMap = new Map<string, { revenue: number; bookings: number }>();
    
    bookingsData.forEach(booking => {
      const date = booking.created_at?.split('T')[0] || '';
      const existing = dailyRevenueMap.get(date) || { revenue: 0, bookings: 0 };
      dailyRevenueMap.set(date, {
        revenue: existing.revenue + (booking.total_amount || 0),
        bookings: existing.bookings + 1
      });
    });
    
    const dailyRevenue: DailyRevenue[] = Array.from(dailyRevenueMap.entries()).map(([date, data]) => ({
      date,
      revenue: data.revenue,
      bookings: data.bookings,
      average_per_booking: data.bookings > 0 ? data.revenue / data.bookings : 0
    }));
    
    // Group by hour for hourly patterns
    const hourlyRevenueMap = new Map<number, { revenue: number; bookings: number }>();
    
    bookingsData.forEach(booking => {
      const hour = new Date(booking.created_at).getHours();
      const existing = hourlyRevenueMap.get(hour) || { revenue: 0, bookings: 0 };
      hourlyRevenueMap.set(hour, {
        revenue: existing.revenue + (booking.total_amount || 0),
        bookings: existing.bookings + 1
      });
    });
    
    const hourlyRevenue: HourlyRevenue[] = Array.from(hourlyRevenueMap.entries()).map(([hour, data]) => ({
      hour,
      revenue: data.revenue,
      bookings: data.bookings
    }));
    
    // Vehicle revenue breakdown
    const vehicleRevenueMap = bookingsData.reduce((acc, booking) => {
      const vehicleType = booking.vehicle_type || 'unknown';
      if (!acc[vehicleType]) {
        acc[vehicleType] = { revenue: 0, bookings: 0 };
      }
      acc[vehicleType].revenue += booking.total_amount || 0;
      acc[vehicleType].bookings += 1;
      return acc;
    }, {} as Record<string, { revenue: number; bookings: number }>);
    
    const carData = vehicleRevenueMap.car || { revenue: 0, bookings: 0 };
    const bikeData = vehicleRevenueMap.bike || { revenue: 0, bookings: 0 };
    const totalVehicleRevenue = carData.revenue + bikeData.revenue;
    
    return {
      metrics: {
        total_revenue: totalRevenue,
        today_revenue: dashboardData.overview?.today_revenue || 0,
        week_revenue: totalRevenue, // Simplified - would need week calculation
        month_revenue: totalRevenue, // Simplified - would need month calculation
        year_revenue: totalRevenue, // Simplified - would need year calculation
        revenue_growth_daily: 0, // Would need historical comparison
        revenue_growth_weekly: 0,
        revenue_growth_monthly: 0,
        average_revenue_per_booking: totalBookings > 0 ? totalRevenue / totalBookings : 0,
        total_bookings: totalBookings
      },
      hourly_revenue: hourlyRevenue.sort((a, b) => a.hour - b.hour),
      daily_revenue: dailyRevenue.sort((a, b) => a.date.localeCompare(b.date)),
      lot_revenue: [], // Will be populated by getRevenueByLot
      vehicle_revenue: {
        car: {
          revenue: carData.revenue,
          bookings: carData.bookings,
          average_per_booking: carData.bookings > 0 ? carData.revenue / carData.bookings : 0,
          percentage: totalVehicleRevenue > 0 ? (carData.revenue / totalVehicleRevenue) * 100 : 0
        },
        bike: {
          revenue: bikeData.revenue,
          bookings: bikeData.bookings,
          average_per_booking: bikeData.bookings > 0 ? bikeData.revenue / bikeData.bookings : 0,
          percentage: totalVehicleRevenue > 0 ? (bikeData.revenue / totalVehicleRevenue) * 100 : 0
        }
      },
      pricing_effectiveness: [] // Would need pricing rule correlation
    };
  }

  /**
   * Calculate system health based on metrics
   */
  private calculateSystemHealth(dashboardData: any): 'excellent' | 'good' | 'fair' | 'poor' {
    const todayBookings = dashboardData.overview?.today_bookings || 0;
    const todayRevenue = dashboardData.overview?.today_revenue || 0;
    const totalLots = dashboardData.overview?.total_parking_lots || 0;
    
    // Simple health calculation based on activity
    const healthScore = (todayBookings * 10) + (todayRevenue / 100) + (totalLots * 5);
    
    if (healthScore >= 100) return 'excellent';
    if (healthScore >= 50) return 'good';
    if (healthScore >= 20) return 'fair';
    return 'poor';
  }

  /**
   * Format currency display
   */
  formatCurrency(amount: number): string {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  /**
   * Format percentage display
   */
  formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  /**
   * Calculate growth percentage
   */
  calculateGrowth(current: number, previous: number): number {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  }

  /**
   * Get date range for common periods
   */
  getDateRange(period: 'today' | 'week' | 'month' | 'year'): { start: string; end: string } {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    switch (period) {
      case 'today':
        return {
          start: today.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0]
        };
      case 'week':
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - 7);
        return {
          start: weekStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0]
        };
      case 'month':
        const monthStart = new Date(today);
        monthStart.setDate(today.getDate() - 30);
        return {
          start: monthStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0]
        };
      case 'year':
        const yearStart = new Date(today);
        yearStart.setDate(today.getDate() - 365);
        return {
          start: yearStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0]
        };
      default:
        return {
          start: today.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0]
        };
    }
  }
}
