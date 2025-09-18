import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Services
import { ParkingLotService, ParkingLot } from '../../../../core/services/parking-lot.service';
import { PricingRuleService, PricingRule, PricingRuleListResponse } from '../../../../core/services/pricing-rule.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from '../shared/loading-state.component';
import { PricingRuleFormComponent } from './pricing-rule-form.component';
import { PricingStatusBadgeComponent } from './shared/pricing-status-badge.component';

@Component({
  selector: 'app-admin-pricing',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingStateComponent, PricingRuleFormComponent, PricingStatusBadgeComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <h2>
            <i class="fas fa-tags me-2"></i>
            Pricing Rules Management
          </h2>
          <p class="text-muted">Manage dynamic pricing rules for parking lots</p>
        </div>
      </div>

      <!-- Lot Selector -->
      <div class="row mb-4">
        <div class="col-md-6">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">
                <i class="fas fa-building me-2"></i>
                Select Parking Lot
              </h5>
              <div class="d-flex gap-2 flex-wrap">
                <div class="flex-grow-1">
                  <select 
                    class="form-select"
                    [(ngModel)]="selectedLotId" 
                    (ngModelChange)="onLotChange()"
                    [disabled]="loadingLots">
                    <option value="">
                      {{ loadingLots ? 'Loading parking lots...' : 'Choose a parking lot...' }}
                    </option>
                    <option *ngFor="let lot of parkingLots" [value]="lot.id">
                      {{ lot.name }} - {{ lot.address }}
                    </option>
                  </select>
                  
                  <!-- Debug info -->
                  <small class="text-muted d-block mt-1" *ngIf="!loadingLots">
                    {{ parkingLots.length }} parking lot{{ parkingLots.length !== 1 ? 's' : '' }} available
                  </small>
                </div>
                
                <button 
                  class="btn btn-outline-secondary"
                  (click)="loadParkingLots()"
                  [disabled]="loadingLots"
                  title="Refresh parking lots">
                  <i class="fas fa-sync-alt" [class.fa-spin]="loadingLots"></i>
                </button>
                
                <button 
                  class="btn btn-primary"
                  (click)="openCreateRuleForm()"
                  [disabled]="!selectedLotId || loadingRules">
                  <i class="fas fa-plus me-1"></i>
                  New Rule
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Quick Stats -->
        <div class="col-md-6" *ngIf="selectedLot && rulesData">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">
                <i class="fas fa-chart-bar me-2"></i>
                Rules Summary
              </h5>
              <div class="row text-center">
                <div class="col-3">
                  <div class="stat-value text-primary">{{ rulesData.summary.total_rules }}</div>
                  <div class="stat-label">Total</div>
                </div>
                <div class="col-3">
                  <div class="stat-value text-success">{{ rulesData.summary.active_rules }}</div>
                  <div class="stat-label">Active</div>
                </div>
                <div class="col-3">
                  <div class="stat-value text-secondary">{{ rulesData.summary.inactive_rules }}</div>
                  <div class="stat-label">Inactive</div>
                </div>
                <div class="col-3">
                  <div class="stat-value text-info">{{ getVehicleRulesCount() }}</div>
                  <div class="stat-label">Types</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rules Content -->
      <div class="row" *ngIf="selectedLot">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">
                <i class="fas fa-list me-2"></i>
                Pricing Rules for {{ selectedLot.name }}
              </h5>
              <div class="d-flex gap-2">
                <button 
                  class="btn btn-outline-primary btn-sm"
                  (click)="refreshRules()"
                  [disabled]="loadingRules">
                  <i class="fas fa-sync-alt me-1" [class.fa-spin]="loadingRules"></i>
                  Refresh
                </button>
                <button 
                  class="btn btn-outline-secondary btn-sm"
                  (click)="createDefaultRules()"
                  [disabled]="loadingRules">
                  <i class="fas fa-magic me-1"></i>
                  Create Defaults
                </button>
              </div>
            </div>
            
            <div class="card-body">
              <!-- Loading State -->
              <div *ngIf="loadingRules && rules.length === 0">
                <app-loading-state 
                  type="spinner" 
                  loadingText="Loading pricing rules..."
                  size="lg">
                </app-loading-state>
              </div>

              <!-- Empty State -->
              <div *ngIf="!loadingRules && rules.length === 0" class="text-center py-5">
                <i class="fas fa-tags fa-3x text-muted mb-3"></i>
                <h5>No Pricing Rules Found</h5>
                <p class="text-muted">This parking lot doesn't have any pricing rules yet.</p>
                <button class="btn btn-primary me-2" (click)="openCreateRuleForm()">
                  <i class="fas fa-plus me-2"></i>Create First Rule
                </button>
                <button class="btn btn-outline-secondary" (click)="createDefaultRules()">
                  <i class="fas fa-magic me-2"></i>Create Default Rules
                </button>
              </div>

              <!-- Rules Table -->
              <div *ngIf="!loadingRules && rules.length > 0" class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Vehicle</th>
                      <th>Time/Days</th>
                      <th>Pricing</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let rule of rules; trackBy: trackByRuleId">
                      <td>
                        <strong>{{ rule.name }}</strong>
                      </td>
                      <td>
                        <app-pricing-status-badge 
                          type="rule_type" 
                          [value]="rule.rule_type">
                        </app-pricing-status-badge>
                      </td>
                      <td>
                        <i class="fas" [class]="rule.vehicle_type === 'car' ? 'fa-car text-primary' : 'fa-motorcycle text-success'"></i>
                        {{ getVehicleTypeDisplayName(rule.vehicle_type) }}
                      </td>
                      <td>
                        <small class="text-muted">
                          {{ getTimeOrDaysDisplay(rule) }}
                        </small>
                      </td>
                      <td>
                        <div>
                          <strong class="text-success">{{ formatPrice(rule.effective_price) }}/hr</strong>
                        </div>
                        <small class="text-muted" *ngIf="rule.multiplier !== 1">
                          {{ formatPrice(rule.price_per_hour) }} × {{ rule.multiplier }}
                        </small>
                      </td>
                      <td>
                        <app-pricing-status-badge 
                          type="priority" 
                          [value]="rule.priority">
                        </app-pricing-status-badge>
                      </td>
                      <td>
                        <div class="form-check form-switch">
                          <input 
                            class="form-check-input" 
                            type="checkbox" 
                            [checked]="rule.is_active"
                            (change)="toggleRuleStatus(rule)"
                            [disabled]="togglingRules.has(rule.id)">
                          <label class="form-check-label">
                            {{ rule.is_active ? 'Active' : 'Inactive' }}
                          </label>
                        </div>
                      </td>
                      <td>
                        <div class="btn-group btn-group-sm">
                          <button 
                            class="btn btn-outline-primary"
                            (click)="editRule(rule)"
                            [disabled]="loadingRules">
                            <i class="fas fa-edit"></i>
                          </button>
                          <button 
                            class="btn btn-outline-danger"
                            (click)="confirmDeleteRule(rule)"
                            [disabled]="loadingRules">
                            <i class="fas fa-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Lot Selected -->
      <div *ngIf="!selectedLot && !loadingLots" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-body text-center py-5">
              <i class="fas fa-building fa-3x text-muted mb-3"></i>
              <h5>Select a Parking Lot</h5>
              <p class="text-muted">Choose a parking lot to view and manage its pricing rules.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pricing Rule Form Modal -->
    <app-pricing-rule-form
      [lotId]="selectedLotId"
      [editRule]="editingRule"
      (ruleCreated)="onRuleCreated($event)"
      (ruleUpdated)="onRuleUpdated($event)">
    </app-pricing-rule-form>
  `,
  styles: [`
    .stat-value {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.875rem;
      color: #6c757d;
      font-weight: 500;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      color: #495057;
      background-color: #f8f9fa;
    }

    .table td {
      vertical-align: middle;
    }

    .btn-group-sm .btn {
      padding: 0.25rem 0.5rem;
    }

    .form-switch .form-check-input {
      margin-top: 0;
    }

    .card {
      border-radius: 12px;
      border: 1px solid #e9ecef;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
      border-radius: 12px 12px 0 0 !important;
    }

    @media (max-width: 768px) {
      .table-responsive {
        border-radius: 8px;
      }
      
      .btn-group-sm .btn {
        padding: 0.125rem 0.25rem;
      }
      
      .stat-value {
        font-size: 1.25rem;
      }
    }
  `]
})
export class AdminPricingComponent implements OnInit {
  @ViewChild(PricingRuleFormComponent) ruleForm!: PricingRuleFormComponent;

  // Data
  parkingLots: ParkingLot[] = [];
  selectedLotId: string = '';
  selectedLot: ParkingLot | null = null;
  rules: PricingRule[] = [];
  rulesData: PricingRuleListResponse | null = null;

  // UI State
  loadingLots = false;
  loadingRules = false;
  togglingRules = new Set<string>();
  editingRule: PricingRule | null = null;

  constructor(
    private parkingLotService: ParkingLotService,
    private pricingRuleService: PricingRuleService,
    private toastService: ToastService
  ) {}

  async ngOnInit(): Promise<void> {
    await this.loadParkingLots();
  }

  async loadParkingLots(): Promise<void> {
    try {
      this.loadingLots = true;
      console.log('🏢 Loading parking lots...');
      
      // Try to get parking lots with filters for active lots only
      this.parkingLots = await this.parkingLotService.getAllLots({ is_active: true });
      console.log('🏢 Loaded parking lots:', this.parkingLots.length, this.parkingLots);
      
      if (this.parkingLots.length === 0) {
        console.warn('⚠️ No parking lots found');
        this.toastService.showWarning('No active parking lots found');
      }
      
    } catch (error) {
      console.error('❌ Error loading parking lots:', error);
      
      // Try fallback without filters
      try {
        console.log('🔄 Trying fallback without filters...');
        this.parkingLots = await this.parkingLotService.getAllLots();
        console.log('🏢 Fallback loaded:', this.parkingLots.length, 'lots');
      } catch (fallbackError) {
        console.error('❌ Fallback also failed:', fallbackError);
        this.toastService.showError('Failed to load parking lots. Please check your connection.');
        this.parkingLots = [];
      }
    } finally {
      this.loadingLots = false;
    }
  }

  async onLotChange(): Promise<void> {
    console.log('🔄 Lot changed to:', this.selectedLotId);
    if (this.selectedLotId) {
      this.selectedLot = this.parkingLots.find(lot => lot.id === this.selectedLotId) || null;
      console.log('🏢 Selected lot:', this.selectedLot);
      await this.loadRules();
    } else {
      this.selectedLot = null;
      this.rules = [];
      this.rulesData = null;
    }
  }

  async loadRules(): Promise<void> {
    if (!this.selectedLotId) return;

    try {
      this.loadingRules = true;
      console.log('📋 Loading pricing rules for lot:', this.selectedLotId);
      this.rulesData = await this.pricingRuleService.getLotPricingRules(this.selectedLotId);
      this.rules = this.rulesData.rules;
      console.log('📋 Loaded pricing rules:', this.rules.length, this.rules);
    } catch (error) {
      console.error('❌ Error loading pricing rules:', error);
      this.toastService.showError('Failed to load pricing rules');
      this.rules = [];
      this.rulesData = null;
    } finally {
      this.loadingRules = false;
    }
  }

  async refreshRules(): Promise<void> {
    await this.loadRules();
    this.toastService.showSuccess('Pricing rules refreshed');
  }

  async toggleRuleStatus(rule: PricingRule): Promise<void> {
    try {
      this.togglingRules.add(rule.id);
      
      const updatedRule = await this.pricingRuleService.togglePricingRule(rule.id);
      
      // Update rule in local array
      const index = this.rules.findIndex(r => r.id === rule.id);
      if (index !== -1) {
        this.rules[index] = updatedRule;
      }
      
      const action = updatedRule.is_active ? 'activated' : 'deactivated';
      this.toastService.showSuccess('Rule "' + rule.name + '" ' + action + ' successfully');
      
    } catch (error) {
      console.error('Error toggling rule status:', error);
      this.toastService.showError('Failed to update rule status');
    } finally {
      this.togglingRules.delete(rule.id);
    }
  }

  openCreateRuleForm(): void {
    this.editingRule = null;
    if (this.ruleForm) {
      this.ruleForm.openModal();
    }
  }

  editRule(rule: PricingRule): void {
    this.editingRule = rule;
    if (this.ruleForm) {
      this.ruleForm.openModal();
    }
  }

  confirmDeleteRule(rule: PricingRule): void {
    const confirmed = confirm('Are you sure you want to delete the pricing rule "' + rule.name + '"?');
    if (confirmed) {
      this.deleteRule(rule);
    }
  }

  async deleteRule(rule: PricingRule): Promise<void> {
    try {
      const success = await this.pricingRuleService.deletePricingRule(rule.id);
      
      if (success) {
        // Remove from local array
        this.rules = this.rules.filter(r => r.id !== rule.id);
        
        // Update summary
        if (this.rulesData) {
          this.rulesData.summary.total_rules--;
          if (rule.is_active) {
            this.rulesData.summary.active_rules--;
          } else {
            this.rulesData.summary.inactive_rules--;
          }
        }
        
        this.toastService.showSuccess('Rule "' + rule.name + '" deleted successfully');
      } else {
        this.toastService.showError('Failed to delete pricing rule');
      }
      
    } catch (error) {
      console.error('Error deleting rule:', error);
      this.toastService.showError('Failed to delete pricing rule');
    }
  }

  async createDefaultRules(): Promise<void> {
    if (!this.selectedLotId) return;
    
    const confirmed = confirm('This will create default pricing rules for this parking lot. Continue?');
    if (!confirmed) return;

    try {
      this.loadingRules = true;
      // TODO: Call create default rules API
      this.toastService.showInfo('Create default rules - Coming soon');
      // await this.pricingRuleService.createDefaultRules(this.selectedLotId);
      // await this.loadRules();
    } catch (error) {
      console.error('Error creating default rules:', error);
      this.toastService.showError('Failed to create default rules');
    } finally {
      this.loadingRules = false;
    }
  }

  // Form event handlers
  onRuleCreated(rule: PricingRule): void {
    // Add new rule to local array
    this.rules.push(rule);
    
    // Update summary
    if (this.rulesData) {
      this.rulesData.summary.total_rules++;
      if (rule.is_active) {
        this.rulesData.summary.active_rules++;
      } else {
        this.rulesData.summary.inactive_rules++;
      }
    }
  }

  onRuleUpdated(updatedRule: PricingRule): void {
    // Update rule in local array
    const index = this.rules.findIndex(r => r.id === updatedRule.id);
    if (index !== -1) {
      this.rules[index] = updatedRule;
    }
  }

  // Helper methods
  trackByRuleId(index: number, rule: PricingRule): string {
    return rule.id;
  }

  getVehicleRulesCount(): number {
    if (!this.rulesData) return 0;
    return Object.keys(this.rulesData.summary.vehicle_types || {}).length;
  }

  getRuleTypeDisplayName(ruleType: string): string {
    return this.pricingRuleService.getRuleTypeDisplayName(ruleType);
  }

  getVehicleTypeDisplayName(vehicleType: string): string {
    return this.pricingRuleService.getVehicleTypeDisplayName(vehicleType);
  }

  getPriorityDisplayName(priority: string): string {
    return this.pricingRuleService.getPriorityDisplayName(priority);
  }

  formatPrice(amount: number): string {
    return this.pricingRuleService.formatPrice(amount);
  }

  getTimeOrDaysDisplay(rule: PricingRule): string {
    if (rule.rule_type === 'time_based') {
      return this.pricingRuleService.formatTimeRange(rule.start_time, rule.end_time);
    } else if (rule.rule_type === 'day_based') {
      return this.pricingRuleService.formatDaysList(rule.days_list);
    }
    return 'Always';
  }

}
