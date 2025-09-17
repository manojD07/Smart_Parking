/**
 * Slot Chunk Models for 30-minute time-based booking system
 */

export interface TimeChunk {
  id: string;
  start_time: string; // ISO format
  end_time: string;   // ISO format
  status: ChunkStatus;
  booking_id?: string | null;
  reserved_by?: string | null;
}

export enum ChunkStatus {
  AVAILABLE = 'available',
  BOOKED = 'booked',
  TEMP_RESERVED = 'temp_reserved'
}

export interface SlotChunkAvailability {
  total_chunks: number;
  available_chunks: number;
  booked_chunks: number;
  temp_reserved_chunks: number;
  availability_rate: number;
  chunks: TimeChunk[];
}

export interface ChunkReservation {
  success: boolean;
  session_id?: string;
  chunk_ids?: string[];
  expires_at?: string; // ISO format
  ttl_seconds?: number;
  error?: string;
  locked_chunks?: string[];
}

export interface BookingSession {
  session_id: string;
  chunk_ids: string[];
  created_at: string;
  expires_at: string;
  is_expired?: boolean;
  remaining_seconds?: number;
}

export interface ChunkSelectionEvent {
  selectedChunks: TimeChunk[];
  startTime: string;
  endTime: string;
  sessionId?: string;
}

export interface DateGroup {
  date: string;
  displayDate: string;
  chunks: TimeChunk[];
}

export interface ChunkColorConfig {
  available: string;
  booked: string;
  temp_reserved: string;
  selected: string;
}

export interface ReservationConfirmation {
  success: boolean;
  message?: string;
  booking_id?: string;
  session_id?: string;
  error?: string;
}
