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

  // Format booking time for display
  formatBookingTime(dateTime: string): string {
    return new Date(dateTime).toLocaleString();
  }

  // Calculate booking duration in hours
  calculateDuration(startTime: string, endTime: string): number {
    const start = new Date(startTime);
    const end = new Date(endTime);
    return Math.abs(end.getTime() - start.getTime()) / (1000 * 60 * 60);
  }

  // Check if booking can be cancelled
  canCancelBooking(booking: Booking): boolean {
    const now = new Date();
    const startTime = new Date(booking.start_time);
    const timeDiff = startTime.getTime() - now.getTime();
    const hoursUntilStart = timeDiff / (1000 * 60 * 60);
    
    // Can cancel if booking hasn't started and is more than 1 hour away
    return booking.status === 'confirmed' && hoursUntilStart > 1;
  }

  // Check if booking can be modified
  canModifyBooking(booking: Booking): boolean {
    const now = new Date();
    const startTime = new Date(booking.start_time);
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
}
