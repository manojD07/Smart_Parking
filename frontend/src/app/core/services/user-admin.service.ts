import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BaseApiService } from './base-api.service';
import { User } from './user.service';

export interface AdminAction {
  userId: string;
  userName: string;
  action: 'make_admin' | 'remove_admin';
  timestamp: string;
  performedBy?: string;
}

export interface AdminValidationResult {
  canPerformAction: boolean;
  reason?: string;
  warnings: string[];
  currentAdminCount: number;
  minimumRequired: number;
}

@Injectable({
  providedIn: 'root'
})
export class UserAdminService extends BaseApiService {

  private readonly MINIMUM_ADMIN_COUNT = 1;

  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Make user an admin
   */
  async makeUserAdmin(userId: string): Promise<boolean> {
    try {
      console.log('👑 Making user admin:', userId);
      
      const response = await this.post<{ message: string }>(`/users/${userId}/make-admin`, {}).toPromise();
      console.log('✅ User made admin:', response);
      
      return !!response;
    } catch (error) {
      console.error('❌ Error making user admin:', error);
      throw error;
    }
  }

  /**
   * Remove admin privileges from user
   */
  async removeUserAdmin(userId: string): Promise<boolean> {
    try {
      console.log('❌ Removing admin from user:', userId);
      
      const response = await this.post<{ message: string }>(`/users/${userId}/remove-admin`, {}).toPromise();
      console.log('✅ Admin removed from user:', response);
      
      return !!response;
    } catch (error) {
      console.error('❌ Error removing admin from user:', error);
      throw error;
    }
  }

  /**
   * Get all admin users
   */
  async getAdminUsers(): Promise<User[]> {
    try {
      console.log('👑 Loading admin users');
      
      const params = { is_admin: 'true' };
      const admins = await this.get<User[]>('/users/', params).toPromise();
      
      console.log('👑 Loaded admin users:', admins?.length || 0);
      return admins || [];
    } catch (error) {
      console.error('❌ Error loading admin users:', error);
      throw error;
    }
  }

  /**
   * Validate if admin action can be performed
   */
  async validateAdminAction(
    userId: string, 
    action: 'make_admin' | 'remove_admin', 
    currentUser?: User,
    allUsers?: User[]
  ): Promise<AdminValidationResult> {
    try {
      console.log('🔍 Validating admin action:', { userId, action });

      const warnings: string[] = [];
      let canPerformAction = true;
      let reason = '';

      // Get current admin count
      const adminUsers = allUsers ? 
        allUsers.filter(u => u.is_admin) : 
        await this.getAdminUsers();
      
      const currentAdminCount = adminUsers.length;

      // Check if trying to remove admin from self
      if (action === 'remove_admin' && currentUser && currentUser.id === userId) {
        canPerformAction = false;
        reason = 'You cannot remove admin privileges from yourself';
      }

      // Check minimum admin count for removal
      if (action === 'remove_admin' && currentAdminCount <= this.MINIMUM_ADMIN_COUNT) {
        canPerformAction = false;
        reason = `Cannot remove admin: At least ${this.MINIMUM_ADMIN_COUNT} admin must remain in the system`;
      }

      // Add warnings for admin removal
      if (action === 'remove_admin' && canPerformAction) {
        warnings.push('This user will lose all administrative privileges immediately');
        warnings.push('They will no longer be able to access admin features');
        
        if (currentAdminCount === this.MINIMUM_ADMIN_COUNT + 1) {
          warnings.push('This will leave only one admin in the system');
        }
      }

      // Add warnings for making admin
      if (action === 'make_admin') {
        warnings.push('This user will gain full administrative privileges');
        warnings.push('They will be able to manage all users, bookings, and system settings');
      }

      const result: AdminValidationResult = {
        canPerformAction,
        reason,
        warnings,
        currentAdminCount,
        minimumRequired: this.MINIMUM_ADMIN_COUNT
      };

      console.log('🔍 Admin action validation result:', result);
      return result;

    } catch (error) {
      console.error('❌ Error validating admin action:', error);
      return {
        canPerformAction: false,
        reason: 'Unable to validate admin action',
        warnings: [],
        currentAdminCount: 0,
        minimumRequired: this.MINIMUM_ADMIN_COUNT
      };
    }
  }

