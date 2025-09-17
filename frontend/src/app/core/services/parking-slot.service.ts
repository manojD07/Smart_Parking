import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BaseApiService } from './base-api.service';

export interface ParkingSlot {
  id: string;
  lot_id: string;
  slot_number: string;
  slot_type: 'car' | 'bike';
  status: string;
  is_occupied: boolean;
  is_reserved: boolean;
  created_at: string;
}

export interface SlotFilters {
  vehicle_type?: 'car' | 'bike';
  status?: string;
  skip?: number;
  limit?: number;
}

export interface AddSlotsData {
  car_slots: number;
  bike_slots: number;
}

export interface SlotAvailability {
  total_slots: number;
  occupied_slots: number;
  available_slots: number;
  occupancy_rate: number;
}

@Injectable({
  providedIn: 'root'
})
export class ParkingSlotService extends BaseApiService {
  constructor() {
    super(inject(HttpClient));
  }

  /**
   * Get all slots for a parking lot (handles pagination automatically)
   */
  async getLotSlots(lotId: string, filters?: SlotFilters): Promise<ParkingSlot[]> {
    try {
      const allSlots: ParkingSlot[] = [];
      let skip = 0;
      const batchSize = 200; // Maximum allowed by backend
      let hasMore = true;

      // Load all slots in batches to bypass the 200 limit
      while (hasMore) {
        const params: any = {
          skip,
          limit: batchSize
        };
        
        if (filters) {
          if (filters.vehicle_type) params.vehicle_type = filters.vehicle_type;
          if (filters.status) params.status = filters.status;
        }

        const batch = await this.get<ParkingSlot[]>(`/parking/lots/${lotId}/slots`, params).toPromise();
        
        if (batch && batch.length > 0) {
          allSlots.push(...batch);
          skip += batchSize;
          
          // If we got less than the batch size, we've reached the end
          hasMore = batch.length === batchSize;
        } else {
          hasMore = false;
        }
      }

      console.log(`📊 Loaded ${allSlots.length} slots for lot ${lotId} in ${Math.ceil(allSlots.length / batchSize)} batch(es)`);
      return allSlots;
    } catch (error) {
      console.error('Error fetching lot slots:', error);
      throw error;
    }
  }

  /**
   * Get slot availability for a parking lot
   */
  async getSlotAvailability(lotId: string, vehicleType?: 'car' | 'bike'): Promise<SlotAvailability> {
    try {
      const params: any = {};
      if (vehicleType) params.vehicle_type = vehicleType;

      const response = await this.get<SlotAvailability>(`/parking/lots/${lotId}/availability`, params).toPromise();
      return response || { total_slots: 0, occupied_slots: 0, available_slots: 0, occupancy_rate: 0 };
    } catch (error) {
      console.error('Error fetching slot availability:', error);
      throw error;
    }
  }

  /**
   * Add slots to an existing parking lot (Admin only)
   */
  async addSlots(lotId: string, data: AddSlotsData): Promise<any> {
    try {
      const response = await this.post<any>(`/admin/parking/lots/${lotId}/slots`, data).toPromise();
      return response;
    } catch (error) {
      console.error('Error adding slots:', error);
      throw error;
    }
  }

  /**
   * Get debug slot information (Admin only)
   */
  async getDebugSlots(lotId: string): Promise<any> {
    try {
      const response = await this.get<any>(`/admin/debug/lots/${lotId}/slots`).toPromise();
      return response;
    } catch (error) {
      console.error('Error fetching debug slots:', error);
      throw error;
    }
  }

  /**
   * Group slots by type for display
   */
  groupSlotsByType(slots: ParkingSlot[]): { carSlots: ParkingSlot[], bikeSlots: ParkingSlot[] } {
    const carSlots = slots.filter(slot => slot.slot_type === 'car');
    const bikeSlots = slots.filter(slot => slot.slot_type === 'bike');
    
    // Sort by slot number for consistent display
    carSlots.sort((a, b) => this.compareSlotNumbers(a.slot_number, b.slot_number));
    bikeSlots.sort((a, b) => this.compareSlotNumbers(a.slot_number, b.slot_number));
    
    return { carSlots, bikeSlots };
  }

  /**
   * Compare slot numbers for sorting (handles C001, B001 format)
   */
  private compareSlotNumbers(a: string, b: string): number {
    // Extract the numeric part from slot numbers like C001, B001
    const getNumericPart = (slotNumber: string): number => {
      const match = slotNumber.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    };

    const numA = getNumericPart(a);
    const numB = getNumericPart(b);
    
    return numA - numB;
  }

  /**
   * Get slot status color class
   */
  getSlotStatusClass(slot: ParkingSlot): string {
    if (!slot.status || slot.status === 'INACTIVE') {
      return 'slot-inactive';
    }
    
    if (slot.is_occupied) {
      return 'slot-occupied';
    }
    
    if (slot.is_reserved) {
      return 'slot-reserved';
    }
    
    return 'slot-available';
  }

  /**
   * Get slot status text
   */
  getSlotStatusText(slot: ParkingSlot): string {
    if (!slot.status || slot.status === 'INACTIVE') {
      return 'Inactive';
    }
    
    if (slot.is_occupied) {
      return 'Occupied';
    }
    
    if (slot.is_reserved) {
      return 'Reserved';
    }
    
    return 'Available';
  }

  /**
   * Get slot type icon
   */
  getSlotTypeIcon(slotType: 'car' | 'bike'): string {
    return slotType === 'car' ? 'fa-car' : 'fa-motorcycle';
  }

  /**
   * Calculate slot statistics
   */
  calculateSlotStats(slots: ParkingSlot[]): {
    total: number;
    available: number;
    occupied: number;
    reserved: number;
    inactive: number;
    occupancyRate: number;
  } {
    const total = slots.length;
    const available = slots.filter(s => !s.is_occupied && !s.is_reserved && s.status !== 'INACTIVE').length;
    const occupied = slots.filter(s => s.is_occupied).length;
    const reserved = slots.filter(s => s.is_reserved).length;
    const inactive = slots.filter(s => s.status === 'INACTIVE').length;
    const occupancyRate = total > 0 ? Math.round((occupied / total) * 100) : 0;

    return {
      total,
      available,
      occupied,
      reserved,
      inactive,
      occupancyRate
    };
  }
}
