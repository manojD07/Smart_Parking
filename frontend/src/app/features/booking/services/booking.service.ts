import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from '../../../core/services/base-api.service';
import { 
  Booking, 
  BookingCreate, 
  BookingUpdate,
  PricingPreviewRequest,
  PricingPreviewResponse
} from '../../../core/models/booking.model';
import { SuccessResponse } from '../../../core/models/common.model';
import { 
  parseBackendDate, 
  formatIST, 
  nowIST,
  toBackendDate 
} from '../../../core/utils/timezone.util';

@Injectable({
  providedIn: 'root'
})
export class BookingService extends BaseApiService {
  
  constructor() {
    super(inject(HttpClient));
  }

  // Create a new booking
  createBooking(bookingData: BookingCreate): Observable<Booking> {
    return this.post<Booking>('/bookings/', bookingData);
  }

  // Get user's bookings
  getMyBookings(params?: {
    status?: string;
    skip?: number;
    limit?: number;
  }): Observable<Booking[]> {
    return this.get<Booking[]>('/bookings/my', params);
  }

  // Get booking by ID
  getBooking(bookingId: string): Observable<Booking> {
    return this.get<Booking>(`/bookings/${bookingId}`);
  }

  // Get booking by reference code
  getBookingByReference(reference: string): Observable<Booking> {
    return this.get<Booking>(`/bookings/reference/${reference}`);
  }


  // Update booking
  updateBooking(bookingId: string, updateData: BookingUpdate): Observable<Booking> {
    return this.put<Booking>(`/bookings/${bookingId}`, updateData);
  }

  // Cancel booking
  cancelBooking(bookingId: string): Observable<SuccessResponse> {
    return this.put<SuccessResponse>(`/bookings/${bookingId}/cancel`, {});
  }

  // Check-in to booking
  checkInBooking(bookingId: string): Observable<SuccessResponse> {
    return this.post<SuccessResponse>(`/bookings/${bookingId}/checkin`, {});
  }

  // Check-out from booking
  checkOutBooking(bookingId: string): Observable<SuccessResponse> {
    return this.post<SuccessResponse>(`/bookings/${bookingId}/checkout`, {});
  }

  // Get pricing preview
  getPricingPreview(pricingRequest: PricingPreviewRequest): Observable<PricingPreviewResponse> {
    return this.post<PricingPreviewResponse>('/bookings/pricing-preview', pricingRequest);
  }

  // Format booking time for display in IST
  formatBookingTime(dateTime: string): string {
    return formatIST(parseBackendDate(dateTime));
  }

  // Calculate booking duration in hours
  calculateDuration(startTime: string, endTime: string): number {
    const start = parseBackendDate(startTime);
    const end = parseBackendDate(endTime);
    return Math.abs(end.getTime() - start.getTime()) / (1000 * 60 * 60);
  }

  // Check if booking can be cancelled
  canCancelBooking(booking: Booking): boolean {
    const now = nowIST();
    const startTime = parseBackendDate(booking.start_time);
    const timeDiff = startTime.getTime() - now.getTime();
    const hoursUntilStart = timeDiff / (1000 * 60 * 60);
    
    // Can cancel if booking hasn't started and is more than 1 hour away
    return booking.status === 'confirmed' && hoursUntilStart > 1;
  }

  // Check if booking can be modified
  canModifyBooking(booking: Booking): boolean {
    const now = nowIST();
    const startTime = parseBackendDate(booking.start_time);
    const timeDiff = startTime.getTime() - now.getTime();
    const hoursUntilStart = timeDiff / (1000 * 60 * 60);
    
    // Can modify if booking hasn't started and is more than 2 hours away
    return booking.status === 'confirmed' && hoursUntilStart > 2;
  }

  // Generate booking QR code data
  generateQRCodeData(booking: Booking): string {
    return JSON.stringify({
      bookingId: booking.id,
      reference: booking.booking_reference,
      vehicleNumber: booking.vehicle_number,
      lotId: booking.lot_id,
      slotId: booking.slot_id
    });
  }

  // ===== CHUNK-BASED BOOKING METHODS =====

  /**
   * Get chunk availability for a specific slot
   */
  getSlotChunkAvailability(
    slotId: string,
    startTime: string,
    endTime: string
  ): Observable<any> {
    return this.get<any>(`/bookings/slots/${slotId}/chunks`, {
      start_time: startTime,
      end_time: endTime
    });
  }

  /**
   * Reserve chunks for payment (10-minute Redis TTL)
   */
  reserveChunks(chunkIds: string[]): Observable<any> {
    return this.post<any>('/bookings/reserve-chunks', {
      chunk_ids: chunkIds
    });
  }

  /**
   * Confirm booking from Redis reservation
   */
  confirmChunkBooking(sessionId: string, vehicleNumber: string): Observable<any> {
    return this.post<any>('/bookings/confirm-chunk-booking', {
      session_id: sessionId,
      vehicle_number: vehicleNumber
    });
  }

  /**
   * Cancel chunk reservation
   */
  cancelChunkReservation(sessionId: string): Observable<any> {
    return this.delete<any>(`/bookings/cancel-reservation/${sessionId}`);
  }

  /**
   * Get session information
   */
  getSessionInfo(sessionId: string): Observable<any> {
    return this.get<any>(`/bookings/session/${sessionId}`);
  }
}
