import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { FormControl, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged, switchMap, of, catchError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { CommonModule, TitleCasePipe } from '@angular/common';

import {
  DurationTier,
  DemandLevel,
  DurationValidationResponse,
  BookingValidationResponse,
  DurationSelection,
  QuickSelectOption,
  DurationPickerConfig,
  BufferTimeInfo,
  DEFAULT_QUICK_SELECT_OPTIONS,
  DURATION_TIER_CONFIGS,
  DurationUtils
} from '../../../core/models/duration.model';

import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-hybrid-duration-picker',
  templateUrl: './hybrid-duration-picker.component.html',
  styleUrls: ['./hybrid-duration-picker.component.scss'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TitleCasePipe]
})
export class HybridDurationPickerComponent implements OnInit, OnDestroy {
  @Input() lotId!: string;
  @Input() vehicleType: string = 'car';
  @Input() startTime?: string;
  @Input() endTime?: string;
  @Input() initialDuration: number = 60;
  @Input() config: DurationPickerConfig = {
    showTierLabels: true,
    showBufferTime: true,
    showDemandIndicator: true,
    enableQuickSelect: true,
    enableCustomDuration: true,
    defaultTier: DurationTier.SHORT,
    maxDuration: 240,
    minDuration: 15
  };

  @Output() durationSelected = new EventEmitter<DurationSelection>();
  @Output() validationChanged = new EventEmitter<boolean>();

  // Form controls
  durationControl = new FormControl(this.initialDuration, [
    Validators.required,
    Validators.min(15),
    Validators.max(240)
  ]);

  // Component state
  selectedDuration: number = this.initialDuration;
  currentTier: DurationTier | null = null;
  currentDemandLevel: DemandLevel = DemandLevel.MEDIUM;
  bufferTimeInfo: BufferTimeInfo | null = null;
  validationResponse: DurationValidationResponse | null = null;
  bookingValidationResponse: BookingValidationResponse | null = null;
  isLoading = false;
  isValid = false;
  errorMessage = '';
  warningMessages: string[] = [];

  // Quick select options
  quickSelectOptions: QuickSelectOption[] = DEFAULT_QUICK_SELECT_OPTIONS;
  tierConfigs = DURATION_TIER_CONFIGS;

  // Utility class
  DurationUtils = DurationUtils;
  DurationTier = DurationTier;
  DemandLevel = DemandLevel;

  private destroy$ = new Subject<void>();
  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.initializeDurationPicker();
    this.setupDurationValidation();
    this.updateSelectedDuration(this.initialDuration);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeDurationPicker(): void {
    // Set initial duration
    this.durationControl.setValue(this.initialDuration);
    
    // Load system configuration if needed
    this.loadDurationSystemInfo();
  }

