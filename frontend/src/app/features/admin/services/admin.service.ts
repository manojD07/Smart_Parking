import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from '../../../core/services/base-api.service';
import { User } from '../../../core/models/user.model';
import { Booking } from '../../../core/models/booking.model';
import { ParkingLot } from '../../../core/models/parking.model';
import { SuccessResponse } from '../../../core/models/common.model';

export interface AdminStats {
  totalUsers: number;
  totalBookings: number;
  totalRevenue: number;
  activeLots: number;
  todayBookings: number;
  todayRevenue: number;
  occupancyRate: number;
  recentActivity: any[];
}

export interface AdminUserCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_admin?: boolean;
}

export interface AdminUserUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  is_admin?: boolean;
  is_active?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  // Dashboard & Analytics
  getAdminStats(): Observable<AdminStats> {
    return this.get<AdminStats>('/admin/stats');
  }

  getSystemAnalytics(params?: {
    start_date?: string;
    end_date?: string;
    granularity?: 'hour' | 'day' | 'week' | 'month';
  }): Observable<any> {
    return this.get<any>('/admin/analytics', params);
  }

  // User Management
  getAllUsers(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_admin?: boolean;
    is_active?: boolean;
  }): Observable<User[]> {
    return this.get<User[]>('/admin/users', params);
  }

  createUser(userData: AdminUserCreate): Observable<User> {
    return this.post<User>('/admin/users', userData);
  }

  updateUser(userId: string, updateData: AdminUserUpdate): Observable<User> {
    return this.put<User>(`/admin/users/${userId}`, updateData);
  }

  deactivateUser(userId: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/admin/users/${userId}/deactivate`, {});
  }

  activateUser(userId: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/admin/users/${userId}/activate`, {});
  }

  // Parking Lot Management
  getAllParkingLots(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
  }): Observable<ParkingLot[]> {
    return this.get<ParkingLot[]>('/admin/parking/lots', params);
  }

  createParkingLot(lotData: any): Observable<ParkingLot> {
    return this.post<ParkingLot>('/admin/parking/lots', lotData);
  }

  updateParkingLot(lotId: string, updateData: any): Observable<ParkingLot> {
    return this.put<ParkingLot>(`/admin/parking/lots/${lotId}`, updateData);
  }

  deactivateParkingLot(lotId: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/admin/parking/lots/${lotId}/deactivate`, {});
  }

  activateParkingLot(lotId: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/admin/parking/lots/${lotId}/activate`, {});
  }

  // Booking Management
  getAllBookings(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    user_id?: string;
    lot_id?: string;
    start_date?: string;
    end_date?: string;
  }): Observable<Booking[]> {
    return this.get<Booking[]>('/admin/bookings', params);
  }

  cancelBooking(bookingId: string, reason?: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/admin/bookings/${bookingId}/cancel`, { reason });
  }

  refundBooking(bookingId: string): Observable<SuccessResponse> {
    return this.post<SuccessResponse>(`/admin/bookings/${bookingId}/refund`, {});
  }

  // Check-in booking by reference code
  checkInBookingByReference(reference: string): Observable<SuccessResponse> {
    return this.post<SuccessResponse>(`/bookings/checkin/${reference}`, {});
  }

  // Reports
  generateReport(reportType: 'revenue' | 'usage' | 'users' | 'bookings', params?: any): Observable<any> {
    return this.post<any>(`/admin/reports/${reportType}`, params);
  }

  exportData(dataType: 'users' | 'bookings' | 'lots', format: 'csv' | 'excel' = 'csv'): Observable<Blob> {
    return this.get<Blob>(`/admin/export/${dataType}?format=${format}`, {});
  }

  // System Management
  getSystemHealth(): Observable<any> {
    return this.get<any>('/admin/system/health');
  }

  getSystemLogs(params?: {
    level?: 'debug' | 'info' | 'warning' | 'error';
    limit?: number;
    start_date?: string;
    end_date?: string;
  }): Observable<any[]> {
    return this.get<any[]>('/admin/system/logs', params);
  }

  // Notifications
  sendNotification(notification: {
    title: string;
    message: string;
    type: 'info' | 'warning' | 'error' | 'success';
    target: 'all' | 'admins' | 'users';
    user_ids?: string[];
  }): Observable<SuccessResponse> {
    return this.post<SuccessResponse>('/admin/notifications/send', notification);
  }
}
