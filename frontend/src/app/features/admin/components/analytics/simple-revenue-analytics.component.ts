import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';
import { AnalyticsService } from '../../services/analytics.service';
import { ParkingService } from '../../../parking/services/parking.service';
import { environment } from '../../../../../environments/environment';

interface DailyRevenue {
  date: string;
  revenue: number;
  bookings: number;
}

interface LotRevenue {
  lot_id: string;
  lot_name: string;
  address: string;
  revenue: number;
  bookings: number;
  utilization: number;
}

@Component({
  selector: 'app-simple-revenue-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container-fluid">
      <!-- Filter Controls -->
      <div class="row mb-4">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h5 class="card-title mb-0">
                <i class="fas fa-filter me-2"></i>Filters
              </h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <label class="form-label">Filter by Period</label>
                  <select 
                    class="form-select" 
                    [(ngModel)]="selectedPeriod" 
                    (change)="onFilterChange()">
                    <option value="7">Last 7 days</option>
                    <option value="30">Last 30 days</option>
                    <option value="90">Last 90 days</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Filter by Lot</label>
                  <select 
                    class="form-select" 
                    [(ngModel)]="selectedLotId" 
                    (change)="onFilterChange()">
                    <option value="">All Lots</option>
                    <option *ngFor="let lot of availableLots" [value]="lot.id">
                      {{ lot.name }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h5 class="card-title mb-0">
                <i class="fas fa-chart-bar me-2"></i>Summary
              </h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-6">
                  <div class="text-center">
                    <h4 class="text-success mb-0">\${{ dashboardStats.total_revenue | number:'1.2-2' }}</h4>
                    <small class="text-muted">Today's Revenue</small>
                  </div>
                </div>
                <div class="col-6">
                  <div class="text-center">
                    <h4 class="text-info mb-0">{{ dashboardStats.total_bookings }}</h4>
                    <small class="text-muted">Today's Bookings</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading revenue analytics...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="!loading && errorMessage" class="alert alert-warning">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>

      <!-- Revenue by Day Analysis -->
      <div *ngIf="!loading && !errorMessage" class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="card-title mb-0">
                <i class="fas fa-calendar-day me-2"></i>
                Revenue by Day
                <span *ngIf="selectedLotId" class="badge bg-info ms-2">
                  {{ getLotName(selectedLotId) }}
                </span>
              </h5>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Revenue</th>
                      <th>Bookings</th>
                      <th>Avg per Booking</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <!-- Total Row -->
                    <tr class="table-primary fw-bold">
                      <td>
                        <strong>TOTAL ({{ selectedPeriod }} days)</strong>
                        <br>
                        <small class="text-muted">{{ formatDateRange() }}</small>
                      </td>
                      <td>
                        <span class="fw-bold text-success fs-5">
                          \${{ getTotalRevenue() | number:'1.2-2' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge bg-success fs-6">{{ getTotalBookings() }}</span>
                      </td>
                      <td>
                        \${{ getOverallAvgPerBooking() | number:'1.2-2' }}
                      </td>
                      <td>
                        <div class="progress" style="height: 20px;">
                          <div class="progress-bar bg-success" style="width: 100%" role="progressbar">
                            100%
                          </div>
                        </div>
                      </td>
                    </tr>
                    <!-- Daily Rows -->
                    <tr *ngFor="let day of dailyRevenueData; let i = index">
                      <td>
                        <strong>{{ formatDate(day.date) }}</strong>
                        <br>
                        <small class="text-muted">{{ getDayOfWeek(day.date) }}</small>
                      </td>
                      <td>
                        <span class="fw-bold text-success">
                          \${{ day.revenue | number:'1.2-2' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge bg-primary">{{ day.bookings }}</span>
                      </td>
                      <td>
                        \${{ getAvgPerBooking(day.revenue, day.bookings) | number:'1.2-2' }}
                      </td>
                      <td>
                        <div class="progress" style="height: 20px;">
                          <div 
                            class="progress-bar" 
                            [class]="getPerformanceClass(day.revenue)"
                            [style.width.%]="getPerformancePercentage(day.revenue)"
                            role="progressbar">
                            {{ getPerformancePercentage(day.revenue) }}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Revenue by Lot Analysis -->
      <div *ngIf="!loading && !errorMessage && !selectedLotId" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="card-title mb-0">
                <i class="fas fa-building me-2"></i>
                Revenue by Parking Lot
              </h5>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>Parking Lot</th>
                      <th>Revenue</th>
                      <th>Bookings</th>
                      <th>Utilization</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let lot of lotRevenueData; let i = index">
                      <td>
                        <strong>{{ lot.lot_name }}</strong>
                        <br>
                        <small class="text-muted">{{ lot.address }}</small>
                      </td>
                      <td>
                        <span class="fw-bold text-success">
                          \${{ lot.revenue | number:'1.2-2' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge bg-primary">{{ lot.bookings }}</span>
                      </td>
                      <td>
                        <span class="badge" [class]="getUtilizationClass(lot.utilization)">
                          {{ lot.utilization | percent:'1.0-0' }}
                        </span>
                      </td>
                      <td>
                        <div class="progress" style="height: 20px;">
                          <div 
                            class="progress-bar" 
                            [class]="getPerformanceClass(lot.revenue)"
                            [style.width.%]="getLotPerformancePercentage(lot.revenue)"
                            role="progressbar">
                            {{ getLotPerformancePercentage(lot.revenue) }}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .card {
      border-radius: 12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 1rem;
    }
    
    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
    }
    
    .progress {
      border-radius: 10px;
    }
    
    .table th {
      border-top: none;
      font-weight: 600;
      color: #495057;
    }
    
    .badge {
      font-size: 0.875rem;
    }
    
    @media (max-width: 768px) {
      .table-responsive {
        font-size: 0.875rem;
      }
    }
  `]
})
export class SimpleRevenueAnalyticsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  loading = true;
  errorMessage = '';
  selectedPeriod = '30';
  selectedLotId = '';
  
  availableLots: any[] = [];
  dailyRevenueData: DailyRevenue[] = [];
  lotRevenueData: LotRevenue[] = [];
  
  // Dashboard stats for consistency
  dashboardStats = {
    total_bookings: 0,
    total_revenue: 0
  };
  
  constructor(
    private analyticsService: AnalyticsService,
    private parkingService: ParkingService,
    private http: HttpClient
  ) {}
  
  ngOnInit(): void {
    this.loadInitialData();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  loadInitialData(): void {
    // Load parking lots first
    this.parkingService.getParkingLots({ skip: 0, limit: 100 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (lots: any[]) => {
          this.availableLots = lots;
          this.loadRevenueData();
        },
        error: (error: any) => {
          console.error('Failed to load parking lots:', error);
          this.errorMessage = 'Failed to load parking lots. Please check your connection.';
          this.loading = false;
        }
      });
  }
  
  loadRevenueData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.getDateRange();
    
    // First try to load admin dashboard data to see if there's any data at all
    this.loadDashboardData(dateRange);
  }
  
  private loadDashboardData(dateRange: { start: string; end: string }): void {
    const url = `${environment.apiUrl}/admin/dashboard`;
    console.log('=== TESTING DASHBOARD API ===');
    console.log('Dashboard URL:', url);
    
    this.http.get<any>(url)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (dashboardData: any) => {
          console.log('=== DASHBOARD RESPONSE ===');
          console.log('Dashboard data:', dashboardData);
          
          // Store dashboard stats for consistency with main dashboard
          this.dashboardStats = {
            total_bookings: dashboardData?.today_statistics?.total_bookings || 0,
            total_revenue: parseFloat(dashboardData?.today_statistics?.total_revenue || 0)
          };
          
          console.log('Analytics using SAME data as Admin Dashboard:', this.dashboardStats);
          
          // If dashboard has data, try bookings API, otherwise show dashboard data
          if (dashboardData?.overview?.today_bookings > 0 || dashboardData?.today_statistics?.total_bookings > 0) {
            console.log('Dashboard shows bookings exist, trying bookings API...');
            this.loadBookingsData(dateRange);
          } else {
            console.log('No bookings in dashboard, showing message...');
            this.createDataFromDashboard(dashboardData);
            this.loadLotSpecificData();
          }
        },
        error: (error: any) => {
          console.error('=== DASHBOARD ERROR ===');
          console.error('Dashboard error:', error);
          // Fallback to bookings API
          this.loadBookingsData(dateRange);
        }
      });
  }
  
  private createDataFromDashboard(dashboardData: any): void {
    const today = new Date().toISOString().split('T')[0];
    
    if (dashboardData?.today_statistics?.total_revenue > 0) {
      this.dailyRevenueData = [{
        date: today,
        revenue: parseFloat(dashboardData.today_statistics.total_revenue),
        bookings: parseInt(dashboardData.today_statistics.total_bookings || 1)
      }];
      this.errorMessage = '';
    } else {
      // Show helpful message with instructions
      this.dailyRevenueData = [];
      this.errorMessage = 'No revenue data available. This could mean: 1) No bookings have been made yet, 2) No confirmed bookings with payments, or 3) Bookings are outside the selected date range. Try selecting "Last 90 days" or create some test bookings.';
    }
    
    console.log('Created data from dashboard:', this.dailyRevenueData);
  }
  
  private loadBookingsData(dateRange: { start: string; end: string }): void {
    console.log('=== ANALYTICS DEBUG ===');
    console.log('Date range:', dateRange);
    console.log('Selected lot ID:', this.selectedLotId);
    console.log('Loading ALL bookings for analytics (no pagination limit)');
    
    // Load ALL bookings for the date range - no pagination limit for analytics
    this.loadAllBookingsForAnalytics(dateRange);
  }
  
  private async loadAllBookingsForAnalytics(dateRange: { start: string; end: string }): Promise<void> {
    const allBookings: any[] = [];
    let skip = 0;
    const batchSize = 1000; // Load in batches for performance
    let hasMore = true;
    
    try {
      while (hasMore) {
        // Build query parameters for current batch
        let params = `skip=${skip}&limit=${batchSize}&start_date=${dateRange.start}&end_date=${dateRange.end}`;
        if (this.selectedLotId) {
          params += `&lot_id=${this.selectedLotId}`;
        }
        
        const url = `${environment.apiUrl}/admin/bookings?${params}`;
        console.log(`Loading batch: skip=${skip}, limit=${batchSize}`);
        
        const batchResponse = await this.http.get<any[]>(url).toPromise();
        const batch = batchResponse || [];
        
        console.log(`Batch loaded: ${batch.length} bookings`);
        
        if (batch.length === 0) {
          hasMore = false;
        } else {
          allBookings.push(...batch);
          
          // If we got less than the batch size, we've reached the end
          if (batch.length < batchSize) {
            hasMore = false;
          } else {
            skip += batchSize;
          }
        }
      }
      
      console.log('=== COMPLETE ANALYTICS DATA ===');
      console.log('Total bookings loaded for analytics:', allBookings.length);
      console.log('No pagination limits applied');
      
      this.processBookingsData(allBookings);
      this.loadLotSpecificData();
      
    } catch (error: any) {
      console.error('=== API ERROR ===');
      console.error('Error details:', error);
      
      if (error.status === 401) {
        this.errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.status === 403) {
        this.errorMessage = 'Access denied. Admin privileges required.';
      } else if (error.status === 404) {
        this.errorMessage = 'Bookings API endpoint not found.';
      } else {
        this.errorMessage = `Failed to load booking data: ${error.status || 'Network error'}`;
      }
      this.loading = false;
    }
  }
  
  private processBookingsData(bookings: any[]): void {
    console.log('Processing bookings data. Total bookings received:', bookings?.length || 0);
    console.log('First booking data:', bookings?.[0]);
    
    if (!bookings || bookings.length === 0) {
      this.dailyRevenueData = [];
      this.errorMessage = 'No bookings found for the selected period. Try a different date range.';
      return;
    }
    
    // Group bookings by date and calculate daily revenue
    const dailyData: { [date: string]: { revenue: number; bookings: number } } = {};
    let processedCount = 0;
    
    bookings.forEach((booking, index) => {
      // Log first 3 bookings in full detail to see the actual structure
      if (index < 3) {
        console.log(`Full booking ${index + 1} data:`, booking);
      }
      
      console.log(`Processing booking ${index + 1}:`, {
        status: booking.status,
        total_amount: booking.total_amount,
        created_at: booking.created_at,
        start_time: booking.start_time,
        allKeys: Object.keys(booking)
      });
      
      // Include ALL possible booking statuses - let's be very permissive
      const validStatuses = [
        'CONFIRMED', 'COMPLETED', 'CHECKED_IN', 'ACTIVE', 'PAID',
        'confirmed', 'completed', 'checked_in', 'active', 'paid',
        'PENDING', 'pending', 'SUCCESS', 'success'
      ];
      
      const bookingStatus = booking.status?.toString().toUpperCase();
      console.log(`Checking status: "${booking.status}" -> "${bookingStatus}"`);
      
      if (validStatuses.includes(booking.status) || validStatuses.includes(bookingStatus)) {
        const bookingDate = new Date(booking.created_at || booking.start_time || booking.booking_date || booking.date).toISOString().split('T')[0];
        const revenue = parseFloat(booking.total_amount || booking.amount || booking.price || booking.cost || booking.fee || 0);
        
        console.log(`Valid booking found - Status: ${booking.status}, Date: ${bookingDate}, Revenue: ${revenue}`);
        
        // Accept any booking with revenue > 0, regardless of status
        if (revenue > 0) {
          if (!dailyData[bookingDate]) {
            dailyData[bookingDate] = { revenue: 0, bookings: 0 };
          }
          
          dailyData[bookingDate].revenue += revenue;
          dailyData[bookingDate].bookings += 1;
          processedCount++;
        } else {
          console.log(`Booking has valid status but no revenue: ${revenue}`);
        }
      } else {
        console.log(`Booking status "${booking.status}" not in valid statuses`);
      }
    });
    
    console.log(`Processed ${processedCount} valid bookings out of ${bookings.length} total`);
    
    // Convert to array format
    this.dailyRevenueData = Object.entries(dailyData)
      .map(([date, data]) => ({
        date,
        revenue: data.revenue,
        bookings: data.bookings
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()); // Latest date first
    
    console.log('Final processed daily revenue data:', this.dailyRevenueData);
    
    if (this.dailyRevenueData.length === 0) {
      console.log('No valid revenue bookings found. Trying to process ALL bookings with any amount...');
      
      // Fallback: Process ALL bookings regardless of status, with any amount > 0
      bookings.forEach((booking, index) => {
        const revenue = parseFloat(booking.total_amount || booking.amount || booking.price || booking.cost || booking.fee || 0);
        if (revenue >= 0) { // Accept even 0 revenue for debugging
          const bookingDate = new Date(booking.created_at || booking.start_time || booking.booking_date || booking.date).toISOString().split('T')[0];
          
          if (!dailyData[bookingDate]) {
            dailyData[bookingDate] = { revenue: 0, bookings: 0 };
          }
          
          dailyData[bookingDate].revenue += revenue;
          dailyData[bookingDate].bookings += 1;
          processedCount++;
          
          if (index < 5) {
            console.log(`Fallback: Added booking with revenue ${revenue} on ${bookingDate}`);
          }
        }
      });
      
      // Recreate the array with fallback data
      this.dailyRevenueData = Object.entries(dailyData)
        .map(([date, data]) => ({
          date,
          revenue: data.revenue,
          bookings: data.bookings
        }))
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()); // Latest date first
      
      console.log('Fallback processed daily revenue data:', this.dailyRevenueData);
      
      if (this.dailyRevenueData.length === 0) {
        this.errorMessage = `No bookings found with any revenue data. Total bookings: ${bookings.length}. Check if bookings have amount fields.`;
      } else {
        this.errorMessage = `Showing ${this.dailyRevenueData.length} days of data (including $0 bookings for debugging)`;
      }
    } else {
      this.errorMessage = ''; // Clear any previous error
    }
  }
  
  loadLotSpecificData(): void {
    if (this.selectedLotId) {
      // Data already loaded and filtered by lot in loadBookingsData
      this.loading = false;
    } else {
      // Load data for all lots
      this.loadAllLotsData();
    }
  }
  
  async loadAllLotsData(): Promise<void> {
    if (this.availableLots.length === 0) {
      this.errorMessage = 'No parking lots available.';
      this.loading = false;
      return;
    }
    
    const dateRange = this.getDateRange();
    
    try {
      // Load ALL bookings for lot analysis (no pagination limit)
      console.log('Loading ALL bookings for lot revenue analysis...');
      const allBookings = await this.loadAllBookingsForPeriod(dateRange);
      
      console.log(`Loaded ${allBookings.length} total bookings for lot analysis`);
      this.processLotRevenueData(allBookings);
      this.loading = false;
    } catch (error: any) {
      console.error('Failed to load lot revenue data:', error);
      this.errorMessage = 'Failed to load parking lot revenue data. Please check your connection.';
      this.loading = false;
    }
  }
  
  private async loadAllBookingsForPeriod(dateRange: { start: string; end: string }): Promise<any[]> {
    const allBookings: any[] = [];
    let skip = 0;
    const batchSize = 1000;
    let hasMore = true;
    
    while (hasMore) {
      let params = `skip=${skip}&limit=${batchSize}&start_date=${dateRange.start}&end_date=${dateRange.end}`;
      if (this.selectedLotId) {
        params += `&lot_id=${this.selectedLotId}`;
      }
      
      const url = `${environment.apiUrl}/admin/bookings?${params}`;
      const batchResponse = await this.http.get<any[]>(url).toPromise();
      const batch = batchResponse || [];
      
      if (batch.length === 0 || batch.length < batchSize) {
        hasMore = false;
      } else {
        skip += batchSize;
      }
      
      allBookings.push(...batch);
    }
    
    return allBookings;
  }
  
  private processLotRevenueData(bookings: any[]): void {
    if (!bookings || bookings.length === 0) {
      this.lotRevenueData = [];
      return;
    }
    
    // Group bookings by lot and calculate revenue
    const lotData: { [lotId: string]: { revenue: number; bookings: number; lotName: string; address: string } } = {};
    
    bookings.forEach(booking => {
      // Use the same permissive status checking as daily revenue
      const validStatuses = [
        'CONFIRMED', 'COMPLETED', 'CHECKED_IN', 'ACTIVE', 'PAID',
        'confirmed', 'completed', 'checked_in', 'active', 'paid',
        'PENDING', 'pending', 'SUCCESS', 'success'
      ];
      
      const bookingStatus = booking.status?.toString().toUpperCase();
      
      if (validStatuses.includes(booking.status) || validStatuses.includes(bookingStatus)) {
        const lotId = booking.lot_id;
        const revenue = parseFloat(booking.total_amount || booking.amount || booking.price || booking.cost || booking.fee || 0);
        
        // Accept any booking with revenue > 0
        if (revenue > 0) {
          if (!lotData[lotId]) {
            // Find lot details from available lots
            const lot = this.availableLots.find(l => l.id === lotId);
            lotData[lotId] = { 
              revenue: 0, 
              bookings: 0, 
              lotName: lot ? lot.name : `Lot ${lotId}`,
              address: lot ? lot.address : 'Address not available'
            };
          }
          
          lotData[lotId].revenue += revenue;
          lotData[lotId].bookings += 1;
        }
      }
    });
    
    // Convert to array format
    this.lotRevenueData = Object.entries(lotData)
      .map(([lotId, data]) => ({
        lot_id: lotId,
        lot_name: data.lotName,
        address: data.address,
        revenue: data.revenue,
        bookings: data.bookings,
        utilization: 0 // No utilization data available
      }))
      .filter(lot => lot.revenue > 0)
      .sort((a, b) => b.revenue - a.revenue);
    
    console.log('Processed lot revenue data:', this.lotRevenueData);
    
    if (this.lotRevenueData.length === 0) {
      this.errorMessage = 'No revenue data available for any parking lots in the selected period.';
    }
  }
  
  onFilterChange(): void {
    this.loadRevenueData();
  }
  
  refreshData(): void {
    this.loadRevenueData();
  }
  
  private getDateRange(): { start: string; end: string } {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(this.selectedPeriod));
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0]
    };
  }
  
  
  
  // Utility methods
  getTotalRevenue(): number {
    return this.dailyRevenueData.reduce((sum, day) => sum + day.revenue, 0);
  }
  
  getTotalBookings(): number {
    return this.dailyRevenueData.reduce((sum, day) => sum + day.bookings, 0);
  }
  
  getLotName(lotId: string): string {
    const lot = this.availableLots.find(l => l.id === lotId);
    return lot ? lot.name : 'Unknown Lot';
  }
  
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  
  getDayOfWeek(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  }
  
  getAvgPerBooking(revenue: number, bookings: number): number {
    return bookings > 0 ? revenue / bookings : 0;
  }
  
  getOverallAvgPerBooking(): number {
    const totalBookings = this.getTotalBookings();
    return totalBookings > 0 ? this.getTotalRevenue() / totalBookings : 0;
  }
  
  formatDateRange(): string {
    if (this.dailyRevenueData.length === 0) return '';
    const dates = this.dailyRevenueData.map(d => d.date).sort();
    const startDate = new Date(dates[0]);
    const endDate = new Date(dates[dates.length - 1]);
    return `${this.formatDate(startDate.toISOString().split('T')[0])} - ${this.formatDate(endDate.toISOString().split('T')[0])}`;
  }
  
  getPerformancePercentage(revenue: number): number {
    const maxRevenue = Math.max(...this.dailyRevenueData.map(d => d.revenue));
    return maxRevenue > 0 ? Math.round((revenue / maxRevenue) * 100) : 0;
  }
  
  getLotPerformancePercentage(revenue: number): number {
    const maxRevenue = Math.max(...this.lotRevenueData.map(l => l.revenue));
    return maxRevenue > 0 ? Math.round((revenue / maxRevenue) * 100) : 0;
  }
  
  getPerformanceClass(revenue: number): string {
    const percentage = this.getPerformancePercentage(revenue);
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 60) return 'bg-warning';
    return 'bg-danger';
  }
  
  getUtilizationClass(utilization: number): string {
    if (utilization >= 0.8) return 'bg-success';
    if (utilization >= 0.6) return 'bg-warning';
    return 'bg-secondary';
  }
}