  private setupDurationValidation(): void {
    // Real-time validation as user types
    this.durationControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntil(this.destroy$),
        switchMap(duration => {
          if (!duration || duration < 15 || duration > 240) {
            return of(null);
          }
          return this.validateDuration(duration);
        })
      )
      .subscribe(response => {
        if (response) {
          this.handleValidationResponse(response);
        }
      });
  }

  private validateDuration(duration: number) {
    this.isLoading = true;
    
    // First try client-side validation for immediate feedback
    const clientValidation = this.validateDurationClientSide(duration);
    if (!clientValidation.isValid) {
      this.isLoading = false;
      return of(clientValidation);
    }
    
    const url = `${this.apiUrl}/duration/validate-duration`;
    const body = {
      duration: duration,
      startTime: this.startTime,
      endTime: this.endTime,
      vehicleType: this.vehicleType,
      lotId: this.lotId
    };

    return this.http.post<DurationValidationResponse>(url, body)
      .pipe(
        catchError(error => {
          console.warn('Backend duration validation unavailable, using client-side validation:', error);
          this.isLoading = false;
          // Fallback to client-side validation if backend is unavailable
          return of(clientValidation);
        })
      );
  }

  private validateDurationClientSide(duration: number): DurationValidationResponse {
    // Basic client-side validation using DurationUtils
    const tier = DurationUtils.getTierForDuration(duration);
    const increment = DurationUtils.getIncrementForDuration(duration);
    
    // Check if duration is within valid ranges
    const isValidDuration = duration >= 15 && duration <= 240;
    const isValidIncrement = tier ? (duration % increment === 0) : false;
    
    let isValid = isValidDuration;
    let reason = '';
    let suggestedDuration = duration;
    let alternatives: number[] = [];
    
    if (!isValidDuration) {
      isValid = false;
      reason = duration < 15 ? 'Duration must be at least 15 minutes' : 'Duration cannot exceed 240 minutes (4 hours)';
      suggestedDuration = duration < 15 ? 15 : 240;
    } else if (!isValidIncrement && tier) {
      // Round to nearest valid increment
      const roundedDown = Math.floor(duration / increment) * increment;
      const roundedUp = Math.ceil(duration / increment) * increment;
      
      suggestedDuration = (duration - roundedDown) < (roundedUp - duration) ? roundedDown : roundedUp;
      
      // Ensure suggested duration is within tier bounds
      const tierConfig = DURATION_TIER_CONFIGS.find(c => c.tier === tier);
      if (tierConfig) {
        suggestedDuration = Math.max(tierConfig.minDuration, Math.min(suggestedDuration, tierConfig.maxDuration));
      }
      
      reason = `Duration must be in ${increment}-minute increments for ${tier} tier`;
      alternatives = [suggestedDuration];
      
      if (suggestedDuration !== duration) {
        isValid = false;
      }
    }

    return {
      isValid,
      suggestedDuration,
      tier: tier || undefined,
      increment,
      reason,
      alternatives
    };
  }

  private handleValidationResponse(response: DurationValidationResponse): void {
    this.validationResponse = response;
    this.isValid = response.isValid;
    this.isLoading = false;
    
    if (response.isValid) {
      this.errorMessage = '';
      this.currentTier = response.tier || null;
      
      // Get buffer time info for valid durations
      if (this.config.showBufferTime) {
        this.loadBufferTimeInfo(this.selectedDuration);
      }
      
      // Emit selection
      this.emitDurationSelection();
    } else {
      this.errorMessage = response.reason || 'Invalid duration';
      this.currentTier = null;
    }

    this.validationChanged.emit(this.isValid);
    this.cdr.detectChanges();
  }

  private loadBufferTimeInfo(duration: number): void {
    const url = `${this.apiUrl}/duration/buffer-time/${duration}`;
    
    this.http.get<BufferTimeInfo>(url)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Buffer time info error:', error);
          return of(null);
        })
      )
      .subscribe(info => {
        this.bufferTimeInfo = info;
        this.cdr.detectChanges();
      });
  }

  private loadDurationSystemInfo(): void {
    // Load system configuration for quick select options
    const url = `${this.apiUrl}/duration/duration-system`;
    
    this.http.get(url)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.warn('Could not load duration system info:', error);
          return of(null);
        })
      )
      .subscribe(systemInfo => {
        if (systemInfo) {
          // Update configuration based on system settings
          console.log('Duration system info loaded:', systemInfo);
        }
      });
  }

  private emitDurationSelection(): void {
    const selection: DurationSelection = {
      duration: this.selectedDuration,
      tier: this.currentTier || DurationTier.SHORT,
      increment: DurationUtils.getIncrementForDuration(this.selectedDuration),
      demandLevel: this.currentDemandLevel,
      bufferTimeMinutes: this.bufferTimeInfo?.bufferTimeMinutes || 0,
      isValid: this.isValid,
      alternatives: this.validationResponse?.alternatives || [],
      warnings: this.warningMessages
    };

    this.durationSelected.emit(selection);
  }

  // Public methods for template
  
  onQuickSelect(option: QuickSelectOption): void {
    this.updateSelectedDuration(option.duration);
    this.durationControl.setValue(option.duration);
  }

  onCustomDurationChange(value: number): void {
    if (!value || value === this.selectedDuration) return;
    
    // Find the closest valid duration
    const validDurations = this.getAllValidDurations();
    const closestValid = this.findClosestValidDuration(value, validDurations);
    
    if (closestValid !== value) {
      // Update input to show the corrected value
      setTimeout(() => {
        this.durationControl.setValue(closestValid, { emitEvent: false });
      }, 100);
    }
    
    this.updateSelectedDuration(closestValid);
  }

  private findClosestValidDuration(target: number, validDurations: number[]): number {
    if (validDurations.includes(target)) {
      return target; // Exact match
    }
    
    // Find closest valid duration
    return validDurations.reduce((closest, current) => {
      return Math.abs(current - target) < Math.abs(closest - target) ? current : closest;
    });
  }

  updateSelectedDuration(duration: number): void {
    this.selectedDuration = duration;
    this.currentTier = DurationUtils.getTierForDuration(duration);
    
    // Validate the new duration
    if (duration >= 15 && duration <= 240) {
      this.validateDuration(duration)?.subscribe(response => {
        if (response) {
          this.handleValidationResponse(response);
        }
      });
    }
  }

  adjustDuration(increment: number): void {
    // Get all valid durations for smart navigation
    const validDurations = this.getAllValidDurations();
    const currentIndex = validDurations.indexOf(this.selectedDuration);
    
    let newIndex: number;
    if (increment > 0) {
      // Find next valid duration
      newIndex = currentIndex + 1;
    } else {
      // Find previous valid duration
      newIndex = currentIndex - 1;
    }
    
    if (newIndex >= 0 && newIndex < validDurations.length) {
      const newDuration = validDurations[newIndex];
      this.updateSelectedDuration(newDuration);
      this.durationControl.setValue(newDuration);
    }
  }

  private getAllValidDurations(): number[] {
    const validDurations: number[] = [];
    
    // Add all tier durations
    DURATION_TIER_CONFIGS.forEach(tierConfig => {
      for (let duration = tierConfig.minDuration; duration <= tierConfig.maxDuration; duration += tierConfig.increment) {
        if (duration >= this.config.minDuration && duration <= this.config.maxDuration) {
          validDurations.push(duration);
        }
      }
    });
    
    // Remove duplicates and sort
    return [...new Set(validDurations)].sort((a, b) => a - b);
  }

  getTierDurations(tier: DurationTier): number[] {
    const config = this.tierConfigs.find(c => c.tier === tier);
    if (!config) return [];

    const durations: number[] = [];
    for (let d = config.minDuration; d <= config.maxDuration; d += config.increment) {
      durations.push(d);
    }
    return durations;
  }

  isQuickOptionSelected(option: QuickSelectOption): boolean {
    return this.selectedDuration === option.duration;
  }

  isDurationInTier(duration: number, tier: DurationTier): boolean {
    return DurationUtils.getTierForDuration(duration) === tier;
  }

  getValidationStatusClass(): string {
    if (this.isLoading) return 'validation-loading';
    if (!this.isValid && this.errorMessage) return 'validation-error';
    if (this.isValid) return 'validation-success';
    return '';
  }

  getBufferTimeDisplay(): string {
    if (!this.bufferTimeInfo) return '';
    
    const buffer = this.bufferTimeInfo.bufferTimeMinutes;
    if (buffer === 0) return 'No buffer time';
    
    return `+${buffer} min buffer`;
  }

  getDemandLevelDisplay(): string {
    switch (this.currentDemandLevel) {
      case DemandLevel.LOW:
        return 'Low demand';
      case DemandLevel.MEDIUM:
        return 'Normal demand';
      case DemandLevel.HIGH:
        return 'High demand';
      case DemandLevel.PEAK:
        return 'Peak demand';
      default:
        return 'Unknown demand';
    }
  }

  // Form validation helpers
  get durationErrors() {
    const control = this.durationControl;
    if (control.hasError('required')) return 'Duration is required';
    if (control.hasError('min')) return `Minimum duration is ${this.config.minDuration} minutes`;
    if (control.hasError('max')) return `Maximum duration is ${this.config.maxDuration} minutes`;
    return null;
  }

  get hasFormErrors(): boolean {
    return this.durationControl.invalid && this.durationControl.touched;
  }
}
