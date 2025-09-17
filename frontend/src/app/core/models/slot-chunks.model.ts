export interface TimeChunk {
  id: string;
  start_time: string;
  end_time: string;
  status: 'available' | 'booked' | 'temp_reserved';
  booking_id?: string;
  reserved_by?: string;
  reserved_at?: string;
}

export interface SlotAvailability {
  slot_id: string;
  total_chunks: number;
  available_chunks: number;
  booked_chunks: number;
  temp_reserved_chunks: number;
  availability_rate: number;
  chunks: TimeChunk[];
}

export interface ChunkReservation {
  session_id: string;
  chunk_ids: string[];
  reserved_until: string;
  slot_id: string;
  chunks: {
    id: string;
    start_time: string;
    end_time: string;
  }[];
}

export interface BookingSession {
  session_id: string;
  slot_id: string;
  selected_chunks: TimeChunk[];
  total_hours: number;
  total_amount: number;
  expires_at: string;
  status: 'reserving' | 'reserved' | 'confirming' | 'confirmed' | 'expired';
}
