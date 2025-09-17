export enum VehicleType {
  CAR = 'car',
  BIKE = 'bike',
  TRUCK = 'truck',
  ELECTRIC_CAR = 'electric_car',
  ELECTRIC_BIKE = 'electric_bike'
}

export enum SlotStatus {
  AVAILABLE = 'available',
  OCCUPIED = 'occupied',
  RESERVED = 'reserved',
  MAINTENANCE = 'maintenance'
}

export interface ParkingLot {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  total_car_slots: number;
  total_bike_slots: number;
  available_car_slots?: number;
  available_bike_slots?: number;
  hourly_rate_car: number;
  hourly_rate_bike: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ParkingSlot {
  id: string;
  lot_id: string;
  slot_number: string;
  slot_type: string;
  status: string;
  is_occupied: boolean;
  is_reserved: boolean;
  created_at: string;
}

export interface AvailabilityRequest {
  vehicle_type: string;
  start_time: string;
  end_time: string;
}

export interface AvailabilityResponse {
  total_slots: number;
  occupied_slots: number;
  available_slots: number;
  occupancy_rate: number;
}

export interface LocationSearchRequest {
  latitude: number;
  longitude: number;
  radius_km?: number;
  skip?: number;
  limit?: number;
}

export interface ParkingLotCreate {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  total_car_slots: number;
  total_bike_slots: number;
  hourly_rate_car: number;
  hourly_rate_bike: number;
}
