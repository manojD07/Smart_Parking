import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BaseApiService } from './base-api.service';
import { environment } from '../../../environments/environment';

export interface ParkingLot {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  total_car_slots: number;
  total_bike_slots: number;
  hourly_rate_car: number;
  hourly_rate_bike: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateLotData {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  total_car_slots: number;
  total_bike_slots: number;
  hourly_rate_car: number;
  hourly_rate_bike: number;
}

export interface UpdateLotData {
  name?: string;
  address?: string;
  total_car_slots?: number;
  total_bike_slots?: number;
  hourly_rate_car?: number;
  hourly_rate_bike?: number;
  is_active?: boolean;
}

export interface LotFilters {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  search?: string;
}

export interface LotStatistics {
  total_lots: number;
  active_lots: number;
  inactive_lots: number;
  total_capacity: number;
  total_car_slots: number;
  total_bike_slots: number;
}

@Injectable({
  providedIn: 'root'
})
export class ParkingLotService extends BaseApiService {
  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Get all parking lots with optional filters
   */
  async getAllLots(filters?: LotFilters): Promise<ParkingLot[]> {
    try {
      const params: any = {};
      
      if (filters) {
        if (filters.skip !== undefined) params.skip = filters.skip;
        if (filters.limit !== undefined) params.limit = filters.limit;
        if (filters.is_active !== undefined) params.is_active = filters.is_active;
      }

      const response = await this.get<ParkingLot[]>('/parking/lots', params).toPromise();
      
      // Apply client-side search filter if provided
      if (filters?.search && response) {
        const searchTerm = filters.search.toLowerCase();
        return response.filter(lot => 
          lot.name.toLowerCase().includes(searchTerm) ||
          lot.address.toLowerCase().includes(searchTerm)
        );
      }
      
      return response || [];
    } catch (error) {
      console.error('Error fetching parking lots:', error);
      throw error;
    }
  }

  /**
   * Get a specific parking lot by ID
   */
  async getLotById(id: string): Promise<ParkingLot> {
    try {
      const response = await this.get<ParkingLot>(`/parking/lots/${id}`).toPromise();
      if (!response) {
        throw new Error('Parking lot not found');
      }
      return response;
    } catch (error) {
      console.error('Error fetching parking lot:', error);
      throw error;
    }
  }

  /**
   * Create a new parking lot with automatic slot generation
   */
  async createLot(data: CreateLotData): Promise<ParkingLot> {
    try {
      const response = await this.post<ParkingLot>('/parking/admin/lots', data).toPromise();
      if (!response) {
        throw new Error('Failed to create parking lot');
      }
      return response;
    } catch (error) {
      console.error('Error creating parking lot:', error);
      throw error;
    }
  }

  /**
   * Update an existing parking lot
   */
  async updateLot(id: string, data: UpdateLotData): Promise<ParkingLot> {
    try {
      const response = await this.put<ParkingLot>(`/parking/admin/lots/${id}`, data).toPromise();
      if (!response) {
        throw new Error('Failed to update parking lot');
      }
      return response;
    } catch (error) {
      console.error('Error updating parking lot:', error);
      throw error;
    }
  }

  /**
   * Delete a parking lot
   */
  async deleteLot(id: string): Promise<boolean> {
    try {
      const response = await this.delete<{message: string}>(`/parking/admin/lots/${id}`).toPromise();
      return !!response;
    } catch (error) {
      console.error('Error deleting parking lot:', error);
      throw error;
    }
  }

  /**
   * Toggle parking lot active status
   */
  async toggleLotStatus(id: string, isActive: boolean): Promise<ParkingLot> {
    try {
      return await this.updateLot(id, { is_active: isActive });
    } catch (error) {
      console.error('Error toggling lot status:', error);
      throw error;
    }
  }

  /**
   * Get parking lot statistics
   */
  async getLotStatistics(lotId?: string): Promise<any> {
    try {
      if (lotId) {
        // Get specific lot statistics
        const response = await this.get<any>(`/parking/admin/lots/${lotId}/statistics`).toPromise();
        return response;
      } else {
        // Calculate overall statistics from all lots
        const lots = await this.getAllLots();
        const stats: LotStatistics = {
          total_lots: lots.length,
          active_lots: lots.filter(lot => lot.is_active).length,
          inactive_lots: lots.filter(lot => !lot.is_active).length,
          total_capacity: lots.reduce((sum, lot) => sum + lot.total_car_slots + lot.total_bike_slots, 0),
          total_car_slots: lots.reduce((sum, lot) => sum + lot.total_car_slots, 0),
          total_bike_slots: lots.reduce((sum, lot) => sum + lot.total_bike_slots, 0)
        };
        return stats;
      }
    } catch (error) {
      console.error('Error fetching lot statistics:', error);
      throw error;
    }
  }

  /**
   * Search parking lots by location
   */
  async searchLotsByLocation(latitude: number, longitude: number, radiusKm: number = 10): Promise<ParkingLot[]> {
    try {
      const searchData = {
        latitude,
        longitude,
        radius_km: radiusKm,
        skip: 0,
        limit: 50
      };

      const response = await this.post<ParkingLot[]>('/parking/search', searchData).toPromise();
      return response || [];
    } catch (error) {
      console.error('Error searching lots by location:', error);
      throw error;
    }
  }

  /**
   * Get lot availability
   */
  async getLotAvailability(lotId: string, vehicleType: 'car' | 'bike'): Promise<any> {
    try {
      const params = { vehicle_type: vehicleType };
      const response = await this.get<any>(`/parking/lots/${lotId}/availability`, params).toPromise();
      return response;
    } catch (error) {
      console.error('Error fetching lot availability:', error);
      throw error;
    }
  }
}
