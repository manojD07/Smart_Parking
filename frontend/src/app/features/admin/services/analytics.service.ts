import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface AnalyticsOverview {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    total_lots: number;
    total_bookings: number;
    average_daily_bookings: number;
    utilization_rate: number;
    total_revenue: number;
    average_daily_revenue: number;
  };
  utilization: any;
  revenue: any;
  booking_patterns: any;
  peak_hours: any;
  vehicle_breakdown: any;
}

export interface RevenueAnalytics {
  total_revenue: number;
  average_daily_revenue: number;
  revenue_by_vehicle_type: any;
  revenue_trends: any[];
  period_breakdown: any[];
}

export interface UtilizationAnalytics {
  overall_utilization_rate: number;
  space_efficiency: number;
  peak_hours: any[];
  hourly_breakdown: any[];
  daily_breakdown: any[];
}

export interface OccupancyAnalytics {
  peak_hours: any[];
  heatmap: any[];
  trends: any[];
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface BookingPatterns {
  booking_patterns: any;
  vehicle_analytics: any;
  duration_patterns: any;
}

export interface PerformanceMetrics {
  performance_benchmarks: any;
  efficiency_metrics: any;
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

export interface DailyReport {
  date: string;
  summary: any;
  revenue: any;
  utilization: any;
  bookings: any;
  performance: any;
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly apiUrl = `${environment.apiUrl}/analytics`;
  
  // Observable subjects for real-time updates
  private analyticsOverviewSubject = new BehaviorSubject<AnalyticsOverview | null>(null);
  private revenueAnalyticsSubject = new BehaviorSubject<RevenueAnalytics | null>(null);
  private utilizationAnalyticsSubject = new BehaviorSubject<UtilizationAnalytics | null>(null);

  // Public observables
  public analyticsOverview$ = this.analyticsOverviewSubject.asObservable();
  public revenueAnalytics$ = this.revenueAnalyticsSubject.asObservable();
  public utilizationAnalytics$ = this.utilizationAnalyticsSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get comprehensive analytics overview
   */
  getAnalyticsOverview(
    startDate?: string,
    endDate?: string,
    lotId?: string
  ): Observable<AnalyticsOverview> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: AnalyticsOverview }>(`${this.apiUrl}/overview`, { params })
      .pipe(
        map(response => {
          const overview = response.data;
          this.analyticsOverviewSubject.next(overview);
          return overview;
        }),
        catchError(error => {
          console.error('Failed to get analytics overview:', error);
          throw error;
        })
      );
  }

  /**
   * Get detailed revenue analytics
   */
  getRevenueAnalytics(
    startDate?: string,
    endDate?: string,
    period: 'hourly' | 'daily' | 'weekly' | 'monthly' = 'daily',
    lotId?: string
  ): Observable<RevenueAnalytics> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    params = params.set('period', period);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: RevenueAnalytics }>(`${this.apiUrl}/revenue`, { params })
      .pipe(
        map(response => {
          const revenue = response.data;
          this.revenueAnalyticsSubject.next(revenue);
          return revenue;
        }),
        catchError(error => {
          console.error('Failed to get revenue analytics:', error);
          throw error;
        })
      );
  }

  /**
   * Get space utilization analytics
   */
  getUtilizationAnalytics(
    startDate?: string,
    endDate?: string,
    lotId?: string
  ): Observable<UtilizationAnalytics> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: UtilizationAnalytics }>(`${this.apiUrl}/utilization`, { params })
      .pipe(
        map(response => {
          const utilization = response.data;
          this.utilizationAnalyticsSubject.next(utilization);
          return utilization;
        }),
        catchError(error => {
          console.error('Failed to get utilization analytics:', error);
          throw error;
        })
      );
  }

  /**
   * Get occupancy patterns and heatmap data
   */
  getOccupancyAnalytics(
    startDate?: string,
    endDate?: string,
    lotId?: string
  ): Observable<OccupancyAnalytics> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: OccupancyAnalytics }>(`${this.apiUrl}/occupancy`, { params })
      .pipe(
        map(response => response.data),
        catchError(error => {
          console.error('Failed to get occupancy analytics:', error);
          throw error;
        })
      );
  }

  /**
   * Get booking pattern analytics
   */
  getBookingPatterns(
    startDate?: string,
    endDate?: string,
    lotId?: string
  ): Observable<BookingPatterns> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: BookingPatterns }>(`${this.apiUrl}/booking-patterns`, { params })
      .pipe(
        map(response => response.data),
        catchError(error => {
          console.error('Failed to get booking patterns:', error);
          throw error;
        })
      );
  }

  /**
   * Get performance metrics and KPIs
   */
  getPerformanceMetrics(
    startDate?: string,
    endDate?: string,
    lotId?: string
  ): Observable<PerformanceMetrics> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (lotId) params = params.set('lot_id', lotId);

    return this.http.get<{ data: PerformanceMetrics }>(`${this.apiUrl}/performance`, { params })
      .pipe(
        map(response => response.data),
        catchError(error => {
          console.error('Failed to get performance metrics:', error);
          throw error;
        })
      );
  }

  /**
   * Get analytics for a specific parking lot
   */
  getLotSpecificAnalytics(
    lotId: string,
    startDate?: string,
    endDate?: string
  ): Observable<any> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);

    return this.http.get<{ data: any }>(`${this.apiUrl}/lots/${lotId}/analytics`, { params })
      .pipe(
        map(response => response.data),
        catchError(error => {
          console.error('Failed to get lot-specific analytics:', error);
          throw error;
        })
      );
  }

  /**
   * Alias for getLotSpecificAnalytics to match component usage
   */
  getLotAnalytics(
    lotId: string,
    startDate?: string,
    endDate?: string
  ): Observable<any> {
    return this.getLotSpecificAnalytics(lotId, startDate, endDate);
  }

  /**
   * Get daily report
   */
  getDailyReport(targetDate?: string): Observable<DailyReport> {
    let params = new HttpParams();
    if (targetDate) params = params.set('target_date', targetDate);

    return this.http.get<{ data: DailyReport }>(`${this.apiUrl}/reports/daily`, { params })
      .pipe(
        map(response => response.data),
        catchError(error => {
          console.error('Failed to get daily report:', error);
          throw error;
        })
      );
  }

  /**
   * Helper method to format date for API calls
   */
  formatDateForApi(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Helper method to get date range for common periods
   */
  getDateRange(period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'): { start: string; end: string } {
    const today = new Date();
    const end = this.formatDateForApi(today);
    let start: string;

    switch (period) {
      case 'daily':
        start = end;
        break;
      case 'weekly':
        const weekAgo = new Date(today);
        weekAgo.setDate(today.getDate() - 7);
        start = this.formatDateForApi(weekAgo);
        break;
      case 'monthly':
        const monthAgo = new Date(today);
        monthAgo.setMonth(today.getMonth() - 1);
        start = this.formatDateForApi(monthAgo);
        break;
      case 'quarterly':
        const quarterAgo = new Date(today);
        quarterAgo.setMonth(today.getMonth() - 3);
        start = this.formatDateForApi(quarterAgo);
        break;
      case 'yearly':
        const yearAgo = new Date(today);
        yearAgo.setFullYear(today.getFullYear() - 1);
        start = this.formatDateForApi(yearAgo);
        break;
      default:
        start = end;
    }

    return { start, end };
  }

  /**
   * Helper method to format currency
   */
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }

  /**
   * Clear cached analytics data
   */
  clearCache(): void {
    this.analyticsOverviewSubject.next(null);
    this.revenueAnalyticsSubject.next(null);
    this.utilizationAnalyticsSubject.next(null);
  }
}
