import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { AdminService } from '../services/admin.service';

interface PricingRule {
  id: string;
  name: string;
  vehicle_type: string;
  rule_type: string;
  start_time?: string;
  end_time?: string;
  multiplier: number;
  price_per_hour: number;
  priority: number;
  is_active: boolean;
  lot_name?: string;
}

@Component({
  selector: 'app-admin-pricing-rules',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  template: `
    <div class="container-fluid mt-4">
      <div class="row">
        <div class="col-12">
          <h1 class="h3 mb-4">
            <i class="fas fa-tags me-2"></i>
            Dynamic Pricing Rules Management
          </h1>
        </div>
      </div>

      <!-- Add New Rule -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-plus me-2"></i>
                Add New Pricing Rule
              </h5>
            </div>
            <div class="card-body">
              <form [formGroup]="ruleForm" (ngSubmit)="addRule()">
                <div class="row">
                  <div class="col-md-3 mb-3">
                    <label for="lotId" class="form-label">Parking Lot</label>
                    <select class="form-select" formControlName="lot_id" required>
                      <option value="">Select lot</option>
                      <option value="19ebc361-a7ac-42ab-9713-e4edd693335d">Airport Long-Term Parking</option>
                      <option value="other-lot-id">Downtown Plaza</option>
                    </select>
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="vehicleType" class="form-label">Vehicle</label>
                    <select class="form-select" formControlName="vehicle_type" required>
                      <option value="">Select</option>
                      <option value="car">Car</option>
                      <option value="bike">Bike</option>
                    </select>
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="ruleType" class="form-label">Rule Type</label>
                    <select class="form-select" formControlName="rule_type" required>
                      <option value="">Select</option>
                      <option value="time_based">Time Based</option>
                      <option value="day_based">Day Based</option>
                    </select>
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="startTime" class="form-label">Start Time</label>
                    <input type="time" class="form-control" formControlName="start_time">
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="endTime" class="form-label">End Time</label>
                    <input type="time" class="form-control" formControlName="end_time">
                  </div>
                  <div class="col-md-1 mb-3">
                    <label for="multiplier" class="form-label">Multiplier</label>
                    <input type="number" class="form-control" formControlName="multiplier" step="0.1" min="0.1" max="3.0" required>
                  </div>
                </div>
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <label for="ruleName" class="form-label">Rule Name</label>
                    <input type="text" class="form-control" formControlName="name" placeholder="e.g., Peak Hours - Car" required>
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="priority" class="form-label">Priority</label>
                    <select class="form-select" formControlName="priority" required>
                      <option value="1">High (1)</option>
                      <option value="2">Medium (2)</option>
                      <option value="3">Low (3)</option>
                    </select>
                  </div>
                  <div class="col-md-2 mb-3">
                    <label for="pricePerHour" class="form-label">Base Rate</label>
                    <input type="number" class="form-control" formControlName="price_per_hour" step="0.5" min="1" required>
                  </div>
                  <div class="col-md-2 mb-3 d-flex align-items-end">
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" formControlName="is_active" checked>
                      <label class="form-check-label">Active</label>
                    </div>
                  </div>
                  <div class="col-md-2 mb-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100" [disabled]="ruleForm.invalid || adding">
                      <span class="spinner-border spinner-border-sm me-1" *ngIf="adding"></span>
                      Add Rule
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Existing Rules -->
      <div class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between">
              <h5 class="mb-0">
                <i class="fas fa-list me-2"></i>
                Current Pricing Rules
              </h5>
              <button class="btn btn-sm btn-outline-primary" (click)="loadRules()">
                <i class="fas fa-sync me-1"></i>
                Refresh
              </button>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>Rule Name</th>
                      <th>Lot</th>
                      <th>Vehicle</th>
                      <th>Time Period</th>
                      <th>Multiplier</th>
                      <th>Base Rate</th>
                      <th>Effective Rate</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let rule of pricingRules">
                      <td><strong>{{ rule.name }}</strong></td>
                      <td>{{ rule.lot_name || 'N/A' }}</td>
                      <td>
                        <span class="badge bg-primary">{{ rule.vehicle_type | titlecase }}</span>
                      </td>
                      <td>
                        <span *ngIf="rule.start_time && rule.end_time">
                          {{ rule.start_time }} - {{ rule.end_time }}
                        </span>
                        <span *ngIf="!rule.start_time" class="text-muted">All Day</span>
                      </td>
                      <td>
                        <span class="badge" 
                              [class.bg-success]="rule.multiplier < 1"
                              [class.bg-warning]="rule.multiplier >= 1 && rule.multiplier <= 1.5"
                              [class.bg-danger]="rule.multiplier > 1.5">
                          {{ rule.multiplier }}x
                        </span>
                      </td>
                      <td>\${{ rule.price_per_hour }}</td>
                      <td><strong>\${{ (rule.price_per_hour * rule.multiplier).toFixed(2) }}</strong></td>
                      <td>{{ rule.priority }}</td>
                      <td>
                        <span class="badge" 
                              [class.bg-success]="rule.is_active"
                              [class.bg-secondary]="!rule.is_active">
                          {{ rule.is_active ? 'Active' : 'Inactive' }}
                        </span>
                      </td>
                      <td>
                        <button class="btn btn-sm btn-outline-danger" (click)="deleteRule(rule.id)">
                          <i class="fas fa-trash"></i>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AdminPricingRulesComponent implements OnInit, OnDestroy {
  ruleForm: FormGroup;
  pricingRules: PricingRule[] = [];
  adding = false;
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private adminService: AdminService
  ) {
    this.ruleForm = this.fb.group({
      lot_id: ['', Validators.required],
      name: ['', Validators.required],
      vehicle_type: ['', Validators.required],
      rule_type: ['time_based', Validators.required],
      start_time: ['18:00'],
      end_time: ['22:00'],
      multiplier: [1.5, [Validators.required, Validators.min(0.1), Validators.max(3.0)]],
      price_per_hour: [5.0, [Validators.required, Validators.min(1)]],
      priority: [1, Validators.required],
      is_active: [true]
    });
  }

  ngOnInit(): void {
    this.loadRules();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadRules(): void {
    // Demo data - replace with actual API call when backend endpoint is ready
    this.pricingRules = [
      {
        id: '1',
        name: 'Peak Hours - Car',
        vehicle_type: 'car',
        rule_type: 'time_based',
        start_time: '18:00',
        end_time: '22:00',
        multiplier: 1.5,
        price_per_hour: 5.0,
        priority: 1,
        is_active: true,
        lot_name: 'Airport Long-Term Parking'
      },
      {
        id: '2',
        name: 'Early Bird - Car',
        vehicle_type: 'car',
        rule_type: 'time_based',
        start_time: '06:00',
        end_time: '09:00',
        multiplier: 0.8,
        price_per_hour: 5.0,
        priority: 2,
        is_active: true,
        lot_name: 'Airport Long-Term Parking'
      }
    ];
  }

  addRule(): void {
    if (this.ruleForm.valid) {
      this.adding = true;
      
      const newRule: PricingRule = {
        id: Date.now().toString(),
        ...this.ruleForm.value,
        lot_name: this.getLotName(this.ruleForm.value.lot_id)
      };
      
      this.pricingRules.unshift(newRule);
      this.ruleForm.reset();
      this.ruleForm.patchValue({
        rule_type: 'time_based',
        start_time: '18:00',
        end_time: '22:00',
        multiplier: 1.5,
        price_per_hour: 5.0,
        priority: 1,
        is_active: true
      });
      
      this.adding = false;
      console.log('Pricing rule added successfully');
    }
  }

  deleteRule(ruleId: string): void {
    if (confirm('Are you sure you want to delete this pricing rule?')) {
      this.pricingRules = this.pricingRules.filter(rule => rule.id !== ruleId);
      console.log('Pricing rule deleted');
    }
  }

  private getLotName(lotId: string): string {
    const lotNames: { [key: string]: string } = {
      '19ebc361-a7ac-42ab-9713-e4edd693335d': 'Airport Long-Term Parking',
      'other-lot-id': 'Downtown Plaza'
    };
    return lotNames[lotId] || 'Unknown Lot';
  }
}
