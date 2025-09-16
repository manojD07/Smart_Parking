import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../../../core/services/base-api.service';

export interface PaymentMethod {
  name: string;
  description: string;
  icon: string;
  fields: string[];
}

export interface PaymentMethodsResponse {
  payment_methods: { [key: string]: PaymentMethod };
  supported_currencies: string[];
  service_charges: { [key: string]: number };
}

export interface PaymentRequest {
  booking_id: string;
  payment_method: string;
  simulate_failure?: boolean;
}

export interface PaymentResult {
  success: boolean;
  payment_id: string;
  transaction_id: string;
  message: string;
  booking_id: string;
  amount: number;
}

export interface PaymentStatus {
  booking_id: string;
  booking_reference: string;
  payment_status: string;
  booking_status: string;
  amount: number;
  currency: string;
}

@Injectable({
  providedIn: 'root'
})
export class PaymentService extends BaseApiService {

  /**
   * Get available payment methods
   */
  getPaymentMethods(): Observable<PaymentMethodsResponse> {
    return this.get<PaymentMethodsResponse>('/payments/methods');
  }

  /**
   * Process a payment
   */
  processPayment(paymentRequest: PaymentRequest): Observable<PaymentResult> {
    return this.post<PaymentResult>('/payments/process', paymentRequest);
  }

  /**
   * Validate payment details
   */
  validatePaymentDetails(paymentMethod: string, paymentDetails: any): Observable<any> {
    return this.post<any>('/payments/validate', {
      payment_method: paymentMethod,
      payment_details: paymentDetails
    });
  }

  /**
   * Get payment status for a booking
   */
  getPaymentStatus(bookingId: string): Observable<PaymentStatus> {
    return this.get<PaymentStatus>(`/payments/booking/${bookingId}/status`);
  }
}
