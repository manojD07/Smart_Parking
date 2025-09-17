import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from '../../../core/services/base-api.service';

// Backend dashboard response interface
export interface DashboardResponse {
  overview: {
    total_users: number;
    total_parking_lots: number;
    today_bookings: number;
    today_revenue: number;
  };
  today_statistics: {
    total_bookings: number;
    total_revenue: number;
    average_booking_value: number;
    status_breakdown: {
      confirmed: number;
      active: number;
      completed: number;
      pending: number;
      cancelled: number;
    };
    vehicle_type_breakdown: {
      bike: {
        count: number;
        revenue: number;
      };
      car: {
        count: number;
        revenue: number;
      };
    };
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  // Dashboard API
  getDashboardData(): Observable<DashboardResponse> {
    return this.get<DashboardResponse>('/admin/dashboard');
  }
}