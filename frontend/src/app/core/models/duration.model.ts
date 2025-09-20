/**
 * Duration model interfaces for the hybrid duration booking system.
 * Matches backend duration validation schemas and hybrid duration calculator.
 */

export enum DurationTier {
  MICRO = 'micro',     // 15-35 min (5-min increments)
  SHORT = 'short',     // 40-65 min (10-min increments)  
  MEDIUM = 'medium',   // 75-125 min (15-min increments)
  LONG = 'long'        // 150-240 min (30-min increments)
}

export enum DemandLevel {
  LOW = 'low',
  MEDIUM = 'medium', 
  HIGH = 'high',
  PEAK = 'peak'
}

export enum ValidationResult {
  VALID = 'valid',
  INVALID_DURATION = 'invalid_duration',
  INVALID_INCREMENT = 'invalid_increment',
  OUTSIDE_RANGE = 'outside_range',
  BUSINESS_RULE_VIOLATION = 'business_rule_violation'
}

export interface DurationConfig {
  tier: DurationTier;
  minDuration: number;
  maxDuration: number;
  increment: number;
  description: string;
}

export interface DurationValidationRequest {
  duration: number;
  startTime?: string;
  endTime?: string;
  vehicleType?: string;
  lotId?: string;
}

export interface DurationValidationResponse {
  isValid: boolean;
  suggestedDuration?: number;
  tier?: DurationTier;
  increment?: number;
  reason?: string;
  alternatives?: number[];
}

export interface BookingValidationRequest {
  startTime: string;
  endTime: string;
  durationMinutes: number;
  vehicleType: string;
  lotId: string;
  userId?: string;
}

export interface BookingValidationResponse {
  isValid: boolean;
  result: ValidationResult;
  message: string;
  durationValidation: DurationValidationResponse;
  alternativeDurations: number[];
  warnings: string[];
  metadata: {
    bufferTimeMinutes?: number;
    demandLevel?: string;
    slotReleaseTime?: string;
    suggestedSlots?: AlternativeTimeSlot[];
  };
}

export interface AlternativeTimeSlot {
  startTime: string;
  endTime: string;
  durationMinutes: number;
  tier: DurationTier;
  demandLevel: DemandLevel;
  bufferTimeMinutes: number;
}

export interface DurationSystemSummary {
  tiers: DurationConfig[];
  allValidDurations: number[];
  durationToTierMap: Record<number, DurationTier>;
  bufferTimeEnabled: boolean;
  bufferStrategy: string;
  demandLevels: DemandLevel[];
}

export interface BufferTimeInfo {
  durationMinutes: number;
  demandLevel: DemandLevel;
  bufferTimeMinutes: number;
  tier: DurationTier;
  tierIncrement: number;
  allDemandLevels: Record<string, number>;
  exampleTiming: {
    bookingStart: string;
    bookingEnd: string;
    slotRelease: string;
    bufferExplanation: string;
  };
  bufferStrategy: string;
  bufferEnabled: boolean;
}

export interface DurationPickerConfig {
  showTierLabels: boolean;
  showBufferTime: boolean;
  showDemandIndicator: boolean;
  enableQuickSelect: boolean;
  enableCustomDuration: boolean;
  defaultTier: DurationTier;
  maxDuration: number;
  minDuration: number;
}

export interface DurationSelection {
  duration: number;
  tier: DurationTier;
  increment: number;
  demandLevel: DemandLevel;
  bufferTimeMinutes: number;
  isValid: boolean;
  alternatives: number[];
  warnings: string[];
}

export interface QuickSelectOption {
  label: string;
  duration: number;
  tier: DurationTier;
  popular: boolean;
  description: string;
}

// Default quick select options based on hybrid duration model
export const DEFAULT_QUICK_SELECT_OPTIONS: QuickSelectOption[] = [
  {
    label: '15 min',
    duration: 15,
    tier: DurationTier.MICRO,
    popular: true,
    description: 'Quick stop'
  },
  {
    label: '30 min',
    duration: 30,
    tier: DurationTier.MICRO,
    popular: true,
    description: 'Short visit'
  },
  {
    label: '1 hour',
    duration: 60,
    tier: DurationTier.SHORT,
    popular: true,
    description: 'Standard parking'
  },
  {
    label: '2 hours',
    duration: 120,
    tier: DurationTier.MEDIUM,
    popular: true,
    description: 'Extended stay'
  },
  {
    label: '4 hours',
    duration: 240,
    tier: DurationTier.LONG,
    popular: false,
    description: 'Long-term parking'
  }
];

// Tier configuration matching backend HybridDurationCalculator
export const DURATION_TIER_CONFIGS: DurationConfig[] = [
  {
    tier: DurationTier.MICRO,
    minDuration: 15,
    maxDuration: 30,
    increment: 5,
    description: 'Short, precise bookings'
  },
  {
    tier: DurationTier.SHORT,
    minDuration: 40,
    maxDuration: 65,
    increment: 10,
    description: 'Standard hourly bookings'
  },
  {
    tier: DurationTier.MEDIUM,
    minDuration: 75,
    maxDuration: 125,
    increment: 15,
    description: 'Extended stay bookings'
  },
  {
    tier: DurationTier.LONG,
    minDuration: 150,
    maxDuration: 240,
    increment: 30,
    description: 'Long-term parking'
  }
];

// Utility functions
export class DurationUtils {
  static getTierForDuration(duration: number): DurationTier | null {
    for (const config of DURATION_TIER_CONFIGS) {
      if (duration >= config.minDuration && duration <= config.maxDuration) {
        return config.tier;
      }
    }
    return null;
  }

  static getIncrementForDuration(duration: number): number {
    const tier = this.getTierForDuration(duration);
    if (!tier) return 5; // default increment
    
    const config = DURATION_TIER_CONFIGS.find(c => c.tier === tier);
    return config?.increment || 5;
  }

  static formatDurationDisplay(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    } else if (minutes % 60 === 0) {
      return `${minutes / 60} hour${minutes > 60 ? 's' : ''}`;
    } else {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `${hours}h ${mins}m`;
    }
  }

  static getTierDescription(tier: DurationTier): string {
    const config = DURATION_TIER_CONFIGS.find(c => c.tier === tier);
    return config?.description || 'Unknown tier';
  }

  static getTierColor(tier: DurationTier): string {
    switch (tier) {
      case DurationTier.MICRO:
        return '#28a745'; // Green
      case DurationTier.SHORT:
        return '#17a2b8'; // Blue
      case DurationTier.MEDIUM:
        return '#ffc107'; // Yellow
      case DurationTier.LONG:
        return '#dc3545'; // Red
      default:
        return '#6c757d'; // Gray
    }
  }

  static getDemandLevelColor(level: DemandLevel): string {
    switch (level) {
      case DemandLevel.LOW:
        return '#28a745'; // Green
      case DemandLevel.MEDIUM:
        return '#ffc107'; // Yellow
      case DemandLevel.HIGH:
        return '#fd7e14'; // Orange
      case DemandLevel.PEAK:
        return '#dc3545'; // Red
      default:
        return '#6c757d'; // Gray
    }
  }

  static getDemandLevelIcon(level: DemandLevel): string {
    switch (level) {
      case DemandLevel.LOW:
        return 'fas fa-circle';
      case DemandLevel.MEDIUM:
        return 'fas fa-circle-half-stroke';
      case DemandLevel.HIGH:
        return 'fas fa-exclamation-circle';
      case DemandLevel.PEAK:
        return 'fas fa-fire';
      default:
        return 'fas fa-question-circle';
    }
  }
}
