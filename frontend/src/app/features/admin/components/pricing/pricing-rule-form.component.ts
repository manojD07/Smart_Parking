import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';

// Services
import { PricingRuleService, PricingRule, PricingRuleCreate, PricingRuleUpdate } from '../../../../core/services/pricing-rule.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-pricing-rule-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <!-- Pricing Rule Form Modal -->
    <div class="modal fade" id="pricingRuleModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas" [class]="isEditMode ? 'fa-edit' : 'fa-plus'"></i>
              {{ isEditMode ? 'Edit' : 'Create' }} Pricing Rule
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          
          <form [formGroup]="ruleForm" (ngSubmit)="onSubmit()">
            <div class="modal-body">
              <!-- Basic Information -->
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-tag me-2"></i>Rule Name *
                  </label>
                  <input 
                    type="text" 
                    class="form-control"
                    formControlName="name"
                    placeholder="e.g., Peak Hours - Car">
                  <div class="form-text">Descriptive name for this pricing rule</div>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-car me-2"></i>Vehicle Type *
                  </label>
                  <select class="form-select" formControlName="vehicle_type">
                    <option value="">Select vehicle type</option>
                    <option value="car">🚗 Car</option>
                    <option value="bike">🏍️ Bike</option>
                  </select>
                </div>
              </div>

              <!-- Rule Type and Priority -->
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-cogs me-2"></i>Rule Type *
                  </label>
                  <select class="form-select" formControlName="rule_type" (change)="onRuleTypeChange()">
                    <option value="">Select rule type</option>
                    <option value="time_based">⏰ Time Based</option>
                    <option value="day_based">📅 Day Based</option>
                    <option value="seasonal">🌟 Seasonal</option>
                    <option value="demand_based">📈 Demand Based</option>
                  </select>
                  <div class="form-text">{{ getRuleTypeDescription() }}</div>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-exclamation me-2"></i>Priority
                  </label>
                  <select class="form-select" formControlName="priority">
                    <option value="normal">🔹 Normal</option>
                    <option value="high">⭐ High</option>
                    <option value="low">🔸 Low</option>
                  </select>
                  <div class="form-text">Higher priority rules override lower priority ones</div>
                </div>
              </div>

              <!-- Pricing Information -->
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-dollar-sign me-2"></i>Price per Hour *
                  </label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input 
                      type="number" 
                      class="form-control"
                      formControlName="price_per_hour"
                      placeholder="10.00"
                      min="0"
                      step="0.01"
                      (input)="calculateEffectivePrice()">
                  </div>
                </div>
                
                <div class="col-md-4">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-times me-2"></i>Multiplier
                  </label>
                  <input 
                    type="number" 
                    class="form-control"
                    formControlName="multiplier"
                    placeholder="1.0"
                    min="0.1"
                    max="10"
                    step="0.1"
                    (input)="calculateEffectivePrice()">
                  <div class="form-text">1.0 = normal, 1.5 = 50% increase</div>
                </div>
                
                <div class="col-md-4">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-calculator me-2"></i>Effective Price
                  </label>
                  <div class="form-control-plaintext fw-bold text-success">
                    $ {{ effectivePrice.toFixed(2) }}/hr
                  </div>
                  <div class="form-text">Final price customers pay</div>
                </div>
              </div>

              <!-- Time Range (Time-based rules) -->
              <div *ngIf="selectedRuleType === 'time_based'" class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-clock me-2"></i>Start Time *
                  </label>
                  <input 
                    type="time" 
                    class="form-control"
                    formControlName="start_time">
                </div>
                
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-clock me-2"></i>End Time *
                  </label>
                  <input 
                    type="time" 
                    class="form-control"
                    formControlName="end_time">
                </div>
              </div>

              <!-- Days Selection (Day-based rules) -->
              <div *ngIf="selectedRuleType === 'day_based'" class="mb-3">
                <label class="form-label fw-semibold">
                  <i class="fas fa-calendar me-2"></i>Days of Week *
                </label>
                <div class="row">
                  <div class="col-md-6">
                    <div class="form-check" *ngFor="let day of weekdays.slice(0, 4)">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        [id]="day.value"
                        [value]="day.value"
                        (change)="onDayChange($event)">
                      <label class="form-check-label" [for]="day.value">
                        {{ day.label }}
                      </label>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="form-check" *ngFor="let day of weekdays.slice(4)">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        [id]="day.value"
                        [value]="day.value"
                        (change)="onDayChange($event)">
                      <label class="form-check-label" [for]="day.value">
                        {{ day.label }}
                      </label>
                    </div>
                  </div>
                </div>
                <div class="form-text">Select the days when this rule applies</div>
                
                <!-- Quick Day Presets -->
                <div class="mt-2">
                  <button type="button" class="btn btn-outline-secondary btn-sm me-2" (click)="selectWeekdays()">
                    Weekdays
                  </button>
                  <button type="button" class="btn btn-outline-secondary btn-sm me-2" (click)="selectWeekends()">
                    Weekends
                  </button>
                  <button type="button" class="btn btn-outline-secondary btn-sm" (click)="selectAllDays()">
                    All Days
                  </button>
                </div>
              </div>

              <!-- Min/Max Charges (Optional) -->
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-arrow-down me-2"></i>Minimum Charge
                  </label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input 
                      type="number" 
                      class="form-control"
                      formControlName="min_charge"
                      placeholder="5.00"
                      min="0"
                      step="0.01">
                  </div>
                  <div class="form-text">Optional minimum charge amount</div>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label fw-semibold">
                    <i class="fas fa-arrow-up me-2"></i>Maximum Charge
                  </label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input 
                      type="number" 
                      class="form-control"
                      formControlName="max_charge"
                      placeholder="100.00"
                      min="0"
                      step="0.01">
                  </div>
                  <div class="form-text">Optional maximum charge cap</div>
                </div>
              </div>

              <!-- Preview Section -->
              <div *ngIf="effectivePrice > 0" class="alert alert-info">
                <h6 class="alert-heading">
                  <i class="fas fa-eye me-2"></i>Preview
                </h6>
                <div class="row">
                  <div class="col-md-6">
                    <strong>Effective Rate:</strong> $ {{ effectivePrice.toFixed(2) }}/hour
                  </div>
                  <div class="col-md-6">
                    <strong>2-hour parking:</strong> $ {{ (effectivePrice * 2).toFixed(2) }}
                  </div>
                </div>
                <div class="mt-2" *ngIf="selectedRuleType">
                  <strong>Applies to:</strong> 
                  {{ getApplicabilityDescription() }}
                </div>
              </div>

              <!-- Validation Errors -->
              <div *ngIf="ruleForm.invalid && (ruleForm.dirty || ruleForm.touched)" class="alert alert-warning">
                <h6 class="alert-heading">
                  <i class="fas fa-exclamation-triangle me-2"></i>Please fix the following:
                </h6>
                <ul class="mb-0">
                  <li *ngIf="ruleForm.get('name')?.errors?.['required']">Rule name is required</li>
                  <li *ngIf="ruleForm.get('vehicle_type')?.errors?.['required']">Vehicle type is required</li>
                  <li *ngIf="ruleForm.get('rule_type')?.errors?.['required']">Rule type is required</li>
                  <li *ngIf="ruleForm.get('price_per_hour')?.errors?.['required']">Price per hour is required</li>
                  <li *ngIf="ruleForm.get('price_per_hour')?.errors?.['min']">Price must be greater than 0</li>
                  <li *ngIf="ruleForm.get('start_time')?.errors?.['required'] && selectedRuleType === 'time_based'">Start time is required for time-based rules</li>
                  <li *ngIf="ruleForm.get('end_time')?.errors?.['required'] && selectedRuleType === 'time_based'">End time is required for time-based rules</li>
                  <li *ngIf="selectedDays.length === 0 && selectedRuleType === 'day_based'">At least one day must be selected for day-based rules</li>
                </ul>
              </div>
            </div>
            
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                [disabled]="ruleForm.invalid || saving || !isFormValid()">
                <span *ngIf="saving" class="spinner-border spinner-border-sm me-2" role="status"></span>
                <i *ngIf="!saving" class="fas" [class]="isEditMode ? 'fa-save' : 'fa-plus'"></i>
                {{ isEditMode ? 'Update' : 'Create' }} Rule
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .form-label {
      margin-bottom: 0.5rem;
    }

    .form-text {
      font-size: 0.875rem;
      color: #6c757d;
    }

    .alert-info {
      background-color: #e3f2fd;
      border-color: #2196f3;
      color: #1976d2;
    }

    .alert-warning {
      background-color: #fff3cd;
      border-color: #ffc107;
      color: #856404;
    }

    .form-check {
      margin-bottom: 0.5rem;
    }

    .btn-group .btn {
      border-radius: 6px;
      margin-right: 0.5rem;
    }

    .input-group-text {
      background-color: #f8f9fa;
      border-color: #ced4da;
    }

    .modal-content {
      border-radius: 12px;
      border: none;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .modal-header {
      border-bottom: 1px solid #dee2e6;
      background-color: #f8f9fa;
    }

    .modal-footer {
      border-top: 1px solid #dee2e6;
    }

    @media (max-width: 768px) {
      .modal-lg {
        max-width: 100vw;
        margin: 0.5rem;
      }
    }
  `]
})
export class PricingRuleFormComponent implements OnInit, OnChanges {
  @Input() lotId: string = '';
  @Input() editRule: PricingRule | null = null;
  @Output() ruleCreated = new EventEmitter<PricingRule>();
  @Output() ruleUpdated = new EventEmitter<PricingRule>();

  // Form
  ruleForm: FormGroup;
  
  // UI State
  saving = false;
  isEditMode = false;
  selectedRuleType = '';
  selectedDays: string[] = [];
  effectivePrice = 0;

  // Constants
  weekdays = [
    { value: 'monday', label: 'Monday' },
    { value: 'tuesday', label: 'Tuesday' },
    { value: 'wednesday', label: 'Wednesday' },
    { value: 'thursday', label: 'Thursday' },
    { value: 'friday', label: 'Friday' },
    { value: 'saturday', label: 'Saturday' },
    { value: 'sunday', label: 'Sunday' }
  ];

  constructor(
    private fb: FormBuilder,
    private pricingRuleService: PricingRuleService,
    private toastService: ToastService
  ) {
    this.ruleForm = this.createForm();
  }

  ngOnInit(): void {
    this.setupFormSubscriptions();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['editRule']) {
      this.isEditMode = !!this.editRule;
      if (this.editRule) {
        this.populateForm(this.editRule);
      } else {
        this.resetForm();
      }
    }
  }

  private createForm(): FormGroup {
    return this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      vehicle_type: ['', Validators.required],
      rule_type: ['', Validators.required],
      price_per_hour: [0, [Validators.required, Validators.min(0.01)]],
      multiplier: [1.0, [Validators.required, Validators.min(0.1), Validators.max(10)]],
      start_time: [''],
      end_time: [''],
      min_charge: [null, Validators.min(0)],
      max_charge: [null, Validators.min(0)],
      priority: ['normal']
    });
  }

  private setupFormSubscriptions(): void {
    // Watch for rule type changes
    this.ruleForm.get('rule_type')?.valueChanges.subscribe(value => {
      this.selectedRuleType = value;
      this.updateValidators();
    });

    // Watch for price changes
    this.ruleForm.get('price_per_hour')?.valueChanges.subscribe(() => this.calculateEffectivePrice());
    this.ruleForm.get('multiplier')?.valueChanges.subscribe(() => this.calculateEffectivePrice());
  }

  private updateValidators(): void {
    const startTimeControl = this.ruleForm.get('start_time');
    const endTimeControl = this.ruleForm.get('end_time');

    if (this.selectedRuleType === 'time_based') {
      startTimeControl?.setValidators([Validators.required]);
      endTimeControl?.setValidators([Validators.required]);
    } else {
      startTimeControl?.clearValidators();
      endTimeControl?.clearValidators();
    }

    startTimeControl?.updateValueAndValidity();
    endTimeControl?.updateValueAndValidity();
  }

  private populateForm(rule: PricingRule): void {
    this.selectedRuleType = rule.rule_type;
    this.selectedDays = rule.days_list || [];
    
    this.ruleForm.patchValue({
      name: rule.name,
      vehicle_type: rule.vehicle_type,
      rule_type: rule.rule_type,
      price_per_hour: rule.price_per_hour,
      multiplier: rule.multiplier,
      start_time: rule.start_time?.slice(0, 5), // Convert to HH:MM format
      end_time: rule.end_time?.slice(0, 5),
      min_charge: rule.min_charge,
      max_charge: rule.max_charge,
      priority: rule.priority
    });

    // Set selected days checkboxes
    this.updateDayCheckboxes();
    this.calculateEffectivePrice();
  }

  private resetForm(): void {
    this.ruleForm.reset({
      multiplier: 1.0,
      priority: 'normal'
    });
    this.selectedRuleType = '';
    this.selectedDays = [];
    this.effectivePrice = 0;
  }

  onRuleTypeChange(): void {
    this.selectedRuleType = this.ruleForm.get('rule_type')?.value || '';
    this.updateValidators();
  }

  onDayChange(event: any): void {
    const day = event.target.value;
    if (event.target.checked) {
      if (!this.selectedDays.includes(day)) {
        this.selectedDays.push(day);
      }
    } else {
      this.selectedDays = this.selectedDays.filter(d => d !== day);
    }
  }

  selectWeekdays(): void {
    this.selectedDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    this.updateDayCheckboxes();
  }

  selectWeekends(): void {
    this.selectedDays = ['saturday', 'sunday'];
    this.updateDayCheckboxes();
  }

  selectAllDays(): void {
    this.selectedDays = this.weekdays.map(d => d.value);
    this.updateDayCheckboxes();
  }

  private updateDayCheckboxes(): void {
    this.weekdays.forEach(day => {
      const checkbox = document.getElementById(day.value) as HTMLInputElement;
      if (checkbox) {
        checkbox.checked = this.selectedDays.includes(day.value);
      }
    });
  }

  calculateEffectivePrice(): void {
    const price = this.ruleForm.get('price_per_hour')?.value || 0;
    const multiplier = this.ruleForm.get('multiplier')?.value || 1;
    this.effectivePrice = price * multiplier;
  }

  isFormValid(): boolean {
    if (this.ruleForm.invalid) return false;
    
    // Additional validation for day-based rules
    if (this.selectedRuleType === 'day_based' && this.selectedDays.length === 0) {
      return false;
    }
    
    return true;
  }

  getRuleTypeDescription(): string {
    const descriptions = {
      'time_based': 'Apply different rates for specific hours (e.g., peak hours)',
      'day_based': 'Apply different rates for specific days (e.g., weekends)',
      'seasonal': 'Apply rates for seasonal periods (e.g., holidays)',
      'demand_based': 'Dynamic rates based on demand and occupancy'
    };
    return descriptions[this.selectedRuleType as keyof typeof descriptions] || 'Select a rule type to see description';
  }

  getApplicabilityDescription(): string {
    if (this.selectedRuleType === 'time_based') {
      const startTime = this.ruleForm.get('start_time')?.value;
      const endTime = this.ruleForm.get('end_time')?.value;
      if (startTime && endTime) {
        return startTime + ' to ' + endTime + ' daily';
      }
    } else if (this.selectedRuleType === 'day_based') {
      if (this.selectedDays.length > 0) {
        return this.pricingRuleService.formatDaysList(this.selectedDays);
      }
    }
    return 'Configuration incomplete';
  }

  async onSubmit(): Promise<void> {
    if (!this.isFormValid() || !this.lotId) return;

    try {
      this.saving = true;
      const formData = this.ruleForm.value;

      if (this.isEditMode && this.editRule) {
        // Update existing rule
        const updateData: PricingRuleUpdate = {
          ...formData,
          days_of_week: this.selectedRuleType === 'day_based' ? this.selectedDays : undefined
        };

        const updatedRule = await this.pricingRuleService.updatePricingRule(this.editRule.id, updateData);
        this.ruleUpdated.emit(updatedRule);
        this.toastService.showSuccess('Pricing rule updated successfully');
        
      } else {
        // Create new rule
        const createData: PricingRuleCreate = {
          lot_id: this.lotId,
          ...formData,
          days_of_week: this.selectedRuleType === 'day_based' ? this.selectedDays : undefined
        };

        const newRule = await this.pricingRuleService.createPricingRule(createData);
        this.ruleCreated.emit(newRule);
        this.toastService.showSuccess('Pricing rule created successfully');
      }

      // Close modal
      this.closeModal();
      
    } catch (error) {
      console.error('Error saving pricing rule:', error);
      const action = this.isEditMode ? 'update' : 'create';
      this.toastService.showError('Failed to ' + action + ' pricing rule');
    } finally {
      this.saving = false;
    }
  }

  private closeModal(): void {
    const modalElement = document.getElementById('pricingRuleModal');
    if (modalElement) {
      const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
      if (modal) {
        modal.hide();
      }
    }
    this.resetForm();
  }

  openModal(): void {
    const modalElement = document.getElementById('pricingRuleModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }
}
