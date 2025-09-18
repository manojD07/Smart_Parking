-- Smart Parking Management System - Sample Data
-- This SQL file contains essential sample data for testing

-- Insert Admin User
INSERT INTO users (id, email, password_hash, first_name, last_name, phone, is_admin, is_active, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@smartparking.com',
    '$2b$12$LQv3c1yqBwlVHpPjrwjlOOY/BdJrjBQbF9nE6qBqBqBqBqBqBqBqBu', -- AdminPassword123!
    'System',
    'Admin',
    '+919876543200',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Insert Test User
INSERT INTO users (id, email, password_hash, first_name, last_name, phone, is_admin, is_active, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'user@smartparking.com',
    '$2b$12$LQv3c1yqBwlVHpPjrwjlOOY/BdJrjBQbF9nE6qBqBqBqBqBqBqBqBu', -- UserPassword123!
    'Test',
    'User',
    '+919876543210',
    false,
    true,
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Insert Sample Parking Lots
INSERT INTO parking_lots (id, name, address, latitude, longitude, total_car_slots, total_bike_slots, hourly_rate_car, hourly_rate_bike, is_active, created_at, updated_at)
VALUES 
(
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'Downtown Plaza Parking',
    'Connaught Place, New Delhi, Delhi 110001',
    28.6315,
    77.2167,
    200,
    150,
    15.00,
    8.00,
    true,
    NOW(),
    NOW()
),
(
    '6a650b0d-2311-4b30-a313-ae7529086f12',
    'Bandra West Mall Parking',
    'Linking Road, Bandra West, Mumbai, Maharashtra 400050',
    19.0596,
    72.8295,
    180,
    120,
    20.00,
    10.00,
    true,
    NOW(),
    NOW()
),
(
    '6a650b0d-2311-4b30-a313-ae7529086f13',
    'Koramangala Tech Park',
    'Koramangala 5th Block, Bangalore, Karnataka 560095',
    12.9352,
    77.6245,
    250,
    200,
    12.00,
    6.00,
    true,
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Insert Sample Parking Slots for Downtown Plaza
INSERT INTO parking_slots (id, lot_id, slot_number, slot_type, is_occupied, is_reserved, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'C' || LPAD(generate_series::text, 3, '0'),
    'car',
    false,
    false,
    NOW(),
    NOW()
FROM generate_series(1, 50);

INSERT INTO parking_slots (id, lot_id, slot_number, slot_type, is_occupied, is_reserved, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'B' || LPAD(generate_series::text, 3, '0'),
    'bike',
    false,
    false,
    NOW(),
    NOW()
FROM generate_series(1, 30);

-- Insert Sample Parking Slots for Bandra Mall
INSERT INTO parking_slots (id, lot_id, slot_number, slot_type, is_occupied, is_reserved, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f12',
    'C' || LPAD(generate_series::text, 3, '0'),
    'car',
    false,
    false,
    NOW(),
    NOW()
FROM generate_series(1, 40);

INSERT INTO parking_slots (id, lot_id, slot_number, slot_type, is_occupied, is_reserved, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f12',
    'B' || LPAD(generate_series::text, 3, '0'),
    'bike',
    false,
    false,
    NOW(),
    NOW()
FROM generate_series(1, 25);

-- Insert Sample Pricing Rules
INSERT INTO pricing_rules (id, lot_id, name, vehicle_type, rule_type, start_time, end_time, multiplier, priority, is_active, created_at, updated_at)
VALUES 
-- Peak hours for Downtown Plaza
(
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'Peak Hours - Car',
    'car',
    'time_based',
    '18:00:00',
    '22:00:00',
    1.5,
    'high',
    true,
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'Early Bird Discount - Car',
    'car',
    'time_based',
    '06:00:00',
    '09:00:00',
    0.8,
    'normal',
    true,
    NOW(),
    NOW()
),
-- Peak hours for Bandra Mall
(
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f12',
    'Peak Hours - Car',
    'car',
    'time_based',
    '18:00:00',
    '22:00:00',
    1.4,
    'high',
    true,
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    '6a650b0d-2311-4b30-a313-ae7529086f12',
    'Weekend Premium - Car',
    'car',
    'day_based',
    NULL,
    NULL,
    1.2,
    'normal',
    true,
    NOW(),
    NOW()
);

-- Update pricing rules with days_of_week for weekend rule
UPDATE pricing_rules 
SET days_of_week = 'saturday,sunday' 
WHERE name LIKE '%Weekend Premium%';

-- Insert Sample Booking (completed)
INSERT INTO bookings (id, user_id, lot_id, vehicle_type, vehicle_number, start_time, end_time, total_amount, status, booking_reference, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000002',
    '6a650b0d-2311-4b30-a313-ae7529086f11',
    'car',
    'DL01AB1234',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '3 hours',
    45.00,
    'completed',
    'SP' || TO_CHAR(NOW(), 'YYYYMMDD') || '1001',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '3 hours'
) ON CONFLICT DO NOTHING;

-- Display summary
DO $$
DECLARE
    user_count INTEGER;
    lot_count INTEGER;
    slot_count INTEGER;
    rule_count INTEGER;
    booking_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO lot_count FROM parking_lots;
    SELECT COUNT(*) INTO slot_count FROM parking_slots;
    SELECT COUNT(*) INTO rule_count FROM pricing_rules;
    SELECT COUNT(*) INTO booking_count FROM bookings;
    
    RAISE NOTICE '🎉 Sample Data Loaded Successfully!';
    RAISE NOTICE '📊 Summary:';
    RAISE NOTICE '   Users: %', user_count;
    RAISE NOTICE '   Parking Lots: %', lot_count;
    RAISE NOTICE '   Parking Slots: %', slot_count;
    RAISE NOTICE '   Pricing Rules: %', rule_count;
    RAISE NOTICE '   Bookings: %', booking_count;
    RAISE NOTICE '';
    RAISE NOTICE '🔐 Login Credentials:';
    RAISE NOTICE '   Admin: admin@smartparking.com / AdminPassword123!';
    RAISE NOTICE '   User: user@smartparking.com / UserPassword123!';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready for testing!';
END $$;
