import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, interval, takeUntil } from 'rxjs';

import { BookingService } from '../../booking/services/booking.service';
import { PaymentService } from '../services/payment.service';

interface PaymentSession {
  sessionId: string;
  slotId: string;
  slotNumber: string;
  lotId: string;
  lotName: string;
  vehicleType: string;
  vehicleNumber: string;
  selectedChunks: any[];
  totalAmount: number;
  expiresAt: string;
}

enum PaymentMethod {
  CREDIT_CARD = 'credit_card',
  DEBIT_CARD = 'debit_card',
  UPI = 'upi',
  NET_BANKING = 'net_banking'
}

interface Bank {
  code: string;
  name: string;
}

@Component({
  selector: 'app-chunk-payment-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="container-fluid py-4">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <!-- Header -->
          <div class="card shadow-sm mb-4">
            <div class="card-header bg-primary text-white">
              <h4 class="mb-0">
                <i class="fas fa-credit-card me-2"></i>
                Complete Payment
              </h4>
            </div>
            <div class="card-body">
              <!-- Countdown Timer -->
              <div class="alert alert-warning d-flex align-items-center mb-4" *ngIf="timeRemaining > 0">
                <i class="fas fa-clock me-2"></i>
                <div>
                  <strong>Payment expires in: {{ formatTime(timeRemaining) }}</strong>
                  <br>
                  <small>Complete payment before your reservation expires</small>
                </div>
              </div>

              <!-- Expired Alert -->
              <div class="alert alert-danger d-flex align-items-center mb-4" *ngIf="timeRemaining <= 0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                  <strong>Reservation Expired</strong>
                  <br>
                  <small>Your parking slot reservation has expired. Please make a new booking.</small>
                </div>
              </div>

              <!-- Booking Summary -->
              <div class="row" *ngIf="paymentSession">
                <div class="col-md-6">
                  <h5>Booking Details</h5>
                  <table class="table table-sm">
                    <tr>
                      <td><strong>Parking Lot:</strong></td>
                      <td>{{ paymentSession.lotName }}</td>
                    </tr>
                    <tr>
                      <td><strong>Slot Number:</strong></td>
                      <td>{{ paymentSession.slotNumber || 'Will be assigned' }}</td>
                    </tr>
                    <tr>
                      <td><strong>Vehicle Type:</strong></td>
                      <td>{{ paymentSession.vehicleType | titlecase }}</td>
                    </tr>
                    <tr>
                      <td><strong>Vehicle Number:</strong></td>
                      <td>{{ paymentSession.vehicleNumber }}</td>
                    </tr>
                    <tr>
                      <td><strong>Duration:</strong></td>
                      <td>{{ calculateDuration() }} hours</td>
                    </tr>
                  </table>
                </div>
                <div class="col-md-6">
                  <h5>Selected Time Slots</h5>
                  <div class="selected-chunks">
                    <div *ngFor="let chunk of paymentSession.selectedChunks" class="chunk-item">
                      <i class="fas fa-clock me-1"></i>
                      {{ formatChunkTime(chunk.start_time) }} - {{ formatChunkTime(chunk.end_time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Payment Form -->
          <div class="card shadow-sm" *ngIf="timeRemaining > 0 && paymentSession">
            <div class="card-header">
              <h5 class="mb-0">Payment Information</h5>
            </div>
            <div class="card-body">
              <form [formGroup]="paymentForm" (ngSubmit)="processPayment()">
                <!-- Payment Amount -->
                <div class="row mb-4">
                  <div class="col-12">
                    <div class="alert alert-info">
                      <h4 class="mb-0">
                        Total Amount: 
                        <span class="text-success">₹{{ paymentSession.totalAmount | number:'1.2-2' }}</span>
                      </h4>
                    </div>
                  </div>
                </div>

                <!-- Payment Method Selection -->
                <div class="row mb-4">
                  <div class="col-12">
                    <label class="form-label">Choose Payment Method</label>
                    <div class="payment-methods">
                      <div class="row">
                        <div class="col-md-3 col-6 mb-2">
                          <input 
                            type="radio" 
                            class="btn-check" 
                            [value]="PaymentMethod.CREDIT_CARD"
                            formControlName="paymentMethod"
                            id="credit-card">
                          <label class="btn btn-outline-primary w-100 payment-method-btn" for="credit-card">
                            <i class="fas fa-credit-card me-2"></i>
                            Credit Card
                          </label>
                        </div>
                        <div class="col-md-3 col-6 mb-2">
                          <input 
                            type="radio" 
                            class="btn-check" 
                            [value]="PaymentMethod.DEBIT_CARD"
                            formControlName="paymentMethod"
                            id="debit-card">
                          <label class="btn btn-outline-primary w-100 payment-method-btn" for="debit-card">
                            <i class="fas fa-credit-card me-2"></i>
                            Debit Card
                          </label>
                        </div>
                        <div class="col-md-3 col-6 mb-2">
                          <input 
                            type="radio" 
                            class="btn-check" 
                            [value]="PaymentMethod.UPI"
                            formControlName="paymentMethod"
                            id="upi">
                          <label class="btn btn-outline-primary w-100 payment-method-btn" for="upi">
                            <i class="fas fa-mobile-alt me-2"></i>
                            UPI
                          </label>
                        </div>
                        <div class="col-md-3 col-6 mb-2">
                          <input 
                            type="radio" 
                            class="btn-check" 
                            [value]="PaymentMethod.NET_BANKING"
                            formControlName="paymentMethod"
                            id="net-banking">
                          <label class="btn btn-outline-primary w-100 payment-method-btn" for="net-banking">
                            <i class="fas fa-university me-2"></i>
                            Net Banking
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Card Details (Credit/Debit Card) -->
                <div *ngIf="selectedPaymentMethod === PaymentMethod.CREDIT_CARD || selectedPaymentMethod === PaymentMethod.DEBIT_CARD">
                  <h6 class="mb-3">
                    <i class="fas fa-credit-card me-2"></i>
                    {{ selectedPaymentMethod === PaymentMethod.CREDIT_CARD ? 'Credit' : 'Debit' }} Card Details
                  </h6>
                  
                  <div class="row mb-3">
                    <div class="col-md-12">
                      <label class="form-label">Card Number</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        formControlName="cardNumber"
                        placeholder="1234 5678 9012 3456"
                        maxlength="19"
                        (input)="formatCardNumber($event)">
                      <div *ngIf="paymentForm.get('cardNumber')?.errors?.['required'] && paymentForm.get('cardNumber')?.touched" 
                           class="text-danger small">
                        Card number is required
                      </div>
                    </div>
                  </div>

                  <div class="row mb-3">
                    <div class="col-md-6">
                      <label class="form-label">Expiry Date</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        formControlName="expiryDate"
                        placeholder="MM/YY"
                        maxlength="5"
                        (input)="formatExpiryDate($event)">
                      <div *ngIf="paymentForm.get('expiryDate')?.errors?.['required'] && paymentForm.get('expiryDate')?.touched" 
                           class="text-danger small">
                        Expiry date is required
                      </div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">CVV</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        formControlName="cvv"
                        placeholder="123"
                        maxlength="4">
                      <div *ngIf="paymentForm.get('cvv')?.errors?.['required'] && paymentForm.get('cvv')?.touched" 
                           class="text-danger small">
                        CVV is required
                      </div>
                    </div>
                  </div>

                  <div class="row mb-3">
                    <div class="col-md-12">
                      <label class="form-label">Cardholder Name</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        formControlName="cardholderName"
                        placeholder="John Doe">
                      <div *ngIf="paymentForm.get('cardholderName')?.errors?.['required'] && paymentForm.get('cardholderName')?.touched" 
                           class="text-danger small">
                        Cardholder name is required
                      </div>
                    </div>
                  </div>
                </div>

                <!-- UPI Details -->
                <div *ngIf="selectedPaymentMethod === PaymentMethod.UPI">
                  <h6 class="mb-3">
                    <i class="fas fa-mobile-alt me-2"></i>
                    UPI Payment Details
                  </h6>
                  
                  <div class="row mb-3">
                    <div class="col-md-12">
                      <label class="form-label">UPI ID</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        formControlName="upiId"
                        placeholder="yourname@paytm / yourname@googlepay">
                      <div *ngIf="paymentForm.get('upiId')?.errors?.['required'] && paymentForm.get('upiId')?.touched" 
                           class="text-danger small">
                        UPI ID is required
                      </div>
                      <div *ngIf="paymentForm.get('upiId')?.errors?.['pattern'] && paymentForm.get('upiId')?.touched" 
                           class="text-danger small">
                        Please enter a valid UPI ID
                      </div>
                    </div>
                  </div>

                  <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Popular UPI Apps:</strong> Google Pay, PhonePe, Paytm, BHIM, Amazon Pay
                  </div>
                </div>

                <!-- Net Banking Details -->
                <div *ngIf="selectedPaymentMethod === PaymentMethod.NET_BANKING">
                  <h6 class="mb-3">
                    <i class="fas fa-university me-2"></i>
                    Net Banking Details
                  </h6>
                  
                  <div class="row mb-3">
                    <div class="col-md-12">
                      <label class="form-label">Select Your Bank</label>
                      <select class="form-control" formControlName="selectedBank">
                        <option value="">Choose your bank</option>
                        <option *ngFor="let bank of banks" [value]="bank.code">
                          {{ bank.name }}
                        </option>
                      </select>
                      <div *ngIf="paymentForm.get('selectedBank')?.errors?.['required'] && paymentForm.get('selectedBank')?.touched" 
                           class="text-danger small">
                        Please select your bank
                      </div>
                    </div>
                  </div>

                  <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    You will be redirected to your bank's secure website to complete the payment.
                  </div>
                </div>

                <!-- Error Message -->
                <div *ngIf="errorMessage" class="alert alert-danger">
                  <i class="fas fa-exclamation-triangle me-2"></i>
                  {{ errorMessage }}
                </div>

                <!-- Action Buttons -->
                <div class="d-flex justify-content-between">
                  <button 
                    type="button" 
                    class="btn btn-outline-secondary"
                    (click)="cancelPayment()"
                    [disabled]="processing">
                    <i class="fas fa-times me-2"></i>
                    Cancel
                  </button>
                  
                  <button 
                    type="submit" 
                    class="btn btn-success btn-lg"
                    [disabled]="paymentForm.invalid || processing || timeRemaining <= 0">
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="processing"></span>
                    <i [class]="getPaymentIcon()" *ngIf="!processing"></i>
                    {{ processing ? 'Processing...' : getPaymentButtonText() }}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <!-- Expired State -->
          <div class="card shadow-sm" *ngIf="timeRemaining <= 0">
            <div class="card-body text-center">
              <i class="fas fa-clock text-danger" style="font-size: 4rem;"></i>
              <h3 class="mt-3">Reservation Expired</h3>
              <p class="text-muted">Your parking slot reservation has expired. Please search for parking again.</p>
              <button class="btn btn-primary" (click)="goBackToSearch()">
                <i class="fas fa-search me-2"></i>
                Search Parking Again
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chunk-item {
      background-color: #f8f9fa;
      border: 1px solid #dee2e6;
      border-radius: 4px;
      padding: 8px 12px;
      margin-bottom: 8px;
      font-size: 0.9rem;
    }

    .selected-chunks {
      max-height: 200px;
      overflow-y: auto;
    }

    .countdown-timer {
      font-size: 1.5rem;
      font-weight: bold;
      color: #dc3545;
    }

    .payment-amount {
      font-size: 2rem;
      font-weight: bold;
      color: #28a745;
    }

    .card {
      border: none;
      border-radius: 12px;
    }

    .card-header {
      border-radius: 12px 12px 0 0 !important;
    }

    .btn {
      border-radius: 8px;
    }

    .form-control {
      border-radius: 8px;
    }

    .alert {
      border-radius: 8px;
    }

    .payment-method-btn {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .payment-method-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .btn-check:checked + .payment-method-btn {
      background-color: #0d6efd;
      border-color: #0d6efd;
      color: white;
      box-shadow: 0 4px 8px rgba(13, 110, 253, 0.3);
    }

    .payment-methods {
      margin-bottom: 1rem;
    }

    .form-control:focus {
      border-color: #0d6efd;
      box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
    }

    select.form-control {
      background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
      background-position: right 0.75rem center;
      background-repeat: no-repeat;
      background-size: 1.5em 1.5em;
      padding-right: 2.5rem;
    }
  `]
})
export class ChunkPaymentPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  paymentForm!: FormGroup;
  paymentSession: PaymentSession | null = null;
  timeRemaining: number = 0;
  processing: boolean = false;
  errorMessage: string = '';
  
  // Payment method properties
  selectedPaymentMethod: PaymentMethod = PaymentMethod.CREDIT_CARD;
  PaymentMethod = PaymentMethod;
  
  // Bank list for net banking
  banks: Bank[] = [
    { code: 'sbi', name: 'State Bank of India' },
    { code: 'hdfc', name: 'HDFC Bank' },
    { code: 'icici', name: 'ICICI Bank' },
    { code: 'axis', name: 'Axis Bank' },
    { code: 'kotak', name: 'Kotak Mahindra Bank' },
    { code: 'pnb', name: 'Punjab National Bank' },
    { code: 'bob', name: 'Bank of Baroda' },
    { code: 'canara', name: 'Canara Bank' },
    { code: 'union', name: 'Union Bank of India' },
    { code: 'indian', name: 'Indian Bank' }
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private bookingService: BookingService,
    private paymentService: PaymentService
  ) {
    this.initializePaymentForm();
  }

  private initializePaymentForm() {
    this.paymentForm = this.fb.group({
      paymentMethod: [PaymentMethod.CREDIT_CARD, [Validators.required]],
      // Card details (Credit/Debit)
      cardNumber: [''],
      expiryDate: [''],
      cvv: [''],
      cardholderName: [''],
      // UPI details
      upiId: [''],
      // Net banking details
      selectedBank: ['']
    });
    
    this.updateFormValidators();
    
    // Listen for payment method changes
    this.paymentForm.get('paymentMethod')?.valueChanges.subscribe((method: PaymentMethod) => {
      this.selectedPaymentMethod = method;
      this.updateFormValidators();
    });
  }

  private updateFormValidators() {
    // Clear all validators first
    Object.keys(this.paymentForm.controls).forEach(key => {
      if (key !== 'paymentMethod') {
        this.paymentForm.get(key)?.clearValidators();
        this.paymentForm.get(key)?.updateValueAndValidity();
      }
    });

    // Add validators based on selected payment method
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.CREDIT_CARD:
      case PaymentMethod.DEBIT_CARD:
        this.paymentForm.get('cardNumber')?.setValidators([
          Validators.required, 
          Validators.pattern(/^\d{4}\s\d{4}\s\d{4}\s\d{4}$/)
        ]);
        this.paymentForm.get('expiryDate')?.setValidators([
          Validators.required, 
          Validators.pattern(/^\d{2}\/\d{2}$/)
        ]);
        this.paymentForm.get('cvv')?.setValidators([
          Validators.required, 
          Validators.pattern(/^\d{3,4}$/)
        ]);
        this.paymentForm.get('cardholderName')?.setValidators([
          Validators.required, 
          Validators.minLength(2)
        ]);
        break;
        
      case PaymentMethod.UPI:
        this.paymentForm.get('upiId')?.setValidators([
          Validators.required,
          Validators.pattern(/^[\w.-]+@[\w.-]+$/)
        ]);
        break;
        
      case PaymentMethod.NET_BANKING:
        this.paymentForm.get('selectedBank')?.setValidators([Validators.required]);
        break;
    }

    // Update validity
    Object.keys(this.paymentForm.controls).forEach(key => {
      this.paymentForm.get(key)?.updateValueAndValidity();
    });
  }

  ngOnInit() {
    this.initializePaymentSession();
    this.startCountdownTimer();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializePaymentSession() {
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
      if (params['sessionId']) {
        this.paymentSession = {
          sessionId: params['sessionId'],
          slotId: params['slotId'] || '',
          slotNumber: params['slotNumber'] || '',
          lotId: params['lotId'] || '',
          lotName: params['lotName'] || '',
          vehicleType: params['vehicleType'] || '',
          vehicleNumber: params['vehicleNumber'] || '',
          selectedChunks: params['chunks'] ? JSON.parse(params['chunks']) : [],
          totalAmount: parseFloat(params['totalAmount']) || 0,
          expiresAt: params['expiresAt'] || ''
        };
        
        console.log('💳 Payment session initialized:', this.paymentSession);
      } else {
        console.error('❌ No session ID found, redirecting to parking search');
        this.router.navigate(['/parking']);
      }
    });
  }

  private startCountdownTimer() {
    interval(1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.paymentSession?.expiresAt) {
          const expiryTime = new Date(this.paymentSession.expiresAt).getTime();
          const currentTime = new Date().getTime();
          this.timeRemaining = Math.max(0, Math.floor((expiryTime - currentTime) / 1000));
          
          if (this.timeRemaining <= 0) {
            console.log('⏰ Payment session expired');
          }
        }
      });
  }

  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  formatChunkTime(dateString: string): string {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  calculateDuration(): number {
    if (!this.paymentSession?.selectedChunks?.length) return 0;
    return this.paymentSession.selectedChunks.length * 0.5; // 30 minutes per chunk
  }

  formatCardNumber(event: any) {
    let value = event.target.value.replace(/\s/g, '').replace(/\D/g, '');
    value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
    event.target.value = value;
    this.paymentForm.get('cardNumber')?.setValue(value);
  }

  formatExpiryDate(event: any) {
    let value = event.target.value.replace(/\D/g, '');
    if (value.length >= 2) {
      value = value.substring(0, 2) + '/' + value.substring(2, 4);
    }
    event.target.value = value;
    this.paymentForm.get('expiryDate')?.setValue(value);
  }

  async processPayment() {
    if (this.paymentForm.invalid || !this.paymentSession || this.timeRemaining <= 0) {
      return;
    }

    this.processing = true;
    this.errorMessage = '';

    try {
      console.log(`💳 Processing ${this.selectedPaymentMethod} payment for session:`, this.paymentSession.sessionId);

      // Simulate different payment processing times and methods
      const processingTime = this.getProcessingTime();
      const paymentData = this.getPaymentData();
      
      console.log('Payment data:', paymentData);
      
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, processingTime));
      
      // Simulate payment gateway response
      const paymentSuccess = Math.random() > 0.1; // 90% success rate for demo
      
      if (!paymentSuccess) {
        throw new Error(`${this.selectedPaymentMethod} payment failed. Please try again.`);
      }

      console.log(`✅ ${this.selectedPaymentMethod} payment successful`);

      // Confirm booking with backend
      const confirmation = await this.bookingService.confirmChunkBooking(
        this.paymentSession.sessionId,
        this.paymentSession.vehicleNumber
      ).toPromise();

      if (confirmation.success) {
        console.log('✅ Booking confirmed');
        
        // Navigate to success page
        this.router.navigate(['/bookings'], {
          queryParams: {
            success: 'true',
            bookingId: confirmation.booking_id,
            paymentMethod: this.selectedPaymentMethod,
            message: `Payment successful via ${this.getPaymentMethodName()}! Your parking slot has been booked.`
          }
        });
      } else {
        throw new Error(confirmation.error || 'Payment confirmation failed');
      }

    } catch (error: any) {
      console.error('❌ Payment failed:', error);
      this.errorMessage = error.message || 'Payment processing failed. Please try again.';
    } finally {
      this.processing = false;
    }
  }

  private getProcessingTime(): number {
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.UPI:
        return 1500; // Faster for UPI
      case PaymentMethod.CREDIT_CARD:
      case PaymentMethod.DEBIT_CARD:
        return 2500; // Standard card processing
      case PaymentMethod.NET_BANKING:
        return 3000; // Slower for net banking
      default:
        return 2000;
    }
  }

  private getPaymentData(): any {
    const formValue = this.paymentForm.value;
    
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.CREDIT_CARD:
      case PaymentMethod.DEBIT_CARD:
        return {
          method: this.selectedPaymentMethod,
          cardNumber: formValue.cardNumber?.replace(/\s/g, ''),
          cardholderName: formValue.cardholderName,
          expiryDate: formValue.expiryDate,
          amount: this.paymentSession?.totalAmount
        };
        
      case PaymentMethod.UPI:
        return {
          method: this.selectedPaymentMethod,
          upiId: formValue.upiId,
          amount: this.paymentSession?.totalAmount
        };
        
      case PaymentMethod.NET_BANKING:
        return {
          method: this.selectedPaymentMethod,
          bankCode: formValue.selectedBank,
          bankName: this.banks.find(b => b.code === formValue.selectedBank)?.name,
          amount: this.paymentSession?.totalAmount
        };
        
      default:
        return { method: this.selectedPaymentMethod };
    }
  }

  private getPaymentMethodName(): string {
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.CREDIT_CARD:
        return 'Credit Card';
      case PaymentMethod.DEBIT_CARD:
        return 'Debit Card';
      case PaymentMethod.UPI:
        return 'UPI';
      case PaymentMethod.NET_BANKING:
        return 'Net Banking';
      default:
        return 'Payment Gateway';
    }
  }

  async cancelPayment() {
    if (!this.paymentSession) return;

    try {
      console.log('❌ Cancelling payment session:', this.paymentSession.sessionId);
      
      await this.bookingService.cancelChunkReservation(this.paymentSession.sessionId).toPromise();
      
      this.router.navigate(['/parking'], {
        queryParams: {
          message: 'Payment cancelled. Your reservation has been released.'
        }
      });
    } catch (error) {
      console.error('Error cancelling reservation:', error);
      // Navigate anyway
      this.router.navigate(['/parking']);
    }
  }

  goBackToSearch() {
    this.router.navigate(['/parking']);
  }

  getPaymentIcon(): string {
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.CREDIT_CARD:
      case PaymentMethod.DEBIT_CARD:
        return 'fas fa-credit-card me-2';
      case PaymentMethod.UPI:
        return 'fas fa-mobile-alt me-2';
      case PaymentMethod.NET_BANKING:
        return 'fas fa-university me-2';
      default:
        return 'fas fa-credit-card me-2';
    }
  }

  getPaymentButtonText(): string {
    switch (this.selectedPaymentMethod) {
      case PaymentMethod.CREDIT_CARD:
        return 'Pay with Credit Card';
      case PaymentMethod.DEBIT_CARD:
        return 'Pay with Debit Card';
      case PaymentMethod.UPI:
        return 'Pay with UPI';
      case PaymentMethod.NET_BANKING:
        return 'Pay with Net Banking';
      default:
        return 'Complete Payment';
    }
  }
}
