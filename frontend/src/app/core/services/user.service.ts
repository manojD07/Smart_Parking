import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from './base-api.service';

// User interfaces
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_admin: boolean;
  is_active: boolean;
  total_spent: number;
  created_at: string;
  updated_at: string;
}

export interface UserFilters {
  search?: string;
  is_active?: boolean;
  is_admin?: boolean;
  skip?: number;
  limit?: number;
}

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  size: number;
}

export interface UserBooking {
  id: string;
  lot_name: string;
  slot_number: string;
  vehicle_type: string;
  vehicle_number: string;
  start_time: string;
  end_time: string;
  total_amount: number;
  status: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserService extends BaseApiService {

  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Get all users with optional filters and pagination
   */
  async getAllUsers(filters?: UserFilters): Promise<User[]> {
    try {
      const params = this.createHttpParams(filters);
      console.log('🔍 Loading users with filters:', filters);
      
      const users = await this.get<User[]>('/users/', params).toPromise();
      console.log('👥 Loaded users:', users?.length || 0);
      
      return users || [];
    } catch (error) {
      console.error('❌ Error loading users:', error);
      throw error;
    }
  }

  /**
   * Get user by ID
   */
  async getUserById(userId: string): Promise<User> {
    try {
      console.log('👤 Loading user details:', userId);
      
      const user = await this.get<User>(`/users/${userId}`).toPromise();
      console.log('👤 Loaded user:', user);
      
      if (!user) {
        throw new Error('User not found');
      }
      
      return user;
    } catch (error) {
      console.error('❌ Error loading user details:', error);
      throw error;
    }
  }

  /**
   * Update user information
   */
  async updateUser(userId: string, userData: UserUpdate): Promise<User> {
    try {
      console.log('✏️ Updating user:', userId, userData);
      
      const updatedUser = await this.put<User>(`/users/${userId}`, userData).toPromise();
      console.log('✅ User updated:', updatedUser);
      
      if (!updatedUser) {
        throw new Error('Failed to update user');
      }
      
      return updatedUser;
    } catch (error) {
      console.error('❌ Error updating user:', error);
      throw error;
    }
  }

  /**
   * Activate user account
   */
  async activateUser(userId: string): Promise<boolean> {
    try {
      console.log('✅ Activating user:', userId);
      
      const response = await this.post<{ message: string }>(`/users/${userId}/activate`, {}).toPromise();
      console.log('✅ User activated:', response);
      
      return !!response;
    } catch (error) {
      console.error('❌ Error activating user:', error);
      throw error;
    }
  }

  /**
   * Deactivate user account
   */
  async deactivateUser(userId: string): Promise<boolean> {
    try {
      console.log('❌ Deactivating user:', userId);
      
      const response = await this.post<{ message: string }>(`/users/${userId}/deactivate`, {}).toPromise();
      console.log('❌ User deactivated:', response);
      
      return !!response;
    } catch (error) {
      console.error('❌ Error deactivating user:', error);
      throw error;
    }
  }

  /**
   * Search users by query
   */
  async searchUsers(query: string, filters?: Omit<UserFilters, 'search'>): Promise<User[]> {
    try {
      const params = this.createHttpParams({ ...filters, q: query });
      console.log('🔍 Searching users:', query, filters);
      
      const users = await this.get<User[]>('/users/search', params).toPromise();
      console.log('🔍 Search results:', users?.length || 0);
      
      return users || [];
    } catch (error) {
      console.error('❌ Error searching users:', error);
      throw error;
    }
  }

  /**
   * Get user's bookings
   */
  async getUserBookings(userId?: string, filters?: { status?: string; skip?: number; limit?: number }): Promise<UserBooking[]> {
    try {
      const endpoint = userId ? `/users/${userId}/bookings` : '/users/me/bookings';
      const params = this.createHttpParams(filters);
      
      console.log('📋 Loading user bookings:', userId || 'current user', filters);
      
      const bookings = await this.get<UserBooking[]>(endpoint, params).toPromise();
      console.log('📋 Loaded bookings:', bookings?.length || 0);
      
      return bookings || [];
    } catch (error) {
      console.error('❌ Error loading user bookings:', error);
      throw error;
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUserProfile(): Promise<User> {
    try {
      console.log('👤 Loading current user profile');
      
      const user = await this.get<User>('/users/me').toPromise();
      console.log('👤 Current user:', user);
      
      if (!user) {
        throw new Error('Failed to load user profile');
      }
      
      return user;
    } catch (error) {
      console.error('❌ Error loading current user profile:', error);
      throw error;
    }
  }

  /**
   * Update current user profile
   */
  async updateCurrentUserProfile(userData: UserUpdate): Promise<User> {
    try {
      console.log('✏️ Updating current user profile:', userData);
      
      const updatedUser = await this.put<User>('/users/me', userData).toPromise();
      console.log('✅ Profile updated:', updatedUser);
      
      if (!updatedUser) {
        throw new Error('Failed to update profile');
      }
      
      return updatedUser;
    } catch (error) {
      console.error('❌ Error updating profile:', error);
      throw error;
    }
  }

  /**
   * Change user password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      console.log('🔒 Changing password');
      
      const response = await this.post<{ message: string }>('/users/me/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      }).toPromise();
      
      console.log('✅ Password changed:', response);
      return !!response;
    } catch (error) {
      console.error('❌ Error changing password:', error);
      throw error;
    }
  }

  /**
   * Helper method to create HTTP params from filters
   */
  private createHttpParams(filters?: any): HttpParams {
    let params = new HttpParams();
    
    if (filters) {
      Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value !== undefined && value !== null && value !== '') {
          params = params.set(key, value.toString());
        }
      });
    }
    
    return params;
  }

  /**
   * Format user display name
   */
  formatUserName(user: User): string {
    return `${user.first_name} ${user.last_name}`.trim();
  }

  /**
   * Format user status
   */
  formatUserStatus(user: User): { text: string; class: string } {
    return user.is_active 
      ? { text: 'Active', class: 'badge bg-success' }
      : { text: 'Inactive', class: 'badge bg-danger' };
  }

  /**
   * Format user role
   */
  formatUserRole(user: User): { text: string; class: string; icon: string } {
    return user.is_admin 
      ? { text: 'Admin', class: 'badge bg-warning text-dark', icon: 'fa-crown' }
      : { text: 'User', class: 'badge bg-secondary', icon: 'fa-user' };
  }

  /**
   * Format currency
   */
  formatCurrency(amount: number): string {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  /**
   * Format date
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /**
   * Format date with time
   */
  formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
