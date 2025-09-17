export enum BookingStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show'
}

export interface Booking {
  id: string;
  user_id: string;
  lot_id: string;
  slot_id?: string;
  vehicle_type: string;
  vehicle_number: string;
  start_time: string;
  end_time: string;
  total_amount: number;
  status: string;
  booking_reference: string;
  check_in_time?: string;
  check_out_time?: string;
  created_at: string;
  updated_at: string;
  // Related object data
  lot_name?: string;
  slot_number?: string;
  user_email?: string;
  lot?: any;
  slot?: any;
  user?: any;
}

export interface BookingCreate {
  lot_id: string;
  vehicle_type: string;
  vehicle_number: string;
  start_time: string;
  end_time: string;
}

export interface BookingUpdate {
  vehicle_number?: string;
  start_time?: string;
  end_time?: string;
}

export interface PricingPreviewRequest {
  lot_id: string;
  vehicle_type: string;
  start_time: string;
  end_time: string;
}

export interface PricingBreakdown {
  rule_name: string;
  rule_type?: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  rate_per_hour: number;
  multiplier?: number;
  amount: number;
}

export interface PricingPreviewResponse {
  total_amount: number;
  duration_hours: number;
  average_rate: number;
  currency: string;
  pricing_breakdown: PricingBreakdown[];
  lot_id: string;
  vehicle_type: string;
  start_time: string;
  end_time: string;
}
