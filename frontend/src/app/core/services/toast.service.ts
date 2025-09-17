import { Injectable } from '@angular/core';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  timestamp: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toasts: Toast[] = [];
  private toastId = 0;

  constructor() {}

  /**
   * Show success toast
   */
  showSuccess(message: string, duration: number = 5000): void {
    this.addToast(message, 'success', duration);
  }

  /**
   * Show error toast
   */
  showError(message: string, duration: number = 8000): void {
    this.addToast(message, 'error', duration);
  }

  /**
   * Show warning toast
   */
  showWarning(message: string, duration: number = 6000): void {
    this.addToast(message, 'warning', duration);
  }

  /**
   * Show info toast
   */
  showInfo(message: string, duration: number = 5000): void {
    this.addToast(message, 'info', duration);
  }

  /**
   * Get all toasts
   */
  getToasts(): Toast[] {
    return this.toasts;
  }

  /**
   * Remove a specific toast
   */
  removeToast(id: string): void {
    this.toasts = this.toasts.filter(toast => toast.id !== id);
  }

  /**
   * Clear all toasts
   */
  clearAll(): void {
    this.toasts = [];
  }

  private addToast(message: string, type: Toast['type'], duration?: number): void {
    const toast: Toast = {
      id: `toast-${++this.toastId}`,
      message,
      type,
      duration,
      timestamp: Date.now()
    };

    this.toasts.push(toast);

    // Auto remove toast after duration
    if (duration && duration > 0) {
      setTimeout(() => {
        this.removeToast(toast.id);
      }, duration);
    }

    // For now, we'll just log to console as we don't have a toast component
    // In a full implementation, this would trigger UI notifications
    const emoji = {
      'success': '✅',
      'error': '❌', 
      'warning': '⚠️',
      'info': 'ℹ️'
    };

    console.log(`${emoji[type]} ${message}`);
  }
}
