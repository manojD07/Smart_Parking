import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map } from 'rxjs/operators';

import { ParkingLot } from '../../../core/models/parking.model';
import { ApiResponse } from '../../../core/models/common.model';
import { environment } from '../../../../environments/environment';

interface GuestSearchParams {
  location: string;
  vehicleType: string;
  startTime: string;
  endTime: string;
}

interface GuestSearchContext extends GuestSearchParams {
  selectedLot?: ParkingLot;
}

interface GuestBookingIntent {
  lotId: string;
  vehicleType: string;
  startTime: string;
  endTime: string;
  location: string;
}

@Injectable({
  providedIn: 'root'
})
export class GuestService {
  private readonly apiUrl = environment.apiUrl;
  private readonly STORAGE_KEY = 'guestSearchContext';
  private readonly RESULTS_KEY = 'guestSearchResults';
  private readonly CONTEXT_EXPIRY = 30 * 60 * 1000; // 30 minutes

  private guestSearchContextSubject = new BehaviorSubject<GuestSearchContext | null>(null);
  private guestSearchResultsSubject = new BehaviorSubject<ParkingLot[]>([]);

  constructor(private http: HttpClient) {
    this.loadPersistedContext();
  }

  /**
   * Search for available parking lots as a guest user
   */
  async searchParkingAsGuest(params: GuestSearchParams): Promise<ParkingLot[]> {
    try {
      const httpParams = new HttpParams()
        .set('location', params.location)
        .set('vehicleType', params.vehicleType)
        .set('startTime', params.startTime)
        .set('endTime', params.endTime);

      const response = await this.http.get<ParkingLot[]>(
        `${this.apiUrl}/parking/search`,
        { params: httpParams }
      ).toPromise();

      const results = response || [];
      
      // Cache the results
      this.setGuestSearchResults(results);
      
      return results;
    } catch (error) {
      console.error('Guest search error:', error);
      throw new Error('Failed to search parking lots. Please try again.');
    }
  }

  /**
   * Get available parking lots without authentication requirement
   */
  getPublicParkingLots(): Observable<ParkingLot[]> {
    return this.http.get<ApiResponse<ParkingLot[]>>(`${this.apiUrl}/parking-lots/public`)
      .pipe(
        map(response => response.data || [])
      );
  }

  /**
   * Get parking lot details for guest preview
   */
  getPublicParkingLotDetails(lotId: string): Observable<ParkingLot | null> {
    return this.http.get<ApiResponse<ParkingLot>>(`${this.apiUrl}/parking-lots/${lotId}/public`)
      .pipe(
        map(response => response.data || null)
      );
  }

