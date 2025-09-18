import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from './base-api.service';

// Interfaces based on backend schemas
export interface PricingRule {
  id: string;
  lot_id: string;
  name: string;
  vehicle_type: 'car' | 'bike';
  rule_type: 'time_based' | 'day_based' | 'seasonal' | 'demand_based';
  start_time?: string;
  end_time?: string;
  days_of_week?: string;
  days_list: string[];
  price_per_hour: number;
  multiplier: number;
  effective_price: number;
  min_charge?: number;
  max_charge?: number;
  is_active: boolean;
  priority: 'high' | 'normal' | 'low';
  valid_from?: string;
  valid_until?: string;
  created_at: string;
  updated_at: string;
}

export interface PricingRuleCreate {
  lot_id: string;
  name: string;
  vehicle_type: 'car' | 'bike';
  rule_type: 'time_based' | 'day_based' | 'seasonal' | 'demand_based';
  price_per_hour: number;
  multiplier?: number;
  start_time?: string;
  end_time?: string;
  days_of_week?: string[];
  priority?: 'high' | 'normal' | 'low';
  min_charge?: number;
  max_charge?: number;
}

export interface PricingRuleUpdate {
  name?: string;
  vehicle_type?: 'car' | 'bike';
  rule_type?: 'time_based' | 'day_based' | 'seasonal' | 'demand_based';
  start_time?: string;
  end_time?: string;
  days_of_week?: string[];
  price_per_hour?: number;
  multiplier?: number;
  min_charge?: number;
  max_charge?: number;
  is_active?: boolean;
  priority?: 'high' | 'normal' | 'low';
  valid_from?: string;
  valid_until?: string;
}

export interface PricingRuleListResponse {
  rules: PricingRule[];
  total: number;
  summary: {
    total_rules: number;
    active_rules: number;
    inactive_rules: number;
    rule_types: Record<string, number>;
    vehicle_types: Record<string, number>;
  };
}

export interface PricingRuleFilters {
  vehicle_type?: 'car' | 'bike';
  is_active?: boolean;
  rule_type?: string;
  skip?: number;
  limit?: number;
}

@Injectable({
  providedIn: 'root'
})
export class PricingRuleService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Get all pricing rules for a parking lot
   */
  async getLotPricingRules(lotId: string, filters?: PricingRuleFilters): Promise<PricingRuleListResponse> {
    try {
      const params: any = {};
      
      if (filters) {
        if (filters.vehicle_type) params.vehicle_type = filters.vehicle_type;
        if (filters.is_active !== undefined) params.is_active = filters.is_active;
        if (filters.rule_type) params.rule_type = filters.rule_type;
        if (filters.skip) params.skip = filters.skip;
        if (filters.limit) params.limit = filters.limit;
      }

      const response = await this.get<PricingRuleListResponse>(`/pricing/admin/lots/${lotId}/rules`, params).toPromise();
      return response || { rules: [], total: 0, summary: { total_rules: 0, active_rules: 0, inactive_rules: 0, rule_types: {}, vehicle_types: {} } };
    } catch (error) {
      console.error('Error fetching pricing rules:', error);
      throw error;
    }
  }

  /**
   * Create a new pricing rule
   */
  async createPricingRule(ruleData: PricingRuleCreate): Promise<PricingRule> {
    try {
      const response = await this.post<PricingRule>('/pricing/admin/rules', ruleData).toPromise();
      return response!;
    } catch (error) {
      console.error('Error creating pricing rule:', error);
      throw error;
    }
  }

  /**
   * Get a specific pricing rule
   */
  async getPricingRule(ruleId: string): Promise<PricingRule> {
    try {
      const response = await this.get<PricingRule>(`/pricing/admin/rules/${ruleId}`).toPromise();
      return response!;
    } catch (error) {
      console.error('Error fetching pricing rule:', error);
      throw error;
    }
  }

  /**
   * Update a pricing rule
   */
  async updatePricingRule(ruleId: string, updates: PricingRuleUpdate): Promise<PricingRule> {
    try {
      const response = await this.put<PricingRule>(`/pricing/admin/rules/${ruleId}`, updates).toPromise();
      return response!;
    } catch (error) {
      console.error('Error updating pricing rule:', error);
      throw error;
    }
  }

  /**
   * Delete a pricing rule
   */
  async deletePricingRule(ruleId: string): Promise<boolean> {
    try {
      const response = await this.delete<{message: string}>(`/pricing/admin/rules/${ruleId}`).toPromise();
      return !!response;
    } catch (error) {
      console.error('Error deleting pricing rule:', error);
      throw error;
    }
  }

  /**
   * Toggle pricing rule status (activate/deactivate)
   */
  async togglePricingRule(ruleId: string): Promise<PricingRule> {
    try {
      const response = await this.put<PricingRule>(`/pricing/admin/rules/${ruleId}/toggle`, {}).toPromise();
      return response!;
    } catch (error) {
      console.error('Error toggling pricing rule:', error);
      throw error;
    }
  }

  /**
   * Helper methods
   */
  getRuleTypeDisplayName(ruleType: string): string {
    const types = {
      'time_based': 'Time Based',
      'day_based': 'Day Based', 
      'seasonal': 'Seasonal',
      'demand_based': 'Demand Based'
    };
    return types[ruleType as keyof typeof types] || ruleType;
  }

  getVehicleTypeDisplayName(vehicleType: string): string {
    return vehicleType === 'car' ? 'Car' : 'Bike';
  }

  getPriorityDisplayName(priority: string): string {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  }

  formatPrice(amount: number): string {
    return `₹${amount.toFixed(2)}`;
  }

  formatTimeRange(startTime?: string, endTime?: string): string {
    if (!startTime || !endTime) return 'All Day';
    return `${startTime.slice(0, 5)} - ${endTime.slice(0, 5)}`;
  }

  formatDaysList(daysList: string[]): string {
    if (!daysList || daysList.length === 0) return 'All Days';
    if (daysList.length === 7) return 'All Days';
    
    const dayAbbr = {
      'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wed',
      'thursday': 'Thu', 'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'
    };
    
    return daysList.map(day => dayAbbr[day as keyof typeof dayAbbr] || day).join(', ');
  }
}
