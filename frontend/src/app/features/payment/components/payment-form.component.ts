import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { PaymentService } from '../services/payment.service';

export interface PaymentMethod {
  value: string;
  name: string;
  description: string;
  icon: string;
  fields: string[];
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

@Component({
  selector: 'app-payment-form',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="payment-form">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-credit-card me-2"></i>
            Payment Details
          </h5>
        </div>
        <div class="card-body">
          <!-- Booking Summary -->
          <div class="alert alert-info mb-4">
            <h6><i class="fas fa-info-circle me-2"></i>Booking Summary</h6>
            <div class="row">
              <div class="col-md-6">
                <small class="text-muted">Booking Reference:</small><br>
                <strong>{{ bookingReference }}</strong>
              </div>
              <div class="col-md-6">
                <small class="text-muted">Total Amount:</small><br>
                <strong class="text-success">₹{{ amount | number:'1.2-2' }}</strong>
              </div>
            </div>
          </div>

          <!-- Payment Methods -->
          <div class="mb-4">
            <h6>Select Payment Method</h6>
            <div class="row">
              <div class="col-md-6 mb-3" *ngFor="let method of paymentMethods">
                <div class="card payment-method-card" 
                     [class.selected]="selectedMethod === method.value"
                     (click)="selectPaymentMethod(method.value)">
                  <div class="card-body text-center p-3">
                    <i class="fas fa-{{ method.icon }} fa-2x mb-2"></i>
                    <h6 class="mb-1">{{ method.name }}</h6>
                    <small class="text-muted">{{ method.description }}</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Payment Form -->
          <form [formGroup]="paymentForm" (ngSubmit)="onSubmit()" *ngIf="selectedMethod">
            <!-- Credit/Debit Card -->
            <div *ngIf="selectedMethod === 'credit_card' || selectedMethod === 'debit_card'">
              <div class="row">
                <div class="col-md-8 mb-3">
                  <label class="form-label">Card Number</label>
                  <input
                    type="text"
                    class="form-control"
                    formControlName="card_number"
                    placeholder="1234 5678 9012 3456"
                    maxlength="19"
                    [class.is-invalid]="isFieldInvalid('card_number')"
                    (input)="formatCardNumber($event)"
                  >
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('card_number')">
                    Please enter a valid card number
                  </div>
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">CVV</label>
                  <input
                    type="text"
                    class="form-control"
                    formControlName="cvv"
                    placeholder="123"
                    maxlength="4"
                    [class.is-invalid]="isFieldInvalid('cvv')"
                  >
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('cvv')">
                    Required
                  </div>
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Card Holder Name</label>
                  <input
                    type="text"
                    class="form-control"
                    formControlName="card_holder_name"
                    placeholder="John Doe"
                    [class.is-invalid]="isFieldInvalid('card_holder_name')"
                  >
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('card_holder_name')">
                    Card holder name is required
                  </div>
                </div>
                <div class="col-md-3 mb-3">
                  <label class="form-label">Expiry Month</label>
                  <select class="form-control" formControlName="expiry_month" [class.is-invalid]="isFieldInvalid('expiry_month')">
                    <option value="">MM</option>
                    <option *ngFor="let month of months" [value]="month.value">{{ month.label }}</option>
                  </select>
                </div>
                <div class="col-md-3 mb-3">
                  <label class="form-label">Expiry Year</label>
                  <select class="form-control" formControlName="expiry_year" [class.is-invalid]="isFieldInvalid('expiry_year')">
                    <option value="">YYYY</option>
                    <option *ngFor="let year of years" [value]="year">{{ year }}</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- UPI -->
            <div *ngIf="selectedMethod === 'upi'">
              <div class="mb-3">
                <label class="form-label">UPI ID</label>
                <input
                  type="text"
                  class="form-control"
                  formControlName="upi_id"
                  placeholder="yourname@paytm"
                  [class.is-invalid]="isFieldInvalid('upi_id')"
                >
                <div class="invalid-feedback" *ngIf="isFieldInvalid('upi_id')">
                  Please enter a valid UPI ID
                </div>
              </div>
            </div>

            <!-- Net Banking -->
            <div *ngIf="selectedMethod === 'net_banking'">
              <div class="mb-3">
                <label class="form-label">Select Bank</label>
                <select class="form-control" formControlName="bank_name" [class.is-invalid]="isFieldInvalid('bank_name')">
                  <option value="">Choose your bank</option>
                  <option value="sbi">State Bank of India</option>
                  <option value="hdfc">HDFC Bank</option>
                  <option value="icici">ICICI Bank</option>
                  <option value="axis">Axis Bank</option>
                  <option value="pnb">Punjab National Bank</option>
                  <option value="other">Other</option>
                </select>
                <div class="invalid-feedback" *ngIf="isFieldInvalid('bank_name')">
                  Please select your bank
                </div>
              </div>
            </div>

            <!-- Test Mode Options -->
            <div class="alert alert-warning mb-3">
              <i class="fas fa-info-circle me-2"></i>
              <strong>Demo Mode:</strong> This is a demonstration payment system. No real payment will be processed.
              <div class="form-check mt-2">
                <input
                  class="form-check-input"
                  type="checkbox"
                  formControlName="simulate_failure"
                  id="simulateFailure"
                >
                <label class="form-check-label" for="simulateFailure">
                  Simulate payment failure (for testing)
                </label>
              </div>
            </div>

            <!-- Error Message -->
            <div class="alert alert-danger" *ngIf="errorMessage">
              <i class="fas fa-exclamation-triangle me-2"></i>
              {{ errorMessage }}
            </div>

            <!-- Submit Button -->
            <div class="d-grid gap-2">
              <button
                type="submit"
                class="btn btn-success btn-lg"
                [disabled]="paymentForm.invalid || processing"
              >
                <span class="spinner-border spinner-border-sm me-2" *ngIf="processing"></span>
                <i class="fas fa-lock me-2" *ngIf="!processing"></i>
                {{ processing ? 'Processing Payment...' : 'Pay ₹' + (amount | number:'1.2-2') }}
              </button>
              <button type="button" class="btn btn-outline-secondary" (click)="onCancel()" [disabled]="processing">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .payment-method-card {
      cursor: pointer;
      transition: all 0.3s ease;
      border: 2px solid transparent;
    }

    .payment-method-card:hover {
      border-color: #007bff;
      box-shadow: 0 4px 8px rgba(0,123,255,0.3);
    }

    .payment-method-card.selected {
      border-color: #28a745;
      background-color: #f8fff9;
    }

    .payment-form {
      max-width: 600px;
      margin: 0 auto;
    }

    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .form-control:focus {
      border-color: #28a745;
      box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
    }
  `]
})
export class PaymentFormComponent implements OnInit, OnDestroy {
  @Input() bookingId: string = '';
  @Input() bookingReference: string = '';
  @Input() amount: number = 0;
  @Output() paymentSuccess = new EventEmitter<PaymentResult>();
  @Output() paymentCancel = new EventEmitter<void>();

  paymentForm: FormGroup;
  paymentMethods: PaymentMethod[] = [];
  selectedMethod: string = '';
  processing = false;
  errorMessage = '';

  months = [
    { value: '01', label: '01 - January' },
    { value: '02', label: '02 - February' },
    { value: '03', label: '03 - March' },
    { value: '04', label: '04 - April' },
    { value: '05', label: '05 - May' },
    { value: '06', label: '06 - June' },
    { value: '07', label: '07 - July' },
    { value: '08', label: '08 - August' },
    { value: '09', label: '09 - September' },
    { value: '10', label: '10 - October' },
    { value: '11', label: '11 - November' },
    { value: '12', label: '12 - December' }
  ];

  years: number[] = [];

  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private paymentService: PaymentService
  ) {
    this.paymentForm = this.createPaymentForm();
    this.generateYears();
  }

  ngOnInit(): void {
    this.loadPaymentMethods();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createPaymentForm(): FormGroup {
    return this.fb.group({
      // Card details
      card_number: [''],
      card_holder_name: [''],
      expiry_month: [''],
      expiry_year: [''],
      cvv: [''],
      // UPI
      upi_id: [''],
      // Net banking
      bank_name: [''],
      // Test options
      simulate_failure: [false]
    });
  }

  private generateYears(): void {
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 10; i++) {
      this.years.push(currentYear + i);
    }
  }

  private loadPaymentMethods(): void {
    this.paymentService.getPaymentMethods()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.paymentMethods = Object.entries(response.payment_methods).map(([key, value]: [string, any]) => ({
            value: key,
            name: value.name,
            description: value.description,
            icon: value.icon,
            fields: value.fields
          }));
        },
        error: (error) => {
          console.error('Error loading payment methods:', error);
          // Fallback payment methods
          this.paymentMethods = [
            { value: 'credit_card', name: 'Credit Card', description: 'Visa, MasterCard', icon: 'credit-card', fields: [] },
            { value: 'upi', name: 'UPI', description: 'Google Pay, PhonePe', icon: 'mobile-alt', fields: [] }
          ];
        }
      });
  }

  selectPaymentMethod(method: string): void {
    this.selectedMethod = method;
    this.errorMessage = '';
    this.updateFormValidators();
  }

  private updateFormValidators(): void {
    // Clear all validators first
    Object.keys(this.paymentForm.controls).forEach(key => {
      this.paymentForm.get(key)?.clearValidators();
      this.paymentForm.get(key)?.updateValueAndValidity();
    });

    // Add validators based on selected payment method
    if (this.selectedMethod === 'credit_card' || this.selectedMethod === 'debit_card') {
      this.paymentForm.get('card_number')?.setValidators([Validators.required, Validators.minLength(16)]);
      this.paymentForm.get('card_holder_name')?.setValidators([Validators.required]);
      this.paymentForm.get('expiry_month')?.setValidators([Validators.required]);
      this.paymentForm.get('expiry_year')?.setValidators([Validators.required]);
      this.paymentForm.get('cvv')?.setValidators([Validators.required, Validators.minLength(3)]);
    } else if (this.selectedMethod === 'upi') {
      this.paymentForm.get('upi_id')?.setValidators([Validators.required, Validators.pattern(/^[\w.-]+@[\w.-]+$/)]);
    } else if (this.selectedMethod === 'net_banking') {
      this.paymentForm.get('bank_name')?.setValidators([Validators.required]);
    }

    // Update validity
    Object.keys(this.paymentForm.controls).forEach(key => {
      this.paymentForm.get(key)?.updateValueAndValidity();
    });
  }

  formatCardNumber(event: any): void {
    let value = event.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
    event.target.value = value;
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.paymentForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  onSubmit(): void {
    if (this.paymentForm.valid && this.selectedMethod) {
      this.processing = true;
      this.errorMessage = '';

      const paymentRequest: PaymentRequest = {
        booking_id: this.bookingId,
        payment_method: this.selectedMethod,
        simulate_failure: this.paymentForm.get('simulate_failure')?.value || false
      };

      this.paymentService.processPayment(paymentRequest)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (result) => {
            this.processing = false;
            if (result.success) {
              this.paymentSuccess.emit(result);
            } else {
              this.errorMessage = result.message;
            }
          },
          error: (error) => {
            this.processing = false;
            this.errorMessage = error.message || 'Payment processing failed. Please try again.';
          }
        });
    }
  }

  onCancel(): void {
    this.paymentCancel.emit();
  }
}
