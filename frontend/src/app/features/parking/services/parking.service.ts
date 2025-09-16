import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from '../../../core/services/base-api.service';
import { 
  ParkingLot, 
  ParkingSlot, 
  AvailabilityRequest, 
  AvailabilityResponse, 
  LocationSearchRequest 
} from '../../../core/models/parking.model';

@Injectable({
  providedIn: 'root'
})
export class ParkingService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  // Get all parking lots
  getParkingLots(params?: {
    skip?: number;
    limit?: number;
    is_active?: boolean;
  }): Observable<ParkingLot[]> {
    return this.get<ParkingLot[]>('/parking/lots', params);
  }

  // Get parking lot by ID
  getParkingLot(lotId: string): Observable<ParkingLot> {
    return this.get<ParkingLot>(`/parking/lots/${lotId}`);
  }

  // Check availability for a parking lot
  checkAvailability(
    lotId: string,
    vehicleType: string,
    startTime?: string,
    endTime?: string
  ): Observable<AvailabilityResponse> {
    const params: any = { vehicle_type: vehicleType };
    if (startTime) params.start_time = startTime;
    if (endTime) params.end_time = endTime;

    return this.get<AvailabilityResponse>(`/parking/lots/${lotId}/availability`, params);
  }

  // Check detailed availability with POST request
  checkDetailedAvailability(
    lotId: string,
    request: AvailabilityRequest
  ): Observable<AvailabilityResponse> {
    return this.post<AvailabilityResponse>(`/parking/lots/${lotId}/availability`, request);
  }

  // Get slots for a parking lot
  getParkingSlots(
    lotId: string,
    params?: {
      vehicle_type?: string;
      status?: string;
      skip?: number;
      limit?: number;
    }
  ): Observable<ParkingSlot[]> {
    return this.get<ParkingSlot[]>(`/parking/lots/${lotId}/slots`, params);
  }

  // Search parking lots by location
  searchParkingLots(searchRequest: LocationSearchRequest): Observable<ParkingLot[]> {
    return this.post<ParkingLot[]>('/parking/search', searchRequest);
  }

  // Get user's current location (browser geolocation)
  getCurrentLocation(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by this browser.'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => resolve(position),
        (error) => reject(error),
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  }

  // Calculate distance between two coordinates (Haversine formula)
  calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 6371; // Earth's radius in kilometers
    const dLat = this.toRadians(lat2 - lat1);
    const dLon = this.toRadians(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRadians(lat1)) *
        Math.cos(this.toRadians(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in kilometers
  }

  private toRadians(degrees: number): number {
    return degrees * (Math.PI / 180);
  }
}