  /**
   * Check if user can remove their own admin privileges
   */
  canRemoveOwnAdmin(currentUser: User, allUsers: User[]): boolean {
    if (!currentUser.is_admin) return false;
    
    const adminCount = allUsers.filter(u => u.is_admin).length;
    return adminCount > this.MINIMUM_ADMIN_COUNT;
  }

  /**
   * Get admin action confirmation message
   */
  getAdminActionMessage(
    action: 'make_admin' | 'remove_admin',
    targetUser: User,
    validation: AdminValidationResult
  ): { title: string; message: string; warnings: string[] } {
    const userName = `${targetUser.first_name} ${targetUser.last_name}`;

    if (action === 'make_admin') {
      return {
        title: 'Make User Admin?',
        message: `Are you sure you want to give ${userName} administrative privileges?`,
        warnings: validation.warnings
      };
    } else {
      return {
        title: 'Remove Admin Privileges?',
        message: `Are you sure you want to remove administrative privileges from ${userName}?`,
        warnings: validation.warnings
      };
    }
  }

  /**
   * Format admin status for display
   */
  formatAdminStatus(user: User): { 
    text: string; 
    class: string; 
    icon: string;
    canToggle: boolean;
  } {
    if (user.is_admin) {
      return {
        text: 'Admin',
        class: 'badge bg-warning text-dark',
        icon: 'fa-crown',
        canToggle: true
      };
    } else {
      return {
        text: 'User',
        class: 'badge bg-secondary',
        icon: 'fa-user',
        canToggle: true
      };
    }
  }

  /**
   * Get admin toggle button text and style
   */
  getAdminToggleButton(user: User): {
    text: string;
    class: string;
    icon: string;
    action: 'make_admin' | 'remove_admin';
  } {
    if (user.is_admin) {
      return {
        text: 'Remove Admin',
        class: 'btn btn-outline-danger btn-sm',
        icon: 'fa-user-minus',
        action: 'remove_admin'
      };
    } else {
      return {
        text: 'Make Admin',
        class: 'btn btn-outline-warning btn-sm',
        icon: 'fa-crown',
        action: 'make_admin'
      };
    }
  }

  /**
   * Log admin action (for audit trail if needed)
   */
  logAdminAction(action: AdminAction): void {
    console.log('📝 Admin action logged:', action);
    
    // In a real application, you might want to send this to an audit service
    // For now, we'll just log it to the console
    
    const logEntry = {
      timestamp: new Date().toISOString(),
      action: action.action,
      targetUser: action.userId,
      targetUserName: action.userName,
      performedBy: action.performedBy || 'current_user'
    };
    
    // Store in localStorage for demo purposes (in production, send to backend)
    const existingLogs = JSON.parse(localStorage.getItem('admin_actions') || '[]');
    existingLogs.push(logEntry);
    localStorage.setItem('admin_actions', JSON.stringify(existingLogs));
  }

  /**
   * Get admin action history (demo implementation)
   */
  getAdminActionHistory(): AdminAction[] {
    try {
      const logs = JSON.parse(localStorage.getItem('admin_actions') || '[]');
      return logs.sort((a: AdminAction, b: AdminAction) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    } catch (error) {
      console.error('Error loading admin action history:', error);
      return [];
    }
  }

  /**
   * Clear admin action history (demo implementation)
   */
  clearAdminActionHistory(): void {
    localStorage.removeItem('admin_actions');
    console.log('🗑️ Admin action history cleared');
  }

  /**
   * Get admin statistics
   */
  getAdminStatistics(users: User[]): {
    totalAdmins: number;
    totalUsers: number;
    adminPercentage: number;
    canRemoveAdmin: boolean;
  } {
    const totalUsers = users.length;
    const totalAdmins = users.filter(u => u.is_admin).length;
    const adminPercentage = totalUsers > 0 ? (totalAdmins / totalUsers) * 100 : 0;
    const canRemoveAdmin = totalAdmins > this.MINIMUM_ADMIN_COUNT;

    return {
      totalAdmins,
      totalUsers,
      adminPercentage,
      canRemoveAdmin
    };
  }
}