  /**
   * Check availability for specific lot without authentication
   */
  checkGuestAvailability(lotId: string, params: {
    vehicleType: string;
    startTime: string;
    endTime: string;
  }): Observable<{ available: boolean; availableSlots: number }> {
    const httpParams = new HttpParams()
      .set('vehicleType', params.vehicleType)
      .set('startTime', params.startTime)
      .set('endTime', params.endTime);

    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/parking-lots/${lotId}/availability/guest`, 
      { params: httpParams }
    ).pipe(
      map(response => response.data)
    );
  }

  /**
   * Store guest search context in memory and localStorage
   */
  setGuestSearchContext(context: GuestSearchContext): void {
    const contextWithTimestamp = {
      ...context,
      timestamp: Date.now()
    };

    // Store in memory
    this.guestSearchContextSubject.next(context);

    // Persist to localStorage
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(contextWithTimestamp));
    } catch (error) {
      console.warn('Failed to persist guest search context:', error);
    }
  }

  /**
   * Get current guest search context
   */
  getGuestSearchContext(): GuestSearchContext | null {
    return this.guestSearchContextSubject.value;
  }

  /**
   * Get guest search context as observable
   */
  getGuestSearchContext$(): Observable<GuestSearchContext | null> {
    return this.guestSearchContextSubject.asObservable();
  }

  /**
   * Store guest search results
   */
  setGuestSearchResults(results: ParkingLot[]): void {
    const resultsWithTimestamp = {
      results,
      timestamp: Date.now()
    };

    // Store in memory
    this.guestSearchResultsSubject.next(results);

    // Persist to localStorage
    try {
      localStorage.setItem(this.RESULTS_KEY, JSON.stringify(resultsWithTimestamp));
    } catch (error) {
      console.warn('Failed to persist guest search results:', error);
    }
  }

  /**
   * Get cached guest search results
   */
  getGuestSearchResults(): ParkingLot[] {
    return this.guestSearchResultsSubject.value;
  }

  /**
   * Get guest search results as observable
   */
  getGuestSearchResults$(): Observable<ParkingLot[]> {
    return this.guestSearchResultsSubject.asObservable();
  }

  /**
   * Create booking intent for guest user (to be completed after auth)
   */
  createGuestBookingIntent(intent: GuestBookingIntent): void {
    const intentWithTimestamp = {
      ...intent,
      timestamp: Date.now()
    };

    try {
      localStorage.setItem('guestBookingIntent', JSON.stringify(intentWithTimestamp));
    } catch (error) {
      console.warn('Failed to persist guest booking intent:', error);
    }
  }

  /**
   * Get and clear guest booking intent
   */
  getAndClearGuestBookingIntent(): GuestBookingIntent | null {
    try {
      const stored = localStorage.getItem('guestBookingIntent');
      if (!stored) return null;

      const intentData = JSON.parse(stored);
      
      // Check if expired (30 minutes)
      if (Date.now() - intentData.timestamp > this.CONTEXT_EXPIRY) {
        localStorage.removeItem('guestBookingIntent');
        return null;
      }

      // Clear after retrieving
      localStorage.removeItem('guestBookingIntent');
      
      return {
        lotId: intentData.lotId,
        vehicleType: intentData.vehicleType,
        startTime: intentData.startTime,
        endTime: intentData.endTime,
        location: intentData.location
      };
    } catch (error) {
      console.warn('Failed to retrieve guest booking intent:', error);
      return null;
    }
  }

  /**
   * Clear all guest data
   */
  clearGuestData(): void {
    // Clear memory
    this.guestSearchContextSubject.next(null);
    this.guestSearchResultsSubject.next([]);

    // Clear localStorage
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      localStorage.removeItem(this.RESULTS_KEY);
      localStorage.removeItem('guestBookingIntent');
    } catch (error) {
      console.warn('Failed to clear guest data:', error);
    }
  }

  /**
   * Check if guest has pending booking intent
   */
  hasPendingBookingIntent(): boolean {
    try {
      const stored = localStorage.getItem('guestBookingIntent');
      if (!stored) return false;

      const intentData = JSON.parse(stored);
      return Date.now() - intentData.timestamp <= this.CONTEXT_EXPIRY;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get popular parking locations for guest landing page
   */
  getPopularLocations(): Observable<Array<{ name: string; lotCount: number }>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/parking-lots/popular-locations`)
      .pipe(
        map(response => response.data || [])
      );
  }

  /**
   * Get nearby parking lots based on coordinates
   */
  getNearbyParkingLots(lat: number, lng: number, radius = 5): Observable<ParkingLot[]> {
    const params = new HttpParams()
      .set('lat', lat.toString())
      .set('lng', lng.toString())
      .set('radius', radius.toString());

    return this.http.get<ApiResponse<ParkingLot[]>>(`${this.apiUrl}/parking-lots/nearby`, { params })
      .pipe(
        map(response => response.data || [])
      );
  }

  /**
   * Convert guest search parameters to booking form data
   */
  convertToBookingParams(context: GuestSearchContext): any {
    if (!context) return null;

    return {
      lotId: context.selectedLot?.id,
      vehicleType: context.vehicleType,
      startTime: context.startTime,
      endTime: context.endTime,
      location: context.location
    };
  }

  /**
   * Load persisted context from localStorage
   */
  private loadPersistedContext(): void {
    try {
      // Load search context
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const contextData = JSON.parse(stored);
        
        // Check if expired
        if (Date.now() - contextData.timestamp <= this.CONTEXT_EXPIRY) {
          const { timestamp, ...context } = contextData;
          this.guestSearchContextSubject.next(context);
        } else {
          localStorage.removeItem(this.STORAGE_KEY);
        }
      }

      // Load search results
      const storedResults = localStorage.getItem(this.RESULTS_KEY);
      if (storedResults) {
        const resultsData = JSON.parse(storedResults);
        
        // Check if expired
        if (Date.now() - resultsData.timestamp <= this.CONTEXT_EXPIRY) {
          this.guestSearchResultsSubject.next(resultsData.results);
        } else {
          localStorage.removeItem(this.RESULTS_KEY);
        }
      }
    } catch (error) {
      console.warn('Failed to load persisted guest context:', error);
      // Clear corrupted data
      this.clearGuestData();
    }
  }

  /**
   * Validate guest search parameters
   */
  validateGuestSearchParams(params: GuestSearchParams): { valid: boolean; error?: string } {
    if (!params.location?.trim()) {
      return { valid: false, error: 'Location is required' };
    }

    if (!params.vehicleType) {
      return { valid: false, error: 'Vehicle type is required' };
    }

    const startTime = new Date(params.startTime);
    const endTime = new Date(params.endTime);
    const now = new Date();

    if (startTime <= now) {
      return { valid: false, error: 'Start time must be in the future' };
    }

    if (endTime <= startTime) {
      return { valid: false, error: 'End time must be after start time' };
    }

    const durationMinutes = (endTime.getTime() - startTime.getTime()) / (1000 * 60);
    if (durationMinutes < 15) {
      return { valid: false, error: 'Minimum booking duration is 15 minutes' };
    }

    return { valid: true };
  }
}
