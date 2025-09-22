--
-- PostgreSQL database dump
--

\restrict hNne62o1fMzeiE6vvXxMadeSoQGYOh3juVUTwqGAUjp9ogLvWzaHaWLt2fB9CN4

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS smart_parking;
--
-- Name: smart_parking; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE smart_parking WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE smart_parking OWNER TO postgres;

\unrestrict hNne62o1fMzeiE6vvXxMadeSoQGYOh3juVUTwqGAUjp9ogLvWzaHaWLt2fB9CN4
\connect smart_parking
\restrict hNne62o1fMzeiE6vvXxMadeSoQGYOh3juVUTwqGAUjp9ogLvWzaHaWLt2fB9CN4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: notificationpriority; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.notificationpriority AS ENUM (
    'low',
    'normal',
    'high',
    'critical'
);


ALTER TYPE public.notificationpriority OWNER TO postgres;

--
-- Name: notificationtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.notificationtype AS ENUM (
    'booking_confirmation',
    'booking_reminder_start',
    'booking_reminder_end',
    'checkin_available',
    'checkin_overdue',
    'booking_cancelled',
    'payment_confirmation',
    'booking_expired',
    'admin_no_show',
    'admin_system_issue',
    'admin_daily_report',
    'admin_maintenance',
    'admin_high_occupancy',
    'checkin_reminder',
    'checkout_reminder'
);


ALTER TYPE public.notificationtype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: bookings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bookings (
    user_id uuid NOT NULL,
    lot_id uuid NOT NULL,
    slot_id uuid,
    vehicle_type character varying(20) NOT NULL,
    vehicle_number character varying(20) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    total_amount numeric(10,2) NOT NULL,
    status character varying(20) NOT NULL,
    booking_reference character varying(20) NOT NULL,
    check_in_time timestamp with time zone,
    check_out_time timestamp with time zone,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    session_id character varying(50),
    reserved_until timestamp with time zone,
    chunk_ids uuid[] DEFAULT '{}'::uuid[] NOT NULL,
    CONSTRAINT check_amount_positive CHECK ((total_amount >= (0)::numeric)),
    CONSTRAINT check_booking_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'confirmed'::character varying, 'active'::character varying, 'completed'::character varying, 'cancelled'::character varying, 'expired'::character varying, 'no_show'::character varying])::text[]))),
    CONSTRAINT check_time_order CHECK ((start_time < end_time))
);


ALTER TABLE public.bookings OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    type public.notificationtype NOT NULL,
    priority public.notificationpriority DEFAULT 'normal'::public.notificationpriority,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    is_sent boolean DEFAULT false,
    scheduled_at timestamp with time zone,
    sent_at timestamp with time zone,
    read_at timestamp with time zone,
    send_email boolean DEFAULT false,
    send_sms boolean DEFAULT false,
    send_push boolean DEFAULT false,
    send_websocket boolean DEFAULT true,
    booking_id uuid,
    lot_id uuid,
    celery_task_id character varying(255),
    notification_metadata text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: parking_lots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parking_lots (
    name character varying(255) NOT NULL,
    address character varying NOT NULL,
    latitude numeric(10,8) NOT NULL,
    longitude numeric(11,8) NOT NULL,
    total_car_slots integer NOT NULL,
    total_bike_slots integer NOT NULL,
    is_active boolean NOT NULL,
    hourly_rate_car numeric(10,2) NOT NULL,
    hourly_rate_bike numeric(10,2) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_bike_rate_positive CHECK ((hourly_rate_bike > (0)::numeric)),
    CONSTRAINT check_bike_slots_positive CHECK ((total_bike_slots >= 0)),
    CONSTRAINT check_car_rate_positive CHECK ((hourly_rate_car > (0)::numeric)),
    CONSTRAINT check_car_slots_positive CHECK ((total_car_slots >= 0))
);


ALTER TABLE public.parking_lots OWNER TO postgres;

--
-- Name: parking_slots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parking_slots (
    lot_id uuid NOT NULL,
    slot_number character varying(10) NOT NULL,
    slot_type character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    is_occupied boolean NOT NULL,
    is_reserved boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_slot_status CHECK (((status)::text = ANY ((ARRAY['available'::character varying, 'occupied'::character varying, 'reserved'::character varying, 'maintenance'::character varying, 'inactive'::character varying])::text[]))),
    CONSTRAINT check_slot_type CHECK (((slot_type)::text = ANY ((ARRAY['car'::character varying, 'bike'::character varying, 'truck'::character varying, 'electric_car'::character varying, 'electric_bike'::character varying])::text[])))
);


ALTER TABLE public.parking_slots OWNER TO postgres;

--
-- Name: payment_cards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payment_cards (
    user_id uuid NOT NULL,
    card_token character varying(100) NOT NULL,
    card_last_four character varying(4) NOT NULL,
    card_brand character varying(20) NOT NULL,
    card_type character varying(20) NOT NULL,
    expiry_month character varying(2) NOT NULL,
    expiry_year character varying(4) NOT NULL,
    cardholder_name character varying(100),
    is_default boolean,
    is_active boolean,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_card_last_four_length CHECK ((length((card_last_four)::text) = 4)),
    CONSTRAINT check_expiry_month_length CHECK ((length((expiry_month)::text) = 2)),
    CONSTRAINT check_expiry_year_length CHECK ((length((expiry_year)::text) = 4))
);


ALTER TABLE public.payment_cards OWNER TO postgres;

--
-- Name: payment_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payment_transactions (
    payment_id uuid NOT NULL,
    transaction_type character varying(20) NOT NULL,
    amount numeric(10,2) NOT NULL,
    status character varying(20) NOT NULL,
    gateway_response json,
    gateway_transaction_id character varying(100),
    reference_number character varying(100),
    notes text,
    processed_at timestamp with time zone,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_amount_non_zero CHECK ((amount <> (0)::numeric)),
    CONSTRAINT check_transaction_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'refunded'::character varying, 'partially_refunded'::character varying])::text[]))),
    CONSTRAINT check_transaction_type CHECK (((transaction_type)::text = ANY ((ARRAY['payment'::character varying, 'refund'::character varying, 'partial_refund'::character varying, 'adjustment'::character varying])::text[])))
);


ALTER TABLE public.payment_transactions OWNER TO postgres;

--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    user_id uuid NOT NULL,
    booking_id uuid,
    amount numeric(10,2) NOT NULL,
    currency character varying(3) NOT NULL,
    payment_method character varying(20) NOT NULL,
    payment_gateway character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    transaction_id character varying(100) NOT NULL,
    gateway_transaction_id character varying(100),
    gateway_reference character varying(100),
    description text,
    payment_metadata json,
    processed_at timestamp with time zone,
    expires_at timestamp with time zone,
    failure_reason text,
    refund_amount numeric(10,2),
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_amount_positive CHECK ((amount > (0)::numeric)),
    CONSTRAINT check_payment_gateway CHECK (((payment_gateway)::text = ANY ((ARRAY['dummy_gateway'::character varying, 'stripe'::character varying, 'razorpay'::character varying, 'paypal'::character varying, 'square'::character varying])::text[]))),
    CONSTRAINT check_payment_method CHECK (((payment_method)::text = ANY ((ARRAY['credit_card'::character varying, 'debit_card'::character varying, 'digital_wallet'::character varying, 'upi'::character varying, 'net_banking'::character varying, 'cash'::character varying])::text[]))),
    CONSTRAINT check_payment_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'refunded'::character varying, 'partially_refunded'::character varying])::text[]))),
    CONSTRAINT check_refund_amount_non_negative CHECK ((refund_amount >= (0)::numeric)),
    CONSTRAINT check_refund_amount_valid CHECK ((refund_amount <= amount))
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: pricing_rules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pricing_rules (
    lot_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    vehicle_type character varying(20) NOT NULL,
    rule_type character varying(20) NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    days_of_week character varying(100),
    price_per_hour numeric(10,2) NOT NULL,
    multiplier numeric(5,2) NOT NULL,
    min_charge numeric(10,2),
    max_charge numeric(10,2),
    is_active boolean NOT NULL,
    priority character varying(10) NOT NULL,
    valid_from time without time zone,
    valid_until time without time zone,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_max_charge CHECK (((max_charge IS NULL) OR (max_charge >= (0)::numeric))),
    CONSTRAINT check_min_charge CHECK (((min_charge IS NULL) OR (min_charge >= (0)::numeric))),
    CONSTRAINT check_min_max_charge CHECK (((min_charge IS NULL) OR (max_charge IS NULL) OR (min_charge <= max_charge))),
    CONSTRAINT check_multiplier_positive CHECK ((multiplier > (0)::numeric)),
    CONSTRAINT check_price_positive CHECK ((price_per_hour > (0)::numeric)),
    CONSTRAINT check_priority CHECK (((priority)::text = ANY ((ARRAY['high'::character varying, 'normal'::character varying, 'low'::character varying])::text[]))),
    CONSTRAINT check_rule_type CHECK (((rule_type)::text = ANY ((ARRAY['time_based'::character varying, 'day_based'::character varying, 'seasonal'::character varying, 'demand_based'::character varying])::text[])))
);


ALTER TABLE public.pricing_rules OWNER TO postgres;

--
-- Name: slot_allocations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.slot_allocations (
    booking_id uuid NOT NULL,
    slot_id uuid NOT NULL,
    allocation_type character varying(10) NOT NULL,
    allocated_space character varying(50),
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_allocation_type CHECK (((allocation_type)::text = ANY ((ARRAY['full'::character varying, 'partial'::character varying])::text[])))
);


ALTER TABLE public.slot_allocations OWNER TO postgres;

--
-- Name: slot_time_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.slot_time_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slot_id uuid NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    status character varying(20) DEFAULT 'available'::character varying NOT NULL,
    booking_id uuid,
    reserved_by uuid,
    reserved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_30_minute_duration CHECK (((end_time - start_time) = '00:30:00'::interval)),
    CONSTRAINT check_chunk_status CHECK (((status)::text = ANY ((ARRAY['available'::character varying, 'booked'::character varying, 'temp_reserved'::character varying])::text[]))),
    CONSTRAINT check_chunk_time_order CHECK ((end_time > start_time))
);


ALTER TABLE public.slot_time_chunks OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    phone character varying(20),
    is_admin boolean NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    total_spent numeric(10,2) DEFAULT 0.00 NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
slot_time_chunks_001
add_notifications_table
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bookings (user_id, lot_id, slot_id, vehicle_type, vehicle_number, start_time, end_time, total_amount, status, booking_reference, check_in_time, check_out_time, id, created_at, updated_at, session_id, reserved_until, chunk_ids) FROM stdin;
0722ba41-40ec-4473-81f6-94fd5fb5cd61	6a650b0d-2311-4b30-a313-ae7529086f11	1989dc43-8ffc-4070-b47b-f21bf278ee29	car	ABC123	2025-12-01 10:00:00+00	2025-12-01 12:00:00+00	10.00	active	8995TD3X	\N	\N	a839b2d6-d6fa-45b7-9edc-3ab8b5bc875f	2025-09-16 14:54:28.431485+00	2025-09-16 14:54:28.431485+00	\N	\N	{}
8fdf35c0-bdcf-48c0-b684-4b830348174c	6a650b0d-2311-4b30-a313-ae7529086f11	a32420d4-302b-431e-816e-88d78c13d29e	car	ABC123	2026-01-01 10:00:00+00	2026-01-01 12:00:00+00	10.00	active	AK0G4YLG	\N	\N	87d4875f-dbab-43e5-a16d-c0c10baf8ac1	2025-09-16 14:58:30.011899+00	2025-09-16 14:58:30.011899+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	51b89dcb-0dd1-4765-be11-850f9c647e67	car	KA123	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	2.50	pending	AG74UKAU	\N	\N	6b1106f0-490d-47d7-a41b-1803d7702e2b	2025-09-18 07:40:31.326378+00	2025-09-18 07:40:31.326378+00	\N	\N	{}
0722ba41-40ec-4473-81f6-94fd5fb5cd61	6a650b0d-2311-4b30-a313-ae7529086f11	09158ccd-1a5c-41a8-ac31-634d72c61886	car	ABC123	2025-12-01 10:00:00+00	2025-12-01 12:00:00+00	10.00	cancelled	JRUWBQE2	\N	\N	42829b96-413d-49d9-bd6c-198098e6dfe7	2025-09-16 15:02:08.144537+00	2025-09-16 15:08:15.671776+00	\N	\N	{}
0722ba41-40ec-4473-81f6-94fd5fb5cd61	6a650b0d-2311-4b30-a313-ae7529086f11	9a80739f-4ec6-4d7d-ae23-f076feef17c9	bike	BIKE456	2025-12-01 14:00:00+00	2025-12-01 16:00:00+00	4.00	cancelled	UGGXEGJX	\N	\N	c504d5c8-298d-4856-a074-647e67fd5e99	2025-09-16 15:08:45.6394+00	2025-09-16 15:08:45.74903+00	\N	\N	{}
8fdf35c0-bdcf-48c0-b684-4b830348174c	6a650b0d-2311-4b30-a313-ae7529086f11	9a80739f-4ec6-4d7d-ae23-f076feef17c9	car	ABC123	2026-02-01 10:00:00+00	2026-02-01 12:00:00+00	10.00	active	F06HPONP	\N	\N	fcad5e2a-0e80-4359-ae78-46ccb30fb71f	2025-09-16 16:38:05.124329+00	2025-09-16 16:38:05.124329+00	\N	\N	{}
8fdf35c0-bdcf-48c0-b684-4b830348174c	6a650b0d-2311-4b30-a313-ae7529086f11	02178346-d1f9-4a2c-887b-4df05877d496	car	ABC123	2025-09-16 22:12:00+00	2025-09-17 12:00:00+00	69.00	active	3O0MJSQ2	\N	\N	48b17e84-f608-401c-b601-46958bc70ca2	2025-09-16 16:40:00.061736+00	2025-09-16 16:40:00.061736+00	\N	\N	{}
e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	19ebc361-a7ac-42ab-9713-e4edd693335d	0fdaae15-b89d-484a-b260-18e9fc297720	car	KA05	2025-09-17 00:59:00+00	2025-09-17 01:57:00+00	4.83	active	NMTJOY0P	\N	\N	73e8c064-afa4-495f-82c8-5f245b7d043f	2025-09-16 19:28:30.625061+00	2025-09-16 19:28:30.625061+00	\N	\N	{}
e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	08c55203-86bf-465f-bc3f-b1cb2cab1088	9d032745-44c7-48e7-a480-c091cf9442a8	car	KA05	2025-09-18 01:02:00+00	2025-09-19 00:02:00+00	115.00	active	K806GNEU	\N	\N	172e35be-142a-46bb-84d9-72d54fa56f5b	2025-09-16 19:34:52.827977+00	2025-09-16 19:34:52.827977+00	\N	\N	{}
e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	6a650b0d-2311-4b30-a313-ae7529086f11	de12fc56-c844-46c8-b7d0-29f6348b571a	bike	KA0QW	2025-09-17 01:55:00+00	2025-09-17 02:54:00+00	1.97	active	IG3VTX54	\N	\N	21710c2f-4780-403b-8a5c-a96afd92e591	2025-09-16 20:24:54.539135+00	2025-09-16 20:24:54.539135+00	\N	\N	{}
e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	6a650b0d-2311-4b30-a313-ae7529086f11	de12fc56-c844-46c8-b7d0-29f6348b571a	bike	KA123	2025-09-17 02:23:00+00	2025-09-17 03:21:00+00	1.93	active	VBKBD0UH	\N	\N	0f2e4a1e-bbbf-404a-9d78-8782e200eac6	2025-09-16 20:52:11.254814+00	2025-09-16 20:52:11.254814+00	\N	\N	{}
e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	19ebc361-a7ac-42ab-9713-e4edd693335d	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	car	MH123	2025-09-16 21:07:00+00	2025-09-16 22:05:00+00	4.83	active	3Q528KAT	\N	\N	ce3dc8c3-c718-4128-9252-2ec51e3398c1	2025-09-16 21:06:33.055373+00	2025-09-16 21:06:33.055373+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	c4921654-ab3a-4908-8381-a29d6717a7cc	car	TEST123	2025-09-17 04:00:00+00	2025-09-17 05:00:00+00	5.00	pending	8IATL6GK	\N	\N	1cf197b6-da80-4be1-8567-2769c137e268	2025-09-16 22:22:51.253553+00	2025-09-16 22:22:51.253553+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	94ee0b96-9b5e-4af2-9934-f3ec41197785	car	TEST999	2025-09-17 06:00:00+00	2025-09-17 07:00:00+00	5.00	pending	0VZ8XI77	\N	\N	e24a2ac1-4611-4d49-874a-ffb07b44ac2b	2025-09-16 22:28:10.150979+00	2025-09-16 22:28:10.150979+00	\N	\N	{}
9f5402f7-1a3d-4f0c-9227-b7a808a64055	6a650b0d-2311-4b30-a313-ae7529086f11	de12fc56-c844-46c8-b7d0-29f6348b571a	car	KA05	2025-09-16 22:35:00+00	2025-09-16 23:32:00+00	4.75	active	1SH5259D	2025-09-16 22:35:03.650853+00	\N	d3e2fb72-ab92-4cf3-ae30-31f947336417	2025-09-16 22:32:59.939053+00	2025-09-16 22:35:03.633021+00	\N	\N	{}
9f5402f7-1a3d-4f0c-9227-b7a808a64055	19ebc361-a7ac-42ab-9713-e4edd693335d	7c4fc29f-a954-48f3-ba9a-db5def5cbc4c	car	KA05	2025-09-16 22:32:00+00	2025-09-16 23:30:00+00	4.83	completed	FALUHTAE	2025-09-16 22:32:21.940894+00	2025-09-16 22:35:10.02195+00	3db90cc3-30d5-4628-a878-7b4a98ff68e1	2025-09-16 22:31:09.854993+00	2025-09-16 22:35:10.004358+00	\N	\N	{}
9f5402f7-1a3d-4f0c-9227-b7a808a64055	19ebc361-a7ac-42ab-9713-e4edd693335d	730a7a60-2535-46cc-a1db-64b92c2eaa43	car	KA05	2025-09-16 22:39:00+00	2025-09-16 23:36:00+00	4.75	pending	RVJ1SH2Q	\N	\N	b28d23a7-de4e-4685-ac2d-e7ad73a8b437	2025-09-16 22:38:07.961939+00	2025-09-16 22:38:07.961939+00	\N	\N	{}
9f5402f7-1a3d-4f0c-9227-b7a808a64055	19ebc361-a7ac-42ab-9713-e4edd693335d	ba02b652-3159-4a2e-8537-e36c944f0f73	bike	KA05	2025-09-16 22:46:00+00	2025-09-16 23:44:00+00	1.93	confirmed	1MSNNHDA	\N	\N	4714c0d0-0abe-42a7-913f-3bfef3ea3ec7	2025-09-16 22:45:20.684275+00	2025-09-16 22:45:41.086899+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	ba02b652-3159-4a2e-8537-e36c944f0f73	car	TEST888	2025-09-17 10:00:00+00	2025-09-17 12:00:00+00	10.00	pending	CQNYD42J	\N	\N	6848ead3-e4f6-4a33-8c59-55ba508edb1d	2025-09-17 00:06:26.332401+00	2025-09-17 00:06:26.332401+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	69afc6ef-5b07-4e2c-b064-1006811e2441	car	KA05	2025-09-17 00:22:00+00	2025-09-17 01:20:00+00	4.83	completed	JRXRPDXH	2025-09-17 00:22:21.313672+00	2025-09-17 00:22:33.856179+00	249c70e5-7eda-4d43-8a73-c6a79f53abbe	2025-09-17 00:20:35.521934+00	2025-09-17 00:22:33.826423+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	\N	car	KA05	2025-09-17 00:24:00+00	2025-09-17 01:22:00+00	4.83	pending	XTCT3198	\N	\N	9ffb5086-eee4-421b-8947-5034326a3244	2025-09-17 00:23:12.475393+00	2025-09-17 00:23:12.475393+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	75e25a61-d293-4ad8-8eb0-72204534e1ad	bike	KA05	2025-09-17 00:28:00+00	2025-09-17 01:25:00+00	1.90	completed	QU7Y7ELR	2025-09-17 00:28:04.526515+00	2025-09-17 00:28:28.599191+00	22d183e7-85d5-47a2-856b-4dd007c84a04	2025-09-17 00:26:30.624223+00	2025-09-17 00:28:28.566816+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	f4e42346-3eb2-4f1b-b1c5-9b1d6088d22a	car	KA05	2025-09-17 01:12:00+00	2025-09-17 02:11:00+00	4.92	completed	262P3MZX	2025-09-17 01:13:19.059343+00	2025-09-17 01:13:23.794437+00	71dda9fe-7b0f-43b5-91ed-98a09051a026	2025-09-17 01:11:41.810018+00	2025-09-17 01:13:23.718573+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	75e25a61-d293-4ad8-8eb0-72204534e1ad	bike	KA123	2025-09-17 01:15:00+00	2025-09-17 02:14:00+00	1.97	completed	PBK2SB3R	2025-09-17 01:15:06.210884+00	2025-09-17 01:15:16.666871+00	5e8dd6e3-6d5c-4b55-8dec-c545efbe4e85	2025-09-17 01:14:35.435579+00	2025-09-17 01:15:16.587811+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	\N	car	SLOT999	2025-09-17 15:00:00+00	2025-09-17 17:00:00+00	10.00	pending	D06EDO81	\N	\N	b4870936-6dac-4d69-a919-f65dd2268c66	2025-09-17 01:26:46.822947+00	2025-09-17 01:26:46.822947+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	\N	car	SLOT999	2025-09-17 15:00:00+00	2025-09-17 17:00:00+00	10.00	pending	Y0GBTZ1B	\N	\N	66dcb681-ff53-42ad-84c7-86ff3a9a6d0f	2025-09-17 01:27:29.750091+00	2025-09-17 01:27:29.750091+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	\N	car	SLOT999	2025-09-17 15:00:00+00	2025-09-17 17:00:00+00	10.00	pending	KNH5G37I	\N	\N	e7ebb4e0-b4e3-4dae-908a-8b1e65ac04e6	2025-09-17 01:29:49.87563+00	2025-09-17 01:29:49.87563+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	\N	car	TEST777	2025-09-17 16:00:00+00	2025-09-17 18:00:00+00	10.00	pending	ZXI4J6R4	\N	\N	48740f73-b7c4-4065-a0ac-b2dfb99d333c	2025-09-17 01:38:54.449217+00	2025-09-17 01:38:54.449217+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	75e25a61-d293-4ad8-8eb0-72204534e1ad	car	TEST777	2025-09-17 16:00:00+00	2025-09-17 18:00:00+00	10.00	pending	G0AW1MM1	\N	\N	7881a3ea-6118-4a1f-8e57-6838a8feee64	2025-09-17 01:41:50.540039+00	2025-09-17 01:41:50.540039+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	07a6cca8-4378-4ae2-a2b1-787095a096e2	car	TEST777	2025-09-17 16:00:00+00	2025-09-17 18:00:00+00	10.00	pending	4O6FM50Q	\N	\N	3ebc6d9b-574b-40b2-873f-6f8a7cf37762	2025-09-17 01:44:00.132873+00	2025-09-17 01:44:00.132873+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	f92ac396-10cb-4769-9473-dc4219133917	car	TEST777	2025-09-17 16:00:00+00	2025-09-17 18:00:00+00	10.00	pending	UKJNPELC	\N	\N	134716c4-d7fa-49ee-b0bf-982d8c3a7a47	2025-09-17 01:48:59.475221+00	2025-09-17 01:48:59.475221+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	77469074-1c57-421c-b741-be1874ffc20e	car	KA123	2025-09-17 01:52:00+00	2025-09-17 02:50:00+00	4.83	completed	Y3HAHTGO	2025-09-17 01:52:12.624753+00	2025-09-17 01:52:48.334061+00	f86fb9a3-dd3b-4355-abb1-363dd80ef9ac	2025-09-17 01:51:30.058877+00	2025-09-17 01:52:48.312949+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	770d358f-74be-456d-8e55-574ccfc63a6f	car	KA123	2025-09-17 01:56:00+00	2025-09-17 02:54:00+00	4.83	completed	8LGJ8ABO	2025-09-17 01:56:05.232823+00	2025-09-17 02:00:03.160403+00	fdd78df5-9efb-4e37-873a-fc8fe4702dfb	2025-09-17 01:55:08.714807+00	2025-09-17 02:00:03.142628+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	96767f13-51c2-4214-9bc5-89167226250f	car	KA123	2025-09-17 02:11:00+00	2025-09-17 03:09:00+00	4.83	confirmed	8MXVEQ1X	\N	\N	bb0e0eef-36de-4594-87e0-8a7659396819	2025-09-17 02:10:07.703016+00	2025-09-17 02:10:16.73097+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	car	KA05	2025-09-17 13:14:00+00	2025-09-17 14:14:00+00	5.00	cancelled	P98C4OSA	\N	\N	ae3f7f91-3b71-469e-aaf5-cc53435ec928	2025-09-17 10:15:35.544604+00	2025-09-17 10:16:04.314555+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	a9ab64f3-810c-478d-8153-71f52ae0e9d7	car	CANCEL123	2025-09-18 14:00:00+00	2025-09-18 16:00:00+00	10.00	cancelled	SII7S8E0	\N	\N	e7db2281-a5b1-4d61-818c-973b7735e6f2	2025-09-17 10:16:34.385982+00	2025-09-17 10:18:28.139064+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	ad18a635-72f1-47a2-8454-2561a5e175ad	car	KA05	2025-09-17 13:21:00+00	2025-09-17 14:21:00+00	5.00	cancelled	ZF2WSN2Z	\N	\N	a4e6e27a-a08b-4362-af7f-27acaefdf610	2025-09-17 10:22:10.789201+00	2025-09-17 10:22:27.358874+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	0f0cf325-b73a-46f7-8f93-c37af1b11f82	car	FLEX123	2025-09-17 11:06:48+00	2025-09-17 13:09:48+00	10.25	pending	30OQ6DVI	\N	\N	bd205075-5b6d-4665-831f-8d08fc189c57	2025-09-17 11:09:48.19824+00	2025-09-17 11:09:48.19824+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	7c4fc29f-a954-48f3-ba9a-db5def5cbc4c	car	KA05	2025-09-17 11:14:00+00	2025-09-17 12:14:00+00	5.00	pending	AWBGHI8K	\N	\N	947ad9a8-89f9-432d-a66c-743b2c5d5d4c	2025-09-17 11:14:19.000154+00	2025-09-17 11:14:19.000154+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	69afc6ef-5b07-4e2c-b064-1006811e2441	car	KA05	2025-09-17 11:25:00+00	2025-09-17 12:25:00+00	5.00	pending	7BIM2WG6	\N	\N	a3e32ea8-7e2d-4050-9600-1836c3a3318c	2025-09-17 11:25:53.346293+00	2025-09-17 11:25:53.346293+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	77469074-1c57-421c-b741-be1874ffc20e	car	KA05	2025-09-17 11:25:00+00	2025-09-17 12:25:00+00	5.00	pending	QD9IPC0S	\N	\N	df52b94d-ac73-46c2-9085-62d76e3626f8	2025-09-17 11:26:11.551292+00	2025-09-17 11:26:11.551292+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	bike	KA05	2025-09-17 11:39:00+00	2025-09-17 12:32:00+00	1.77	confirmed	J5WY4G70	\N	\N	52e2e1b6-45cb-4e62-83f1-8a5414380cbd	2025-09-17 11:36:12.607081+00	2025-09-17 11:38:37.970916+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	2adf58fb-1940-411c-bedf-09b807e576da	car	KA123	2025-09-17 11:48:00+00	2025-09-17 12:47:00+00	4.92	confirmed	P1Q42GQJ	\N	\N	8c3f2189-a74b-4ed4-90db-76bbca711a0f	2025-09-17 11:48:47.339712+00	2025-09-17 11:48:54.170419+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	bike	BIKE123	2025-09-18 14:00:00+00	2025-09-18 16:00:00+00	4.00	pending	OECL7XD9	\N	\N	1ac5e546-963c-44e1-ad5e-c1d415703eba	2025-09-17 11:53:39.08082+00	2025-09-17 11:53:39.08082+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	b1ad04e1-530d-4bf1-b4a5-94201487bd22	bike	KA123	2025-09-17 11:45:00+00	2025-09-17 12:44:00+00	1.97	completed	L7MMVZUO	2025-09-17 11:45:15.439181+00	2025-09-18 03:10:11.631101+00	63c17482-cc20-4880-ba6b-75ef5169a15d	2025-09-17 11:45:04.668625+00	2025-09-18 03:10:11.617032+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	6a650b0d-2311-4b30-a313-ae7529086f11	f78203d8-1ebb-46c8-8a92-ae5055f99508	car	KA123	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	2.50	pending	XSFJV6L3	\N	\N	bed7a9a9-62cc-4048-815c-848261d9dc4f	2025-09-18 10:36:15.91756+00	2025-09-18 10:36:15.91756+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	bike	BIKENOW123	2025-09-17 11:55:04+00	2025-09-17 13:55:04+00	4.00	pending	05ONNQ2B	\N	\N	3fe23984-f479-4859-8b7d-b5417755d344	2025-09-17 11:55:04.554015+00	2025-09-17 11:55:04.554015+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	021f915f-61fa-4e83-a1a4-f428a5c7cef1	bike	KA05	2025-09-17 11:59:00+00	2025-09-17 12:58:00+00	1.97	confirmed	IYWD670S	\N	\N	5a6fc274-9767-4ad5-a18e-ff5f480a82f6	2025-09-17 11:59:01.961458+00	2025-09-17 11:59:07.893691+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	11eee77b-1e5b-46d6-a0af-a22a1e3670a8	bike	KA123	2025-09-17 11:47:00+00	2025-09-17 12:46:00+00	1.97	completed	RA4WL3BB	2025-09-17 11:47:07.443874+00	2025-09-17 11:59:27.183258+00	4698a26b-468c-4c19-9032-05a91f2ac7f2	2025-09-17 11:47:00.231605+00	2025-09-17 11:59:27.141718+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	bike	BIKE456	2025-09-18 14:00:00+00	2025-09-18 16:00:00+00	4.00	pending	Q5EC6JAC	\N	\N	816246ba-c8a9-496c-8c94-b31041a34632	2025-09-17 12:05:00.750013+00	2025-09-17 12:05:00.750013+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	021f915f-61fa-4e83-a1a4-f428a5c7cef1	bike	KA05	2025-09-17 12:08:00+00	2025-09-17 13:07:00+00	1.97	confirmed	G7EL2WU8	\N	\N	2fd16f72-3a05-4ddc-be07-01e3ddb2df73	2025-09-17 12:08:25.709483+00	2025-09-17 12:08:37.028116+00	\N	\N	{}
c1842768-eeb5-468b-beb6-4e356bc66a62	19ebc361-a7ac-42ab-9713-e4edd693335d	a9ab64f3-810c-478d-8153-71f52ae0e9d7	bike	BIKE789	2025-09-18 14:00:00+00	2025-09-18 16:00:00+00	4.00	pending	Q1XMPSN5	\N	\N	3eaf41df-3b13-4372-9f8c-e138507a9ae3	2025-09-17 12:12:08.851801+00	2025-09-17 12:12:08.851801+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	a9ab64f3-810c-478d-8153-71f52ae0e9d7	car	KA05	2025-09-17 14:00:00+00	2025-09-17 15:30:00+00	7.50	confirmed	S1VP1K4N	\N	\N	355d542e-0436-4ba1-a5c3-4e217f701caa	2025-09-17 13:32:59.376569+00	2025-09-17 13:33:09.996389+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	ad18a635-72f1-47a2-8454-2561a5e175ad	car	KA05	2025-09-17 14:00:00+00	2025-09-17 16:30:00+00	12.50	pending	MB1IEF5H	\N	\N	2a82571b-c651-49b9-9610-2c4d5f8e4bd1	2025-09-17 13:34:10.216217+00	2025-09-17 13:34:10.216217+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	6a650b0d-2311-4b30-a313-ae7529086f11	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	car	FINAL001	2025-09-20 08:00:00+00	2025-09-20 09:00:00+00	8.00	pending	E2XNZM7C	\N	\N	954e27f4-bef9-4b84-ae94-1d758c5dfe36	2025-09-20 03:09:02.770059+00	2025-09-20 03:09:02.770059+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	eb84e3d3-e7b9-4449-817f-be669b58ce41	bike	KA123	2025-09-17 14:00:00+00	2025-09-17 15:30:00+00	3.00	confirmed	JGE2XNCG	\N	\N	11a0365e-2a50-42d1-91ae-c43b2cc9bde8	2025-09-17 13:35:50.854856+00	2025-09-17 13:36:00.273009+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	08c55203-86bf-465f-bc3f-b1cb2cab1088	fe509eba-32af-4941-92f8-6d65deb6fc3c	car	ABCDE	2025-09-20 03:14:19.821+00	2025-09-20 04:09:07.978+00	4.57	pending	0WG1C1HK	\N	\N	410b034d-2db1-4783-8607-803b7bd14ca9	2025-09-20 03:09:19.884399+00	2025-09-20 03:09:19.884399+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	eb84e3d3-e7b9-4449-817f-be669b58ce41	car	KA123	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	2.50	confirmed	A5F91SOO	\N	\N	14261ddc-a5ec-4445-8d4c-7f0f00d13787	2025-09-17 13:36:59.280465+00	2025-09-17 13:37:13.807571+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	08c55203-86bf-465f-bc3f-b1cb2cab1088	a704960a-8750-4a1d-be7f-1553ed110778	bike	ABCDE	2025-09-20 03:15:33.636+00	2025-09-20 04:10:18.099+00	1.82	pending	PP6TRLSX	\N	\N	c8fdf651-9d55-427f-8257-fa7fd47fbfbc	2025-09-20 03:10:33.707769+00	2025-09-20 03:10:33.707769+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	car	KA123	2025-09-17 15:36:00+00	2025-09-17 16:33:00+00	4.75	confirmed	7T7MKYWO	\N	\N	479061b4-9aea-4331-93e0-709aa16bcbc8	2025-09-17 15:33:21.316803+00	2025-09-17 15:33:25.997921+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	6a650b0d-2311-4b30-a313-ae7529086f11	41a3e636-f6f4-45d2-9dd3-621b27985589	car	GRACE002	2025-09-20 03:20:00+00	2025-09-20 04:20:00+00	12.00	pending	J2B1KR31	\N	\N	291d42b5-bce4-4354-a6b7-396bef311c31	2025-09-20 03:16:55.371863+00	2025-09-20 03:16:55.371863+00	\N	\N	{}
5b0c9625-bf8a-4e7c-81b4-903c34465157	08c55203-86bf-465f-bc3f-b1cb2cab1088	47491068-c3e6-48ed-93ca-d0eee23ad389	car	ABCDE	2025-09-20 03:41:48.192+00	2025-09-20 04:41:48.192+00	5.00	pending	HSL5WP45	\N	\N	74afad85-cdda-45a0-885d-abbdf0e10560	2025-09-20 03:41:58.77605+00	2025-09-20 03:41:58.77605+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	29fe9803-57d5-40cd-8a51-859ca4cf47e5	car	KA123	2025-09-17 17:01:00+00	2025-09-17 18:30:00+00	7.42	confirmed	LGB9PWRG	\N	\N	a2a03b23-fbc0-470a-99c9-46ee5d4aa99d	2025-09-17 16:45:01.82043+00	2025-09-17 16:45:08.274111+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	68d5ded7-79c8-45bc-97cf-05ed5b4f9191	car	ABCDE	2025-09-20 16:20:16.959+00	2025-09-20 17:20:16.959+00	5.00	pending	FILK79TV	\N	\N	abe40b95-8fc1-411c-9fdc-620b63774291	2025-09-20 16:20:26.639794+00	2025-09-20 16:20:26.639794+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	021f915f-61fa-4e83-a1a4-f428a5c7cef1	car	KA123	2025-09-17 18:01:00+00	2025-09-17 18:30:00+00	2.42	confirmed	48QX5NAK	\N	\N	08984a73-af52-4a40-846a-f385bc66c9fc	2025-09-17 17:48:37.828551+00	2025-09-17 17:48:47.990347+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	c309a8d6-77e5-469b-9595-c503d0e3b07e	car	ABCDE	2025-09-20 16:27:56.871+00	2025-09-20 17:27:56.871+00	30.00	pending	B8VHOF1Z	\N	\N	f734c673-f0ab-41b0-9176-7297a48d95c2	2025-09-20 16:28:05.419037+00	2025-09-20 16:28:05.419037+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	36a7cea3-2c6d-45c1-964d-9b6d40249d00	car	KA123	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	2.50	confirmed	SJ8F8T50	\N	\N	11be4ded-ea1a-422a-bfc9-d15c1af4d484	2025-09-17 17:53:48.054063+00	2025-09-17 17:53:53.348895+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	b188d489-15e0-4c4f-83b0-4cc68bc920da	car	KA123	2025-09-17 16:35:00+00	2025-09-17 17:34:00+00	4.92	completed	DLBSY41C	2025-09-17 16:35:02.803665+00	2025-09-18 03:09:59.059434+00	f630ea92-646c-49c5-97dd-1a893dc12c3b	2025-09-17 16:34:56.367642+00	2025-09-18 03:09:59.00247+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	4cf4da74-02b5-450c-9098-942c007cfd02	car	KA123	2025-09-17 15:55:00+00	2025-09-17 16:54:00+00	4.92	completed	28F8VG41	2025-09-17 15:55:03.155431+00	2025-09-18 03:10:00.791901+00	401de1ab-9cd2-4a71-850e-8361b0d0162c	2025-09-17 15:54:53.97682+00	2025-09-18 03:10:00.77868+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	car	KA05	2025-09-17 13:16:00+00	2025-09-17 14:15:00+00	4.92	completed	1KSJPC4F	2025-09-17 13:16:07.317159+00	2025-09-18 03:10:03.784033+00	f5d27fa3-f908-4332-b5ad-5b43a4f57966	2025-09-17 13:15:39.574356+00	2025-09-18 03:10:03.768447+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	41037616-20b5-4a9b-a0f2-288504f84d2b	bike	KA05	2025-09-17 12:09:00+00	2025-09-17 13:08:00+00	1.97	completed	V4Q78B46	2025-09-17 12:09:19.162318+00	2025-09-18 03:10:06.282202+00	41a21c20-12af-4d18-a46e-60b3a6a30b13	2025-09-17 12:09:11.028905+00	2025-09-18 03:10:06.273294+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	6a650b0d-2311-4b30-a313-ae7529086f11	11eee77b-1e5b-46d6-a0af-a22a1e3670a8	bike	KA123	2025-09-17 11:46:00+00	2025-09-17 12:45:00+00	1.97	completed	OKM67N00	2025-09-17 11:51:47.097757+00	2025-09-18 03:10:09.484974+00	bbca2869-f474-47c5-a87d-92cb9e3a2df5	2025-09-17 11:45:47.904761+00	2025-09-18 03:10:09.448982+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	cedffa56-a5b9-421e-8cf3-4dab8aa44d36	bike	ABCDE	2025-09-21 08:42:07.909+00	2025-09-21 09:42:07.909+00	2.00	pending	6TZK6DAN	\N	\N	9cbb2822-c23c-4278-b90f-356e050e202c	2025-09-21 08:42:22.296129+00	2025-09-21 08:42:22.296129+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	5d5747f7-b6e8-42c7-bb83-9159057b949b	car	ABCDE	2025-09-21 09:18:23.287+00	2025-09-21 10:18:23.287+00	5.00	pending	V5QAX3WQ	\N	\N	0e35beef-08d9-42ef-bbe1-c330ddac97b1	2025-09-21 09:18:31.824734+00	2025-09-21 09:18:31.824734+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	05d8aa52-d6f0-4ac4-b595-b8e708b695d6	bike	ABCDE	2025-09-21 09:56:46.892+00	2025-09-21 10:56:46.892+00	2.00	completed	EOVQ97YU	2025-09-21 10:50:18.581989+00	2025-09-21 10:50:34.597246+00	0323eab7-f0f0-462a-a969-837cb27a9e6f	2025-09-21 09:56:55.550392+00	2025-09-21 10:50:34.579519+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	a276b69a-5df7-4dd8-84df-c7874543fa4e	car	ABCDE	2025-09-21 10:52:56.137+00	2025-09-21 11:52:56.137+00	5.00	completed	0440S2QH	2025-09-21 10:53:15.082432+00	2025-09-21 10:53:24.087373+00	17ed2b0c-605b-4773-b10a-408fc45dad93	2025-09-21 10:53:05.517814+00	2025-09-21 10:53:24.075159+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	0dfeb933-6940-4c2b-9b81-f71a9035e8f8	car	ABCDE	2025-09-21 11:50:09.429+00	2025-09-21 12:50:09.429+00	5.00	completed	905819TV	2025-09-21 11:50:32.765535+00	2025-09-21 11:50:41.360415+00	ecf03eaf-14cf-41c0-a73d-ae31d4ff55c9	2025-09-21 11:50:18.431841+00	2025-09-21 11:50:41.286859+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	ea268287-f5d1-4ffd-bd58-dc17b1ae2464	car	ABCDE	2025-09-21 12:40:09.452+00	2025-09-21 13:40:09.452+00	5.00	completed	G52KRC0G	2025-09-21 12:40:24.83161+00	2025-09-21 12:40:29.690172+00	a1f56ea6-43f9-40c0-873e-a717405a6fae	2025-09-21 12:40:17.249452+00	2025-09-21 12:40:29.675907+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	b9360900-0194-4a58-ac78-c4ed9e833461	car	ABCDE	2025-09-21 11:24:01.566+00	2025-09-21 12:24:01.566+00	5.00	completed	9YAU0DOV	2025-09-21 11:24:24.968721+00	2025-09-21 12:40:32.349835+00	a4599bf0-5b53-4c84-9bd0-4d39d38427c4	2025-09-21 11:24:10.950637+00	2025-09-21 12:40:32.337098+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	3391a24e-ccb4-43d0-b859-6627cd0efc00	car	ABCDE	2025-09-21 13:01:40.936+00	2025-09-21 14:01:40.936+00	5.00	completed	ZZIZ6ABG	2025-09-21 13:01:59.754239+00	2025-09-21 13:02:03.734913+00	bf5076dc-644f-47cb-af1c-7afe53e3c49c	2025-09-21 13:01:51.051903+00	2025-09-21 13:02:03.725722+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	81c7545e-b387-4a2a-9927-b0c54e770955	car	ABCDE	2025-09-21 13:10:23.075+00	2025-09-21 14:10:23.075+00	5.00	completed	LWLFQ9DB	2025-09-21 13:10:42.288399+00	2025-09-21 13:10:45.9923+00	e43c7b82-8e1a-43ed-a4f2-39c181fcc21d	2025-09-21 13:10:37.628636+00	2025-09-21 13:10:45.886618+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	6d780bf6-e999-40f1-88b6-473a4ecdda18	car	ABCDE	2025-09-21 16:36:08.279+00	2025-09-21 17:36:08.279+00	5.00	completed	Q9BGMMIC	2025-09-21 16:36:24.456513+00	2025-09-21 16:36:31.336259+00	8b00cc2c-46c0-4e47-83bb-d7c480a42ab5	2025-09-21 16:36:17.789604+00	2025-09-21 16:36:31.229606+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	707a46b3-2c9d-4be0-8c4e-0b7671ac6931	car	ABCDE	2025-09-21 17:22:50.793+00	2025-09-21 18:22:50.793+00	5.00	completed	CY96RI5P	2025-09-21 17:23:07.689153+00	2025-09-21 17:23:13.194635+00	121fb8fa-0704-4303-8e77-a432bbfe48fd	2025-09-21 17:23:01.835113+00	2025-09-21 17:23:13.167986+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	ffaad7bd-a5e3-448a-9828-b7643f94fefe	car	ABCDE	2025-09-21 18:56:32.708+00	2025-09-21 19:56:32.708+00	5.00	completed	GQG4WNQ8	2025-09-21 18:56:47.202064+00	2025-09-21 18:56:53.116608+00	a2e9ca25-ca47-4748-a18c-8b133a4eb776	2025-09-21 18:56:41.823072+00	2025-09-21 18:56:53.06955+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	bc2929e5-9ba7-4964-893b-c4efa02c368b	car	ABCDE	2025-09-21 19:48:38.356+00	2025-09-21 20:48:38.356+00	5.00	completed	QUHS1RI1	2025-09-21 19:48:56.793384+00	2025-09-21 19:50:16.341629+00	5b8d3929-0cc4-41a3-bae1-30644ebafb06	2025-09-21 19:48:47.736551+00	2025-09-21 19:50:16.291448+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	19ebc361-a7ac-42ab-9713-e4edd693335d	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	car	ABCDE	2025-09-21 20:10:35.713+00	2025-09-21 21:10:35.713+00	12.00	completed	M2W3RJ7F	2025-09-21 20:10:51.463601+00	2025-09-21 20:10:55.30412+00	8c84b7c2-2fea-4830-84bd-92bcd3a70c25	2025-09-21 20:10:46.089844+00	2025-09-21 20:10:55.293564+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	a4f1bcea-2fbe-4271-b576-b4cbe0d44dd3	bike	ABCDE	2025-09-21 20:21:51.914+00	2025-09-21 21:21:51.914+00	2.00	completed	TGMG1TC3	2025-09-21 20:22:11.079883+00	2025-09-21 20:22:28.608647+00	7465b795-68cd-4365-8dba-ec5132736c96	2025-09-21 20:21:59.85407+00	2025-09-21 20:22:28.571236+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	4c71e1ab-50f6-4b91-a886-b11982dd3474	car	ABCDE	2025-09-21 20:52:46.101+00	2025-09-21 21:52:46.101+00	5.00	completed	82D47BL3	2025-09-21 20:52:57.700782+00	2025-09-21 20:53:02.17042+00	f11a4792-cab3-46db-886b-479d8e5bebe7	2025-09-21 20:52:54.61045+00	2025-09-21 20:53:02.153063+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	cd81f033-7248-45a3-ac82-1c310665f985	490cd266-cdf0-440a-abef-9a85292aabec	car	ABCDE	2025-09-21 20:53:35.296+00	2025-09-21 21:53:35.296+00	6.00	completed	XJSYFA3Q	2025-09-21 20:53:46.352122+00	2025-09-21 20:53:49.935782+00	d78b84d2-16a5-48d8-85df-8d05b74c6728	2025-09-21 20:53:43.139548+00	2025-09-21 20:53:49.925578+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	f74d4035-4855-418e-8852-e990b7dd7e75	car	ABCDE	2025-09-21 21:55:59.192+00	2025-09-21 22:55:59.192+00	5.00	completed	2LXJFHXH	2025-09-21 21:56:13.797376+00	2025-09-21 21:56:16.917409+00	b092e09a-ad61-4b91-b9a7-9d400e720862	2025-09-21 21:56:07.829568+00	2025-09-21 21:56:16.906136+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	13025bce-1592-4b97-96a6-726003a8b211	car	ABCDE	2025-09-21 22:36:18.135+00	2025-09-21 23:36:18.135+00	5.00	completed	MJY1ULS4	2025-09-21 22:36:32.634362+00	2025-09-21 22:36:55.766132+00	03efa86b-e588-4e83-9156-5a90cbdfb507	2025-09-21 22:36:28.221515+00	2025-09-21 22:36:55.755736+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	0e5faa49-cd4c-4a39-bda6-ffe43ccb386c	car	ABCDE	2025-09-21 22:42:44.456+00	2025-09-21 23:42:44.456+00	5.00	active	HNOO4E6V	2025-09-21 22:47:28.773464+00	\N	decdceea-bd8f-45b9-ae10-e156244af0dc	2025-09-21 22:42:57.339987+00	2025-09-21 22:47:28.741173+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	cd81f033-7248-45a3-ac82-1c310665f985	599b9887-075f-4667-8992-0a3c07801975	car	ABCDE	2025-09-21 23:00:24.225+00	2025-09-22 00:00:24.225+00	6.00	active	DP28VHXZ	2025-09-21 23:12:06.867553+00	\N	c181c544-2c9f-4459-8fbf-01a9b5d3a932	2025-09-21 23:00:50.433907+00	2025-09-21 23:12:06.838966+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	cd81f033-7248-45a3-ac82-1c310665f985	9e4f166f-8894-426d-97b6-8d0a51e3bbc6	car	ABCDE	2025-09-21 23:26:16.587+00	2025-09-22 00:26:16.587+00	6.00	active	V012KLEF	2025-09-21 23:27:05.789594+00	\N	0027fc1b-8c8e-4cf9-b7c7-bbc453d5b60e	2025-09-21 23:26:35.494586+00	2025-09-21 23:27:05.710197+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	931c3658-819b-4843-95ba-85e7b7ec5360	car	ABCDE	2025-09-21 23:24:12.476+00	2025-09-22 00:24:12.476+00	5.00	active	G0DJ47U4	2025-09-21 23:27:13.06368+00	\N	7c55d769-1886-4a9a-aea5-e25b4686bd23	2025-09-21 23:24:26.367927+00	2025-09-21 23:27:12.987512+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	17715b50-c74a-4fae-a9fc-d59a5d008729	car	ABCDE	2025-09-21 23:16:00.691+00	2025-09-22 00:16:00.691+00	5.00	active	1T0INJO8	2025-09-21 23:27:17.493315+00	\N	03ae1893-f495-481c-86e0-63bb89559d5c	2025-09-21 23:16:12.895404+00	2025-09-21 23:27:17.405378+00	\N	\N	{}
af99f3e6-84eb-42d7-8d10-c80ad4138e4e	08c55203-86bf-465f-bc3f-b1cb2cab1088	c4d71026-9b0c-4e45-a465-0350378d7036	car	ABCDE	2025-09-21 23:12:44.95+00	2025-09-22 00:12:44.95+00	5.00	active	ARTNSOBE	2025-09-21 23:27:22.243134+00	\N	dbf8d886-108e-4516-a387-02387a6ae2d0	2025-09-21 23:12:57.335645+00	2025-09-21 23:27:22.198557+00	\N	\N	{}
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, user_id, type, priority, title, message, is_read, is_sent, scheduled_at, sent_at, read_at, send_email, send_sms, send_push, send_websocket, booking_id, lot_id, celery_task_id, notification_metadata, created_at, updated_at) FROM stdin;
46e70a67-9b0e-475d-93dc-785421277bb6	ac1ef1d8-d27e-43b3-9e96-d5ba839628fc	payment_confirmation	normal	Payment Confirmed	Payment of $25.50 has been processed successfully.	t	t	\N	\N	\N	f	f	f	t	\N	\N	\N	\N	2025-09-21 22:41:04.244868+00	2025-09-21 22:41:04.244868+00
8a428727-65dd-4542-8ed9-9f34a8cb0063	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	booking_confirmation	normal	Booking Created Successfully	Your parking booking at University Campus Parking has been created successfully. Booking ID: DP28VHXZ	f	t	\N	2025-09-21 23:00:50.631293+00	\N	f	f	f	t	c181c544-2c9f-4459-8fbf-01a9b5d3a932	cd81f033-7248-45a3-ac82-1c310665f985	\N	{"booking_reference": "DP28VHXZ", "lot_name": "University Campus Parking", "start_time": "2025-09-21T23:00:24.225000+00:00", "end_time": "2025-09-22T00:00:24.225000+00:00", "total_amount": 6.0, "vehicle_type": "car", "slot_number": "C002"}	2025-09-21 23:00:50.433907+00	2025-09-21 23:00:50.597947+00
f9165005-9f83-4176-83ea-f717df66b3a7	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	booking_confirmation	normal	Booking Created Successfully	Your parking booking at Shopping Mall Parking has been created successfully. Booking ID: ARTNSOBE	f	t	\N	\N	\N	f	f	f	t	dbf8d886-108e-4516-a387-02387a6ae2d0	08c55203-86bf-465f-bc3f-b1cb2cab1088	\N	{"booking_reference": "ARTNSOBE", "lot_name": "Shopping Mall Parking", "start_time": "2025-09-21T23:12:44.950000+00:00", "end_time": "2025-09-22T00:12:44.950000+00:00", "total_amount": 5.0, "vehicle_type": "car", "slot_number": "C022"}	2025-09-21 23:12:57.335645+00	2025-09-21 23:12:57.335645+00
79365139-948e-4925-aeb0-a3aaca9ebefb	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	booking_confirmation	normal	Booking Created Successfully	Your parking booking at Shopping Mall Parking has been created successfully. Booking ID: 1T0INJO8	f	t	\N	\N	\N	f	f	f	t	03ae1893-f495-481c-86e0-63bb89559d5c	08c55203-86bf-465f-bc3f-b1cb2cab1088	\N	{"booking_reference": "1T0INJO8", "lot_name": "Shopping Mall Parking", "start_time": "2025-09-21T23:16:00.691000+00:00", "end_time": "2025-09-22T00:16:00.691000+00:00", "total_amount": 5.0, "vehicle_type": "car", "slot_number": "C023"}	2025-09-21 23:16:12.895404+00	2025-09-21 23:16:12.895404+00
d104d355-0a19-48cd-aeae-58d47ec71342	2307bee9-d3eb-4d2c-ba37-d0acd4f5de76	checkin_reminder	high	Check-in Reminder	Your parking booking starts in 5 minutes. Please check in now to secure your spot at Downtown Plaza.	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-001", "lot_name": "Downtown Plaza", "minutes_before": 5, "reminder_type": "checkin"}	2025-09-21 23:23:10.73349+00	2025-09-21 23:23:10.73349+00
9f307948-f395-4b6f-8375-a95bdcbb74e8	2307bee9-d3eb-4d2c-ba37-d0acd4f5de76	checkout_reminder	high	Check-out Reminder	Your parking booking ends in 5 minutes. Please check out soon to avoid overstay charges at Mall Parking.	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-002", "lot_name": "Mall Parking", "minutes_before": 5, "reminder_type": "checkout"}	2025-09-21 23:23:10.73349+00	2025-09-21 23:23:10.73349+00
577aeddc-1739-4f64-8ddd-a956af59d22b	2307bee9-d3eb-4d2c-ba37-d0acd4f5de76	booking_confirmation	normal	Booking Created Successfully	Your parking booking at Business District has been created successfully. Booking ID: SP-2024-003	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-003", "lot_name": "Business District", "total_amount": 18.75, "vehicle_type": "car"}	2025-09-21 23:23:10.73349+00	2025-09-21 23:23:10.73349+00
ce6a9b35-7c6d-4462-8e98-36919ac9725e	5b0c9625-bf8a-4e7c-81b4-903c34465157	checkin_reminder	high	Check-in Reminder	Your parking booking starts in 5 minutes. Please check in now to secure your spot at Downtown Plaza.	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-001", "lot_name": "Downtown Plaza", "minutes_before": 5, "reminder_type": "checkin"}	2025-09-21 23:24:17.143715+00	2025-09-21 23:24:17.143715+00
ec5cf0f0-1528-4945-9f5e-baa612f93f50	5b0c9625-bf8a-4e7c-81b4-903c34465157	checkout_reminder	high	Check-out Reminder	Your parking booking ends in 5 minutes. Please check out soon to avoid overstay charges at Mall Parking.	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-002", "lot_name": "Mall Parking", "minutes_before": 5, "reminder_type": "checkout"}	2025-09-21 23:24:17.143715+00	2025-09-21 23:24:17.143715+00
7bbcb4fc-846a-43e3-96e7-1e871e720372	5b0c9625-bf8a-4e7c-81b4-903c34465157	booking_confirmation	normal	Booking Created Successfully	Your parking booking at Business District has been created successfully. Booking ID: SP-2024-003	f	t	\N	\N	\N	f	f	f	t	\N	\N	\N	{"booking_reference": "SP-2024-003", "lot_name": "Business District", "total_amount": 18.75, "vehicle_type": "car"}	2025-09-21 23:24:17.143715+00	2025-09-21 23:24:17.143715+00
b9159228-f271-4f88-8895-d59d47861c11	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	booking_confirmation	normal	Booking Created Successfully	Your parking booking at Shopping Mall Parking has been created successfully. Booking ID: G0DJ47U4	f	t	\N	\N	\N	f	f	f	t	7c55d769-1886-4a9a-aea5-e25b4686bd23	08c55203-86bf-465f-bc3f-b1cb2cab1088	\N	{"booking_reference": "G0DJ47U4", "lot_name": "Shopping Mall Parking", "start_time": "2025-09-21T23:24:12.476000+00:00", "end_time": "2025-09-22T00:24:12.476000+00:00", "total_amount": 5.0, "vehicle_type": "car", "slot_number": "C024"}	2025-09-21 23:24:26.367927+00	2025-09-21 23:24:26.367927+00
75a8f2af-d82b-46c8-a618-48dd099afe15	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	booking_confirmation	normal	Booking Created Successfully	Your parking booking at University Campus Parking has been created successfully. Booking ID: V012KLEF	f	t	\N	\N	\N	f	f	f	t	0027fc1b-8c8e-4cf9-b7c7-bbc453d5b60e	cd81f033-7248-45a3-ac82-1c310665f985	\N	{"booking_reference": "V012KLEF", "lot_name": "University Campus Parking", "start_time": "2025-09-21T23:26:16.587000+00:00", "end_time": "2025-09-22T00:26:16.587000+00:00", "total_amount": 6.0, "vehicle_type": "car", "slot_number": "C003"}	2025-09-21 23:26:35.494586+00	2025-09-21 23:26:35.494586+00
\.


--
-- Data for Name: parking_lots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_lots (name, address, latitude, longitude, total_car_slots, total_bike_slots, is_active, hourly_rate_car, hourly_rate_bike, id, created_at, updated_at) FROM stdin;
Downtown Plaza Parking	123 Main Street, Downtown, NY 10001	40.71280000	-74.00600000	150	75	t	8.00	3.00	6a650b0d-2311-4b30-a313-ae7529086f11	2025-09-16 11:30:31.317959+00	2025-09-16 11:30:31.317959+00
Shopping Mall Parking	789 Mall Avenue, Brooklyn, NY 11201	40.68920000	-73.94420000	200	100	t	5.00	2.00	08c55203-86bf-465f-bc3f-b1cb2cab1088	2025-09-16 11:30:31.317959+00	2025-09-16 11:30:31.317959+00
University Campus Parking	321 College Street, Manhattan, NY 10003	40.72820000	-73.99420000	100	150	t	6.00	2.50	cd81f033-7248-45a3-ac82-1c310665f985	2025-09-16 11:30:31.317959+00	2025-09-16 11:30:31.317959+00
Central Mall	somewhere	1.00000000	1.00000000	100	100	t	5.00	3.00	a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	2025-09-17 19:09:38.279597+00	2025-09-17 19:09:38.279597+00
Test Parking Lot Name Updated	123 Test Street, Test City Updated	40.70000000	-74.00000000	51	26	t	10.00	7.00	0a897ba2-06ae-4748-a192-0f139f6831cf	2025-09-16 13:41:24.269488+00	2025-09-17 23:21:15.442233+00
Airport Long-Term Parking	456 Airport Drive, Queens, NY 11430	40.64130000	-73.77810000	301	51	t	12.00	4.00	19ebc361-a7ac-42ab-9713-e4edd693335d	2025-09-16 11:30:31.317959+00	2025-09-17 23:36:26.155833+00
Test Admin Lot	123 Admin Street, Test City	40.71280000	-74.00600000	10	10	t	10.00	4.00	59fa0039-1f4c-468a-b434-b67cdd7a20d4	2025-09-17 18:58:43.650278+00	2025-09-17 23:49:26.350287+00
\.


--
-- Data for Name: parking_slots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_slots (lot_id, slot_number, slot_type, status, is_occupied, is_reserved, id, created_at, updated_at) FROM stdin;
6a650b0d-2311-4b30-a313-ae7529086f11	C022	car	available	f	f	f775ffa1-953c-4e09-8a5a-2f0f02ef46ba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C023	car	available	f	f	445bbc05-db02-4daa-b90a-4093f9ef1162	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C024	car	available	f	f	c441aa5a-ed48-4d2f-b154-ee572e33ebdf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C025	car	available	f	f	5b902e0f-8a4f-429e-b1bf-99e52790758e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C026	car	available	f	f	4e29d52e-f4ce-4aaa-a59b-5dcdabaf2d9e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C027	car	available	f	f	f73e9680-5bfd-4510-a8a1-d1b64b9b77c5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C028	car	available	f	f	37f0f35e-258a-42c5-8b46-5bc36a1addac	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C029	car	available	f	f	f3b25f21-e924-4765-a4e0-9013a2727b31	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C030	car	available	f	f	efab2105-5eb9-45f0-bd57-7b412fd0a0ff	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C031	car	available	f	f	093d3749-35da-40c7-b8a7-fc158d42add2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C032	car	available	f	f	deb4276f-5abb-47f2-be66-1a8074b1e04e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C033	car	available	f	f	41b6e3ac-d0e2-43ab-9c6b-6c2775300895	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C034	car	available	f	f	d5ea9ff4-ae13-4705-9d5f-4ba6eefb4cd5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C035	car	available	f	f	5b6d8e8b-17da-478f-84f8-f4053a6158d5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C036	car	available	f	f	2e1d827f-a3e1-4ecd-a399-82c210d8aa4c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C037	car	available	f	f	5a35fd12-bede-4bcb-8105-577b64919cf1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C038	car	available	f	f	9e8706a1-cde6-40f0-9382-43f76184ed2b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C039	car	available	f	f	43bdbd75-bd08-40d9-97de-557f5ae1bcda	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C040	car	available	f	f	d124eb83-6190-4875-b591-1342e67a7b71	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C041	car	available	f	f	85da2483-a0d5-4be9-8593-10925dfa321b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C042	car	available	f	f	7522774d-ec4a-49f5-91ec-cbd4c2b087c9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C043	car	available	f	f	9a1445dc-9b52-462b-adcb-db7d8bba4ed7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C044	car	available	f	f	51227361-b26e-4fc4-b5da-ae03107052a0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C045	car	available	f	f	1e520423-de45-4312-9de7-2c82a89726f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C046	car	available	f	f	9e28d61a-2bcf-49d2-8ff0-7dbf9c843385	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C047	car	available	f	f	61f83580-d191-4bcd-9a26-a3f40606ec81	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C048	car	available	f	f	30359de6-2ed4-4d8a-86bd-0305292f267e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C049	car	available	f	f	9f3c6b9a-e271-473a-ab54-ca2dfb5e9379	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C050	car	available	f	f	6deb7406-ca43-4304-a9a3-852fc56cd254	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C051	car	available	f	f	d6c154be-5fa4-4525-b472-318fd4cfc93d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C052	car	available	f	f	3c747bd3-f352-413e-b8e2-b876c0a05e80	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C053	car	available	f	f	1ca323e4-563d-4f69-a2ef-cfc19896fb41	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C054	car	available	f	f	4258b488-dd4f-4199-8df7-7e31315c5ee7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C055	car	available	f	f	b9a02855-df82-47b5-9850-c128e94eac4e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C056	car	available	f	f	7dc08a19-0525-4053-8197-e1db4e25390e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C057	car	available	f	f	e1406553-f0be-44b1-ba42-f9bddb810cdd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C058	car	available	f	f	a4c4d104-8527-41f6-b892-e3bf088802e5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C059	car	available	f	f	374f6804-6936-4d7b-bd21-c17e67a0a1a3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C060	car	available	f	f	de1f231c-c5c3-47a4-b924-5129797484a6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C061	car	available	f	f	9b4c80a1-0aab-4ad5-8120-cee37a9d7927	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C062	car	available	f	f	e0aa5982-2d6e-47a8-8e95-34bea4c29217	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C063	car	available	f	f	6ab8a3cc-699a-4a01-a53d-187b84d0628d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C064	car	available	f	f	db600f15-0310-4615-96d0-37f8a81dd74d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C065	car	available	f	f	259e2506-d2ae-4a9e-b2ce-c388961acbbd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C066	car	available	f	f	0962566c-e0da-4996-9633-cab83f4147cb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C067	car	available	f	f	06dc5a9a-5f80-431f-b7e2-0b5276e08057	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C068	car	available	f	f	21ab37d1-f0da-4723-ad2d-fbee1905444d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C069	car	available	f	f	020e78c7-2e4e-4a12-932c-90d10f15a975	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C070	car	available	f	f	8a15ee6f-141a-418e-afd1-61ace4f9baf5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C071	car	available	f	f	0d8e350c-881d-4e49-aa66-1a236d6aefc8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C072	car	available	f	f	3e32d8a2-6fd9-44ea-a74d-e510d73fc14f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C073	car	available	f	f	e22e7599-22e5-4a2c-b9ea-08beecb8c642	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C074	car	available	f	f	85e7664b-dc19-4adc-82e0-7dc6e810a219	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C075	car	available	f	f	db222eed-f657-4f24-8bfa-62e88aefa5bd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C076	car	available	f	f	ad0465a9-875f-49d9-b756-e804a32bd4b3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C077	car	available	f	f	cf8c6e56-7051-413e-93f6-409c4a72ca4b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C078	car	available	f	f	c1a91308-d611-425d-a075-cbe5cca9b18a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C079	car	available	f	f	0146f319-1332-4ec0-8c8c-9ff27fb8f96e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C080	car	available	f	f	00024934-96ba-4176-a84a-56f1d1c6f006	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C081	car	available	f	f	7e8df876-f378-4f54-bec8-d8fd794d82e6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C002	car	reserved	f	t	a32420d4-302b-431e-816e-88d78c13d29e	2025-09-16 11:30:31.351032+00	2025-09-16 14:58:30.011899+00
6a650b0d-2311-4b30-a313-ae7529086f11	C003	car	available	f	f	09158ccd-1a5c-41a8-ac31-634d72c61886	2025-09-16 11:30:31.351032+00	2025-09-16 15:08:15.671776+00
6a650b0d-2311-4b30-a313-ae7529086f11	C004	car	reserved	f	t	9a80739f-4ec6-4d7d-ae23-f076feef17c9	2025-09-16 11:30:31.351032+00	2025-09-16 16:38:05.124329+00
6a650b0d-2311-4b30-a313-ae7529086f11	C005	car	reserved	f	t	02178346-d1f9-4a2c-887b-4df05877d496	2025-09-16 11:30:31.351032+00	2025-09-16 16:40:00.061736+00
6a650b0d-2311-4b30-a313-ae7529086f11	C006	car	occupied	t	t	de12fc56-c844-46c8-b7d0-29f6348b571a	2025-09-16 11:30:31.351032+00	2025-09-16 22:35:03.633021+00
6a650b0d-2311-4b30-a313-ae7529086f11	C007	car	available	f	f	f4e42346-3eb2-4f1b-b1c5-9b1d6088d22a	2025-09-16 11:30:31.351032+00	2025-09-17 01:13:23.718573+00
6a650b0d-2311-4b30-a313-ae7529086f11	C010	car	reserved	f	t	2adf58fb-1940-411c-bedf-09b807e576da	2025-09-16 11:30:31.351032+00	2025-09-17 11:48:47.339712+00
6a650b0d-2311-4b30-a313-ae7529086f11	C009	car	available	f	f	11eee77b-1e5b-46d6-a0af-a22a1e3670a8	2025-09-16 11:30:31.351032+00	2025-09-17 11:59:27.141718+00
6a650b0d-2311-4b30-a313-ae7529086f11	C011	car	reserved	f	t	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-16 11:30:31.351032+00	2025-09-17 17:48:37.828551+00
6a650b0d-2311-4b30-a313-ae7529086f11	C013	car	available	f	f	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-16 11:30:31.351032+00	2025-09-18 00:55:34.530857+00
6a650b0d-2311-4b30-a313-ae7529086f11	C017	car	inactive	f	f	6a25bb6f-ef7d-49e8-a013-19af8b6f1499	2025-09-16 11:30:31.351032+00	2025-09-18 01:37:55.214567+00
6a650b0d-2311-4b30-a313-ae7529086f11	C012	car	available	f	f	41037616-20b5-4a9b-a0f2-288504f84d2b	2025-09-16 11:30:31.351032+00	2025-09-18 03:10:06.273294+00
6a650b0d-2311-4b30-a313-ae7529086f11	C008	car	available	f	f	b1ad04e1-530d-4bf1-b4a5-94201487bd22	2025-09-16 11:30:31.351032+00	2025-09-18 03:10:11.617032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C015	car	reserved	f	t	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-16 11:30:31.351032+00	2025-09-18 07:40:31.326378+00
6a650b0d-2311-4b30-a313-ae7529086f11	C018	car	reserved	f	t	f78203d8-1ebb-46c8-8a92-ae5055f99508	2025-09-16 11:30:31.351032+00	2025-09-18 10:36:15.91756+00
6a650b0d-2311-4b30-a313-ae7529086f11	C019	car	reserved	f	t	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-16 11:30:31.351032+00	2025-09-20 03:09:02.770059+00
6a650b0d-2311-4b30-a313-ae7529086f11	C020	car	reserved	f	t	41a3e636-f6f4-45d2-9dd3-621b27985589	2025-09-16 11:30:31.351032+00	2025-09-20 03:16:55.371863+00
6a650b0d-2311-4b30-a313-ae7529086f11	C021	car	reserved	f	t	c309a8d6-77e5-469b-9595-c503d0e3b07e	2025-09-16 11:30:31.351032+00	2025-09-20 16:28:05.419037+00
6a650b0d-2311-4b30-a313-ae7529086f11	C082	car	available	f	f	9126d2dd-d560-44dd-829d-abcd2cc795f3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C083	car	available	f	f	192059b5-8362-4f21-8725-baefe49236f5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C084	car	available	f	f	97c9b8ac-aced-4725-a03b-0249bb4a50be	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C085	car	available	f	f	0d8a245a-5023-4b23-9fa6-f5b0cec17d00	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C086	car	available	f	f	5c172059-1e8d-44d9-b90b-f52846ec8fc6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C087	car	available	f	f	1f373524-fd67-4184-ac2b-3aaebc15b08c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C088	car	available	f	f	7f754032-59ab-4503-add7-31c258d2d0f9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C089	car	available	f	f	1a965d96-b402-4ced-bc18-f488e294aaf1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C090	car	available	f	f	72f50750-e94f-4c15-b3ee-42c8d829a63f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C091	car	available	f	f	50651a5e-325a-403d-b5b6-d1d29e692d21	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C092	car	available	f	f	9ba2c11d-426b-483b-be07-3716a2aa0a30	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C093	car	available	f	f	9fdc3ec8-edc5-4430-90e8-a9d86409ef77	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C094	car	available	f	f	d623f3db-4302-41c1-9f5a-5cd86fd4efbd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C095	car	available	f	f	10770db6-ce31-4a4c-b5d2-49b1a5f3da49	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C096	car	available	f	f	e764f1f7-18ae-4488-864f-0a423e514037	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C097	car	available	f	f	b9dc7f87-594d-4d59-ba15-96bab68aae8c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C098	car	available	f	f	c52928cc-5287-48f8-ac66-45c9f98fa65a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C099	car	available	f	f	e50a81b1-f057-4d5d-bea3-0eaf19db83c0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C100	car	available	f	f	4a0ebdb1-d89f-4ef3-9df6-a837c3cefbec	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C101	car	available	f	f	e46c26a8-1856-4414-a0c1-368b32f27886	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C102	car	available	f	f	6712e37f-a02d-4f79-b213-7936226855c5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C103	car	available	f	f	5e58fb9d-25a9-48c5-884e-071f24d646e9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C104	car	available	f	f	82286020-db67-444f-a4f0-5a6da0a11d28	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C105	car	available	f	f	fccf047d-ebc3-4eff-864e-a394ab766b65	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C106	car	available	f	f	5c0c0d88-5c0d-48ab-924d-0c0991365be8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C107	car	available	f	f	b826452c-158e-45ed-bdc0-8dd7988ebe7b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C108	car	available	f	f	b1536143-2eec-422e-b00f-907045824d2f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C109	car	available	f	f	cb4555a1-ae48-4e83-90b7-4091f1016ea8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C110	car	available	f	f	856b0f5e-1dc7-4e0c-ab18-ae27b4f6745d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C111	car	available	f	f	af7f0881-84d9-432c-85af-2f4024082ded	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C112	car	available	f	f	3a567c19-d65f-48ba-8f71-281e865a5d18	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C113	car	available	f	f	7be19604-5321-47a9-a082-7e0e871d497e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C114	car	available	f	f	71d476fd-db33-4a04-b663-2a4bf23e6dfe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C115	car	available	f	f	994956aa-2bd9-455a-a311-b9720dbeb15f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C116	car	available	f	f	52d89341-bc1b-44d1-bbaa-e78f1487d9c1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C117	car	available	f	f	60d0827c-fed1-4270-8003-9f7758b7d0bd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C118	car	available	f	f	3b5d7b49-2ea7-471e-9511-98943488cb31	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C119	car	available	f	f	035abbcb-255f-4206-a13b-87395d5cc6b1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C120	car	available	f	f	2060d118-b377-4322-a336-be25d1a16ecc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C121	car	available	f	f	e4f20c8b-7faf-4c4a-8c36-8e40b912019c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C122	car	available	f	f	02307a17-dac0-48aa-ac26-01f7e674bb3d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C123	car	available	f	f	0e4f094d-2850-48db-8c48-a72a993c90ee	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C124	car	available	f	f	35ca90b6-fa60-4ff2-a36c-20951fdb7006	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C125	car	available	f	f	c17122d8-8474-46a4-89f6-36646703092c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C126	car	available	f	f	3dd97e5f-a7a8-4d67-ac85-5d36306ed850	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C127	car	available	f	f	1b1800db-13df-4374-94fb-8f4dc5d3ebfe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C128	car	available	f	f	5e00fad2-450b-4f00-8514-64d0096aa877	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C129	car	available	f	f	cf55b4f6-1928-4f8e-82da-334d9e2ff270	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C130	car	available	f	f	8dbc275d-bb86-457a-9681-39635ba34349	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C131	car	available	f	f	92fd6ebc-b339-47a9-910e-5bd8e753ba41	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C132	car	available	f	f	c15ed9b3-281c-4350-bea1-4a4ff8e02dbe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C133	car	available	f	f	149e826c-6d13-4530-9d02-5172f15bff44	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C134	car	available	f	f	a68b2ece-b8f8-4b1a-add7-0b4cdb63b8b4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C135	car	available	f	f	a1d7977b-c31c-483e-8b56-1387f5fcb1ec	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C136	car	available	f	f	9c47d0f0-e968-4bc9-8bfd-069168eec845	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C137	car	available	f	f	f8186152-1374-45ab-85f8-bbd47ad9a583	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C138	car	available	f	f	2d1fcd1a-c064-45c3-858e-05b2a0d05c19	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C139	car	available	f	f	9faeb070-ee54-47a2-a3e6-49054750ed9e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C140	car	available	f	f	e4933163-2986-42cb-a02d-a8e315111e59	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C141	car	available	f	f	566cab76-cca1-47d6-b71b-cf3560307b99	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C142	car	available	f	f	a7e5e19f-7e12-4d26-851a-0b369e42cc1f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C143	car	available	f	f	e60060ee-5400-481f-a436-b71a1d61f1da	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C144	car	available	f	f	9eb105de-fe44-40d1-bbf9-067d50079562	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C145	car	available	f	f	346672e5-5a7f-4a80-a3ea-1cce94ad5332	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C146	car	available	f	f	22062452-d980-4c4f-be28-f84f4e41fdb4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C147	car	available	f	f	0f61bf6c-2de1-45ea-a7d8-e7eb09dee0d2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C148	car	available	f	f	ae615e38-e2d7-41ab-9c61-9bb90840e5d3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C149	car	available	f	f	5430528e-4fc5-4853-a276-339e7fbf0e81	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C150	car	available	f	f	699af718-790c-47d5-8c1a-ebbf00ce42e0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B001	bike	available	f	f	b70f596e-aafd-42d0-9868-bfbd6457b9d6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B002	bike	available	f	f	52d73912-e8da-4f63-bcc9-04f70e2375d5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B003	bike	available	f	f	98117a39-d648-4846-b932-3506f3ca1b89	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B004	bike	available	f	f	e7251e96-c514-4b12-b801-ad02e50c9349	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B005	bike	available	f	f	4d9d5f89-9143-4f6f-959c-4d1dcfc155ea	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B006	bike	available	f	f	3200bbd6-2832-4f8d-9292-79d438377142	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B007	bike	available	f	f	7c9ba727-18d4-47b6-afe0-8b3effc8e517	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B008	bike	available	f	f	37bf8317-8ff9-4eee-a777-e14733c933f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B009	bike	available	f	f	e9a37f35-fb53-4496-943b-80adc84105bb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B010	bike	available	f	f	0a6e86e1-e087-4819-8020-56c6e4412438	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B011	bike	available	f	f	0f06a69b-0a43-44be-b287-c659fd3d2e59	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B012	bike	available	f	f	ae5bc696-9317-4d8b-9a03-5dbc5e1fdb9d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B013	bike	available	f	f	c60edae2-33ed-496e-bbcd-83d2d95b64d7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B014	bike	available	f	f	1f96f3b1-79bf-44b8-8ee1-8ac3c1fa992f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B015	bike	available	f	f	1cda495b-2a95-419b-8a56-9408ab046c64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B016	bike	available	f	f	387e0b98-9561-4d33-9c5c-a50c84891c8a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B017	bike	available	f	f	5942355b-ddc5-48e8-a619-2ad065dad98d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B018	bike	available	f	f	e2b529ca-2e73-4486-850e-a3c9a95cd53a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B019	bike	available	f	f	11a87c20-0616-4e1a-bfe2-44f814e50d7d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B020	bike	available	f	f	4c483a35-a068-450d-98f8-76815d7bb5ff	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B021	bike	available	f	f	a5871a9e-bc76-408d-9c4c-8c571415c94c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B022	bike	available	f	f	a0b4b366-da6e-4707-a4e3-4d3f167d7c65	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B023	bike	available	f	f	258496f1-ca5f-4b74-826f-7b8b0e18729b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B024	bike	available	f	f	f5178b75-b939-4dda-8397-f8582c8b61e3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B025	bike	available	f	f	b940cbe1-981a-4440-8a20-01b362f5763f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B026	bike	available	f	f	5e00bfdd-fa16-441a-b784-72470e44ce8e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B027	bike	available	f	f	ceb6c938-fb10-42a4-adda-165da4ac5f6d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B028	bike	available	f	f	4e1f3ab4-f021-436e-941d-3426a37f57fe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B029	bike	available	f	f	84cec4a3-c31a-492b-9f19-9d9c49f6ca0f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B030	bike	available	f	f	8f4ec8cc-fd36-4d97-a8be-d6ef75d22b2c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B031	bike	available	f	f	ce647c90-0eaa-4e9c-bef9-38a2b86bf2e0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B032	bike	available	f	f	1bc6bf2d-5aa6-4217-989c-3c7e0c62d784	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B033	bike	available	f	f	cd8d3422-af7b-428b-804b-7f1759315824	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B034	bike	available	f	f	2b7f11ab-b5a5-4e8c-aae9-24628d0d1345	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B035	bike	available	f	f	6640146f-9863-447a-b717-d077fbbd3e09	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B036	bike	available	f	f	cab27733-17cf-4351-ac0a-a03d004fc7ab	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B037	bike	available	f	f	d831612a-e38c-42ac-9e9b-f9529e381fc5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B038	bike	available	f	f	2a2bc636-fcfd-4e0b-8562-7d33c890d097	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B039	bike	available	f	f	70c4cb2c-ddc5-4101-9607-18d3ef4447be	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B040	bike	available	f	f	7174dfef-89ab-4b88-8b50-3ebe8168e532	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B041	bike	available	f	f	e47be0c2-5866-4f11-ba69-310a6580df12	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B042	bike	available	f	f	f3c562c7-1429-4f9e-b3e8-7a50b32283a6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B043	bike	available	f	f	875d1ad0-3a81-4071-a152-f5599170b820	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B044	bike	available	f	f	b5308036-36c0-48a6-8880-755de88000bc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B045	bike	available	f	f	422cc355-ab41-44d5-9568-ecd9c42850e7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B046	bike	available	f	f	8894fc64-1426-404c-9395-130308d92cae	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B047	bike	available	f	f	b518f01f-8aaa-4986-a018-23348b214765	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B048	bike	available	f	f	25d88361-89bc-498a-8353-973afff63121	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B049	bike	available	f	f	b538ddbe-f36f-4ee4-a3c6-4a1641423ab3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B050	bike	available	f	f	ad8d697d-e2f1-4477-9239-10844c6a0347	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B051	bike	available	f	f	eedbaf9f-af24-4627-b293-4685e5e77ed4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B052	bike	available	f	f	8c961e0e-bb5b-4b3e-90bf-cf2369a88ae5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B053	bike	available	f	f	170298fa-0029-4e15-82b2-eada369b5592	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B054	bike	available	f	f	b2a38bf2-4542-4318-ab83-10d5f956fd9a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B055	bike	available	f	f	91dfee84-179f-40a7-8adb-51b5de9c67ef	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B056	bike	available	f	f	c70308d4-f4a6-4bac-8154-c3e54c8708da	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B057	bike	available	f	f	6573fc54-d202-4ee4-b0e1-62fed51d09d9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B058	bike	available	f	f	c9986093-f98a-40df-9d8d-3154d39b269b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B059	bike	available	f	f	2e2893ff-8953-41a0-b31f-7f8f5e993494	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B060	bike	available	f	f	23487160-1af4-4ec5-9be9-9e940cf87488	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B061	bike	available	f	f	fc3c594d-0f78-43a9-ae41-20578eea9e48	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B062	bike	available	f	f	a69e572a-5d53-4a88-b912-e5c3ed2a11f4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B063	bike	available	f	f	8d9bef7c-2392-46e1-b439-64e267d34a49	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B064	bike	available	f	f	1008ec97-c088-4e10-b775-158038881729	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B065	bike	available	f	f	04818aa7-8541-4a74-92f5-79b6b11e29f1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B066	bike	available	f	f	81df00d4-f3d6-4a17-8633-d0fda63efffc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B067	bike	available	f	f	79107ec9-9800-463c-bda6-338e5a367c53	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B068	bike	available	f	f	5f5dd3a7-34f0-412e-98d6-300bfaf8cd05	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B069	bike	available	f	f	a2a75cfe-73d8-4bfd-a097-a0ca2f5b96df	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B070	bike	available	f	f	97ca048a-497b-4c68-a5c9-c3a22da638b2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B071	bike	available	f	f	839f4d0f-f05e-404f-bc7f-cea672a09bcd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B072	bike	available	f	f	a5f77c5b-1f42-4f57-9885-23a87d04246c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B073	bike	available	f	f	995ebd35-4c8e-4aba-a6e7-64e47ed59444	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B074	bike	available	f	f	349f01f3-729e-48fc-beb3-b0c752707586	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	B075	bike	available	f	f	7b545a81-ed74-4e51-9da4-0993fc0c55b3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C002	car	reserved	f	t	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-16 11:30:31.351032+00	2025-09-16 21:06:33.055373+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C003	car	reserved	f	t	c4921654-ab3a-4908-8381-a29d6717a7cc	2025-09-16 11:30:31.351032+00	2025-09-16 22:22:51.253553+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C004	car	reserved	f	t	94ee0b96-9b5e-4af2-9934-f3ec41197785	2025-09-16 11:30:31.351032+00	2025-09-16 22:28:10.150979+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C006	car	reserved	f	t	730a7a60-2535-46cc-a1db-64b92c2eaa43	2025-09-16 11:30:31.351032+00	2025-09-16 22:38:07.961939+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C007	car	reserved	f	t	ba02b652-3159-4a2e-8537-e36c944f0f73	2025-09-16 11:30:31.351032+00	2025-09-17 00:06:26.332401+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C009	car	reserved	f	t	75e25a61-d293-4ad8-8eb0-72204534e1ad	2025-09-16 11:30:31.351032+00	2025-09-17 01:41:50.540039+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C010	car	reserved	f	t	07a6cca8-4378-4ae2-a2b1-787095a096e2	2025-09-16 11:30:31.351032+00	2025-09-17 01:44:00.132873+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C011	car	reserved	f	t	f92ac396-10cb-4769-9473-dc4219133917	2025-09-16 11:30:31.351032+00	2025-09-17 01:48:59.475221+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C014	car	reserved	f	t	96767f13-51c2-4214-9bc5-89167226250f	2025-09-16 11:30:31.351032+00	2025-09-17 02:10:07.703016+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C018	car	reserved	f	t	0f0cf325-b73a-46f7-8f93-c37af1b11f82	2025-09-16 11:30:31.351032+00	2025-09-17 11:09:48.19824+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C005	car	reserved	f	t	7c4fc29f-a954-48f3-ba9a-db5def5cbc4c	2025-09-16 11:30:31.351032+00	2025-09-17 11:14:19.000154+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C008	car	reserved	f	t	69afc6ef-5b07-4e2c-b064-1006811e2441	2025-09-16 11:30:31.351032+00	2025-09-17 11:25:53.346293+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C012	car	reserved	f	t	77469074-1c57-421c-b741-be1874ffc20e	2025-09-16 11:30:31.351032+00	2025-09-17 11:26:11.551292+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C016	car	reserved	f	t	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-16 11:30:31.351032+00	2025-09-17 13:32:59.376569+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C017	car	reserved	f	t	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-16 11:30:31.351032+00	2025-09-17 13:34:10.216217+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C015	car	available	f	f	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-16 11:30:31.351032+00	2025-09-21 20:10:55.293564+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C025	car	available	f	f	09459640-8e49-4700-b93b-a4854be61b0d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C026	car	available	f	f	2e3ca1e3-c1cf-45a2-b7ad-6e594457c773	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C027	car	available	f	f	32ff6e4b-1fdf-4fc7-9520-a9175551c4fe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C028	car	available	f	f	52ff832c-5b93-48a2-ac5e-f85e4c8fcdca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C029	car	available	f	f	cde4c4ea-cd30-40f2-a989-b5f5e83312e4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C030	car	available	f	f	aa500c65-b70b-4152-9476-9ca56b7c3368	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C031	car	available	f	f	657a0023-ffd4-4db6-ac14-f4d86aad90fd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C032	car	available	f	f	d49540ac-0659-4cbc-948e-f63d9d15506d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C033	car	available	f	f	95ada58c-88be-41ed-82df-2610af2a4049	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C035	car	available	f	f	4705510e-3cc4-40ca-8aaa-8bc51012c670	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C043	car	available	f	f	9e315ba9-087b-4116-889b-fad28128af54	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C044	car	available	f	f	ec71e572-35cc-4507-a520-d023d6b1c6f2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C045	car	available	f	f	cbd9d5fd-2a29-46fb-bdf3-1502b54e50ab	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C046	car	available	f	f	57bbf385-5307-4ffc-9b58-ca459866f483	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C047	car	available	f	f	de521fa9-6254-426b-bd41-170013168cf5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C048	car	available	f	f	a9aa8eb8-f57e-42fd-9c96-09f2b7044c3e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C049	car	available	f	f	5903f91c-fbce-472e-a116-96ce9a271b7c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C050	car	available	f	f	001a9902-002d-481b-8d82-0c20eed37ab2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C052	car	available	f	f	e19ebcf5-5bb4-4155-80a3-a6b267400e26	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C053	car	available	f	f	743413d7-eac6-4f89-8a50-f5035585e482	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C054	car	available	f	f	1f3e818e-78fa-4187-becc-ddc572c6ef6a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C055	car	available	f	f	41cf641a-2171-44c4-bbd1-91676db21d21	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C056	car	available	f	f	92ee66c7-7108-49e7-a890-6e48528b328d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C057	car	available	f	f	878373ac-5f92-43fd-b3a2-92470ab61d74	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C058	car	available	f	f	db335582-2f86-420b-9c4f-a493988e0d4c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C059	car	available	f	f	10156804-e2f2-46ba-9ff8-0872d5aeed50	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C060	car	available	f	f	cfe1949d-1e19-4018-a478-41880495920c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C061	car	available	f	f	6ca453ac-17b6-48bf-94b2-e9869ad7753f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C063	car	available	f	f	b56467f1-94ad-43bc-84ff-1de94e560f15	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C064	car	available	f	f	54fba6a3-7dfc-40df-b288-7571d7c786a7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C065	car	available	f	f	fe8bc13b-ea8f-4464-9639-39419bc9800d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C066	car	available	f	f	c42c2872-4f35-410b-a3a3-627a2c1ed16a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C067	car	available	f	f	ab95d95f-2ddf-46e8-981f-39222aa56921	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C068	car	available	f	f	57fe18de-8bb4-4388-8b78-dc1094870a5e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C069	car	available	f	f	653074d3-3d8b-4f53-a8e5-82420b58e196	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C070	car	available	f	f	25a1427d-240e-437d-a308-f41a053438a1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C071	car	available	f	f	848a2070-87a5-4acf-849a-46c9b1647684	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C072	car	available	f	f	6a986502-d5df-4b11-8381-9daebc153f48	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C073	car	available	f	f	0a796fcc-8fa1-400e-ba77-601f1fdda244	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C074	car	available	f	f	ced79a0d-33d1-448b-9156-7e4b59cf4866	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C075	car	available	f	f	0a143621-99c1-4b24-847a-fbf4c59b7dcf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C076	car	available	f	f	27eeec40-eece-493a-8f23-267716a316df	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C077	car	available	f	f	39d6a520-0d9f-4c83-815c-e079888584a2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C078	car	available	f	f	a0ee14b1-d338-46e5-bdb7-df2921c39781	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C079	car	available	f	f	89562ba6-ae7a-4ee3-921a-5400ead8fd13	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C080	car	available	f	f	3854a7fc-4d4e-426a-a359-064fc8ba7c97	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C081	car	available	f	f	caaedb90-67a4-493f-a1a1-eb215aa4d2f0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C086	car	available	f	f	50102393-c222-4f16-918f-a73429d43d5f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C087	car	available	f	f	3bebf1ef-ebed-440d-8da8-09a2d25dbb16	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C088	car	available	f	f	487160fb-ec8c-4c38-bac9-be0a9269ce93	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C089	car	available	f	f	3426ab45-02e8-4aaf-b876-d970c2fa68df	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C090	car	available	f	f	1b0adff3-a186-471d-941f-c5126de78a2f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C091	car	available	f	f	b9edd82c-dee0-46f8-a3c2-d9ce408b480e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C092	car	available	f	f	718f7a17-0dba-4de2-9a28-2798e9704c80	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C093	car	available	f	f	516abfd5-f237-43c4-8719-f694b886bea0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C094	car	available	f	f	68b156aa-659b-4c6c-8d01-554f2e7f9bc5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C095	car	available	f	f	5bea1aea-9d10-4b34-9e70-fe1a35ed63f5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C096	car	available	f	f	9e8405ee-d87c-4872-b9e7-5e9af2f55f4a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C097	car	available	f	f	65f90472-a07c-4b43-a8b7-60a76affea0a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C098	car	available	f	f	17b383cb-e8cf-4813-adce-360ca87f46db	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C099	car	available	f	f	c69efa08-4f08-4d4a-9940-ee6e7ae90c49	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C020	car	reserved	f	t	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-16 11:30:31.351032+00	2025-09-17 15:33:21.316803+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C023	car	reserved	f	t	29fe9803-57d5-40cd-8a51-859ca4cf47e5	2025-09-16 11:30:31.351032+00	2025-09-17 16:45:01.82043+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C024	car	reserved	f	t	36a7cea3-2c6d-45c1-964d-9b6d40249d00	2025-09-16 11:30:31.351032+00	2025-09-17 17:53:48.054063+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C034	car	maintenance	f	f	a7be4209-a17e-4dcb-a7a0-67b05e58a7da	2025-09-16 11:30:31.351032+00	2025-09-18 00:59:13.79692+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C082	car	inactive	f	f	1f8e87bd-f495-46db-bf5d-fcb5f7f90d70	2025-09-16 11:30:31.351032+00	2025-09-18 02:01:10.361904+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C084	car	inactive	f	f	9b94e02f-f226-4237-a717-a01e3d8c7d4d	2025-09-16 11:30:31.351032+00	2025-09-18 02:01:16.636942+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C085	car	inactive	f	f	29ca9116-76ad-4b48-b441-bf9083423e0b	2025-09-16 11:30:31.351032+00	2025-09-18 02:01:18.180453+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C022	car	available	f	f	b188d489-15e0-4c4f-83b0-4cc68bc920da	2025-09-16 11:30:31.351032+00	2025-09-18 03:09:59.00247+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C021	car	available	f	f	4cf4da74-02b5-450c-9098-942c007cfd02	2025-09-16 11:30:31.351032+00	2025-09-18 03:10:00.77868+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C042	car	inactive	f	f	9190ccff-4dcd-4a62-8cdc-9012799a0a0e	2025-09-16 11:30:31.351032+00	2025-09-18 03:49:57.995333+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C062	car	available	f	f	74662be6-817c-4f61-a11c-c8b462a5b805	2025-09-16 11:30:31.351032+00	2025-09-18 06:39:09.788937+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C051	car	available	f	f	cf9028fd-91ee-48b6-9933-bf091857beaa	2025-09-16 11:30:31.351032+00	2025-09-20 16:21:44.729143+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C100	car	available	f	f	2f2764b4-da83-4e3e-b9bf-7a8343c99c6a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C101	car	available	f	f	cf8628c1-bbb2-4e23-9294-f00af854db8a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C102	car	available	f	f	f4156db9-811e-4955-bb8f-97d4f02409ed	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C103	car	available	f	f	bd7b9a61-d7c4-4b84-8f1c-18b5883be8cb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C104	car	available	f	f	31728b35-7688-46e5-ae02-6e595115cfda	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C105	car	available	f	f	baf0c5e5-c2af-48b2-98eb-e4a6736ff9ac	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C106	car	available	f	f	197f8783-0a1e-4afe-be01-02f2e03bb44d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C107	car	available	f	f	2f823791-a653-4ca0-9539-8a40d2467fd0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C108	car	available	f	f	839b268b-f095-42b1-ad40-5ee796a05274	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C109	car	available	f	f	c4e882eb-f248-4131-9d41-bffd6246e438	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C110	car	available	f	f	017c49c0-0d30-4b21-af8b-f47cd5dbfc6d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C111	car	available	f	f	6b75cff3-1e27-4f22-924a-527208cfa7aa	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C112	car	available	f	f	3700db99-71fd-4080-861a-e251a402e00f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C113	car	available	f	f	9b79a205-e1f0-4ea6-b2cc-2aa219d71c97	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C114	car	available	f	f	2681aee6-082b-4fa8-bc53-5b736240c355	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C115	car	available	f	f	31545918-2b23-4a2c-83c9-f53d224fe0d1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C116	car	available	f	f	8afd38cc-cdf5-4f49-b98f-4d7d60e54865	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C117	car	available	f	f	f9e55785-1c2d-4248-8d89-199f4f7b2562	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C118	car	available	f	f	4609cd7f-9de2-4ccb-8b2e-77ef8954500e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C119	car	available	f	f	f11fd1f7-3960-4ddb-aac6-588ab3121df8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C120	car	available	f	f	c8f87ee6-b03c-4db1-b8de-3f33ab0c7263	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C121	car	available	f	f	b17526fe-392e-438e-94b9-cd771b58beb5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C122	car	available	f	f	401bed0c-1487-4615-9802-9bcd38e37bfe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C123	car	available	f	f	d8664582-eb5f-4ce2-942f-457a69a80170	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C124	car	available	f	f	e189ecb8-83a5-4c43-a72d-1f02fc1e89c4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C125	car	available	f	f	96f971b9-c129-407b-8a97-65cf08140b21	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C126	car	available	f	f	57436d03-0f00-438c-9dea-9dfa5a015240	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C127	car	available	f	f	0b958544-f88f-4030-a6dd-b4e59a8676e5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C128	car	available	f	f	4a381fbd-4be0-4b56-ad93-34fa57ad1854	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C129	car	available	f	f	7943fd66-021a-4545-8a44-9232a30bda33	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C130	car	available	f	f	affb3222-4e0b-4501-a3bc-11b483647d83	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C131	car	available	f	f	56ec023f-24ab-43bf-b0f8-6d943dcb4e3b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C132	car	available	f	f	48490886-e2fe-4320-8bb1-bb78319a0e84	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C133	car	available	f	f	48b395cf-d9c0-4656-919a-9eb838c27c79	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C134	car	available	f	f	366a1b55-6995-4db5-b5a1-67cb114ed2c7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C135	car	available	f	f	a092c6ea-d5c3-4328-8171-d69ce1920444	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C136	car	available	f	f	95d3dfd6-7169-4189-9e62-6f4adeacede5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C137	car	available	f	f	60b5458d-6629-48f1-b7f4-56af6dc807e3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C138	car	available	f	f	0581fcf1-a2ae-4e4c-b87d-6a10df2827fa	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C139	car	available	f	f	2c26a4f0-0fa1-483b-84b9-31cf7795f6b4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C140	car	available	f	f	8484022e-8c0d-4deb-8c6d-42e953102aca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C141	car	available	f	f	8f059301-118b-48b2-81e6-173bf61758b2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C142	car	available	f	f	25cb2fce-703b-406d-9866-8d9fca45713d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C143	car	available	f	f	a15bcd2f-22cc-4fa6-8f25-e9e26119a291	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C144	car	available	f	f	570a0dce-303c-4c84-8e95-e19f9285af89	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C145	car	available	f	f	411b2295-0447-462b-880e-edcde86cd9e7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C146	car	available	f	f	b28ada86-1d75-47a8-bdf2-42e82f1d8f96	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C147	car	available	f	f	7ff43569-c112-45a8-87cd-1e6d75106bc8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C148	car	available	f	f	62dd3e3f-f439-4816-bfd6-f523077cf26e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C149	car	available	f	f	5904973c-5bab-4b2a-af1e-bb6036cc7168	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C150	car	available	f	f	d7a9f7c9-d926-47e7-9ffa-30456bde80c4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C151	car	available	f	f	a93196b9-98e4-4034-9917-4cde1aa8a6d7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C152	car	available	f	f	16b1d62d-6051-4d48-8aaf-d108f875fdc7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C153	car	available	f	f	9936a5d0-b55f-4348-bf0c-f7bc707e3c64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C154	car	available	f	f	ee7efdc6-cebd-4849-955a-cfd005ab64b4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C155	car	available	f	f	d5645608-ea5f-4e2d-a16a-f5d703219852	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C156	car	available	f	f	ebb441d2-0f96-4e8a-8d9d-d681baeb97e7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C157	car	available	f	f	257f6a17-b547-4f58-93b5-bec1170eb59f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C158	car	available	f	f	18fab598-7eea-483b-8a9d-7a88d4209c1c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C159	car	available	f	f	18516c21-412e-417e-91dc-47c2c4513ce9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C160	car	available	f	f	eceb49c0-4ba8-41a6-99b2-96dc5438b201	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C161	car	available	f	f	b2a02ccd-5c23-4086-86c4-fd7d6bbdde5a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C162	car	available	f	f	fe018672-df2f-4ef5-98c7-103926ae3f53	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C163	car	available	f	f	1c446abd-20a9-469d-8827-a9fb46dc67fc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C164	car	available	f	f	76248b98-9956-47a3-a77b-dc6f1921ee8b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C165	car	available	f	f	dbbe1a4a-b717-4c75-836a-88d452cffaeb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C166	car	available	f	f	36ebf159-3f2c-413f-8552-fce916d0c3f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C167	car	available	f	f	a126c971-96fc-4a42-88ce-d00af13b774c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C168	car	available	f	f	800118c5-cef9-4a54-8457-84439dc319ca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C169	car	available	f	f	1eeddb77-97f9-4820-a8cd-177335e442e7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C170	car	available	f	f	a8b8be4c-263a-445a-bd0e-35301d687b08	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C171	car	available	f	f	64187c8f-6e97-47ba-87d8-2b2d788e0aa0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C172	car	available	f	f	d570f357-e706-42a5-9d8b-83afb59187da	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C173	car	available	f	f	cd207ae3-edd1-44e8-89af-9170bad6f73f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C174	car	available	f	f	1fd59347-3c00-42be-98c8-5c1ffd306cec	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C175	car	available	f	f	8368e958-8d70-4332-b763-57254b95346d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C176	car	available	f	f	eb7a726f-cf44-41a4-9400-aeaed7d6be72	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C177	car	available	f	f	d3ce2f36-3b23-4b7a-b269-8f068af76a4a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C178	car	available	f	f	e01e7eb9-59e3-44c4-b569-50ce5d183cba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C179	car	available	f	f	2ad9e69e-07f1-4210-afee-025d148d72c6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C180	car	available	f	f	e828eee0-5c6b-42d8-98a7-2f9e7c5eede2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C181	car	available	f	f	92ca4101-3b1f-40bf-95bf-a87dc0559033	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C182	car	available	f	f	77cbb332-54dc-45c4-8963-c751645c8897	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C183	car	available	f	f	f444bbc8-ec45-4c72-a172-e6ced91d6d39	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C184	car	available	f	f	1b274cde-557a-414f-b429-4940d2148cc5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C185	car	available	f	f	340ccaf2-f17a-4871-8167-42960f7f2c1f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C186	car	available	f	f	bf9a6d1f-43fc-45e5-a389-0d2f75c31a47	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C187	car	available	f	f	460048e8-fc6c-4d35-8486-fd5796dabfd4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C188	car	available	f	f	f1964e29-df4f-452a-b1a3-b508ee20af29	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C189	car	available	f	f	8678308c-427a-47fc-ba11-f042c9467dea	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C190	car	available	f	f	a514608e-030b-43b4-8495-f525f832f32e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C191	car	available	f	f	ebadf585-bad5-45ca-9d57-09f844192223	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C192	car	available	f	f	b8cf020e-4d17-4121-bbc4-8d27207c56f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C193	car	available	f	f	49af2c04-0213-41be-a57f-bb8fb5a3108d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C194	car	available	f	f	56373cc9-28bb-4ec2-8c9f-f05312d21622	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C195	car	available	f	f	ce98e039-0b14-4100-81e3-7de37f54c566	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C196	car	available	f	f	7171b405-68cc-4799-9830-6bd1cd17682b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C197	car	available	f	f	a2be0b8f-65d3-4d7f-84d2-a689b3e03d58	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C198	car	available	f	f	18f7de4d-0531-4c82-8f90-6c476ed7e42d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C199	car	available	f	f	c080e164-1d95-45a7-a9a9-7f6a6f555b26	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C200	car	available	f	f	8cb74850-629a-4f3a-938d-3b073fc1f661	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C201	car	available	f	f	bc2ceff0-5193-4bac-bfbb-e76d76b64c64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C202	car	available	f	f	499e3444-ea15-4980-aee5-5e8a8af995a5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C203	car	available	f	f	39a4fab0-9756-4af9-8a80-c988b6cce7bd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C204	car	available	f	f	03c39b86-1a06-43c9-99a2-f8477b31b14d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C205	car	available	f	f	c96ab71d-d5ac-4978-ab42-5d3b5afa2603	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C206	car	available	f	f	0342f0bc-df09-49b2-8401-f855473e4643	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C207	car	available	f	f	2d01f0f4-ff20-498f-80b2-da5892526130	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C208	car	available	f	f	e17b986a-4631-4b42-9b6a-16f4cccc0cba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C209	car	available	f	f	615a8aa1-f096-4696-8be9-2c38c4b25acd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C210	car	available	f	f	4d46e35b-3ec4-4591-a0b1-852d80eb4922	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C211	car	available	f	f	3e6db635-2305-4d84-852e-d146abf5e460	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C212	car	available	f	f	e3efc7f4-0926-4b3b-ae67-aedd085a5c15	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C213	car	available	f	f	91cfb850-8080-44a4-ae45-226d7d6b8d66	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C214	car	available	f	f	843f3998-3a19-4213-afdb-e927020dd2a5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C215	car	available	f	f	b9ed46fa-9ed0-4d85-845c-04d7874c949e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C216	car	available	f	f	69b78ec6-d032-4c6f-b0fa-eeb3f4e97244	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C217	car	available	f	f	9ec3dd5f-b47c-4dde-be04-f0cd28c13db6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C218	car	available	f	f	272bea73-6d63-4d0c-a320-e41a40a465a4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C219	car	available	f	f	a17aee97-ceef-4f48-8f14-f5ec7465d555	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C220	car	available	f	f	85bc3b0a-9895-4af7-999f-1765f0435972	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C221	car	available	f	f	36d560d0-891d-40cf-a8e1-2b8e650f951a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C222	car	available	f	f	c11f5c78-3cd3-4853-9833-dc95402a38d2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C223	car	available	f	f	d3617302-5041-4d0a-b744-ac4c61b8229c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C224	car	available	f	f	0820e31b-7287-4928-bb6c-2edf2f2445d0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C225	car	available	f	f	eded643b-5f0b-4cf0-a8d3-94a80e45297c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C226	car	available	f	f	412a885d-cddf-4cc0-afcd-0b036049138c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C227	car	available	f	f	13eea8a1-3f7b-4caa-b5aa-94b4323aca28	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C228	car	available	f	f	4d1ff881-850f-4b4a-8db8-4422d5d50132	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C229	car	available	f	f	007278a4-93a0-42d4-b961-792724d39672	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C230	car	available	f	f	50f337c9-59c7-4bc5-a744-ddb653f6b483	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C231	car	available	f	f	3be96833-a32d-443a-ab13-351c010d5bcb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C232	car	available	f	f	24472186-ea6c-4cff-8704-b9e7fbf277f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C233	car	available	f	f	29f00b5f-e530-433a-a4a7-8f35e71cba5e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C234	car	available	f	f	b86ba3e4-b842-4c90-a3e1-9c51489adbd3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C235	car	available	f	f	d600a864-e50f-4940-8921-be3e1b2d03a3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C236	car	available	f	f	1ec27c1f-1b28-4fca-83c6-9de8073420a9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C237	car	available	f	f	da0e66c7-5f50-40fa-a2fd-714dfb7af077	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C238	car	available	f	f	fa7e78a6-0379-4d9c-80f0-961f7604d967	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C239	car	available	f	f	bc0ed8b8-c4a2-479b-becc-6b4257f09ef9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C240	car	available	f	f	9887746b-83f3-437c-ace0-08cd59ca2dbc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C241	car	available	f	f	c780d262-c28f-42ba-bb66-f3b7deec60bb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C242	car	available	f	f	55ac53fe-dec7-47d7-a684-8a597b79255a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C243	car	available	f	f	371e7133-c184-4033-a0b1-48f07de1c332	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C244	car	available	f	f	3377ee3f-5cb2-45c3-942c-3a28256d8e1a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C245	car	available	f	f	6fc6d70d-ca42-4a57-9a45-000dbf993371	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C246	car	available	f	f	752c11d6-2dc8-4431-94d8-2222b01d3893	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C247	car	available	f	f	c14bf8b4-eb71-4d7a-be28-5345f4e830cc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C248	car	available	f	f	06fe1825-3a5f-4c85-956f-e85aef7c34af	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C249	car	available	f	f	6495d3db-cb01-492c-8f56-9812732cf0de	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C250	car	available	f	f	2ff310db-3668-41ff-a502-620a78aeab46	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C251	car	available	f	f	d7f48a56-8b60-4525-bdb5-cff380f5d48e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C252	car	available	f	f	ebdfa89d-109c-42d7-a446-e1033eb49219	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C253	car	available	f	f	d0f711d6-a839-40bc-bfd4-0e5e63037bf3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C254	car	available	f	f	eb51b027-065a-4bd0-bef0-7d3b55f06674	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C255	car	available	f	f	1801b137-889f-4bba-a721-4ee1bd40a829	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C256	car	available	f	f	c061b087-f46a-43e9-b39c-6ab95d767e76	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C257	car	available	f	f	b0891d2b-073c-43b3-af74-717af36681f1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C258	car	available	f	f	8a75e0d1-cb05-4b04-94b3-fe8c364008ef	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C259	car	available	f	f	e7c8de81-446f-4928-b0a7-e5d67a596bf9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C260	car	available	f	f	dbba9f01-12dd-49a4-9064-4253d32d5b8d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C261	car	available	f	f	2e0f57c8-e198-4118-92d0-8a937fdef909	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C262	car	available	f	f	4ab4eecb-b2b7-4755-b3ef-aace94551205	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C263	car	available	f	f	2a1acd08-a621-4f50-931e-2bd2e6611b95	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C264	car	available	f	f	1d041aba-f2e6-4b7a-ad85-c8fdf483f3c1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C265	car	available	f	f	81713857-df29-4437-b289-4703ad9f71ba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C266	car	available	f	f	dd075c6d-d4a1-4dcc-ac5f-dcc0c54fd95a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C267	car	available	f	f	d047760a-e687-4cf1-b735-63d47bf34048	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C268	car	available	f	f	37389c12-d58e-4446-b943-fab6274dcd01	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C269	car	available	f	f	d39dbae8-f288-48b7-a0e1-7cf4186d494c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C270	car	available	f	f	74c9dda8-0f6e-4044-ac5c-3f9e57e3a349	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C271	car	available	f	f	8c9a642a-1fc7-4c0b-85d5-d41ef2905a6c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C272	car	available	f	f	00f11bbc-9c48-4151-8fdd-984e6ea1c82f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C273	car	available	f	f	9d150f64-6389-4be1-af2d-0114d7e22a1e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C274	car	available	f	f	b0fa5aa4-b49f-45b6-811f-b27c72433477	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C275	car	available	f	f	8efb1f9b-b876-415f-9b75-20c9d6f601ba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C276	car	available	f	f	95ef5cf2-2b07-4e99-95a8-f0cd34dbdacf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C277	car	available	f	f	ec2a3d58-cbfb-4d1b-9442-552135667036	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C278	car	available	f	f	ea44dc31-4ed1-45e7-b256-b2e27762c260	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C279	car	available	f	f	36ef71ff-d974-4175-95fd-cb184f226208	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C280	car	available	f	f	d45712fc-2be7-453e-951a-2788365a256b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C281	car	available	f	f	fc5f856e-a4f9-4675-8f4c-68c49d4383d3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C282	car	available	f	f	1a4f18ce-24aa-4695-a2e8-f584d4319e02	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C283	car	available	f	f	5b73d67f-8042-4a87-9782-50991a72f73d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C284	car	available	f	f	82015aa0-510a-4e2c-b442-bb508802b415	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C285	car	available	f	f	df36842c-87a9-459e-b560-7c2787931f09	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C286	car	available	f	f	4888e2c4-4ac2-401a-9796-3206b0b057ae	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C287	car	available	f	f	8d7192b6-a16d-4237-a96c-3587a2d0cf20	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C288	car	available	f	f	d968c3e4-d94a-498f-a30a-550e0ede741c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C289	car	available	f	f	7008ad5d-8928-413b-b85d-6ca12c54acf4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C290	car	available	f	f	c01c98ac-f08a-42d1-a59f-bc2916760f10	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C291	car	available	f	f	b1567158-4625-4aea-8a2b-ccecd80ad47b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C292	car	available	f	f	69a2092a-e740-4d57-9754-d620cc93e550	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C293	car	available	f	f	97f1248b-475e-4855-ae14-034c156d8737	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C294	car	available	f	f	3947702e-096e-47d7-8c29-26edba67d025	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C295	car	available	f	f	747302a5-b54c-4fa7-9c5a-460650e38188	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C296	car	available	f	f	c4ceb1dd-6460-4688-ac70-2d3df27bcca9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C297	car	available	f	f	dbba03f7-cd8d-4327-a7e6-df0846d99bd4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C298	car	available	f	f	801157ee-2df9-4c39-958f-351d24edef3e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C299	car	available	f	f	cf6edceb-3ea1-4791-aad4-70b1de20144d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C300	car	available	f	f	4683bdc8-7811-458b-9df4-602046c01377	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B001	bike	available	f	f	f635205a-3921-4c31-b6b7-192382cb9c80	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B002	bike	available	f	f	f0254bb4-fa23-492f-9e85-9ddb56c4196f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B003	bike	available	f	f	784bd312-4e08-4c30-8527-ffa17b29e367	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B004	bike	available	f	f	79169ffc-450b-49c2-89b1-bd7f33bd1c26	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B005	bike	available	f	f	97eda465-f0f0-49ec-9c20-65cc1f6d51fe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B006	bike	available	f	f	89690b3a-6b94-4216-b952-31ef5976d146	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B007	bike	available	f	f	80f22dec-8d40-4d13-a938-4589eb985e01	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B008	bike	available	f	f	1edef417-5148-4dde-897e-85a83e74b421	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B009	bike	available	f	f	3afe22b8-4cf5-4843-abf0-5e962a3f45d3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B010	bike	available	f	f	bc9931b2-272c-4a51-95ea-ceffce7784a8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B011	bike	available	f	f	4c3c94d1-a993-454f-aa37-3632908898c6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B012	bike	available	f	f	f37f4115-e6d5-418f-b0d4-96a443637065	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B013	bike	available	f	f	3d2c995e-6721-4304-91a7-35b62f66e335	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B014	bike	available	f	f	9fc0a753-7531-40f4-829b-1f510dd85798	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B015	bike	available	f	f	d9782e18-8708-423d-be29-0557883da8f0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B016	bike	available	f	f	94dc65c3-5cc6-4bbf-92df-04f1c85c9b7c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B017	bike	available	f	f	b2ae8e78-c61f-4608-9892-a1cc525f92ec	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B018	bike	available	f	f	9b09c8a9-62d4-4a44-8c52-c3a1e816ad03	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B019	bike	available	f	f	ce512074-8fdf-4d0e-9dec-78688b640654	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B020	bike	available	f	f	50187be7-90d4-4e43-bd35-9230a0fd7bd6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B021	bike	available	f	f	8ee16de4-3e92-4ca5-a376-a559db3ab187	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B022	bike	available	f	f	b293547d-c971-4a82-b374-b3c6f7b2eb37	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B023	bike	available	f	f	0bfff781-9a43-449b-be9d-b7ddc1fc2a2e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B024	bike	available	f	f	ede6335b-27da-4605-8314-d587dded4bc8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B025	bike	available	f	f	e1083525-b977-48fd-afdb-86574a33e7f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B026	bike	available	f	f	4901ba87-9606-44c3-84b3-48d409e72cb7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B027	bike	available	f	f	6500e6f8-7f19-44ca-9ba5-999a4642f20a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B028	bike	available	f	f	5dbce1cd-71c1-4c03-bf85-2ef658208a32	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B029	bike	available	f	f	747a1754-e845-4ee5-b8da-2dfdd6a5d450	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B030	bike	available	f	f	757b6fb8-948e-4f09-bd65-dbde22bea7b5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B031	bike	available	f	f	5d2f43ee-37e7-4f00-8922-6790a06e54d8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B032	bike	available	f	f	47484649-fe13-40d2-8374-a2fe8e775d45	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B033	bike	available	f	f	4a67d1b6-2b20-4abf-ad5f-b7571cc5b080	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B034	bike	available	f	f	18905f00-5a5b-4319-ad0b-edee0958f73a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B035	bike	available	f	f	abdf1ad4-793d-4412-9d11-c65c4eb7f5ea	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B036	bike	available	f	f	1cf3af59-ff3c-43fd-8948-e580c580a454	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B037	bike	available	f	f	c64d1015-a168-42c7-9411-b9ee0adb8410	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B038	bike	available	f	f	700e5867-9f64-432b-b9ce-1d99abad4fd3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B039	bike	available	f	f	6816f2c3-5b75-4a89-9333-c7da42d25041	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B040	bike	available	f	f	41d15b58-d1f8-472f-8ddb-e1ef9ad6a70a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B041	bike	available	f	f	aae77cf2-0b2e-4e79-ae05-693b92d6729e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B042	bike	available	f	f	023fe76c-e207-4fad-a0f9-1d89ee662787	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B043	bike	available	f	f	4fc118a5-c7fd-4d6b-9f23-eb055485c219	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B044	bike	available	f	f	cf1048d8-2e39-499e-9669-83e32f2549a2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B045	bike	available	f	f	6b412b4d-2b26-4fb0-8df4-f54d4c051ba2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B046	bike	available	f	f	0c754d46-0769-43b6-9eba-ed1c8afad16b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B047	bike	available	f	f	e6601688-3bfb-4add-8843-b058c927b813	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B048	bike	available	f	f	0579f35c-8476-4247-8db9-353b87d2e834	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B049	bike	available	f	f	eaba1bad-79b3-45b8-8a3f-29e19913ce46	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B050	bike	available	f	f	edc74464-db75-4d55-a72b-1fc8ee3a184a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C025	car	available	f	f	1505f7b5-bb84-4bb2-bb47-6473aa8ce2b3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C026	car	available	f	f	f69bd0e4-0f68-491e-9a2c-dabdc87c0e46	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C027	car	available	f	f	a4e428ea-88d1-4b72-ac8b-0dae4eb376c4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C028	car	available	f	f	91a964b9-842b-4f6e-b9d5-90d374a64cf6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C029	car	available	f	f	77dddc36-97e9-46da-a469-97c14cb6b01b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C030	car	available	f	f	e40d06af-5c74-4ea7-a334-04f32b55ba3d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C031	car	available	f	f	c386ca8e-1242-4a3c-807b-58c016592929	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C032	car	available	f	f	553c436a-6dcc-44bf-b28e-93f06d42348d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C033	car	available	f	f	deaab026-1742-4c0f-a1ab-221cb30aefa9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C034	car	available	f	f	5ce7a4de-e5ae-4e98-82da-da522a0d52d8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C035	car	available	f	f	50a39bdf-31d7-443e-bed4-4c192fa78e84	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C036	car	available	f	f	8ca4a80d-5314-4e65-9534-3507ad2f3f18	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C037	car	available	f	f	4898a06c-78da-4de9-af8b-98c816bb4021	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C038	car	available	f	f	4d490dd3-1143-4c40-92a2-b1468884ae3b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C039	car	available	f	f	33954e57-903c-4abd-8985-d2d2bace31d4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C040	car	available	f	f	727cebf0-4b2c-48c5-9737-326904826b3a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C041	car	available	f	f	7c214d07-07b9-4619-894d-2122949c6cd1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C042	car	available	f	f	3795cdec-234d-4b20-a9a3-0cf3ab92e4a5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C043	car	available	f	f	015717b4-452b-40d6-afb5-13c441985938	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C044	car	available	f	f	bb2dd03b-dc15-4a55-b9ca-71279d2ee569	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C045	car	available	f	f	c2f09942-a880-4f77-90c5-885267e62748	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C046	car	available	f	f	5e31194a-269a-4687-84ca-0876a901a439	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C047	car	available	f	f	0d4d1a51-b401-4ef1-9920-0d50f3d2197d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C048	car	available	f	f	3cbc0c63-1f53-4fc3-9827-aa0e027ec275	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C049	car	available	f	f	9aecb650-d6e8-4884-9468-8210fa06f354	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C050	car	available	f	f	266d51e3-5ab4-4b89-b52d-b8f809abf8d2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C051	car	available	f	f	f9279440-fb05-4772-90f6-df6c0f5eff4c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C052	car	available	f	f	1d1cfaa3-7051-4ead-b466-43aff3da0440	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C053	car	available	f	f	7840db82-458a-4609-af1d-358e0df98bd1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C054	car	available	f	f	05227c0d-3e56-43e6-833f-be94eaf6ff77	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C055	car	available	f	f	ba50a122-5a03-4029-82f4-6ceeb51db34a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C056	car	available	f	f	fd97ee8e-a819-418d-8c05-7ede93a8b478	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C057	car	available	f	f	3e64c1fe-2f8f-4855-8696-611ba3ff4a66	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C058	car	available	f	f	8c855c83-3809-424e-bad7-d5db1c6b30d8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C059	car	available	f	f	d03b560c-33bc-47ab-9c13-fff5dba7bc90	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C060	car	available	f	f	58a26a05-dcd2-4031-8bda-c13ffaf8101b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C061	car	available	f	f	db4d0361-7bd6-4cfa-a281-fe00c5265894	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C062	car	available	f	f	e526b376-d4b5-49bd-aa7c-53afb8142549	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C063	car	available	f	f	e450d194-9b76-47a1-b082-523d41878ccc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C064	car	available	f	f	506e6e2e-6962-4f27-8462-020b5bb7b0ad	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C065	car	available	f	f	69033e2a-e1fe-4042-87c4-7aef8351a53c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C066	car	available	f	f	0cd1c5bd-ea07-4d4c-9183-aa36c3dd2a60	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C067	car	available	f	f	48bccd55-f5f3-4a6b-9c30-272c2ffed295	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C068	car	available	f	f	5cb6d4e9-eb3e-4077-a64b-7361258e8c03	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C069	car	available	f	f	029f925b-f669-4dda-881b-7f9bb176309c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C070	car	available	f	f	d68d35da-7a33-4b74-bc56-942b07783a19	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C071	car	available	f	f	d0fa57e4-7c49-46f4-8951-903403f50849	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C072	car	available	f	f	bd962c90-79ab-43dd-bfac-030f522d82b3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C073	car	available	f	f	b2ed3276-fdb5-4b84-8157-de008585a858	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C002	car	reserved	f	t	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-16 11:30:31.351032+00	2025-09-20 03:09:19.884399+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C003	car	reserved	f	t	a704960a-8750-4a1d-be7f-1553ed110778	2025-09-16 11:30:31.351032+00	2025-09-20 03:10:33.707769+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C004	car	reserved	f	t	47491068-c3e6-48ed-93ca-d0eee23ad389	2025-09-16 11:30:31.351032+00	2025-09-20 03:41:58.77605+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C005	car	reserved	f	t	68d5ded7-79c8-45bc-97cf-05ed5b4f9191	2025-09-16 11:30:31.351032+00	2025-09-20 16:20:26.639794+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C006	car	reserved	f	t	cedffa56-a5b9-421e-8cf3-4dab8aa44d36	2025-09-16 11:30:31.351032+00	2025-09-21 08:42:22.296129+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C007	car	reserved	f	t	5d5747f7-b6e8-42c7-bb83-9159057b949b	2025-09-16 11:30:31.351032+00	2025-09-21 09:18:31.824734+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C008	car	available	f	f	05d8aa52-d6f0-4ac4-b595-b8e708b695d6	2025-09-16 11:30:31.351032+00	2025-09-21 10:50:34.579519+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C009	car	available	f	f	a276b69a-5df7-4dd8-84df-c7874543fa4e	2025-09-16 11:30:31.351032+00	2025-09-21 10:53:24.075159+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C010	car	reserved	f	t	b9360900-0194-4a58-ac78-c4ed9e833461	2025-09-16 11:30:31.351032+00	2025-09-21 11:24:10.950637+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C011	car	available	f	f	0dfeb933-6940-4c2b-9b81-f71a9035e8f8	2025-09-16 11:30:31.351032+00	2025-09-21 11:50:41.286859+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C012	car	available	f	f	ea268287-f5d1-4ffd-bd58-dc17b1ae2464	2025-09-16 11:30:31.351032+00	2025-09-21 12:40:29.675907+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C013	car	available	f	f	3391a24e-ccb4-43d0-b859-6627cd0efc00	2025-09-16 11:30:31.351032+00	2025-09-21 13:02:03.725722+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C015	car	available	f	f	6d780bf6-e999-40f1-88b6-473a4ecdda18	2025-09-16 11:30:31.351032+00	2025-09-21 16:36:31.229606+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C016	car	available	f	f	707a46b3-2c9d-4be0-8c4e-0b7671ac6931	2025-09-16 11:30:31.351032+00	2025-09-21 17:23:13.167986+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C017	car	available	f	f	ffaad7bd-a5e3-448a-9828-b7643f94fefe	2025-09-16 11:30:31.351032+00	2025-09-21 18:56:53.06955+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C018	car	available	f	f	bc2929e5-9ba7-4964-893b-c4efa02c368b	2025-09-16 11:30:31.351032+00	2025-09-21 19:50:16.291448+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C019	car	available	f	f	a4f1bcea-2fbe-4271-b576-b4cbe0d44dd3	2025-09-16 11:30:31.351032+00	2025-09-21 20:22:28.571236+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C020	car	available	f	f	13025bce-1592-4b97-96a6-726003a8b211	2025-09-16 11:30:31.351032+00	2025-09-21 22:36:55.755736+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C021	car	reserved	f	t	0e5faa49-cd4c-4a39-bda6-ffe43ccb386c	2025-09-16 11:30:31.351032+00	2025-09-21 22:42:57.339987+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C022	car	reserved	f	t	c4d71026-9b0c-4e45-a465-0350378d7036	2025-09-16 11:30:31.351032+00	2025-09-21 23:12:57.335645+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C023	car	reserved	f	t	17715b50-c74a-4fae-a9fc-d59a5d008729	2025-09-16 11:30:31.351032+00	2025-09-21 23:16:12.895404+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C024	car	reserved	f	t	931c3658-819b-4843-95ba-85e7b7ec5360	2025-09-16 11:30:31.351032+00	2025-09-21 23:24:26.367927+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C074	car	available	f	f	3f6c6726-3265-4d3c-b4f2-35f51286664e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C075	car	available	f	f	577800af-4ce6-48be-99e8-03a0b3ba292c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C076	car	available	f	f	3c22e70d-1001-4c94-97a6-0f39c9d40c6d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C077	car	available	f	f	b431226a-2824-466b-afa2-c120278c1064	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C078	car	available	f	f	5a2ecfc6-a97d-4cc2-a15c-bf1efb314ed4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C079	car	available	f	f	383cf7ff-5102-4c61-b980-dea4b68dc533	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C080	car	available	f	f	1b50d670-a138-4119-9a5f-e1cb1fb70933	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C081	car	available	f	f	dad45d22-546f-44dd-a8e3-5e9980142afc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C082	car	available	f	f	062c8d0a-7428-471b-9d09-c2f457ecd789	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C083	car	available	f	f	e0d6624b-c69f-4a76-95a1-afe8865855b0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C084	car	available	f	f	1bd9efce-332e-4b7d-ac47-850ef2cb2b99	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C085	car	available	f	f	038fdb6f-5a63-47f8-ae83-7e01fe819ff6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C086	car	available	f	f	3b22a075-bc0c-4ed0-ad2d-d25c37c45e28	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C087	car	available	f	f	ea910d13-3518-4b46-b84a-291b3214d134	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C088	car	available	f	f	b836d074-8e4a-42c3-b3f3-6ae704f65bf5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C089	car	available	f	f	01e98a4c-ae82-4a83-9c46-328ac940e48e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C090	car	available	f	f	a6a9d33c-da07-4104-b19d-ce2dab61d34f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C091	car	available	f	f	5115592b-2aba-4d92-8bb2-adfc1b3729fe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C092	car	available	f	f	38dd585d-c760-4ead-953c-78d17fadf04b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C093	car	available	f	f	b9721364-f79c-40d4-8933-ed6b40465db8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C094	car	available	f	f	da1213d0-69d4-4c69-8a50-0e6b770ccf59	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C095	car	available	f	f	53b60430-f6b4-4250-98ba-ba45d2892159	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C096	car	available	f	f	db17ba84-d6f7-4662-bc7f-8b57530b2da9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C097	car	available	f	f	73054dc7-b7b0-4e6d-ba1d-0f7c9e7f3b82	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C098	car	available	f	f	22bce1a8-6311-48e8-96f9-2a0e2950ed0a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C099	car	available	f	f	44413c24-c6c8-4931-87dc-0980848bb479	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C100	car	available	f	f	f347e82c-b62e-44cd-8e50-5cff4598c596	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C101	car	available	f	f	828faae3-61f5-492b-947e-0df4d37b2bf9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C102	car	available	f	f	e7618a23-ae5e-409f-b67a-5115bf5678ad	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C103	car	available	f	f	5784d7f9-5013-4e2b-a7ba-151021567ef9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C104	car	available	f	f	b85f5ca4-9b7e-477f-b4c8-c8c98c52f8b6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C105	car	available	f	f	696039eb-5e94-4770-b2ef-f1250f76cca3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C106	car	available	f	f	675e2cdf-6ddd-48f0-98c5-cb588e8720d2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C107	car	available	f	f	e220d352-8caf-4c58-b5d4-517133164b82	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C108	car	available	f	f	a2e944b0-762a-4a84-ae88-6718089d6f20	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C109	car	available	f	f	30b6c286-7359-4c29-bc37-9dc4f0910fe4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C110	car	available	f	f	dd8b9a52-2923-4df4-9fe4-4b951d2f7c33	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C111	car	available	f	f	c88f335a-a63b-4637-9a86-a6a39cfcd410	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C112	car	available	f	f	d0bc34fc-5c49-4601-86cc-7f423db73d70	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C113	car	available	f	f	bf16101b-759d-43bb-9d4e-f832ac994fed	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C114	car	available	f	f	e71dffd9-3c21-4800-a5f0-73eaca00b994	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C115	car	available	f	f	6d6509b2-dd2e-4ec8-b715-a3c2868f29c0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C116	car	available	f	f	19d2736c-7a26-4a1e-bf62-1fbcf5887d00	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C117	car	available	f	f	645d18b8-087a-4acf-a044-6d2369116aba	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C118	car	available	f	f	7d1a9cb7-9f83-4f95-9210-8e8a541086ae	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C119	car	available	f	f	2d83f2d7-6e12-4a78-b6a7-3fb65dc19431	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C120	car	available	f	f	c4c5234a-5a73-442d-b42e-c4b72f987244	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C121	car	available	f	f	6ef9980b-46c2-4851-a3e8-f307a20efa6b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C122	car	available	f	f	219d7054-404e-4b2b-8a4f-e8e87e3e3573	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C123	car	available	f	f	d0d27f70-bcb7-451c-ae96-4a190202a49c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C124	car	available	f	f	a34484c4-ab1d-4f45-a710-fe261b810925	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C125	car	available	f	f	ce02a683-a6f3-4446-b3a9-6e11f16c19c4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C126	car	available	f	f	4d55f11c-5b5b-4717-9e50-862ac84086e9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C127	car	available	f	f	3a11fa43-665d-44ee-b42b-8e5822469e19	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C128	car	available	f	f	bf85e2e6-4970-468b-85dc-1ba5e2e791f3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C129	car	available	f	f	3409bb74-5c5e-4405-b2fd-86839bea4fc2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C130	car	available	f	f	93c493e8-1618-4f10-9593-7cf49ddf78c9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C131	car	available	f	f	5709d2eb-69ef-4180-ae23-c4d2cb077ad2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C132	car	available	f	f	4e924ca0-1375-42f1-99fe-4a9adc562946	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C133	car	available	f	f	df5ff78e-06eb-4fff-b4d6-4c4ab3133f61	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C134	car	available	f	f	b39a330e-ced3-4281-9e7a-b80c45683b63	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C135	car	available	f	f	3f280b59-05b8-4937-b38c-212f6756618c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C136	car	available	f	f	d306cd63-c7e6-4c60-8e56-fb1a20789eca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C137	car	available	f	f	d56af979-ef6a-4c2a-9de5-1a108bba05e2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C138	car	available	f	f	4122e28c-d091-4c03-a2df-b4b25cbc174f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C139	car	available	f	f	6059b619-5bfc-4294-88a3-aa58d2939002	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C140	car	available	f	f	f4ca5287-709b-4d64-af01-30e4bf241dde	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C141	car	available	f	f	c9b146c6-71cb-45ad-8237-0c71be4e1a54	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C142	car	available	f	f	6776d115-218f-4527-9025-0358c8e6be34	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C143	car	available	f	f	add4ec0f-3d7c-43e7-80e1-b5972f4f5a71	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C144	car	available	f	f	20f92a37-026b-4bc8-bf7c-0fd87f032e62	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C145	car	available	f	f	04bc9614-7a45-45e2-8570-acc36aee1ae2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C146	car	available	f	f	5caaf6e4-a508-4a83-9fec-ea5b7ce83ebe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C147	car	available	f	f	d63826cf-6590-4d5a-bd3e-90fef4572ddc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C148	car	available	f	f	ee48c803-da40-4e9d-96b9-36fb66bd7f57	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C149	car	available	f	f	74f665ec-ee68-440c-b346-c109cc4badf8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C150	car	available	f	f	08d2e2b9-6c18-444c-be8f-3ffefa431a2b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C151	car	available	f	f	a977fe52-d147-40ac-8001-cb21b73b6bbf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C152	car	available	f	f	7e33c316-810a-40ca-9c71-26bd2dff1e3f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C153	car	available	f	f	1b409532-2fbc-4f64-9ef3-b807325403f1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C154	car	available	f	f	e3b2fbc9-2016-438d-a217-75c4a310841a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C155	car	available	f	f	0ee87697-86a2-4d40-8589-5927b7a9139b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C156	car	available	f	f	ad121c8f-69d3-41b5-9823-35fca32ab2b8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C157	car	available	f	f	4c5c5f3f-3aa4-4d41-ad96-96ceb1493a18	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C158	car	available	f	f	038d3e0b-5d2c-4c42-a1cb-413732537fe8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C159	car	available	f	f	ca15edef-11dd-42e8-b036-b0d0d53a7ad6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C160	car	available	f	f	66170dda-49f8-445b-a9c1-4948df71bc4a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C161	car	available	f	f	26f3f979-05fb-4e2a-b967-11ac0ab31443	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C162	car	available	f	f	48b9aa23-38a0-476c-ab05-660a84bdeb7d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C163	car	available	f	f	ea806f38-d961-40ec-aa96-bcb9d46fbb19	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C164	car	available	f	f	29217ab1-ac2c-4d4b-b98f-1a581a354ecb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C165	car	available	f	f	216bb989-ead7-49f9-8628-92f4839ce911	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C166	car	available	f	f	b9e811e7-315e-4133-8c20-2668cbf9beb8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C167	car	available	f	f	f3031541-2c39-4840-bbaa-ab7b61ca5991	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C168	car	available	f	f	37b514b5-8b23-462e-983f-55c22cfb1944	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C169	car	available	f	f	1fb11bea-c31b-423f-93cf-f872bfae1617	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C170	car	available	f	f	1c773d91-e923-473e-89d8-9d1d50b9605f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C171	car	available	f	f	9979a5d5-9754-4307-8533-edc06bdda354	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C172	car	available	f	f	99d08014-5e60-4141-a5a4-ec13ae4ca62d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C173	car	available	f	f	942a7872-5122-42f8-953e-77a8a6f81090	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C174	car	available	f	f	4a08dabb-a1c0-4898-8d43-04187e89b35a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C175	car	available	f	f	78c9dd68-84a9-4e7f-82d4-c74a0ffd97ce	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C176	car	available	f	f	6581677d-37d4-4085-a87a-bd7935ebb695	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C177	car	available	f	f	37ac2bcf-d7ee-4e2f-a1f2-766a2a1ac49c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C178	car	available	f	f	a69e06cb-fd91-40f8-a464-3a4cf4a7b722	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C179	car	available	f	f	a7128cfc-1628-48e5-952e-34dcc93a4a4d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C180	car	available	f	f	196f5daf-fece-4da2-b402-5b83726bce1d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C181	car	available	f	f	cb770fe1-1ad0-43cd-bfb4-7c7667026939	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C182	car	available	f	f	5f5ec487-3c82-45b4-89d4-869dcb3cf3ae	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C183	car	available	f	f	97990f89-132b-401b-9da6-82faf106d580	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C184	car	available	f	f	f2d83ed4-4b11-48d2-b2ee-67ae4651af87	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C185	car	available	f	f	af566c58-71ad-491e-90d2-b150c3833425	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C186	car	available	f	f	d7886b1d-d57c-4ade-91a2-7966760516de	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C187	car	available	f	f	38ea7984-38f9-4e39-98dd-1b43c204eae2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C188	car	available	f	f	8e29e987-24f0-4f84-8cde-a8ac03a5e56a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C189	car	available	f	f	a954cc44-06e9-4606-ad65-01c47c964cb3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C190	car	available	f	f	768072be-c84d-4789-a3d1-758e9898bfbd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C191	car	available	f	f	963bea57-d5cb-46fc-a112-9db21b96d627	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C192	car	available	f	f	6e430639-d080-48bc-80f4-e92610db4077	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C193	car	available	f	f	3d500b00-b811-4992-985e-bcbf3530a981	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C194	car	available	f	f	b31db00e-870d-4a42-bffb-7d8496af167b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C195	car	available	f	f	3927ed47-d548-45ca-9ad3-274682103f66	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C196	car	available	f	f	e3f42a31-c3c2-4abe-b26e-03825cc0b486	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C197	car	available	f	f	f017ce70-a5c7-4a61-875d-f43a3181eb3c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C198	car	available	f	f	f829b80c-9ac8-4742-915c-1cbd64947831	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C199	car	available	f	f	64e42433-d039-4f47-b02f-4329f2050ac5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C200	car	available	f	f	8ffaf0ca-ade5-476e-ae6a-cb00c74759ca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B001	bike	available	f	f	cfa4cf27-59a7-4001-a471-f147ed716520	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B002	bike	available	f	f	72b06873-da9f-4be1-bd0a-7778a6f8f973	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B003	bike	available	f	f	6dafd2ad-fbff-45fa-b67a-413509b5edb1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B004	bike	available	f	f	367c563e-adc9-47a2-848d-383a419bb79d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B005	bike	available	f	f	c7958bf7-e91b-4e73-92b7-53149d6774df	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B006	bike	available	f	f	6ba8efa3-59f1-4227-9e10-9ca2b7b527be	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B007	bike	available	f	f	af7923fb-5a97-447a-b871-7d952a210b97	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B008	bike	available	f	f	da5aa896-23e3-4eb7-beed-0dfb884cd370	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B009	bike	available	f	f	63ee934e-8021-4d0f-bfa1-cb31daed4749	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B010	bike	available	f	f	54435af7-82d9-4a60-98d8-537fa534c517	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B011	bike	available	f	f	b20af2b3-fe7d-4866-bede-3efd37b3dbe3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B012	bike	available	f	f	e3fd0871-5cfa-440f-ab4e-be36b353df4d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B013	bike	available	f	f	b6afda77-ba93-41a6-8abf-89bec26e629d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B014	bike	available	f	f	70ab2e8c-91e7-4d65-81a5-43f8c3bb6d2d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B015	bike	available	f	f	64582dd1-b806-45f9-b720-eae5c4a53d52	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B016	bike	available	f	f	8fd05331-1d90-4c8c-ba56-8257b0bdba6f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B017	bike	available	f	f	432be3fa-f076-4b06-95bb-d0c614da51a1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B018	bike	available	f	f	b5639fb7-44ba-4f46-bb7d-7e56cb46b891	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B019	bike	available	f	f	96b99336-4ebb-4a28-a6a0-69e0ad587b2b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B020	bike	available	f	f	a1110409-baa9-49eb-8fe7-ee158d6a5df2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B021	bike	available	f	f	81e4bc80-1add-43f8-a108-b75f94491312	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B022	bike	available	f	f	6d7a1692-bfa0-4c66-a0c6-829309d6e92e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B023	bike	available	f	f	80483a34-39c1-4823-8d6a-e1df1b54818f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B024	bike	available	f	f	f906e5c8-f6d8-4be5-9f95-6e95487aaa37	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B025	bike	available	f	f	d8a88d72-9887-4539-88a6-e281a404cfa1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B026	bike	available	f	f	66264693-0105-4853-867a-1698984ee6fd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B027	bike	available	f	f	236b57ab-9568-4045-bc66-0a4c8d57ae30	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B028	bike	available	f	f	1e663fd9-a99c-404b-84fb-198adcc76887	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B029	bike	available	f	f	bd4b5881-8240-4cee-a140-8b3c8283e4f5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B030	bike	available	f	f	90f4fecc-50d7-4ba6-9af4-1c1bb2dfcbc0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B031	bike	available	f	f	c058eeef-2b74-48c4-a717-2d895c099fcc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B032	bike	available	f	f	82073a4e-cf50-4d49-b925-8a1aef09f4bd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B033	bike	available	f	f	311fbf61-a658-4ea9-a588-89d4eff4c63a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B034	bike	available	f	f	43792f5f-9ca7-4224-9169-0247dfb53930	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B035	bike	available	f	f	5d08f454-5902-4ddb-ab5d-34b7e4845597	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B036	bike	available	f	f	6b38c909-eab1-4bf3-9f91-1a3de22918c1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B037	bike	available	f	f	09eb37b4-6bdc-4f3f-9561-c0791a2cc1f8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B038	bike	available	f	f	6b8be61d-15fb-4b8d-9148-eb248ed1acb6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B039	bike	available	f	f	597af18c-42e9-4ee8-be56-e1a258407e86	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B040	bike	available	f	f	06fff507-1efd-4269-b7d1-8f6e3e5b9451	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B041	bike	available	f	f	9a151ba4-7f2d-483c-81cb-c16fbea9a1fe	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B042	bike	available	f	f	534cb5b2-7cab-4cd5-85ad-9180cbed3b51	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B043	bike	available	f	f	0ad98dcc-edf6-4897-84a8-f85495f714a8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B044	bike	available	f	f	77ee9cc4-edfe-4abb-8579-724c96438ff5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B045	bike	available	f	f	34fa4186-7c80-498e-8717-cee617910f0d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B046	bike	available	f	f	3cd56869-8aa9-449e-bbb6-13b59766b33f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B047	bike	available	f	f	86a3d6af-e0b6-47b3-ab33-1c71c291335a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B048	bike	available	f	f	205302bb-7d0b-41d7-8f34-f80c1d3ccc79	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B049	bike	available	f	f	0461041f-ec9a-4514-86b1-22bcf3902b91	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B050	bike	available	f	f	94a6800e-2bda-4764-84b4-8c2d8004be05	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B051	bike	available	f	f	43fe5ca1-ff17-4032-aadb-670e122022b9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B052	bike	available	f	f	ac41cc46-bbe6-443a-b7c9-7e0ac8c61749	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B053	bike	available	f	f	c10aa680-ee75-4808-8996-0430dfc0a36b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B054	bike	available	f	f	53231358-bd3b-4f65-b3c8-acd58b325d67	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B055	bike	available	f	f	d7e286ac-a980-47c3-8c40-c92c63c8910e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B056	bike	available	f	f	f02197f5-892b-4cf8-8e50-8fd909a0fe7e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B057	bike	available	f	f	4529d98a-0eef-4e8b-9a6e-ee7f057ac28e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B058	bike	available	f	f	c92f4a82-f671-4709-8887-c7e6528f558f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B059	bike	available	f	f	0540e160-cd76-4449-9286-d8d45ac92ab0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B060	bike	available	f	f	057db89b-7162-4951-a1f6-15c98cceb7d4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B061	bike	available	f	f	3931115f-5768-4bf3-b04a-6d95dacacf50	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B062	bike	available	f	f	76ca7f4a-d956-4977-9931-dc2e4b7413ee	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B063	bike	available	f	f	9c19c940-5b42-458f-b336-14a62e38eaed	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B064	bike	available	f	f	239e39ed-5183-453a-b209-ab88370e5c87	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B065	bike	available	f	f	5aeffb46-7730-433d-9d02-b0c984463fa3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B066	bike	available	f	f	43fdaf01-9c48-44b4-8e5f-57c049e6ae94	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B067	bike	available	f	f	9048d560-1b49-4563-9c37-27d12cd98424	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B068	bike	available	f	f	021f5665-6a53-4f3a-aeb8-b8ad43adcf03	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B069	bike	available	f	f	88cdf140-a664-4b4c-96a9-37dee41470a6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B070	bike	available	f	f	f1125157-ed6d-4e86-a80e-aab33611c758	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B071	bike	available	f	f	e3d18570-f03f-4b9a-8c24-cea1b9a5377b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B072	bike	available	f	f	e57a6d92-37a4-413d-b402-e96eff9f1566	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B073	bike	available	f	f	553cfae2-2bf4-4ba7-841b-4fe96264a45a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B074	bike	available	f	f	e66fc3cc-bb92-4e4e-a6d5-8ff0406b7e78	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B075	bike	available	f	f	df1db5b6-72be-4713-b71c-e046847f166e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B076	bike	available	f	f	49eff572-0d94-4393-93b9-02fa3a4d4bef	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B077	bike	available	f	f	91092fc4-e3c4-4e23-8d5a-905eeaf83265	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B078	bike	available	f	f	fd35c121-a0c5-4ba3-a8b9-b02659e56bbd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B079	bike	available	f	f	45002f84-e273-4b7a-9e4c-e360615d1a84	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B080	bike	available	f	f	ed5bbd43-599f-4b13-b661-cc9a9b68244e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B081	bike	available	f	f	73c7c602-5a7d-4147-9185-6b18156d827f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B082	bike	available	f	f	5e0a021d-7bed-4f5c-b9ad-5b38eff083e4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B083	bike	available	f	f	a90c7f0f-0f0b-4930-a717-bbe908033585	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B084	bike	available	f	f	6707f772-2bff-4635-87e5-c822a3880dce	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B085	bike	available	f	f	45741089-fb4a-45e8-8502-04a4c779ccce	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B086	bike	available	f	f	81e12d8f-b330-4e9f-b3ec-c46f93c61d1a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B087	bike	available	f	f	cfe511fd-f07c-46c8-a150-52a7cab37281	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B088	bike	available	f	f	d002fce9-2ca1-423f-9be8-1c8443d867ff	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B089	bike	available	f	f	39d9703d-6757-4a8c-8748-20d94277b3f1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B090	bike	available	f	f	4e137194-541a-4158-b003-cdebeb95f18d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B091	bike	available	f	f	4dd33a5a-c0a5-4400-82e5-6a04093344c4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B092	bike	available	f	f	fbe25bee-4a3b-4898-91b1-3ab6792803fb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B093	bike	available	f	f	2a7c3bd3-28a5-45dc-a501-a67415c9c0df	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B094	bike	available	f	f	ca06f55b-11c3-4744-acd9-4d3be85f9b6f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B095	bike	available	f	f	7087d7da-87a6-4434-9eae-1086161484da	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B096	bike	available	f	f	fbd82872-e4da-41e6-be0f-2f57e16b137f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B097	bike	available	f	f	3fbd5017-0272-4777-8356-59dabf54f434	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B098	bike	available	f	f	b74dacbd-7b2d-427b-8ed3-281c0cefc76b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B099	bike	available	f	f	d49cc45a-e7a9-4d34-a4bc-63f756117432	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	B100	bike	available	f	f	9b8e660c-ad72-4581-b149-27175c8e350f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C004	car	available	f	f	b5d196d2-3fed-4649-a6a6-ce909bd1de39	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C005	car	available	f	f	bf6e8dd4-8dd8-49fa-8948-c3dca63959de	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C006	car	available	f	f	ad3176e5-f582-4097-a4b4-2121793d1443	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C007	car	available	f	f	ef0167bf-ad8e-4c33-8151-48dfda37293c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C008	car	available	f	f	36ca275c-c6dc-4aac-ac75-cfff7be2b039	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C009	car	available	f	f	80ce3d6c-24c2-496f-a6e9-93ff56056a7c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C010	car	available	f	f	8cf1c549-f8f3-4fd0-bc60-56ac88cec309	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C011	car	available	f	f	e1f58aeb-c803-4fce-988b-69d58ff7b5b3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C012	car	available	f	f	8f460447-48db-4926-8a37-7edde9bc4daf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C013	car	available	f	f	cb0d49a4-3a9b-4bb6-9836-95cf2d01a98f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C014	car	available	f	f	c8a547d3-5c8a-4034-ab85-84b2f1ece278	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C015	car	available	f	f	7c379b18-a0ff-4edc-a85e-20e659e93c2a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C016	car	available	f	f	0213a11c-c34a-4979-bb9f-38c8a5c56f75	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C002	car	reserved	f	t	599b9887-075f-4667-8992-0a3c07801975	2025-09-16 11:30:31.351032+00	2025-09-21 23:00:50.433907+00
cd81f033-7248-45a3-ac82-1c310665f985	C003	car	reserved	f	t	9e4f166f-8894-426d-97b6-8d0a51e3bbc6	2025-09-16 11:30:31.351032+00	2025-09-21 23:26:35.494586+00
cd81f033-7248-45a3-ac82-1c310665f985	C017	car	available	f	f	6433cfe3-ecf8-4d7e-a086-48f70aaa09d0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C018	car	available	f	f	e10a6576-ab47-47a8-bb2c-be80447b16b1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C019	car	available	f	f	05ec09d1-1735-4ea3-9437-b93e65ce4a64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C020	car	available	f	f	192f0203-0cae-48a8-91bd-981284a72329	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C021	car	available	f	f	2935467f-35ee-4e89-99e8-0392bf7b916a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C022	car	available	f	f	1e626677-5134-4ca3-86bc-dc515a5abe61	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C023	car	available	f	f	b81cbba4-adba-4b52-8f7f-0859ea2001b5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C024	car	available	f	f	b22660cd-dcf7-46fc-b6aa-9df7a67dbb5f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C025	car	available	f	f	67c3e6ba-495e-4f8a-b1a8-6b4fbf6e3864	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C026	car	available	f	f	e6d608a3-f611-42fc-8a67-b45c20701ba1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C027	car	available	f	f	a3d94dc3-5551-4ede-ba39-1bd5cdbb49c0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C028	car	available	f	f	d8acc7df-ec5c-4472-aa58-e03ef7580bc4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C029	car	available	f	f	8009f549-ca48-4b70-b68f-f0da6435b99f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C030	car	available	f	f	bb510fa1-1417-4e97-b02b-110eaab527b0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C031	car	available	f	f	c67707a1-039c-44cc-a1ff-72044d09439e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C032	car	available	f	f	82c061ec-327c-44bc-9907-d4de2b62dc11	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C033	car	available	f	f	f855564f-bb26-4fc2-bde2-960c01156758	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C034	car	available	f	f	eb9e53de-29b3-42af-84ce-99449777307b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C035	car	available	f	f	51f4a284-fccd-4f51-bac7-5673c18a1367	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C036	car	available	f	f	a63dcb64-c80f-4b63-b4ad-b89d16c38443	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C037	car	available	f	f	2916fd37-a8bf-48c0-aaf3-096d2786e027	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C038	car	available	f	f	332c9664-a79c-44bb-bc61-fe099636c1e6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C039	car	available	f	f	6205189f-02d8-4599-9473-4c70332a1cdb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C040	car	available	f	f	23ed0b68-95d5-4c7d-881a-ce9e9d739cdf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C041	car	available	f	f	97d48832-b74e-4fb8-b828-0ef128bba7ad	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C042	car	available	f	f	4395d23f-9bf0-4fd0-83de-1ac9be8ce2b6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C043	car	available	f	f	384a44c2-afb4-4625-a642-68162af9e1e7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C044	car	available	f	f	838b1d0e-90c4-4a46-b19a-76432e8a358a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C045	car	available	f	f	7c1fc08e-1579-46c8-8987-50dc69fb891b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C046	car	available	f	f	62d152db-ff55-4371-a0f0-5ac02135ad0d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C047	car	available	f	f	7be70aad-82aa-4af5-89e2-2dfea040aafd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C048	car	available	f	f	f3c31cad-aea0-4003-a0dd-ef7681a49d95	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C049	car	available	f	f	1b91f988-dd9c-4f27-a499-20cbac460716	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C050	car	available	f	f	466bc5b7-8f85-4298-baf8-dd604142dab4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C051	car	available	f	f	39d69ca5-c04a-4650-b3a3-27140fc198b4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C052	car	available	f	f	4e745f82-0a48-475e-926e-d0d1f8139aa3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C053	car	available	f	f	adc6fe82-2510-454f-b045-e2aeacb1c199	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C054	car	available	f	f	b392139a-3083-4e40-afc6-03f9e38156fc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C055	car	available	f	f	98569b45-ee6b-4555-8987-a706c064b699	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C056	car	available	f	f	28e959af-e02c-4edd-bf2d-a0e5c73a4376	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C057	car	available	f	f	19c46e4f-cb7a-422e-a447-47c27c2feddb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C058	car	available	f	f	70601391-d818-42d9-8ae8-55740546d20a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C059	car	available	f	f	6a7012d8-5bbf-4b43-9721-582a2095f8db	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C060	car	available	f	f	0fba85be-02b6-47e5-80ef-9e947f931bb8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C061	car	available	f	f	5e2f8f6a-6b79-4ba8-a3fe-2d1a890f0220	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C062	car	available	f	f	fb3054a4-b5d4-41b2-9aca-5d3670fcc35c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C063	car	available	f	f	c2a86e8a-917f-44d0-8dca-fe93b06cfb31	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C064	car	available	f	f	5dbf7299-60a6-464b-8121-37f53e15f813	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C065	car	available	f	f	66fcc959-a6d8-4baa-804b-92979fcf6e97	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C066	car	available	f	f	06d57552-6848-4771-8da4-2eea5cf36662	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C067	car	available	f	f	5d7622cc-f3d6-44a7-87eb-c64fcb063373	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C068	car	available	f	f	a91a4a30-6d04-4f73-a216-4220df427b66	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C069	car	available	f	f	65a212f4-8ea6-42c7-8088-aadf5fd356f7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C070	car	available	f	f	2d674a9b-3311-4569-8df8-b68d74fe8e9e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C071	car	available	f	f	88a25f7c-3cba-488a-a7c3-abf065c68f2c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C072	car	available	f	f	a12ebc75-b814-46b6-9108-56f2339e1a0d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C073	car	available	f	f	ab2a3e64-4508-44ab-80b0-68d60405b737	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C074	car	available	f	f	022892bb-c6eb-4668-aafe-869b51a4ba15	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C075	car	available	f	f	4468068d-3bc8-45ee-a27d-ee8b45d26f47	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C076	car	available	f	f	a6401dcd-b2ae-43f6-aa18-49858cb7a3a8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C077	car	available	f	f	f5857dd4-06b2-4d0b-83ab-a34a1c66d39f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C078	car	available	f	f	988b8f3f-ad15-44bd-8a52-6e9a04f28ab6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C079	car	available	f	f	499067df-69f0-41fc-90cf-c35c04a6e4f7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C080	car	available	f	f	a9881f18-bd61-4989-b37b-2d871a2bd939	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C081	car	available	f	f	baff4781-0e33-46ed-9e16-bc70df6aa116	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C082	car	available	f	f	529fe71c-e6ac-4c48-939d-a39bdf61f656	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C083	car	available	f	f	c0da4cfc-b906-4ed9-837a-34296b5519a9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C084	car	available	f	f	90dd4ba7-64a6-496e-b276-ad5f9d54559a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C085	car	available	f	f	fc7e8a62-02f2-43f5-a8c4-42c8604ceea1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C086	car	available	f	f	8ba4d005-b501-4ac4-90cf-8603ad7aaed2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C087	car	available	f	f	87730d52-23b3-43fe-b1f9-0c5cdaabdb74	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C088	car	available	f	f	cfae87a8-b0b3-49d5-8cc0-e2053c29a746	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C089	car	available	f	f	39147f7b-70c6-49f7-9287-094e519c28cb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C090	car	available	f	f	bd417802-ce6b-4461-af85-4fb243d995d5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C091	car	available	f	f	27cf3f12-b3fc-4c2b-91c4-117b93936fb8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C092	car	available	f	f	44c5f688-8986-483f-86e3-b6833f2e5262	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C093	car	available	f	f	805374bc-d3ad-40e8-8002-5abd81112568	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C094	car	available	f	f	5046fdae-6d08-43d5-961d-79c2afa9e9c0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C095	car	available	f	f	b6d48e19-d745-4d56-9f4a-f4ee743889a0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C096	car	available	f	f	cf3131f2-3dbb-48a8-b8fb-71ef69c7356f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C097	car	available	f	f	77a9d66b-dbb4-433e-ba94-2602c2a8074f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C098	car	available	f	f	ed9e765e-04f2-4a64-89c5-759c183cdc15	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C099	car	available	f	f	24b7d3dd-70d2-4a79-84a7-52512cfd0c24	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	C100	car	available	f	f	46fb3cc3-be98-4e21-a0ea-29471560dc1e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B001	bike	available	f	f	f62c1354-282a-4db8-8dca-194963b0993f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B002	bike	available	f	f	3ab02b20-cd08-40ec-ac23-466f473efb0c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B003	bike	available	f	f	f45e4d15-6da6-4bbf-b5c5-99f6b296edb4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B004	bike	available	f	f	0ae3c751-0345-4464-80de-e7853bf27b8b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B005	bike	available	f	f	ef70115b-9ec4-459e-be8f-192a927f14e8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B006	bike	available	f	f	41a61ce1-60e5-480a-8d89-5f46d457bc24	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B007	bike	available	f	f	3fb7d775-c117-430d-972b-7e225522ea12	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B008	bike	available	f	f	bdcf2936-e63a-4fa5-b2ba-f2869b3096d4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B009	bike	available	f	f	d4d72511-5f16-4031-b3dc-993e09a35213	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B010	bike	available	f	f	ff834e06-0bff-4524-a4d8-90b09da200a9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B011	bike	available	f	f	13d7a9d3-cffc-49f2-8cd1-1eba60604e78	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B012	bike	available	f	f	6879eff1-baf6-44eb-bffd-bedd17c69489	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B013	bike	available	f	f	c7aa4f24-a75a-4439-a059-b963e8b2573b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B014	bike	available	f	f	1feb2818-434d-4779-82f0-d26c4d5b3e00	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B015	bike	available	f	f	9f6722f9-cd05-47b1-a4c2-845364e2055b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B016	bike	available	f	f	bb78d1c1-1fb8-46ac-a3ea-8688ad5d6cc1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B017	bike	available	f	f	5ad35515-4d22-4961-aaea-1662f4d25e28	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B018	bike	available	f	f	919ec74e-58a4-4a4d-bc7c-10b1f44a145d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B019	bike	available	f	f	a3d2d8ca-7f5c-4e51-a019-d86cd3c1448c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B020	bike	available	f	f	7bae0a6b-95b0-4b47-a181-33292c57db4b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B021	bike	available	f	f	b1190de8-f96b-418a-a9c8-9bff7b67500c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B022	bike	available	f	f	6c541f69-6475-4a27-a539-beeab829cccd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B023	bike	available	f	f	90a679a1-6052-4618-a5aa-6a1687c097c7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B024	bike	available	f	f	0423918d-bffa-4410-b2f2-8a09e73418ab	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B025	bike	available	f	f	4dbfe346-512a-4cf9-80eb-b348393e288a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B026	bike	available	f	f	dfc29f52-5597-4e41-8653-672bc229bad4	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B027	bike	available	f	f	0a2ab886-9431-4359-87b0-79718f4e7de6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B028	bike	available	f	f	49c41ebb-8403-41cc-8871-2efab74e14dc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B029	bike	available	f	f	8d15f2da-f36e-4a33-af5e-5502df3e860f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B030	bike	available	f	f	3b96822a-df36-40c3-a79d-2c63d051dd2d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B031	bike	available	f	f	8f36de78-234d-4551-9615-787a949c89dd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B032	bike	available	f	f	aa459b21-f0a4-4b92-8a1e-3d58c4a383ec	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B033	bike	available	f	f	f173bd7d-820a-4dc1-bd1e-8eca68393328	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B034	bike	available	f	f	8909cd1d-8245-43c1-83f3-3771c5a8bd3b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B035	bike	available	f	f	5d3a96d3-1516-4c71-aa45-aa0963e637cd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B036	bike	available	f	f	95cb6277-95f7-4827-8b01-4de09b2fe843	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B037	bike	available	f	f	9acfcd30-6014-4bb0-b782-8480821eb77c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B038	bike	available	f	f	e14ddb53-e8e2-40af-9600-428c90e39151	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B039	bike	available	f	f	7d188e05-ee39-47a8-a8e0-c8a3055a361d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B040	bike	available	f	f	f5585aa0-9a44-42ec-9bc5-824c2f15574a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B041	bike	available	f	f	2f07aac2-cde4-4e3f-86b1-2d960039ad55	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B042	bike	available	f	f	41907c08-c8fb-4ca1-914d-14b96b27c00d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B043	bike	available	f	f	fc1edde0-519d-4e7c-a820-63243ea28045	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B044	bike	available	f	f	15973595-a839-4de4-981d-f1e9f2b855e9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B045	bike	available	f	f	e30e456c-9a16-4e32-9188-ca0889cb8c58	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B046	bike	available	f	f	86b379c5-91fd-42a1-903b-8b2117aa38af	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B047	bike	available	f	f	aa13c49a-0e49-4938-b68b-ccef074f82ca	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B048	bike	available	f	f	d8c8036d-c1dd-4d47-8f8d-8ebaa6f25291	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B049	bike	available	f	f	f94d2a30-7493-4ad6-bf9f-1e42150eb3da	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B050	bike	available	f	f	27626ea0-da30-40de-a9d6-fd474443ac64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B051	bike	available	f	f	d8666cbb-4033-478b-aa31-9cfbc8964c7c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B052	bike	available	f	f	a72af864-3dd4-44a7-88f1-33dd5b024209	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B053	bike	available	f	f	5ff1c917-ce47-4561-9553-7ebb796fa87f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B054	bike	available	f	f	8affb41b-dd85-4950-8626-8270c1206211	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B055	bike	available	f	f	9eec90ea-e250-4881-9148-346257082f22	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B056	bike	available	f	f	82078207-9d0a-4699-abed-8c13b3e50e61	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B057	bike	available	f	f	627f30f6-60e0-42f9-b56c-48eb23fa626c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B058	bike	available	f	f	008128fe-46b0-4086-b56a-4d3a86c903a6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B059	bike	available	f	f	855a978d-fd5e-469e-9502-53ea304ca872	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B060	bike	available	f	f	b3246ea3-d402-400e-9d0d-133b3ac3d7ee	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B061	bike	available	f	f	67b33f70-9963-48fe-b8ff-7fbe0be92d81	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B062	bike	available	f	f	cad2f2cd-b57c-4b1b-aa30-b351a422b904	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B063	bike	available	f	f	90883483-af96-4859-80f7-f525e7f9f4c9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B064	bike	available	f	f	29a97726-4498-4bc0-9d59-a9e2d6c04852	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B065	bike	available	f	f	dd149cec-5a10-4314-bd9b-9ed5190c961b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B066	bike	available	f	f	390dc58e-3a77-436e-b25f-622478e0375d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B067	bike	available	f	f	af450751-99d1-4357-a11e-0bb99349ea31	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B068	bike	available	f	f	c5e71da4-e628-4692-96fc-03f03654b50c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B069	bike	available	f	f	16fbb580-3baf-47d6-9714-e5f0ac112986	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B070	bike	available	f	f	abf6ff10-6b32-49d0-9610-e47f0aae5593	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B071	bike	available	f	f	6c07d033-b956-4ca9-99ae-0066217dd6ff	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B072	bike	available	f	f	62ba56a2-c84a-4d41-9628-47fe7401106d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B073	bike	available	f	f	a2f29cda-5126-4fc6-80d2-654cebfaa48c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B074	bike	available	f	f	16ec5ac7-bfcc-4325-b9a0-4788a811aee8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B075	bike	available	f	f	9189a830-c076-4ee8-90ea-cc857b3bda83	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B076	bike	available	f	f	3402a54a-4003-4b24-b9e0-896b9d6c0294	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B077	bike	available	f	f	b9b78783-f41b-451f-a9c4-d7d552f7c69d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B078	bike	available	f	f	bcbd9eb1-4a3e-4f37-8012-b91f5873b33c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B079	bike	available	f	f	a77a9c88-c100-4d34-a7de-9efa4b3909e3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B080	bike	available	f	f	38caf2a0-f577-43ec-aad7-eb05fd5d1903	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B081	bike	available	f	f	9ba9aa46-e47a-45b4-a853-e97ebdcde6a3	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B082	bike	available	f	f	0f383d8c-1cc8-4c20-a2b3-8ff29c59a9f0	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B083	bike	available	f	f	b20c7aed-5ec2-44bc-8953-15398222d8e5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B084	bike	available	f	f	d2476b18-6dd8-4d9b-b83c-0ce52f17798e	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B085	bike	available	f	f	460a56cd-0d48-4a17-b8b0-f0e0c6bbaab9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B086	bike	available	f	f	862c2479-141a-4d88-8376-971f477126c2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B087	bike	available	f	f	9072c8e7-1f33-405e-937f-b5a9a8f52a68	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B088	bike	available	f	f	27dc7f6c-62e7-4298-95e5-056de7ee5102	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B089	bike	available	f	f	73ed1a23-e7f3-4096-a08e-d1ce8347a1cf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B090	bike	available	f	f	b35693a9-5c1a-41cd-813f-8ac7b8f59d64	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B091	bike	available	f	f	54b32bfa-a4d8-458a-a79b-ecc28ce17741	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B092	bike	available	f	f	0df27aeb-a179-4021-b5d2-a3ba6428e822	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B093	bike	available	f	f	03844b39-c1ca-4b34-a5eb-6d47c60a43cb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B094	bike	available	f	f	7a24c611-1de4-4b22-b2f2-150557682df6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B095	bike	available	f	f	dcd7b14a-5868-47e4-a873-0e3c50cdbbf6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B096	bike	available	f	f	cae25432-79b8-469d-8bbf-d2c5ece5e47c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B097	bike	available	f	f	aa709e6a-32f8-4c66-a381-a320a6b153d5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B098	bike	available	f	f	b30e3176-b892-4edd-9dd5-8f4f761d4f38	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B099	bike	available	f	f	55653b75-5c51-41d1-aa02-787b3c8bca73	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B100	bike	available	f	f	28c5b545-2b70-47ea-9bfd-c78facd09abb	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B101	bike	available	f	f	332ea91d-2326-4e6a-ba12-31cce0177899	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B102	bike	available	f	f	9f569596-0199-4859-b75d-607d1b6188b8	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B103	bike	available	f	f	0a2400e8-784b-4684-ab34-79520af619c6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B104	bike	available	f	f	8ad6a4a1-f743-4de4-840d-85fbd2e79539	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B105	bike	available	f	f	c871ae2a-ba49-4b78-9ae3-31cb9032a91d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B106	bike	available	f	f	ce287f30-0481-4dba-a865-ab10c754aec2	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B107	bike	available	f	f	3f897a02-88e1-47e9-bdcf-6ec9fbe78e51	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B108	bike	available	f	f	213de7f3-7069-4189-b22e-3e7c9b81de38	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B109	bike	available	f	f	ab92f606-4116-47b2-a791-49422b5b6b9a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B110	bike	available	f	f	f72f1354-e5f8-436e-b9fe-b3ff8599c4d5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B111	bike	available	f	f	1c5d3bcd-55e3-4dc5-bdea-0a4bc71bc09c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B112	bike	available	f	f	4116792b-8ea6-4d77-9b54-6a76ff975e92	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B113	bike	available	f	f	93ed2949-fe37-4f4c-91bd-451a35c30492	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B114	bike	available	f	f	3ffebaa6-be24-4f41-b426-23ac9fd48216	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B115	bike	available	f	f	e4f18976-1c09-4396-8ff7-b2b7d2f43dc9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B116	bike	available	f	f	04b105e0-5f1e-45a8-860a-585cf30a8991	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B117	bike	available	f	f	d132ce81-c5a5-4bd4-a2c0-56f66fa4588d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B118	bike	available	f	f	e8a844b3-5b6c-47bb-9e42-34d47d0f043b	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B119	bike	available	f	f	e1690eea-88b2-448d-b0d8-143311824c04	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B120	bike	available	f	f	05ebb7a6-dc30-4c39-af5a-2115ec753504	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B121	bike	available	f	f	b720893c-7e6d-4491-8098-07a5b11a84bd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B122	bike	available	f	f	0844dbfb-a75a-4eb1-8c04-9003132079c5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B123	bike	available	f	f	1ac8ca63-1452-4601-ba12-7b10d900cac7	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B124	bike	available	f	f	6fafe7ef-cef0-47bc-a2e5-01df2cecffcf	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B125	bike	available	f	f	6fed0031-e33d-4678-af1a-7005a4906652	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B126	bike	available	f	f	f05a37d3-7edf-4ee6-a7b7-04aad4fc5403	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B127	bike	available	f	f	10002997-b175-468a-a9aa-2f224dd5ef87	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B128	bike	available	f	f	60166060-b8ce-42a9-86dd-08922de7a112	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B129	bike	available	f	f	72ab0ab0-6450-4373-98f4-a4e81c6fc354	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B130	bike	available	f	f	e37de547-d0f9-49b0-a69e-433d10d353f1	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B131	bike	available	f	f	b8773a6f-1284-4ddb-9a0a-1869890f0922	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B132	bike	available	f	f	f2ca44f1-4bab-46ab-99d8-238c450fe02c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B133	bike	available	f	f	4dc93bfe-b4bb-4db0-be0d-92d64989f165	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B134	bike	available	f	f	46909de8-f07e-4c6e-8c7d-95ef004eefae	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B135	bike	available	f	f	16151167-946d-4573-ac98-9382987f84a9	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B136	bike	available	f	f	153574d4-11ca-4275-a445-90c1a055bfe5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B137	bike	available	f	f	e79b6b3e-75ea-43c3-b058-30976f34cc76	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B138	bike	available	f	f	0afa89fc-f736-4ae9-b668-0157765e2686	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B139	bike	available	f	f	51abfdb9-06c9-494b-a360-9e2aa67a6fde	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B140	bike	available	f	f	217c1da0-d589-44ca-9912-67fcc2880b30	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B141	bike	available	f	f	47e952f0-1e8c-4e0d-be0d-5d14b4fa1a0f	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B142	bike	available	f	f	c5894c03-2650-4ffb-a0b5-b20977bf7f67	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B143	bike	available	f	f	a2442ff6-d6ff-4ce7-aa3a-ad4ea893a57d	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B144	bike	available	f	f	46c7d0a6-0934-497f-bdcd-e14ea589b58a	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B145	bike	available	f	f	f637a4bf-0e08-40f1-9437-7273d09bbfcd	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B146	bike	available	f	f	cc1b415d-683c-4226-8d9b-02c208c295c5	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B147	bike	available	f	f	9f5f0663-b768-43fb-b5ad-3b9a75436fbc	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B148	bike	available	f	f	7e890083-8cc0-4999-bf71-a49da794b4f6	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B149	bike	available	f	f	e6ddf392-7574-47d3-b58b-e3594c5f3640	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
cd81f033-7248-45a3-ac82-1c310665f985	B150	bike	available	f	f	31dbc721-f1f7-4294-9968-48d8eb6d5e0c	2025-09-16 11:30:31.351032+00	2025-09-16 11:30:31.351032+00
6a650b0d-2311-4b30-a313-ae7529086f11	C001	car	reserved	f	t	1989dc43-8ffc-4070-b47b-f21bf278ee29	2025-09-16 11:30:31.351032+00	2025-09-16 14:54:28.431485+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C001	car	reserved	f	t	0fdaae15-b89d-484a-b260-18e9fc297720	2025-09-16 11:30:31.351032+00	2025-09-16 19:28:30.625061+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C001	car	reserved	f	t	9d032745-44c7-48e7-a480-c091cf9442a8	2025-09-16 11:30:31.351032+00	2025-09-16 19:34:52.827977+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C019	car	reserved	f	t	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-16 11:30:31.351032+00	2025-09-17 13:36:59.280465+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C001	car	available	f	f	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C002	car	available	f	f	ffdcb441-3523-4a9e-92e6-b1206106baca	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C003	car	available	f	f	b87651b0-1712-4b58-81fd-b91a03d67a0b	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C004	car	available	f	f	1bf0871d-94a8-495b-b9ab-147a238e0f65	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C005	car	available	f	f	60391a32-1776-47e5-a0f5-51da014399c5	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B001	bike	available	f	f	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B002	bike	available	f	f	00ab4909-a3d6-44cb-98eb-f2b3d3fbe079	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B003	bike	available	f	f	6f829e52-8b42-4b26-b481-b03a7f856034	2025-09-17 18:58:43.66199+00	2025-09-17 18:58:43.66199+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C006	car	available	f	f	d8cef6c8-ef14-49b1-b810-3120ddab1f5c	2025-09-17 18:59:13.479967+00	2025-09-17 18:59:13.479967+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C007	car	available	f	f	c33a5909-b50f-4545-a4d2-14d7f332bf84	2025-09-17 18:59:13.479967+00	2025-09-17 18:59:13.479967+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C008	car	available	f	f	57f2926e-149b-46c6-8640-bcf9f1dfdb7a	2025-09-17 18:59:13.479967+00	2025-09-17 18:59:13.479967+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B004	bike	available	f	f	4a0fbf70-a914-47f5-a0f7-dfb9a7404959	2025-09-17 18:59:13.479967+00	2025-09-17 18:59:13.479967+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B005	bike	available	f	f	2164e7b4-1238-44f3-836f-a4963b105434	2025-09-17 18:59:13.479967+00	2025-09-17 18:59:13.479967+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C003	car	available	f	f	a8efe1e0-feff-4eec-b134-0c99e1ddddf9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C004	car	available	f	f	2a2c55a8-8dd3-49a3-8f31-a786b349fec4	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C005	car	available	f	f	28b86843-5763-47fb-8419-e063db25ef94	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C006	car	available	f	f	5fd7a7d9-5b33-4074-8977-7c40d902ca63	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C007	car	available	f	f	64478fc1-b39c-48a4-9f33-de6f0a18bf48	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C008	car	available	f	f	600c83d1-f110-4564-a4a7-70db71c89c1f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C009	car	available	f	f	2ffe0b01-2136-46bb-b9a8-f9f7b27700d0	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C010	car	available	f	f	94079c4b-deda-422b-99bb-c27e0531bf47	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C011	car	available	f	f	6d234a08-c766-4ee6-96dc-962c2add8694	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C012	car	available	f	f	b351ab7e-a01f-4b34-8059-de597cbdc824	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C013	car	available	f	f	815d010b-6e94-47cf-a5e4-cd77e1cbc685	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C014	car	available	f	f	bbd2ca62-dcaa-49d1-83a8-bfabde43c96a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C015	car	available	f	f	34cb73dd-d9d8-4ccf-a571-78b5c37145cd	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C016	car	available	f	f	5c5261b8-24d5-448b-ba7f-e68d2234dc89	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C017	car	available	f	f	e95726a2-8ba2-4e6c-8978-0f69a0d469a2	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C018	car	available	f	f	5be66115-deba-4e1b-8f6a-343b500a149e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C019	car	available	f	f	ba30c7ee-c288-43f4-b133-72bf4f9e3ec9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C020	car	available	f	f	abe0aa68-cb31-4f9a-a715-49d0ebbd4974	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C021	car	available	f	f	8ea1cd48-030f-46f0-9f67-185aac143317	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C022	car	available	f	f	ba8ca468-d27e-40d0-982f-4aebfb813daa	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C023	car	available	f	f	7254ae83-f6f8-45c5-b14f-998ce9987284	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C024	car	available	f	f	d83d7073-ed09-4d2c-9ade-d60bb2473347	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C025	car	available	f	f	f48b7cae-ab65-4de5-98cd-96ea78602698	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C026	car	available	f	f	91a466de-01d4-48b8-8f28-5728e10783cb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C027	car	available	f	f	b1fe28bf-4321-4bdb-8cf8-760183197adf	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C028	car	available	f	f	ca8dafd4-615f-4bb3-ac6c-d75dad820b1b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C029	car	available	f	f	7a76d238-5348-4e22-a8c9-0c40630de920	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C030	car	available	f	f	8005d451-3b6c-4ef8-be5c-f1e5ee34f8b5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C031	car	available	f	f	1a497a2f-055c-46c4-aad3-163d2eeabee9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C032	car	available	f	f	9d271261-1d5f-4951-a696-a6a887d60efb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C033	car	available	f	f	2678ca34-6206-407d-8608-717da04dd7ae	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C034	car	available	f	f	83337397-b39c-4048-9147-2928dae5790f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C035	car	available	f	f	7d956690-1b64-4599-ac03-8629d064557c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C036	car	available	f	f	8168ea73-d11c-492a-b0d5-c6b13751ec63	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C037	car	available	f	f	e1dc1108-b1d4-46b9-a53a-a5933262aae5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C038	car	available	f	f	4950d00b-b7c6-4a78-98c1-dce622e8644a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C039	car	available	f	f	72788c95-3643-4544-954d-12bae02cc0c5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C040	car	available	f	f	f754c4fc-468d-43f3-9e91-fc6166eb5ad6	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C041	car	available	f	f	dea67899-9d5e-4199-9f2f-aaf8a4678777	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C042	car	available	f	f	6e6b3eed-fb91-455d-96d2-b83a3da3d5b8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C043	car	available	f	f	9ad22b91-03ac-421b-9377-c991fb7f7ef5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C044	car	available	f	f	618177f3-bc59-41cb-81d7-356958309bd4	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C045	car	available	f	f	f143435c-15a1-44a1-8eea-908879ae89cc	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C046	car	available	f	f	b95a599c-752b-4e0d-a9da-6ae00c8e2d1e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C047	car	available	f	f	988b2546-b03d-41f7-a370-1a5810161a14	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C048	car	available	f	f	b5584061-5249-41f9-aa7d-ecb5381d2398	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C049	car	available	f	f	41c889dd-c06f-4bbc-9102-eff0dfbeebd4	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C050	car	available	f	f	2ff7ead6-4d6b-4c0b-a834-90f927560a73	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C051	car	available	f	f	a477981d-759d-4794-8d3f-9b9891f8089b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C052	car	available	f	f	292a8e7e-28f2-4895-ab28-def4c148b29c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C053	car	available	f	f	4b252e07-b478-4d10-bdf8-d3aeb6ca2eaa	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C054	car	available	f	f	962614fb-bacc-4e30-9db7-58bf85d2f2fb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C055	car	available	f	f	2b59a51a-3b53-4ba6-a802-21afcf832075	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C056	car	available	f	f	f02f5094-3ddd-4a26-92e0-ad8c79a0148c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C057	car	available	f	f	c9affa0b-4e63-40bc-9e8d-5f107b66a7f9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C058	car	available	f	f	0d2ad5d0-c818-4bff-b282-aed1a8f96339	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C059	car	available	f	f	02624bbe-600e-4fdc-932f-1d19507f3dfc	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C060	car	available	f	f	677e530b-1455-435b-bc79-d60a13c45d4a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C061	car	available	f	f	b2041e41-e342-4a9d-9182-c145b392f495	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C062	car	available	f	f	2921d59f-60b3-44b1-aa67-34fef5266e5d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C063	car	available	f	f	2510adf6-989d-4e76-aae0-b7bbc5dd3757	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C064	car	available	f	f	a96db9f7-0443-4de2-a299-dbd27b6cb792	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C065	car	available	f	f	0b94d32a-9c0d-4f73-a9a2-95c397a2ccce	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C066	car	available	f	f	d1250b1a-f80f-4351-8a81-89dc45f5a6b6	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C067	car	available	f	f	98c44f57-ec8b-4b2c-8fcd-c275ae22af50	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C068	car	available	f	f	0341ee4b-9a34-42d6-989b-a499f26d6c3f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C069	car	available	f	f	68b1101d-bf95-4b6c-8cf1-ac7d1608d990	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C070	car	available	f	f	2eb71f02-4d2e-4bfc-bbfd-2444b8387539	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C071	car	available	f	f	db90e53f-17b7-4a8c-a4f9-65bcf2b9720d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C072	car	available	f	f	bd79139d-fe3c-4faf-8b83-5e32b0e66bd8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C002	car	available	f	f	f74d4035-4855-418e-8852-e990b7dd7e75	2025-09-17 19:09:38.320772+00	2025-09-21 21:56:16.906136+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C073	car	available	f	f	cd8e6533-5076-4071-ae6f-6310c3966010	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C074	car	available	f	f	f132787f-9a0b-4a9a-b67c-bdfd42fd0f87	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C075	car	available	f	f	f82fa3eb-afff-4365-98ff-0196107c705e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C076	car	available	f	f	1282348b-2efd-4fbd-b3ca-5507b3b81fab	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C077	car	available	f	f	11e2b263-0018-434d-b5d4-dcb6589ff9e9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C078	car	available	f	f	3ecc1424-f053-450c-a3a5-89b149c3ae13	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C079	car	available	f	f	aef6719e-a1a4-4728-b38e-25442a744c89	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C080	car	available	f	f	d358ca56-0f1f-452d-afee-f992c456cd30	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C081	car	available	f	f	65f69903-7aed-47d5-be06-3d6a36e578e8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C082	car	available	f	f	52559539-96cd-429b-9e17-1ce9991c253d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C083	car	available	f	f	bd79a0c8-5fb0-433c-839f-ca74220195a0	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C084	car	available	f	f	f534266e-e442-43a1-9aff-260b850e36ea	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C085	car	available	f	f	ed70476e-7736-4f9c-a77c-43575da2d708	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C086	car	available	f	f	bda73ea0-e73e-4384-9453-8da060431d48	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C087	car	available	f	f	6da4035d-477a-48c8-9e82-81ea2336e05b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C088	car	available	f	f	859308f3-e749-483d-8657-2240d8e3c8bb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C089	car	available	f	f	ba2f48ad-adcb-429e-bf86-3b04168194a4	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C090	car	available	f	f	cf58a01b-70b3-40e4-849e-da2bc97e5758	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C091	car	available	f	f	f16646cc-34cd-4707-a6b7-bdef89d4f29d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C092	car	available	f	f	4b0e76a7-1e10-4c3d-b2ab-fbc1d4096832	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C093	car	available	f	f	d30b6abc-f3d3-44c5-a3c2-17a6508752a7	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C094	car	available	f	f	5039b4a7-fd07-4f8f-acb0-ff0e3e7caaf8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C095	car	available	f	f	df3ef75d-9b64-4781-a13c-631c374dca6c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C096	car	available	f	f	4c16ffa4-4cb2-4fb2-9163-7d0532ab5edf	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C097	car	available	f	f	8c77f10c-cc04-4938-adfc-bf6410e468d9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C098	car	available	f	f	9941f71c-1a2c-45c0-8705-57e84be5d40e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C099	car	available	f	f	10182c31-1d94-4c61-b6a0-af1dce722767	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C100	car	available	f	f	e95c2375-0c27-4cdc-a8f8-76d67c9e84b8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B001	bike	available	f	f	730557cd-130e-4150-a297-f3df1f52c9d0	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B002	bike	available	f	f	381f2a21-fdc4-42af-8498-eb2e2ac93db1	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B003	bike	available	f	f	20c6276a-04c7-4846-ae50-1a72ee184123	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B004	bike	available	f	f	867d86b8-0760-490f-ad37-895669589440	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B005	bike	available	f	f	119d1d32-4b21-46f8-b87f-824a9381da1c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B006	bike	available	f	f	5a8ccd3e-5bf0-47ad-b475-24f9a9598f83	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B007	bike	available	f	f	2978b91a-ca0b-4419-8164-5d8795407754	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B008	bike	available	f	f	7dc93c84-a2c1-4402-9043-257a2e8e7594	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B009	bike	available	f	f	030ee6b3-7252-47f3-b9f2-f9c6916b0fce	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B010	bike	available	f	f	202bc06d-e878-45e4-84b9-b6691cb5609e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B011	bike	available	f	f	686b2fed-02a7-473d-bd8c-99d524450bc5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B012	bike	available	f	f	f4dc4667-d2d5-480b-af9e-9d6ee3cdef5a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B013	bike	available	f	f	dd210ec7-6bac-4043-8bea-f53d82317e23	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B014	bike	available	f	f	75af73ac-8fb0-4df5-a6b7-996f488386d2	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B015	bike	available	f	f	04fcb7c5-2aae-49db-ba29-be2c17cfd39a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B016	bike	available	f	f	c5b85428-1ae8-4763-b17d-19bc1c19fb88	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B017	bike	available	f	f	0d42de93-ffd5-4822-9c6c-f9681f855d02	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B018	bike	available	f	f	679a4a3b-6bf8-48d3-b5a3-af31c33d098f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B019	bike	available	f	f	1aef57a3-bef5-4fa6-87bc-95e45cd6da6f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B020	bike	available	f	f	ad7617d2-f80d-44e5-8dbf-a00e521924f7	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B021	bike	available	f	f	90d19b53-aec9-40dc-8638-8c88c2641be9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B022	bike	available	f	f	45561b68-8390-4c9e-8ad7-5a98713e8903	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B023	bike	available	f	f	eda4fa5c-01fb-442c-9bb7-4d587aa24a9d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B024	bike	available	f	f	f72748f3-dba1-413c-b9ca-4929ba7448d0	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B025	bike	available	f	f	908be474-9e4c-45fa-8a88-cc81ef902781	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B026	bike	available	f	f	11964fd8-5e59-41ac-9a15-1e310b577a90	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B027	bike	available	f	f	92cb5d37-bdd5-44d2-97e1-f8037d20cf70	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B028	bike	available	f	f	2a9d7de8-07c8-45e0-9fe7-afa63dbf2d9b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B029	bike	available	f	f	7d002d53-ba2f-48c2-8bb5-bb707cc78e03	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B030	bike	available	f	f	d852b850-f3f6-407e-b026-a281fec111a8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B031	bike	available	f	f	fb0ec21a-fb17-4edb-adfd-e0e9cbff5e42	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B032	bike	available	f	f	1e6f101d-78ca-4df7-b67a-be192bab1ec3	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B033	bike	available	f	f	ad0af862-5120-4e69-b099-c6fadf3323de	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B034	bike	available	f	f	b7e8c754-6b91-4085-b062-a27e02e0248f	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B035	bike	available	f	f	3b9ae221-44a0-40d0-8405-00098ebc190c	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B036	bike	available	f	f	c46ea406-e7cd-4b95-a239-7c2bb10d519d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B037	bike	available	f	f	84b08199-00e1-4072-ba3c-4a4b84409998	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B038	bike	available	f	f	be2887f0-e0dd-44b8-b560-b8761a9d064b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B039	bike	available	f	f	33346369-bd22-487a-b3f3-7ee2dd78ae05	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B040	bike	available	f	f	d9b9d12d-c656-45b8-a8d0-bb224bb7b70b	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B041	bike	available	f	f	31000038-8f28-41ef-899a-282d674b9e81	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B042	bike	available	f	f	28bc837b-a5b8-499a-83e8-38d4fb8750cf	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B043	bike	available	f	f	67843cb1-1d69-4e35-89c1-da1802af2fd0	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B044	bike	available	f	f	27367c4c-372f-4377-bc1e-9cf59f11f71d	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B045	bike	available	f	f	66a479b8-3cb8-42e8-ac46-8ab106317c61	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B046	bike	available	f	f	32f44887-83a4-45c1-a405-cf39f63700fb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B047	bike	available	f	f	5cd50896-c28c-4a8a-acc5-4a2601f28343	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B048	bike	available	f	f	75a05a93-6c26-482d-9ba2-a46138a44658	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B049	bike	available	f	f	2e79d278-407c-4254-a805-14f407080839	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B050	bike	available	f	f	7ad9b042-ec3f-4725-86c7-308346e81dea	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B051	bike	available	f	f	baa5f0ca-2cf6-46ee-9dda-a8f8197513de	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B052	bike	available	f	f	b2ab623e-c06d-45f2-adf5-e134fd195f9e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B053	bike	available	f	f	325389cd-25fe-4e94-87bd-67e56f57f9d1	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B054	bike	available	f	f	f441743e-ad2d-4a4b-baa7-efa2b0a1491a	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B055	bike	available	f	f	6df9e6e3-1835-45e6-84ab-b287ed33fcaf	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B056	bike	available	f	f	816b0e9f-d419-4c7a-905a-46bac85cbbe5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B057	bike	available	f	f	2d0af837-ca9b-4f1c-9e64-2a2e8fee75eb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B058	bike	available	f	f	95039134-73eb-43f9-acd4-bab7dc04016e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B059	bike	available	f	f	074da57d-924a-45a9-9ade-70ac3efb9679	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B060	bike	available	f	f	4e42303b-7cc6-408b-a31f-e52a71d09ee6	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B061	bike	available	f	f	fabd8111-be41-4d26-ba30-66d904bf8d44	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B062	bike	available	f	f	a8c162dc-8969-4fba-a504-c6cf7e0ab242	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B063	bike	available	f	f	e14c4b00-4bcd-4c1a-b056-c8c33e345738	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B064	bike	available	f	f	fbe88c0f-6201-4aa5-a047-582f6f89e490	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B065	bike	available	f	f	c1169a5f-23e6-42dc-bbe0-11af1032bfb6	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B066	bike	available	f	f	eea463cb-32e0-49be-b91e-55de19f9d376	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B067	bike	available	f	f	f85d01d9-4752-4be3-82c3-8844b71a5ffc	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B068	bike	available	f	f	bb2924a4-dcfb-4f40-b73e-1bba3b1577c6	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B069	bike	available	f	f	09e771b7-418b-4a15-86e1-a7438e488d3e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B070	bike	available	f	f	6a05e4e4-2244-4e5a-b164-a27b0d9d7e80	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B071	bike	available	f	f	9eabc264-f43c-4d04-8b7f-d9a4530d9cde	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B072	bike	available	f	f	a0112299-cbce-4831-89b2-9c13f81a88f2	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B073	bike	available	f	f	4eec6972-c511-4144-ae3d-0ee59998eb1e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B074	bike	available	f	f	8584a0ec-d04a-4c1c-b362-25406cda4b90	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B075	bike	available	f	f	c68902a1-a2c1-4a99-9a7d-679bdbaeb029	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B076	bike	available	f	f	f0fde55c-c1c3-4b12-8977-ff2211ca6469	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B077	bike	available	f	f	740b07fd-458d-4730-9caf-d45ea2830772	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B078	bike	available	f	f	6d937fec-a768-4d63-bfce-b472c94c9fd9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B079	bike	available	f	f	fd088500-d8b1-4b74-a058-ba673e592db9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B080	bike	available	f	f	f4de4bc0-13be-4812-a2d3-2d8990a2da15	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B081	bike	available	f	f	4bf6e1be-e097-4251-bfd8-9cb7397c61a8	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B082	bike	available	f	f	18bb599a-62b6-448e-964f-0cfddb429276	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B083	bike	available	f	f	e2679017-db70-44dd-b58f-9a7de3123751	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B084	bike	available	f	f	6d5b6b8a-1a1a-474c-ad6d-8f56e30d40d2	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B085	bike	available	f	f	477bf89d-ec1f-45af-8068-79c1233fb45e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B086	bike	available	f	f	144aaa66-fafc-4d2d-9368-a8e233b1f6f9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B087	bike	available	f	f	e6599a84-b29c-402d-b769-e4dfa66c98e5	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B088	bike	available	f	f	a9ea4c61-bde9-479a-827c-11508239f7d1	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B089	bike	available	f	f	c7aabe4f-9061-4baa-aa71-2b540db36897	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B090	bike	available	f	f	c27d42ae-8b09-4f93-96e6-4c883e162479	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B091	bike	available	f	f	4983cc3e-d71c-4e40-b44c-e07617546a29	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B092	bike	available	f	f	608dd2be-e5a7-414d-afa3-46d0e1296d97	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B093	bike	available	f	f	79aad002-a9d4-4afc-ab15-74556ed772de	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B094	bike	available	f	f	18eb8bd3-d739-4faa-bda7-8faedbf9a2dd	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B095	bike	available	f	f	d466827b-ce4a-466e-99cc-c21d97974e91	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B096	bike	available	f	f	452d35ca-01fd-4087-8c5c-fc81b33c6eeb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B097	bike	available	f	f	9a2dcfe2-a388-4cb0-86de-5e9fdb2f9a2e	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B098	bike	available	f	f	5fc21fdd-4a44-4e24-8fee-3dec8ab392eb	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B099	bike	available	f	f	324aea31-fde2-4762-8464-699916eb0911	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	B100	bike	available	f	f	a269ff9d-0049-4d10-8c65-3a5169af6fe9	2025-09-17 19:09:38.320772+00	2025-09-17 19:09:38.320772+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C301	car	available	f	f	aaeeb411-fa18-45a5-8524-bd577c937537	2025-09-17 23:36:26.155833+00	2025-09-17 23:36:26.155833+00
19ebc361-a7ac-42ab-9713-e4edd693335d	B051	bike	available	f	f	dbf91e53-4583-4718-ad0a-99e94a5ce777	2025-09-17 23:36:26.155833+00	2025-09-17 23:36:26.155833+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C009	car	available	f	f	57c4a893-a89b-4bb1-9475-f257f7d06eac	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	C010	car	available	f	f	72218591-2951-452c-96ed-f5e9741c7ca0	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B006	bike	available	f	f	9c04b14d-5dae-45cf-87e8-053a18c253f4	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B007	bike	available	f	f	a91c1be5-5a4a-4263-80d2-849b1fb834b6	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B008	bike	available	f	f	051a3c2c-9f9b-48e4-8016-c4a377c3bee0	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B009	bike	available	f	f	e469ab64-6ab8-4c1b-81e7-f2d3c5bd6799	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
59fa0039-1f4c-468a-b434-b67cdd7a20d4	B010	bike	available	f	f	8baec182-a13c-4a44-98b0-82a94d0b6d2d	2025-09-17 23:49:26.350287+00	2025-09-17 23:49:26.350287+00
6a650b0d-2311-4b30-a313-ae7529086f11	C014	car	available	f	f	ef99a082-1e86-4678-adfa-f2101c7aba40	2025-09-16 11:30:31.351032+00	2025-09-18 00:56:35.663911+00
19ebc361-a7ac-42ab-9713-e4edd693335d	C013	car	maintenance	f	f	770d358f-74be-456d-8e55-574ccfc63a6f	2025-09-16 11:30:31.351032+00	2025-09-18 00:58:11.640677+00
08c55203-86bf-465f-bc3f-b1cb2cab1088	C014	car	available	f	f	81c7545e-b387-4a2a-9927-b0c54e770955	2025-09-16 11:30:31.351032+00	2025-09-21 13:10:45.886618+00
a1c37af6-469f-4cbf-a5b9-ac3b45a3ec4f	C001	car	available	f	f	4c71e1ab-50f6-4b91-a886-b11982dd3474	2025-09-17 19:09:38.320772+00	2025-09-21 20:53:02.153063+00
cd81f033-7248-45a3-ac82-1c310665f985	C001	car	available	f	f	490cd266-cdf0-440a-abef-9a85292aabec	2025-09-16 11:30:31.351032+00	2025-09-21 20:53:49.925578+00
\.


--
-- Data for Name: payment_cards; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payment_cards (user_id, card_token, card_last_four, card_brand, card_type, expiry_month, expiry_year, cardholder_name, is_default, is_active, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: payment_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payment_transactions (payment_id, transaction_type, amount, status, gateway_response, gateway_transaction_id, reference_number, notes, processed_at, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (user_id, booking_id, amount, currency, payment_method, payment_gateway, status, transaction_id, gateway_transaction_id, gateway_reference, description, payment_metadata, processed_at, expires_at, failure_reason, refund_amount, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: pricing_rules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pricing_rules (lot_id, name, vehicle_type, rule_type, start_time, end_time, days_of_week, price_per_hour, multiplier, min_charge, max_charge, is_active, priority, valid_from, valid_until, id, created_at, updated_at) FROM stdin;
6a650b0d-2311-4b30-a313-ae7529086f11	Early Bird Discount	car	time_based	05:00:00	09:00:00	\N	10.00	0.80	\N	\N	t	normal	\N	\N	b6601924-694c-4fc6-bf29-55529c2455d6	2025-09-18 03:05:08.227795+00	2025-09-18 03:05:08.227795+00
6a650b0d-2311-4b30-a313-ae7529086f11	Weekend Night	car	day_based	\N	\N	saturday,sunday,friday	15.00	2.00	\N	\N	t	high	\N	\N	bbdc7c67-e9f6-4d57-8bb0-168718dcb9f7	2025-09-20 16:25:56.330119+00	2025-09-20 16:25:56.330119+00
6a650b0d-2311-4b30-a313-ae7529086f11	Weekend Premium	car	day_based	00:00:00	23:59:59	\N	10.00	1.20	\N	\N	f	normal	\N	\N	d15cf322-8c67-4695-9f0d-80b54d813e1e	2025-09-20 00:53:02.857259+00	2025-09-20 16:27:12.652096+00
6a650b0d-2311-4b30-a313-ae7529086f11	Peak Hour - Car	car	time_based	16:00:00	22:00:00	\N	10.00	1.30	10.00	\N	f	normal	\N	\N	2548a868-1439-4fdd-b034-9958ef635c17	2025-09-18 03:03:30.438469+00	2025-09-20 16:27:18.590427+00
6a650b0d-2311-4b30-a313-ae7529086f11	Peak Hour - Bike	bike	time_based	16:00:00	22:00:00	\N	5.00	1.50	\N	\N	f	high	\N	\N	d66a93c5-8e89-4b29-9ad7-32e9516a4eb7	2025-09-20 00:52:03.448384+00	2025-09-20 16:27:20.558209+00
\.


--
-- Data for Name: slot_allocations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.slot_allocations (booking_id, slot_id, allocation_type, allocated_space, id, created_at, updated_at) FROM stdin;
a839b2d6-d6fa-45b7-9edc-3ab8b5bc875f	1989dc43-8ffc-4070-b47b-f21bf278ee29	full	\N	5feae9b0-150d-46f4-abf0-11e515ea4178	2025-09-16 14:54:28.431485+00	2025-09-16 14:54:28.431485+00
87d4875f-dbab-43e5-a16d-c0c10baf8ac1	a32420d4-302b-431e-816e-88d78c13d29e	full	\N	ec049a60-b741-4a60-bb8c-7d6f10c3b857	2025-09-16 14:58:30.011899+00	2025-09-16 14:58:30.011899+00
42829b96-413d-49d9-bd6c-198098e6dfe7	09158ccd-1a5c-41a8-ac31-634d72c61886	full	\N	11d77544-c531-4dba-b45e-9acf64ac6b24	2025-09-16 15:02:08.144537+00	2025-09-16 15:02:08.144537+00
c504d5c8-298d-4856-a074-647e67fd5e99	9a80739f-4ec6-4d7d-ae23-f076feef17c9	partial	left_half	3809f27b-73c5-445e-8544-263e8bde931c	2025-09-16 15:08:45.6394+00	2025-09-16 15:08:45.6394+00
fcad5e2a-0e80-4359-ae78-46ccb30fb71f	9a80739f-4ec6-4d7d-ae23-f076feef17c9	full	\N	cfca43ff-d9e5-4102-a6b3-f98ce8d4b554	2025-09-16 16:38:05.124329+00	2025-09-16 16:38:05.124329+00
48b17e84-f608-401c-b601-46958bc70ca2	02178346-d1f9-4a2c-887b-4df05877d496	full	\N	f59e40aa-2c7f-4b4a-a5cb-bd1a2b0379cd	2025-09-16 16:40:00.061736+00	2025-09-16 16:40:00.061736+00
73e8c064-afa4-495f-82c8-5f245b7d043f	0fdaae15-b89d-484a-b260-18e9fc297720	full	\N	9c979a97-ce90-4247-a032-e6f60f47cb8c	2025-09-16 19:28:30.625061+00	2025-09-16 19:28:30.625061+00
172e35be-142a-46bb-84d9-72d54fa56f5b	9d032745-44c7-48e7-a480-c091cf9442a8	full	\N	d2dd17fc-b789-4728-a57b-5ec3efb378db	2025-09-16 19:34:52.827977+00	2025-09-16 19:34:52.827977+00
21710c2f-4780-403b-8a5c-a96afd92e591	de12fc56-c844-46c8-b7d0-29f6348b571a	partial	left_half	596b24fd-f13f-442e-90f4-04385512121c	2025-09-16 20:24:54.539135+00	2025-09-16 20:24:54.539135+00
0f2e4a1e-bbbf-404a-9d78-8782e200eac6	de12fc56-c844-46c8-b7d0-29f6348b571a	partial	right_half	9c6e3a37-5785-431e-aec5-e82c8063be69	2025-09-16 20:52:11.254814+00	2025-09-16 20:52:11.254814+00
ce3dc8c3-c718-4128-9252-2ec51e3398c1	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	full	\N	a7f3bca1-61f7-4be0-a029-673fe177c653	2025-09-16 21:06:33.055373+00	2025-09-16 21:06:33.055373+00
1cf197b6-da80-4be1-8567-2769c137e268	c4921654-ab3a-4908-8381-a29d6717a7cc	full	\N	95339203-98fd-4ea2-8fb0-a260de5bc039	2025-09-16 22:22:51.253553+00	2025-09-16 22:22:51.253553+00
e24a2ac1-4611-4d49-874a-ffb07b44ac2b	94ee0b96-9b5e-4af2-9934-f3ec41197785	full	\N	0955e8e2-e96d-45c0-b7af-ea67ed67fce2	2025-09-16 22:28:10.150979+00	2025-09-16 22:28:10.150979+00
3db90cc3-30d5-4628-a878-7b4a98ff68e1	7c4fc29f-a954-48f3-ba9a-db5def5cbc4c	full	\N	036fb32b-cce0-4887-a790-637f3d6ddc67	2025-09-16 22:31:09.854993+00	2025-09-16 22:31:09.854993+00
d3e2fb72-ab92-4cf3-ae30-31f947336417	de12fc56-c844-46c8-b7d0-29f6348b571a	full	\N	3045736c-bcbc-49a9-8239-85c78effea3e	2025-09-16 22:32:59.939053+00	2025-09-16 22:32:59.939053+00
b28d23a7-de4e-4685-ac2d-e7ad73a8b437	730a7a60-2535-46cc-a1db-64b92c2eaa43	full	\N	d6002bd9-833f-44f2-bdfb-6eebd00515f9	2025-09-16 22:38:07.961939+00	2025-09-16 22:38:07.961939+00
4714c0d0-0abe-42a7-913f-3bfef3ea3ec7	ba02b652-3159-4a2e-8537-e36c944f0f73	partial	left_half	8649f428-046e-4d9c-920c-8af997f9ab8d	2025-09-16 22:45:20.684275+00	2025-09-16 22:45:20.684275+00
6848ead3-e4f6-4a33-8c59-55ba508edb1d	ba02b652-3159-4a2e-8537-e36c944f0f73	full	\N	1647ae77-f665-4b55-8cca-8300e1bb754b	2025-09-17 00:06:26.332401+00	2025-09-17 00:06:26.332401+00
249c70e5-7eda-4d43-8a73-c6a79f53abbe	69afc6ef-5b07-4e2c-b064-1006811e2441	full	\N	9c0783e4-f3ad-4025-8616-f5b5ebe690f4	2025-09-17 00:22:21.19023+00	2025-09-17 00:22:21.19023+00
22d183e7-85d5-47a2-856b-4dd007c84a04	75e25a61-d293-4ad8-8eb0-72204534e1ad	partial	left_half	caf8c32c-f20a-476c-bd64-10928212f412	2025-09-17 00:28:04.434181+00	2025-09-17 00:28:04.434181+00
71dda9fe-7b0f-43b5-91ed-98a09051a026	f4e42346-3eb2-4f1b-b1c5-9b1d6088d22a	full	\N	295d8b5e-3dfe-4171-ab2a-c93aa67cac8b	2025-09-17 01:13:18.070687+00	2025-09-17 01:13:18.070687+00
5e8dd6e3-6d5c-4b55-8dec-c545efbe4e85	75e25a61-d293-4ad8-8eb0-72204534e1ad	partial	left_half	340bcedd-600c-4b16-add7-7a986f131d6c	2025-09-17 01:15:06.100434+00	2025-09-17 01:15:06.100434+00
7881a3ea-6118-4a1f-8e57-6838a8feee64	75e25a61-d293-4ad8-8eb0-72204534e1ad	full	\N	89d644a9-7ac1-4408-8001-5031a9ebc225	2025-09-17 01:41:50.540039+00	2025-09-17 01:41:50.540039+00
3ebc6d9b-574b-40b2-873f-6f8a7cf37762	07a6cca8-4378-4ae2-a2b1-787095a096e2	full	\N	0a836752-9f00-433a-8bf7-72449fa06c56	2025-09-17 01:44:00.132873+00	2025-09-17 01:44:00.132873+00
134716c4-d7fa-49ee-b0bf-982d8c3a7a47	f92ac396-10cb-4769-9473-dc4219133917	full	\N	05b1ad45-2e6a-4394-8b77-45b2724f7da5	2025-09-17 01:48:59.475221+00	2025-09-17 01:48:59.475221+00
f86fb9a3-dd3b-4355-abb1-363dd80ef9ac	77469074-1c57-421c-b741-be1874ffc20e	full	\N	f65d9a7e-f482-4f54-bf33-eb04b3dd8799	2025-09-17 01:51:30.058877+00	2025-09-17 01:51:30.058877+00
fdd78df5-9efb-4e37-873a-fc8fe4702dfb	770d358f-74be-456d-8e55-574ccfc63a6f	full	\N	da77fa59-ade3-4eb4-bab8-699c97eed425	2025-09-17 01:55:08.714807+00	2025-09-17 01:55:08.714807+00
bb0e0eef-36de-4594-87e0-8a7659396819	96767f13-51c2-4214-9bc5-89167226250f	full	\N	19920077-0916-4e1f-81b1-abf22a5ed3ee	2025-09-17 02:10:07.703016+00	2025-09-17 02:10:07.703016+00
ae3f7f91-3b71-469e-aaf5-cc53435ec928	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	full	\N	0e59de21-4958-4ad9-a695-7811fdea3073	2025-09-17 10:15:35.544604+00	2025-09-17 10:15:35.544604+00
e7db2281-a5b1-4d61-818c-973b7735e6f2	a9ab64f3-810c-478d-8153-71f52ae0e9d7	full	\N	87a70a98-f63f-403c-af9f-84c8835d3906	2025-09-17 10:16:34.385982+00	2025-09-17 10:16:34.385982+00
a4e6e27a-a08b-4362-af7f-27acaefdf610	ad18a635-72f1-47a2-8454-2561a5e175ad	full	\N	ec199222-dd81-4656-896e-cd2b363b9f08	2025-09-17 10:22:10.789201+00	2025-09-17 10:22:10.789201+00
bd205075-5b6d-4665-831f-8d08fc189c57	0f0cf325-b73a-46f7-8f93-c37af1b11f82	full	\N	c564646e-b3cc-4d94-a372-bf72ce8f124a	2025-09-17 11:09:48.19824+00	2025-09-17 11:09:48.19824+00
947ad9a8-89f9-432d-a66c-743b2c5d5d4c	7c4fc29f-a954-48f3-ba9a-db5def5cbc4c	full	\N	ed0de4e7-d43f-47be-bc7e-0f15eb906c25	2025-09-17 11:14:19.000154+00	2025-09-17 11:14:19.000154+00
a3e32ea8-7e2d-4050-9600-1836c3a3318c	69afc6ef-5b07-4e2c-b064-1006811e2441	full	\N	d72daf83-4655-4f22-ae7c-3836e25dd519	2025-09-17 11:25:53.346293+00	2025-09-17 11:25:53.346293+00
df52b94d-ac73-46c2-9085-62d76e3626f8	77469074-1c57-421c-b741-be1874ffc20e	full	\N	7ae178b8-10c0-44f8-b007-f893ff1b5580	2025-09-17 11:26:11.551292+00	2025-09-17 11:26:11.551292+00
52e2e1b6-45cb-4e62-83f1-8a5414380cbd	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	partial	left_half	df6cd09c-5361-437e-9015-a5bbcaf71a26	2025-09-17 11:36:12.607081+00	2025-09-17 11:36:12.607081+00
63c17482-cc20-4880-ba6b-75ef5169a15d	b1ad04e1-530d-4bf1-b4a5-94201487bd22	partial	left_half	47c0a3c8-4570-478f-ae96-f1106701d1ab	2025-09-17 11:45:04.668625+00	2025-09-17 11:45:04.668625+00
bbca2869-f474-47c5-a87d-92cb9e3a2df5	11eee77b-1e5b-46d6-a0af-a22a1e3670a8	partial	left_half	921998f7-0031-4fb2-aca8-dfe9d2233a9d	2025-09-17 11:45:47.904761+00	2025-09-17 11:45:47.904761+00
4698a26b-468c-4c19-9032-05a91f2ac7f2	11eee77b-1e5b-46d6-a0af-a22a1e3670a8	partial	left_half	93a30df1-49a0-407a-b7ba-245c1e6f91d6	2025-09-17 11:47:00.231605+00	2025-09-17 11:47:00.231605+00
8c3f2189-a74b-4ed4-90db-76bbca711a0f	2adf58fb-1940-411c-bedf-09b807e576da	full	\N	ebb4d9db-340b-47bd-accc-441485b9f764	2025-09-17 11:48:47.339712+00	2025-09-17 11:48:47.339712+00
1ac5e546-963c-44e1-ad5e-c1d415703eba	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	partial	left_half	10490e62-c8e7-4496-bab8-9dc0fc32a26e	2025-09-17 11:53:39.08082+00	2025-09-17 11:53:39.08082+00
3fe23984-f479-4859-8b7d-b5417755d344	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	partial	left_half	25cb310d-5646-4031-8c10-9b88a9bc0757	2025-09-17 11:55:04.554015+00	2025-09-17 11:55:04.554015+00
5a6fc274-9767-4ad5-a18e-ff5f480a82f6	021f915f-61fa-4e83-a1a4-f428a5c7cef1	partial	left_half	dc161684-b92d-4837-8070-30512c7ec4e6	2025-09-17 11:59:01.961458+00	2025-09-17 11:59:01.961458+00
816246ba-c8a9-496c-8c94-b31041a34632	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	partial	left_half	39f2c595-b258-4c08-97e9-e9e17b5682ae	2025-09-17 12:05:00.750013+00	2025-09-17 12:05:00.750013+00
2fd16f72-3a05-4ddc-be07-01e3ddb2df73	021f915f-61fa-4e83-a1a4-f428a5c7cef1	partial	left_half	0a13a0d9-a35b-408b-976c-6943d9d70c8d	2025-09-17 12:08:25.709483+00	2025-09-17 12:08:25.709483+00
41a21c20-12af-4d18-a46e-60b3a6a30b13	41037616-20b5-4a9b-a0f2-288504f84d2b	partial	left_half	8cd02343-e120-431e-b5b7-1b7dfc182fd3	2025-09-17 12:09:11.028905+00	2025-09-17 12:09:11.028905+00
3eaf41df-3b13-4372-9f8c-e138507a9ae3	a9ab64f3-810c-478d-8153-71f52ae0e9d7	partial	left_half	f08f90e4-7248-4c34-802a-d02e7147a51b	2025-09-17 12:12:08.851801+00	2025-09-17 12:12:08.851801+00
f5d27fa3-f908-4332-b5ad-5b43a4f57966	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	full	\N	0c9dfd3c-0339-4c67-8848-80dfe8d694cc	2025-09-17 13:15:39.574356+00	2025-09-17 13:15:39.574356+00
355d542e-0436-4ba1-a5c3-4e217f701caa	a9ab64f3-810c-478d-8153-71f52ae0e9d7	full	\N	8f4c7012-b4ae-473b-b555-a41e8ea2362c	2025-09-17 13:32:59.376569+00	2025-09-17 13:32:59.376569+00
2a82571b-c651-49b9-9610-2c4d5f8e4bd1	ad18a635-72f1-47a2-8454-2561a5e175ad	full	\N	88824888-924f-4d1f-8eb7-d0a38224aded	2025-09-17 13:34:10.216217+00	2025-09-17 13:34:10.216217+00
11a0365e-2a50-42d1-91ae-c43b2cc9bde8	eb84e3d3-e7b9-4449-817f-be669b58ce41	partial	left_half	0ce1d5e6-6300-4c47-a7f4-2a998ff877b0	2025-09-17 13:35:50.854856+00	2025-09-17 13:35:50.854856+00
14261ddc-a5ec-4445-8d4c-7f0f00d13787	eb84e3d3-e7b9-4449-817f-be669b58ce41	full	\N	6307f7df-60fa-45e4-8958-d2c32ec7b458	2025-09-17 13:36:59.280465+00	2025-09-17 13:36:59.280465+00
479061b4-9aea-4331-93e0-709aa16bcbc8	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	full	\N	9503c370-6123-439c-b738-5813fa374a38	2025-09-17 15:33:21.316803+00	2025-09-17 15:33:21.316803+00
401de1ab-9cd2-4a71-850e-8361b0d0162c	4cf4da74-02b5-450c-9098-942c007cfd02	full	\N	b51dcf5b-1086-41ed-844a-de2039945f8f	2025-09-17 15:54:53.97682+00	2025-09-17 15:54:53.97682+00
f630ea92-646c-49c5-97dd-1a893dc12c3b	b188d489-15e0-4c4f-83b0-4cc68bc920da	full	\N	5fde7334-bc81-4bd6-aba2-d731cb3006eb	2025-09-17 16:34:56.367642+00	2025-09-17 16:34:56.367642+00
a2a03b23-fbc0-470a-99c9-46ee5d4aa99d	29fe9803-57d5-40cd-8a51-859ca4cf47e5	full	\N	41b02d81-0c61-4221-9ebc-20290eeaec11	2025-09-17 16:45:01.82043+00	2025-09-17 16:45:01.82043+00
08984a73-af52-4a40-846a-f385bc66c9fc	021f915f-61fa-4e83-a1a4-f428a5c7cef1	full	\N	7f40cdc4-a67f-4109-b290-06a7168cb7c2	2025-09-17 17:48:37.828551+00	2025-09-17 17:48:37.828551+00
11be4ded-ea1a-422a-bfc9-d15c1af4d484	36a7cea3-2c6d-45c1-964d-9b6d40249d00	full	\N	03f97474-11d9-43cd-a451-dfb480012091	2025-09-17 17:53:48.054063+00	2025-09-17 17:53:48.054063+00
6b1106f0-490d-47d7-a41b-1803d7702e2b	51b89dcb-0dd1-4765-be11-850f9c647e67	full	\N	04e0799a-9d78-4eac-ba7c-3266acab3bb7	2025-09-18 07:40:31.326378+00	2025-09-18 07:40:31.326378+00
bed7a9a9-62cc-4048-815c-848261d9dc4f	f78203d8-1ebb-46c8-8a92-ae5055f99508	full	\N	b932f1db-1df3-4277-9baa-5d5fcd829a97	2025-09-18 10:36:15.91756+00	2025-09-18 10:36:15.91756+00
954e27f4-bef9-4b84-ae94-1d758c5dfe36	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	full	\N	51b4f619-66e9-4a3d-8d5a-d59c34d60b22	2025-09-20 03:09:02.770059+00	2025-09-20 03:09:02.770059+00
410b034d-2db1-4783-8607-803b7bd14ca9	fe509eba-32af-4941-92f8-6d65deb6fc3c	full	\N	f720120f-5ff2-4e49-b647-202008d2cb3a	2025-09-20 03:09:19.884399+00	2025-09-20 03:09:19.884399+00
c8fdf651-9d55-427f-8257-fa7fd47fbfbc	a704960a-8750-4a1d-be7f-1553ed110778	partial	left_half	5171ff75-1915-4ef3-9404-50638290eb39	2025-09-20 03:10:33.707769+00	2025-09-20 03:10:33.707769+00
291d42b5-bce4-4354-a6b7-396bef311c31	41a3e636-f6f4-45d2-9dd3-621b27985589	full	\N	15399e87-b9ed-4bf4-b57a-9da9a2faf70d	2025-09-20 03:16:55.371863+00	2025-09-20 03:16:55.371863+00
74afad85-cdda-45a0-885d-abbdf0e10560	47491068-c3e6-48ed-93ca-d0eee23ad389	full	\N	9d75b6c2-8000-404e-a1de-8cbdaa859860	2025-09-20 03:41:58.77605+00	2025-09-20 03:41:58.77605+00
abe40b95-8fc1-411c-9fdc-620b63774291	68d5ded7-79c8-45bc-97cf-05ed5b4f9191	full	\N	f67c7e89-b783-4e71-bffb-b2103500d96c	2025-09-20 16:20:26.639794+00	2025-09-20 16:20:26.639794+00
f734c673-f0ab-41b0-9176-7297a48d95c2	c309a8d6-77e5-469b-9595-c503d0e3b07e	full	\N	c5474729-1fae-4f4b-b5d7-945e38e514d3	2025-09-20 16:28:05.419037+00	2025-09-20 16:28:05.419037+00
9cbb2822-c23c-4278-b90f-356e050e202c	cedffa56-a5b9-421e-8cf3-4dab8aa44d36	partial	left_half	18e2525a-2450-464d-8631-b332975cf168	2025-09-21 08:42:22.296129+00	2025-09-21 08:42:22.296129+00
0e35beef-08d9-42ef-bbe1-c330ddac97b1	5d5747f7-b6e8-42c7-bb83-9159057b949b	full	\N	ab38ae1b-f0c6-448d-9068-7a195fa712a6	2025-09-21 09:18:31.824734+00	2025-09-21 09:18:31.824734+00
0323eab7-f0f0-462a-a969-837cb27a9e6f	05d8aa52-d6f0-4ac4-b595-b8e708b695d6	partial	left_half	71ce399a-1328-4dc0-9872-adb5822113fa	2025-09-21 09:56:55.550392+00	2025-09-21 09:56:55.550392+00
17ed2b0c-605b-4773-b10a-408fc45dad93	a276b69a-5df7-4dd8-84df-c7874543fa4e	full	\N	fa77421c-540f-4153-96dd-2283957444f0	2025-09-21 10:53:05.517814+00	2025-09-21 10:53:05.517814+00
a4599bf0-5b53-4c84-9bd0-4d39d38427c4	b9360900-0194-4a58-ac78-c4ed9e833461	full	\N	957268a5-e078-46c7-9a89-252f7c13ade7	2025-09-21 11:24:10.950637+00	2025-09-21 11:24:10.950637+00
ecf03eaf-14cf-41c0-a73d-ae31d4ff55c9	0dfeb933-6940-4c2b-9b81-f71a9035e8f8	full	\N	81136662-4a08-4d33-977c-1be9c02fb5b1	2025-09-21 11:50:18.431841+00	2025-09-21 11:50:18.431841+00
a1f56ea6-43f9-40c0-873e-a717405a6fae	ea268287-f5d1-4ffd-bd58-dc17b1ae2464	full	\N	974d2a19-2837-4918-b4a6-2fef4ac7c5f2	2025-09-21 12:40:17.249452+00	2025-09-21 12:40:17.249452+00
bf5076dc-644f-47cb-af1c-7afe53e3c49c	3391a24e-ccb4-43d0-b859-6627cd0efc00	full	\N	9af5fe90-3310-4404-bde8-586cfde0427a	2025-09-21 13:01:51.051903+00	2025-09-21 13:01:51.051903+00
e43c7b82-8e1a-43ed-a4f2-39c181fcc21d	81c7545e-b387-4a2a-9927-b0c54e770955	full	\N	20b4150e-acd9-46f2-8d7b-f218ad9531d8	2025-09-21 13:10:37.628636+00	2025-09-21 13:10:37.628636+00
8b00cc2c-46c0-4e47-83bb-d7c480a42ab5	6d780bf6-e999-40f1-88b6-473a4ecdda18	full	\N	20bcb21f-d92f-46e9-adc1-3a87ad6a5971	2025-09-21 16:36:17.789604+00	2025-09-21 16:36:17.789604+00
121fb8fa-0704-4303-8e77-a432bbfe48fd	707a46b3-2c9d-4be0-8c4e-0b7671ac6931	full	\N	60187a0d-3c8a-4388-8a66-7af571c9f988	2025-09-21 17:23:01.835113+00	2025-09-21 17:23:01.835113+00
a2e9ca25-ca47-4748-a18c-8b133a4eb776	ffaad7bd-a5e3-448a-9828-b7643f94fefe	full	\N	f17e9c4a-3b0f-4ff9-a4e7-6835d31b4a09	2025-09-21 18:56:41.823072+00	2025-09-21 18:56:41.823072+00
5b8d3929-0cc4-41a3-bae1-30644ebafb06	bc2929e5-9ba7-4964-893b-c4efa02c368b	full	\N	770ccc94-373f-4c61-885c-d5ca6f137122	2025-09-21 19:48:47.736551+00	2025-09-21 19:48:47.736551+00
8c84b7c2-2fea-4830-84bd-92bcd3a70c25	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	full	\N	a29f231f-ca29-4683-908d-c3dd5d6968de	2025-09-21 20:10:46.089844+00	2025-09-21 20:10:46.089844+00
7465b795-68cd-4365-8dba-ec5132736c96	a4f1bcea-2fbe-4271-b576-b4cbe0d44dd3	partial	left_half	dfa35543-8c72-4b54-a4d2-7778a1b812ee	2025-09-21 20:21:59.85407+00	2025-09-21 20:21:59.85407+00
f11a4792-cab3-46db-886b-479d8e5bebe7	4c71e1ab-50f6-4b91-a886-b11982dd3474	full	\N	9bfaa04b-e2cd-4fd8-bd6e-fab9fb6dcba3	2025-09-21 20:52:54.61045+00	2025-09-21 20:52:54.61045+00
d78b84d2-16a5-48d8-85df-8d05b74c6728	490cd266-cdf0-440a-abef-9a85292aabec	full	\N	95203126-cc21-40a3-ab07-ad6562f00a95	2025-09-21 20:53:43.139548+00	2025-09-21 20:53:43.139548+00
b092e09a-ad61-4b91-b9a7-9d400e720862	f74d4035-4855-418e-8852-e990b7dd7e75	full	\N	bf565465-0730-4c75-9da8-af1ca7785443	2025-09-21 21:56:07.829568+00	2025-09-21 21:56:07.829568+00
03efa86b-e588-4e83-9156-5a90cbdfb507	13025bce-1592-4b97-96a6-726003a8b211	full	\N	36f59b6f-d70a-4592-878c-769eed32e83b	2025-09-21 22:36:28.221515+00	2025-09-21 22:36:28.221515+00
decdceea-bd8f-45b9-ae10-e156244af0dc	0e5faa49-cd4c-4a39-bda6-ffe43ccb386c	full	\N	e0904f31-4589-4e81-8b50-b50c692c375a	2025-09-21 22:42:57.339987+00	2025-09-21 22:42:57.339987+00
c181c544-2c9f-4459-8fbf-01a9b5d3a932	599b9887-075f-4667-8992-0a3c07801975	full	\N	58ff4fad-9d1f-4dfb-ab32-85d01aca03c3	2025-09-21 23:00:50.433907+00	2025-09-21 23:00:50.433907+00
dbf8d886-108e-4516-a387-02387a6ae2d0	c4d71026-9b0c-4e45-a465-0350378d7036	full	\N	5ce07a68-2c7a-438b-872b-725a0bb19df9	2025-09-21 23:12:57.335645+00	2025-09-21 23:12:57.335645+00
03ae1893-f495-481c-86e0-63bb89559d5c	17715b50-c74a-4fae-a9fc-d59a5d008729	full	\N	05b03e6f-343f-4ae7-8c5f-0d5a2c33ed2e	2025-09-21 23:16:12.895404+00	2025-09-21 23:16:12.895404+00
7c55d769-1886-4a9a-aea5-e25b4686bd23	931c3658-819b-4843-95ba-85e7b7ec5360	full	\N	0e1ecedc-9cc8-424d-a037-8158ef873d31	2025-09-21 23:24:26.367927+00	2025-09-21 23:24:26.367927+00
0027fc1b-8c8e-4cf9-b7c7-bbc453d5b60e	9e4f166f-8894-426d-97b6-8d0a51e3bbc6	full	\N	87277d4d-ce3b-4791-ae67-474fef497723	2025-09-21 23:26:35.494586+00	2025-09-21 23:26:35.494586+00
\.


--
-- Data for Name: slot_time_chunks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.slot_time_chunks (id, slot_id, start_time, end_time, status, booking_id, reserved_by, reserved_at, created_at, updated_at) FROM stdin;
e6ba5c13-ddec-4c44-add7-fc6686b77313	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
d866f8a0-32f7-48dc-8b48-57100b5401b3	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 13:30:00+00	2025-09-17 14:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
3dcc15ce-4fb2-46a1-9fe1-cd5f85dbd476	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
335d885b-ffff-464f-a8d8-a53e28519836	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
e9e25d1b-1065-461c-990a-3e140e4daa47	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
d637bbec-139d-4dbb-9b7a-75ace9965888	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
b1698511-dcc8-4c8f-bd5b-45706371b5fe	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 14:30:00+00	2025-09-17 15:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
1923e7c0-f062-409a-af78-a4a164892dc4	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 15:00:00+00	2025-09-17 15:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
fca22f6a-0041-4daa-8ee8-82bcdb04c2bd	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
d9041782-0708-4c08-9415-5177f2762a05	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 15:30:00+00	2025-09-17 16:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
40f6309e-ac43-4767-ae2d-219fee64e9d1	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 16:00:00+00	2025-09-17 16:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
b6590179-a67c-4030-b9c0-16d98856d0e6	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
c2b80a4d-cdcd-4d87-9a57-b0be4a274cbb	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
5cf43fd0-aa7b-4bdd-980e-94d3a75d8112	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
6e6e8919-c85f-41c5-8efb-17f05d86af70	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
afb8856b-a5e6-4eb8-9275-a5c83bc8c5ef	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
27b856f7-8534-4343-85cf-7c393b3a1eb9	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
d53dd71a-b461-40ce-aace-7a1a18f908be	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:18.416145+00
174317f8-df58-4b67-87f8-c78084dac16f	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	temp_reserved	\N	c1842768-eeb5-468b-beb6-4e356bc66a62	2025-09-17 13:05:54.745921+00	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:54.73582+00
41b14fa1-4540-4e70-a717-d2db3630879a	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	temp_reserved	\N	c1842768-eeb5-468b-beb6-4e356bc66a62	2025-09-17 13:05:54.745921+00	2025-09-17 13:05:18.416145+00	2025-09-17 13:05:54.73582+00
9fd5c1f9-2e40-4f09-bfd8-d5cc36d0026c	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	temp_reserved	\N	c1842768-eeb5-468b-beb6-4e356bc66a62	2025-09-17 13:10:38.733728+00	2025-09-17 13:05:18.416145+00	2025-09-17 13:10:38.726107+00
1c1a2c57-86fb-4b09-98da-5ad01e07ff9c	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	temp_reserved	\N	c1842768-eeb5-468b-beb6-4e356bc66a62	2025-09-17 13:10:38.733728+00	2025-09-17 13:05:18.416145+00	2025-09-17 13:10:38.726107+00
632222f6-962a-42b6-a4b4-d23799e550ee	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
d222ba3b-9a57-4cf1-bb8b-e1958ccf634a	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
7c523df3-961e-4ac0-9a16-76f91f2b00d6	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 18:30:00+00	2025-09-18 19:00:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
3c3da3f2-3989-444e-9ab0-1262ddfaa051	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 19:00:00+00	2025-09-18 19:30:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
70aef2c1-4630-4a66-9538-7110d8a0153f	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 19:30:00+00	2025-09-18 20:00:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
7c85b1fd-8ce2-4e14-bad1-156cc2cf3ff4	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 20:00:00+00	2025-09-18 20:30:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
51b621bc-7f39-456a-8019-f2a6ada6c435	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 20:30:00+00	2025-09-18 21:00:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
41e1df0d-029f-446c-a9a2-f04f9b068082	d0cde2d4-ea1d-4a69-8c94-83d6a78730aa	2025-09-18 21:00:00+00	2025-09-18 21:30:00+00	available	\N	\N	\N	2025-09-17 13:27:41.192615+00	2025-09-17 13:27:41.192615+00
b05db3d0-ad1e-4369-a5af-98127b49b6a4	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
d3ef3fdf-f5ca-4ba8-a5ff-41ddeb321f54	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
b7ed8038-70d4-4078-9750-266d00c9f896	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
a27e5edc-398b-48d9-8ac0-0e90e49a2a87	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
6fadd2dd-78db-4b94-ae25-8e6919693d5d	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
c3eea23c-bbff-47fc-ab2b-fc834b610169	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
7fd5d207-bcc1-4d76-a7c2-32ea1bbd1a5f	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
8117de8e-ff27-414c-966c-190285f4b6e1	a9ab64f3-810c-478d-8153-71f52ae0e9d7	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 13:32:34.548145+00	2025-09-17 13:32:34.548145+00
4589919f-736e-49b4-b7ea-7c27c3156e9a	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
4242fbdb-3aa3-42ef-9fba-72fe83622fb7	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
b101cbaa-531a-4f02-802d-b2efcc07eb7e	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
1aec257b-990e-4fca-9e52-8c8f0975f384	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
faae922b-eec6-42c3-a1e3-befdcee08ccf	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
d3565f60-e63b-44e0-9143-556e3cfd2082	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
4258856f-b42d-4c81-8136-69b7f1d3b28d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
be342253-201e-4279-86d6-6f914ce52f94	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
82ba7597-6dcb-42b5-bb6d-1324aed211e5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 18:30:00+00	2025-09-18 19:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
a5893755-79a9-4e13-b3ee-7da7732692c5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 19:00:00+00	2025-09-18 19:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
8e6b6bae-df21-4e61-a6e8-7a3404ba59ed	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 19:30:00+00	2025-09-18 20:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
b8b7bb31-54a3-4d65-9476-3927a210758d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 20:00:00+00	2025-09-18 20:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
c3a542bd-478a-48dc-a130-724688fe10f8	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 20:30:00+00	2025-09-18 21:00:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
a51478a2-9804-4422-9f5c-bca509c3dfdb	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 21:00:00+00	2025-09-18 21:30:00+00	available	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 13:31:00.423284+00
a9797c56-b65d-48df-91aa-b5215980ec1d	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 13:30:00+00	2025-09-17 14:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
dbea8004-2156-4e3d-8526-aa791e1c68d2	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
c6a53515-f53b-4f3e-9597-f28b915db024	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 14:30:00+00	2025-09-17 15:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
e770ff13-4716-4ab3-9808-eddb8e9995f2	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 15:00:00+00	2025-09-17 15:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
0c66c08e-6ebe-4d50-b83c-929c28c233a8	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 15:30:00+00	2025-09-17 16:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
13040ffe-1382-405b-819b-ed1cc112bb4b	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 16:00:00+00	2025-09-17 16:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
62650623-3617-4e9b-8d7a-00d3996bd6db	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
bc408ab4-7bb7-45e5-9327-be21115293f3	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
1e64323c-30bb-4e44-89e4-eeca31adc0be	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
3d2cd82a-ac26-43b8-98c6-5870b8c183dd	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
1c6c6c31-85b8-468f-9d5e-3957aaa98fd5	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
f8ef2a9e-9609-4907-9bfc-7d5d3a28d788	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
d7cb1c86-5d5d-42dc-8afc-3bba1ca613a9	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
3eeb2ac8-3604-4675-8f49-227891174dbb	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
14594196-e058-4ac1-b676-f1c0831c1f4c	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
042bc925-7f8a-4f3b-8bb8-8241b0956487	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	booked	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 16:55:31.191485+00
64285234-6d73-4e6f-833b-f445f3b1a0ac	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	booked	\N	\N	\N	2025-09-17 13:31:00.423284+00	2025-09-17 16:55:31.220622+00
de2df391-90f2-431a-b177-43a16848880a	ad18a635-72f1-47a2-8454-2561a5e175ad	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 13:33:34.378481+00	2025-09-17 13:33:34.378481+00
225ab79f-dffb-44c4-b343-fbe80f671014	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 13:30:00+00	2025-09-17 14:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
d1d9a4a6-e648-4df9-b59a-3cdd194da5e3	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
e42d50d0-cf99-4cc9-9c63-09b81568e8ce	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 14:30:00+00	2025-09-17 15:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
ccf5a6c6-15b9-4078-b321-736333819557	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 15:00:00+00	2025-09-17 15:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
9b141930-89fa-4944-9377-35ec8894e49f	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 15:30:00+00	2025-09-17 16:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
1d584107-e254-4d68-8788-24c4c117f683	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 16:00:00+00	2025-09-17 16:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
b7ba8e30-1e9f-44e6-9258-02ce0ecbcccd	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
0563c587-36aa-4295-9cbb-4dacefe79e6f	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
428c9eb4-6806-4664-821e-8b51c7ad79ef	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
fb28bb93-b0dd-45d5-80a2-e93b66d01efa	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
c21b6302-a7d0-4704-aaf0-a70b7a59dd4c	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
d087523a-d5ae-4814-b249-643d9e85969f	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
5f762d90-91cb-4699-80d0-e8a3d37d6a81	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
873067b2-f4d3-401d-a41d-f15bc090f646	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
aa92cbbe-9e8a-4f30-ad79-577f3749661a	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
16fa2abe-2992-4b7e-9fa4-f8fcd393d7ad	eb84e3d3-e7b9-4449-817f-be669b58ce41	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 13:34:24.684372+00	2025-09-17 13:34:24.684372+00
479dd9c5-466c-459c-ae27-8d1efc742962	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 13:30:00+00	2025-09-17 14:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
9cfb5f68-e26a-4295-912f-9f99859d224d	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
acb4b783-f38a-421a-91e3-dd46c81bbd92	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 14:30:00+00	2025-09-17 15:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
eb0b0e30-e04a-4fae-afa6-bc20936ec129	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 15:00:00+00	2025-09-17 15:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
d9157d05-2d20-46bc-be01-7c91249eb4da	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 15:30:00+00	2025-09-17 16:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
7c78dd55-5b84-4c1d-85af-be80888f77b5	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 16:00:00+00	2025-09-17 16:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
83749e6a-f4cb-4543-90ea-1a023d492a12	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
5159a2b6-2d88-42d8-8a62-01227fe3b706	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
45b35224-9309-48fb-aa1b-6115b86926d1	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
e9e60caa-c107-4f84-81f6-ca08acdc6348	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
dcfaa5b4-0cd9-401c-b083-b85dfc10c00d	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
6ff8a29a-cff5-48be-be1f-2790c1ce80fb	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
dea48c8e-748a-479a-bf7f-25abd0350e53	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
5ee7fc20-1453-48a3-a2d7-8c3ca4f15a77	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
3000cf4d-025f-49ef-8d20-24ca290c7280	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
c551e22c-bbc5-4a41-8b33-f98a5347ef22	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 13:39:56.803662+00	2025-09-17 13:39:56.803662+00
2f1f9c37-405d-40d6-bdf2-8833854eaee4	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 21:30:00+00	2025-09-17 22:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
cbe09275-86b7-491b-b069-2e3f3889b414	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 22:00:00+00	2025-09-17 22:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
f54421c9-7672-4e71-88a2-ad61afee8e52	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 22:30:00+00	2025-09-17 23:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
5f0e5158-42c5-472c-8022-763046c35cad	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 23:00:00+00	2025-09-17 23:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
78e282c2-99d0-4607-aad5-c8f522e5b4e9	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-17 23:30:00+00	2025-09-18 00:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
b24fb6d9-26f9-45f2-883d-cc862693ee18	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 00:00:00+00	2025-09-18 00:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
dbaaf1e4-43d1-4078-a39a-b49cbbd6988c	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 00:30:00+00	2025-09-18 01:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
b2d46b1e-3152-4ca9-866a-d6c7e1ff9ebe	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
4b5d32af-0e83-46d8-a25f-e7afb154f4a7	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
f907f4a7-c943-4715-83e8-59ab5b1f0a0d	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
0f8c9313-5a3f-499d-9fb1-be2c5e7e3960	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
8d569f3e-e1af-4526-93de-b4e268e0e63a	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
1edbce01-f10c-4d87-828f-b2ba383c9783	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
708137ad-4b02-45a2-910b-23cf8f55e404	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
407cdc95-4312-4c28-9aed-97e0eb6c6d0f	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
1b9a4f1a-87c0-49dd-880e-094c8b7dc075	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
e9a1a1d9-d5fd-45e7-b5d5-a23a9db0935d	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
56224479-47dc-40ce-b5d4-cc536e7c18bc	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
c66ca2d2-7d84-40ee-a20b-730826a17cf4	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
a8b83709-e6a6-41e4-949a-2b0dc56ef0a3	2a94d516-a5aa-4724-ae66-91c89ad8fcf7	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-17 13:40:28.073278+00	2025-09-17 13:40:28.073278+00
7bd2ea37-6a5d-45cf-a0e6-e6dd72b1cdd5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 13:30:00+00	2025-09-17 14:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
95cb3c69-3b6d-4f57-ae66-16b4216c7575	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 14:00:00+00	2025-09-17 14:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
88768446-d3c9-4602-8383-fe3e578a4e3f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 14:30:00+00	2025-09-17 15:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
e53a93d5-a7d0-41f8-a391-11b226f994da	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 15:00:00+00	2025-09-17 15:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
07e8717b-8b6e-48fd-9f3d-30a7cdcf5b17	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 15:30:00+00	2025-09-17 16:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
d737bed7-ec2b-4804-b698-70d1790cec94	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 16:00:00+00	2025-09-17 16:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
364e7c7d-601d-4999-8e6e-19b23fb44db4	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
5080924f-23d6-4864-857a-368d8dfde7a9	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
115190ea-927e-4ec7-b39a-c50a6edb831c	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
b80ea21f-04b7-4ad4-8210-2e7de408968d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
0a2e2dc9-4ffb-4a46-9b74-ee1fc81ef1f2	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
e710741b-7b3f-4dc1-83f6-436c913661cb	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
e95365c4-2a74-4829-a9f3-63b818c478f6	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
86aefc54-a105-4634-904b-dddf94e57320	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
250c127d-f50b-43a1-9247-a8c89d22b73f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
9304140f-9eae-4c37-af9d-04e509df55a2	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
af4c5dfb-9461-4c38-846d-d2d4ac3f0b05	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 21:30:00+00	2025-09-17 22:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
21508634-3100-4e61-a397-1cdb2d5407a6	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 22:00:00+00	2025-09-17 22:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
3e2940fc-5e12-41a9-999b-c7d20eb0434a	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 22:30:00+00	2025-09-17 23:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
db0270dd-b85a-4d4f-95c5-4c7f1f531d94	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 23:00:00+00	2025-09-17 23:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
186d494b-96ab-42f3-b8e8-96a27aab31eb	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-17 23:30:00+00	2025-09-18 00:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
a1a8bf9c-e606-4f4e-97e9-c24b14da74d5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 00:00:00+00	2025-09-18 00:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
8d929ea2-0e4c-48ec-983e-27e75ccc97be	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 00:30:00+00	2025-09-18 01:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
45a5db06-092d-41a8-b8e5-c2c8df3a1ded	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
a5f4f651-2409-4493-bb62-ee5f07e5a242	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
85e6b5ef-95b4-471d-8c49-df1bc100150f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
decde9cd-9495-4f9b-9ec1-c46a3febc822	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
410468fe-752b-4881-bf4c-4c718d97d3cf	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
042f7f85-35f5-4b8a-b7d6-25eb9c8f18e4	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
4add28d2-9ad7-4594-b84c-f8e65700ee2e	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
f6bdb2f8-411d-4927-b4ad-52bb91d7c062	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
fa7db7da-56bc-4571-b4a7-e4b4be8b2e85	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
2fb8b28e-8b55-4094-9443-e1a7a13d2be1	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
12b858f8-2bf1-4af2-8597-9623405a0bef	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
dd83c1a2-008a-4b98-879f-25d4979e0de6	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
bd872423-21f5-484a-ab36-caf6ebe1aeed	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
6b2a4076-7b55-4cd9-a5ed-36e555e173ed	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
8f86542c-05bd-4a2a-892a-814ca7eb38b3	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
dbea1800-8a02-4c90-a946-565ce956f652	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
32bc9a27-1fc3-493c-97f8-802f074d1c71	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
25063040-9225-4f1d-a9ee-c1d6df42aecb	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
deb73dcd-5865-46ee-80c1-a939f425ce0a	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
d44ac057-e75a-4d89-9e11-191440882f4c	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
55c44114-3526-4fce-af50-6ae39a551cef	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
645d0de9-9b97-468f-9afe-6615833500ec	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
335b57bc-238a-492a-9d4f-8b6aa0e1668e	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-17 13:42:44.150647+00	2025-09-17 13:42:44.150647+00
f833f43c-3f95-49d3-ad20-a819ec0759e4	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 16:30:00+00	2025-09-17 17:00:00+00	available	\N	\N	\N	2025-09-17 16:41:53.831948+00	2025-09-17 16:41:53.831948+00
5db18682-d585-4bc4-b5c1-9c13611f8b8f	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 17:00:00+00	2025-09-17 17:30:00+00	available	\N	\N	\N	2025-09-17 16:41:53.831948+00	2025-09-17 16:41:53.831948+00
ddeef599-e1a6-4365-8ead-40febece80df	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 17:30:00+00	2025-09-17 18:00:00+00	available	\N	\N	\N	2025-09-17 16:41:53.831948+00	2025-09-17 16:41:53.831948+00
3219d9ca-863f-4c3c-8152-acf2c9aaae55	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 18:00:00+00	2025-09-17 18:30:00+00	available	\N	\N	\N	2025-09-17 16:41:53.831948+00	2025-09-17 16:41:53.831948+00
e2723a02-32da-422e-a1c9-c17773ecb34c	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
cb5055a1-f702-4c1d-81e4-a26454583a72	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
3531edfc-ef11-4262-b787-b5d951037f26	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 21:30:00+00	2025-09-18 22:00:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
e0a61227-9c14-4c8d-a95f-6e36ab873a51	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 22:00:00+00	2025-09-18 22:30:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
7465d9bb-5885-46d7-98c4-ee7104779595	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 22:30:00+00	2025-09-18 23:00:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
27869812-4d7c-4b39-9ee7-f9c2b92411ef	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 23:00:00+00	2025-09-18 23:30:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
8d5bc2d8-5b28-436f-a47f-3649bf9e42d5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-18 23:30:00+00	2025-09-19 00:00:00+00	available	\N	\N	\N	2025-09-17 18:11:22.127517+00	2025-09-17 18:11:22.127517+00
0ea3bbff-1818-498f-9701-0565203b9f4f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 00:00:00+00	2025-09-19 00:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
7ff80d50-3aa1-4c5e-bbab-8ec2570bc33d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 00:30:00+00	2025-09-19 01:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
0cc2249c-0541-4593-a11e-44e34e1483f0	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 01:00:00+00	2025-09-19 01:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
69358fd0-0404-4c37-ac8f-56daa7bce8a2	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 01:30:00+00	2025-09-19 02:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
4edb9efa-8059-471e-bd31-66b112c3bfc4	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 02:00:00+00	2025-09-19 02:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
836bcca4-b7b3-427c-9a28-2a9a65b065f7	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 02:30:00+00	2025-09-19 03:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
437617f8-0e78-4e09-8f7c-b249dc0d5bb5	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 03:00:00+00	2025-09-19 03:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
3702113d-df4f-45cb-9086-26341184ad7f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 03:30:00+00	2025-09-19 04:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
0d39d84c-3e81-4598-9320-ea4f313a90a8	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 04:00:00+00	2025-09-19 04:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
9dc12955-6ea3-432b-b516-9fcd95b8d58a	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 04:30:00+00	2025-09-19 05:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
628b8046-2047-4f03-9f09-3865011e305e	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 05:00:00+00	2025-09-19 05:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
ec632bbf-cb23-4f07-b24c-88c7a8d6aadc	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 05:30:00+00	2025-09-19 06:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
6733bca9-7f52-4a42-9fa7-2f7db4fe7287	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 06:00:00+00	2025-09-19 06:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
e1bdcece-d4ee-44c2-88f8-c647271e95b4	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 06:30:00+00	2025-09-19 07:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
ca6f4922-4fd5-49e4-94fe-ef21b76ebd42	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 07:00:00+00	2025-09-19 07:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
e9443b49-4771-4f4c-aa81-e7f329108ff0	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 07:30:00+00	2025-09-19 08:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
e05ca89f-c320-4337-bf06-98de45d064c3	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 08:00:00+00	2025-09-19 08:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
44a475c6-8f71-4624-bb73-2beaef065f7f	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 08:30:00+00	2025-09-19 09:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
8fdb391e-5692-4585-8216-73b559746b0d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 09:00:00+00	2025-09-19 09:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
cfb6dabd-6482-498a-ab5b-ef82535e6d81	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 09:30:00+00	2025-09-19 10:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
526f20ee-2a25-40fa-9941-16db9a1d1308	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 10:00:00+00	2025-09-19 10:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
c4f5eb4c-b53c-48fb-9086-97f2e31a5b4d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 10:30:00+00	2025-09-19 11:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
9ea7148e-96da-4966-9279-1fc624569876	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 11:00:00+00	2025-09-19 11:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
e8047cff-8023-46f9-b147-c61ba13252d6	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 11:30:00+00	2025-09-19 12:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
33662ff1-b933-48e1-b703-47f3209584e1	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 12:00:00+00	2025-09-19 12:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
9c65facd-cd1c-49ad-a26a-f10f79a9b535	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 12:30:00+00	2025-09-19 13:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
d77b7e9f-68f9-405a-aa98-ec2d83a3a6cf	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 13:00:00+00	2025-09-19 13:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
a590e4c4-0380-4106-812c-e4a9d132978d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 13:30:00+00	2025-09-19 14:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
c7fdc9ec-8c35-46ad-92cc-88d1aed0fc6d	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 14:00:00+00	2025-09-19 14:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
8cbc5093-da91-48a8-bfdc-fe9c04e8ae51	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 14:30:00+00	2025-09-19 15:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
414e03a5-e082-472f-bdaa-318f899451b1	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 15:00:00+00	2025-09-19 15:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
2488927d-8633-4899-bfb0-718f38287196	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 15:30:00+00	2025-09-19 16:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
f89e5fcf-46bf-426f-905a-11680eb09456	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 16:00:00+00	2025-09-19 16:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
7adeddc2-532f-4418-b87a-2f3e893c00ce	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 16:30:00+00	2025-09-19 17:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
b35fa87b-22cd-4111-9a22-afa0a75ff700	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 17:00:00+00	2025-09-19 17:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
a8badfcc-d11d-4f3c-a895-1ed318f24452	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 17:30:00+00	2025-09-19 18:00:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
f2434c75-5226-4456-a8a2-e95d8dd8955e	021f915f-61fa-4e83-a1a4-f428a5c7cef1	2025-09-19 18:00:00+00	2025-09-19 18:30:00+00	available	\N	\N	\N	2025-09-17 18:14:12.249663+00	2025-09-17 18:14:12.249663+00
34561501-f5f7-4421-83f6-cd1295a5fe8c	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 21:30:00+00	2025-09-17 22:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
94ce3087-c3b7-4041-bd7f-14c89f8f23ae	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 22:00:00+00	2025-09-17 22:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
ca81c015-5a65-4220-9fa3-0945d7a0af12	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 22:30:00+00	2025-09-17 23:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
e2df4c32-28b8-4270-bbc5-17bfb8a924ec	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 23:00:00+00	2025-09-17 23:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
f2df8ef8-ad80-4b42-af21-6bc5a54ade76	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-17 23:30:00+00	2025-09-18 00:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
9cf3ce75-bd5f-48f0-8bed-895157eb1bca	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 00:00:00+00	2025-09-18 00:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
6ab48dda-fa73-412e-a259-9993a5e93c37	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 00:30:00+00	2025-09-18 01:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
6f9f0005-888d-44f8-b786-e6a106ced8f2	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
0fe06c43-12b5-415c-a105-a1ed1ea33b87	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
fd7014a0-23c6-4882-91a5-abdb30fc0782	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
534fad5e-dc98-4f53-adeb-d43d076719eb	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
595c2d04-a48e-477c-94d2-8771b633581b	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
5443cc58-7be0-469e-a11f-7b9aa887440c	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
7dfa8d86-2ba4-4720-874d-f6d4c7cd7c87	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
ef0fc8c0-15b7-4334-afca-2aa6acadf450	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
fc8b55ba-4e43-4d35-874e-6bcefccd2443	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
daa2d2ab-317b-42e2-af1e-26a187afdf60	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
7f1cf13b-8f11-47a2-adba-e8bfb3f13896	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
d2ce7855-d045-43c4-bbb3-535fde521f6c	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
44597875-8094-48a6-877c-384bf8df596d	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
638c7f58-212b-48ee-949a-87bf7ac94341	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
abaa7a2e-fd28-4c5a-913c-9d669c390bb6	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
6311a68b-061d-4659-b522-2d943905afca	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
85c3bf7e-5c2d-42f2-919f-01cd6ae9db9b	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
e9ed5f81-e01f-4a3c-814f-9640e93d34c0	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
c2d597e3-f9b4-4371-bcff-64dd898e3769	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
b51871c0-a604-432d-9f7c-39b0a301e190	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
25525b40-a9b5-4d75-8ec5-c296fa23e9a3	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
76118a78-bfd7-4f87-96ec-9748a8606249	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
d6357fd5-a4ea-4c7b-bc57-0249394fa59a	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
b509ff9b-eb2f-4c03-930b-6c2ae99258a2	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
be29307e-42cf-43a6-bc6a-f02082fdc027	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
bac4bf99-9b43-4327-b692-bc2557fee00c	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
6eb18ec1-9af1-41c1-a571-1fbec2a112d6	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
df4078af-0cf5-48b0-8b0a-f702ef014150	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
3b038521-1ed3-46f2-abc5-f03eadd7b810	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
2e4b190e-1399-45fb-b16a-0b9423e09f43	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
87f21e54-93ad-4571-900d-668ca2c7407f	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
458250ae-640f-48d6-a081-e794d6f54d75	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
bfa3935d-bb54-424e-9350-dc19d8ba00e7	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
f2383567-77f8-460f-aa5b-50d9387f3993	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
1b9d2ae7-c66a-4263-91fd-d80eaa9d63b8	37ed1a20-ac2f-47bb-a11a-8f4139e2f846	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-17 18:30:06.543352+00	2025-09-17 18:30:06.543352+00
2168b446-5892-4d4f-87df-78c099a88423	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 18:30:00+00	2025-09-17 19:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
fc0b5d39-c6ba-4631-80e0-ef97d737c8e7	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
cbfe5741-f909-4096-8616-01f5e245d7ea	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
58c8c92d-a77e-4a31-b79f-12457b984954	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
26d0b7be-6f80-46c0-b4f4-40968725b362	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
53ce642a-e698-47c7-b10b-453768e0eb7a	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
f5303e67-9eed-4cf1-b6e1-625621d27d82	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 21:30:00+00	2025-09-17 22:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
01986075-249e-44fa-ba20-18bd2c1340e9	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 22:00:00+00	2025-09-17 22:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
188eb016-fda7-4987-b8c4-b07b21831379	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 22:30:00+00	2025-09-17 23:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
0cf60985-2b11-40df-9b46-21538bd9cce5	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 23:00:00+00	2025-09-17 23:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
8e7c17b0-469e-46a0-942e-c99060dfe74e	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-17 23:30:00+00	2025-09-18 00:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
9f274c84-6234-426f-8d03-68c32dabbcec	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 00:00:00+00	2025-09-18 00:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
491532b6-6ce8-4f7f-9de9-7dd1e37296ad	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 00:30:00+00	2025-09-18 01:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
4acc3a27-d432-4026-8a2e-dd85b0e4c756	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
6e5a8946-d811-49f3-8f93-406cf37625d5	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
a607366b-5bd0-427b-9c12-b8e93054f8ae	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
e5fac02a-d37b-4414-8e26-06f52bad884e	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
2ac0c46a-61b6-40a0-9ddb-073f875ef710	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
389b9a48-3fa0-4a2a-aec0-1b68bc0dc10c	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
c69bd2c9-f0ed-4f08-bc47-9006668bd1b2	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
8e7bfe37-0522-4e54-9393-e00cbeedb260	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
a2729dfe-ce29-42fa-8df8-8d7435c05746	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
42bba40a-b2f0-4e67-a2f7-335ecc5cc2dd	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
1da58548-0957-42a5-b631-6c3097264cb0	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
1d403e6f-26ac-4945-b9e5-c49feafcbe7c	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
830091c4-b956-4882-98a3-166362117708	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
8abf3b87-0409-48a9-a776-c77885d7fbea	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
a6ab6a28-c125-42a8-8f98-67b79b8c1237	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
3ca547b6-f51d-476b-bbc3-b5ed5a7cf136	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
2e003644-9c53-42d1-8fed-a84e63c49215	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
91306cea-1e40-434a-8ef9-98a743e9bf27	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
671ad8df-18e1-4a8f-8c1b-173030465fcc	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
2c14c758-ae8e-4fd2-8a0a-489db750ca7a	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
79df32ac-8af3-4440-8c53-fa95c532213d	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
6eabc78a-6fe4-4e05-8b61-0008107ebca9	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
18eaaf18-f264-4790-b1b4-b13de4c75311	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
b4dbd864-ed84-4534-bdea-e4e65f669c4f	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
4e36a4d1-1a57-46df-8fe7-35f5bfdf72b0	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
d47bff12-4ad0-4c93-9ed9-d6d3cf662d34	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
5cbb64d9-9bc0-499a-bd2d-76bc2090b85f	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
47da45b7-03d5-4449-a92d-15dac6931314	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
823bc67d-6b34-467b-ab88-56115ee8eeda	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
29a7eb0c-7c1a-4d3a-a316-558435802bea	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
24c29734-0c4d-4a29-ae34-89eed31d6e7e	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
908d747b-de25-4d9d-9483-4ab927d9b82f	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
2d7c23d0-ba54-4030-9899-dd4e69f8a9da	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
1d597b0c-2f56-4e62-92ed-a6236b0bfb02	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
d5a038dc-0f35-4092-a794-aa2e3f5af667	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
afcdbe82-c49f-4a4c-b49d-74644e7abf2d	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 18:30:00+00	2025-09-18 19:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
1c604abe-6248-4c0c-92e8-d1a7d947621b	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 19:00:00+00	2025-09-18 19:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
919ed6e0-dc73-4890-ab4c-85d25fa809ab	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 19:30:00+00	2025-09-18 20:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
d5674c04-14bb-4726-89db-dc01f1b2bf10	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 20:00:00+00	2025-09-18 20:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
5aa563cb-269c-4007-85c0-a96709b84e6a	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 20:30:00+00	2025-09-18 21:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
38a05ee3-3a4e-4e58-a96e-ebbaa69b49db	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 21:00:00+00	2025-09-18 21:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
9714f754-9589-442d-b4d4-2d30df703c50	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 21:30:00+00	2025-09-18 22:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
88d6d3d4-b7c2-4be1-8ff9-279e1fa9d3d7	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 22:00:00+00	2025-09-18 22:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
560e5b63-5b54-4e69-a5c8-b6b7a8aabfd6	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 22:30:00+00	2025-09-18 23:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
d040bf9d-1a1e-4127-adeb-08f90f3dd1d9	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 23:00:00+00	2025-09-18 23:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
8f8d6580-cc37-4ac7-9e1f-8c8a0d3e5ede	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-18 23:30:00+00	2025-09-19 00:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
c709590e-976a-4855-b2ae-6d98bbe74939	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 00:00:00+00	2025-09-19 00:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
77655362-2d1e-4d7c-b454-37e0a32e9e20	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 00:30:00+00	2025-09-19 01:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
3630e2ee-a832-4e5e-a2ad-7e129c6f1bf1	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 01:00:00+00	2025-09-19 01:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
249b8936-15a2-4c1f-83b9-b05abede8204	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 01:30:00+00	2025-09-19 02:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
6f297a1f-180f-438e-a921-da7d8af52392	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 02:00:00+00	2025-09-19 02:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
acfb9fe0-efba-4381-924f-55d0e979cbe4	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 02:30:00+00	2025-09-19 03:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
826bf368-734f-459f-b7ff-0f6f121b7da6	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 03:00:00+00	2025-09-19 03:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
c684d065-d228-4787-9211-dda5ef5f0a84	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 03:30:00+00	2025-09-19 04:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
784a0eb0-485a-44b7-bcb1-8387e6aee37e	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 04:00:00+00	2025-09-19 04:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
e48695bd-358b-4422-b0d6-5204cb36b74f	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 04:30:00+00	2025-09-19 05:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
99ce15ef-615d-43f7-b4b0-443754b8a6c1	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 05:00:00+00	2025-09-19 05:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
4ee7ae9e-f88f-4f79-af13-b996663e2da9	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 05:30:00+00	2025-09-19 06:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
99308016-335f-4dfe-93d2-d4ac7098b4bb	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 06:00:00+00	2025-09-19 06:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
84ce67e8-75f6-4ad9-9b36-33b706568d57	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 06:30:00+00	2025-09-19 07:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
2f4c5346-3460-4147-9d4f-ee1958e28337	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 07:00:00+00	2025-09-19 07:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
18216705-3e09-412d-a32a-c51393ef6f32	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 07:30:00+00	2025-09-19 08:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
efcc7c23-6106-4ed6-b701-49cde0211859	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 08:00:00+00	2025-09-19 08:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
dd5fc54f-fdb2-4add-a7f5-04b01c06a461	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 08:30:00+00	2025-09-19 09:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
79ac1524-9812-4447-bf7e-3ff58f52207c	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 09:00:00+00	2025-09-19 09:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
f004f544-622e-41f1-9aef-145bdcc75bc1	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 09:30:00+00	2025-09-19 10:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
f2a50686-f610-4de3-a4b8-fa35c94e6467	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 10:00:00+00	2025-09-19 10:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
944b7911-38cb-4c46-bfb9-290e0b64ade4	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 10:30:00+00	2025-09-19 11:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
9ea841fc-f59d-4e0b-a610-168f1c8f251a	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 11:00:00+00	2025-09-19 11:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
60328593-28b6-4cba-9a34-c5e5c12106d5	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 11:30:00+00	2025-09-19 12:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
6dab007c-8195-485b-b45b-7a482479a86a	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 12:00:00+00	2025-09-19 12:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
d35ff1de-5413-4630-bed5-7225f37c8f75	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 12:30:00+00	2025-09-19 13:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
93eaa609-4ded-439f-a13a-7fb1c90e5bb2	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 13:00:00+00	2025-09-19 13:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
321a64c8-5a1d-4830-b2e4-f9e9e3c4a548	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 13:30:00+00	2025-09-19 14:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
68590acb-cd1e-45ea-a7cc-2b051dbb4d33	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 14:00:00+00	2025-09-19 14:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
715f1933-2618-4061-9428-8989fb424958	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 14:30:00+00	2025-09-19 15:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
72fc6278-c35c-485e-afa0-20074cf67ca9	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 15:00:00+00	2025-09-19 15:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
37ef7c73-9534-4f3b-a76d-79f59dce33fc	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 15:30:00+00	2025-09-19 16:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
a44124e6-85d1-4774-80c5-406e94c0aeef	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 16:00:00+00	2025-09-19 16:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
b6526d18-31d9-4b14-beb0-d4460c441870	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 16:30:00+00	2025-09-19 17:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
bbddbd86-8eec-4d59-8176-2d5fa87924dc	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 17:00:00+00	2025-09-19 17:30:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
06c121e4-fab3-4607-b748-023116015592	e3770710-18a2-42ca-9c4d-71a651a8c789	2025-09-19 17:30:00+00	2025-09-19 18:00:00+00	available	\N	\N	\N	2025-09-17 18:43:41.115877+00	2025-09-17 18:43:41.115877+00
b7526274-739c-4ba2-a434-157342f193a9	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 19:00:00+00	2025-09-17 19:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
eff691cf-9610-4b36-8eac-294f657be359	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 19:30:00+00	2025-09-17 20:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5c73bed6-30a0-4a1a-9934-53ecd34da4a0	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 20:00:00+00	2025-09-17 20:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
6b943060-dd97-4fa0-a4fa-ad4ecf40cabc	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 20:30:00+00	2025-09-17 21:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
701078d1-9092-4f62-adc5-ebc124ae60b4	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 21:00:00+00	2025-09-17 21:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a228eb5a-49f9-4bae-a3f1-a96fb36c4a17	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 21:30:00+00	2025-09-17 22:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
588991b2-10ea-4e49-8cc8-d91ac4041da1	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 22:00:00+00	2025-09-17 22:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
2ab78d66-6d81-418a-be4c-89a7f8f57e98	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 22:30:00+00	2025-09-17 23:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
1242ffa6-3e20-474a-bd22-c8f65e03c448	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 23:00:00+00	2025-09-17 23:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
f8d03fcb-1189-4233-8245-27ebbcf37b31	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-17 23:30:00+00	2025-09-18 00:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5c9ba7dd-1d4d-4f18-80b3-2a259ba68294	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 00:00:00+00	2025-09-18 00:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
7702c88c-b222-4dbe-9ede-6f7b2094feb7	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 00:30:00+00	2025-09-18 01:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
052c0e7f-d041-4b87-8932-304be8645211	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
43862b1e-8733-4772-a318-f3b272fba7e8	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
0fb95aa7-5010-49ee-8d05-279309fae524	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
173669fe-6be1-41a3-b2ad-fbd3999befcd	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
dcc224dd-486d-4700-b018-95280df5eccd	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
4902b11f-80fa-4890-84ac-c8f06dea5e03	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
b45f2829-6355-452f-84df-8c9f940dcc97	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5b4c92d2-ec8c-4d8d-b638-e6f79f939bc3	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
cff4570c-774f-422d-9e0b-804bbed6dbb9	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
f33f02ec-337a-49e8-88ac-1cd6e564910c	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
e7ddb17a-32cb-4840-baf0-e476483455a5	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ae157679-87f8-4688-80f1-04dadc80b2dd	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
f914ebae-08a5-4da4-b650-6d3b912546a2	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
3cf80f07-c7c2-4522-bd5b-d00264ee5120	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
05d4a349-49c7-4f30-9364-4fb5d7922410	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
926ad2f8-6a88-4c16-b5a5-60a0e6465493	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
875f1e26-bb2e-4fe4-bf30-e297b05d3562	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
2ac03342-efd9-4b75-ba88-1bc7692473c2	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
319ee713-b1b4-4af6-9ff6-5a17f35f7421	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
449bf434-dd63-4afc-833d-50b2d0692c17	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c87f76f3-80cf-4d2b-8d67-6cdde3cdb880	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5d56130b-db43-46ff-87a9-659b68a159fe	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
b59b3393-6d11-4465-8a61-d22cff297b58	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
8e51ebd5-380b-4d6b-bdd1-8f1d8543e0e4	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
05ee9c74-7183-4ef8-90a7-0c47b1ff1d24	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
d077ce66-8aa5-425a-890b-b5992dcdbe65	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
e55420f3-d8ef-462c-a394-ccdd8948cbf8	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
2aabf7fa-b675-4fb8-81bf-059f2d88e117	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
1b3f56eb-1298-4fe0-b7b9-64da0676da41	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
8d7f62d8-6ba9-4594-94ad-b9c72e3f07b9	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ab1d644c-f8f3-4c3a-be9b-a0b6ae9ae3a0	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
d76b19fa-7628-433d-a3a2-7d73277e5a00	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
73b4f89e-36d7-41ba-b831-99a87684c6f4	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a71d34a9-9e9a-43fc-b0f6-6fd92bfbdc2a	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ac687450-bec0-4465-b22f-7f0a2d9fdb47	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
7aacccb4-f19a-4670-a8ad-aa611459f41c	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 18:30:00+00	2025-09-18 19:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
de119413-e01f-4f65-a1fa-c2137271cd58	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 19:00:00+00	2025-09-18 19:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
7dfa5e74-d055-4ea6-b07c-4ba3b1605731	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 19:30:00+00	2025-09-18 20:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
710aebc5-9dde-4e67-884c-2810ff9910bb	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 20:00:00+00	2025-09-18 20:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
b9f0eaa3-59b2-48f7-ad86-b1cabcb21e2b	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 20:30:00+00	2025-09-18 21:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a0beb341-c7fc-47aa-83a0-d17ffe604fc7	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 21:00:00+00	2025-09-18 21:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
65d9c620-45c1-477e-b5ad-be137d19e6d3	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 21:30:00+00	2025-09-18 22:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c972c008-1d3f-4317-b5c5-a3953d57997b	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 22:00:00+00	2025-09-18 22:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ee6c83fb-6b39-4d6a-bf4f-dba5d6634d00	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 22:30:00+00	2025-09-18 23:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5dcd23bc-e78d-4c3e-a9c6-51aecb37b782	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 23:00:00+00	2025-09-18 23:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
1867e9bb-b675-496e-8e7d-3e4c947fe9e0	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-18 23:30:00+00	2025-09-19 00:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
3ff9a03f-1071-437e-b999-ad15126cebbb	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 00:00:00+00	2025-09-19 00:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
6265431f-fd92-49e1-b7ab-ae63e3df101d	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 00:30:00+00	2025-09-19 01:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
1a8d360a-4378-4116-b1de-1a3e4a1dc6ab	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 01:00:00+00	2025-09-19 01:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
23604ce7-2ec7-4dc3-b18e-6ee3bdea6aa2	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 01:30:00+00	2025-09-19 02:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
6f402056-5211-479d-8b54-9dd44f7d264c	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 02:00:00+00	2025-09-19 02:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c310931c-0e7c-40d4-a41f-f00fbb2cd63f	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 02:30:00+00	2025-09-19 03:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
0bb7e8ac-cde1-431a-8d5a-1e9b9b7716f2	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 03:00:00+00	2025-09-19 03:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
f0eaf91d-ff4b-4fb1-a99e-b05254ab5c70	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 03:30:00+00	2025-09-19 04:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a97a1ab6-d34b-4961-a74c-fd1b0006f4ac	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 04:00:00+00	2025-09-19 04:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a671b424-3375-4006-bb31-b831cbe37e3e	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 04:30:00+00	2025-09-19 05:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c09f089c-702c-4b1a-afaf-9894ab833dd0	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 05:00:00+00	2025-09-19 05:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5b2a286f-f321-4988-87b7-b5cb4c8fe1e2	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 05:30:00+00	2025-09-19 06:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5d0f40ca-2a56-4995-a783-227b9dc3ee11	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 06:00:00+00	2025-09-19 06:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
49675c52-9bb3-4a84-9fe5-7ecf9a8fa99c	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 06:30:00+00	2025-09-19 07:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
20350306-3d88-42e0-8919-18fb24be1142	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 07:00:00+00	2025-09-19 07:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
a95f6f0d-62e1-43a7-a8b9-54b4f08850f3	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 07:30:00+00	2025-09-19 08:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ad9642c1-07cf-4e7e-9e8e-23d1ffc9732a	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 08:00:00+00	2025-09-19 08:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
58253194-04ce-445d-a538-70b6a319fe08	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 08:30:00+00	2025-09-19 09:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
e1345607-8da6-4cd8-9739-0b3fa6531067	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 09:00:00+00	2025-09-19 09:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
0bf6fbca-3287-47e8-96e7-f123f390cc81	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 09:30:00+00	2025-09-19 10:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
44975d0f-f607-42bf-a92b-5fc4b1defa94	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 10:00:00+00	2025-09-19 10:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
41073870-09b8-44ec-bbdd-8c126907dac3	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 10:30:00+00	2025-09-19 11:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
43e60c4b-0669-4911-9fd5-70ebaed6e32c	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 11:00:00+00	2025-09-19 11:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
e6c9035b-9a15-43e5-8cc2-46e5415d7102	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 11:30:00+00	2025-09-19 12:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5ed6125e-4880-4e22-aa37-3517e18160b7	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 12:00:00+00	2025-09-19 12:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
688e77d1-e1d5-488f-b4f7-760c87615717	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 12:30:00+00	2025-09-19 13:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
ac39250e-5f27-4a0f-9c06-2f9f2b74dd9f	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 13:00:00+00	2025-09-19 13:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
eba5a597-9874-429a-beb2-3587c804c811	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 13:30:00+00	2025-09-19 14:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c402daa9-d928-4b7f-b4c7-5acbae87047e	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 14:00:00+00	2025-09-19 14:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
2e3c69c0-ecfa-48b2-a541-e218fb69ca3e	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 14:30:00+00	2025-09-19 15:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
c4f1bb03-bb17-46c1-a2fc-e47552826e78	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 15:00:00+00	2025-09-19 15:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
405e7506-4ac7-4c98-a0f6-bde04e4cd4e3	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 15:30:00+00	2025-09-19 16:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
37eda5b0-d909-43d7-ae19-4aec0af4eae9	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 16:00:00+00	2025-09-19 16:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
5d5911ea-05b7-4720-bd3b-4a4d7e8905ee	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 16:30:00+00	2025-09-19 17:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
3086886d-d5a4-41e8-a30a-bbb287802712	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 17:00:00+00	2025-09-19 17:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
9690d068-846d-470c-a482-c53cb5061a57	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 17:30:00+00	2025-09-19 18:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
07c8818b-dacf-4c2e-9b32-70901f146a16	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 18:00:00+00	2025-09-19 18:30:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
d1a1e8d6-010f-4f78-ae18-b88e75f1027b	d8fc3c4b-cd24-4dc8-bf96-c80ec66b70a6	2025-09-19 18:30:00+00	2025-09-19 19:00:00+00	available	\N	\N	\N	2025-09-17 19:07:05.886329+00	2025-09-17 19:07:05.886329+00
6313a59e-2052-4a0e-8459-cd669026fad6	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 01:00:00+00	2025-09-18 01:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
3b1368c7-f6f1-4e41-ba1d-8c8d7825e238	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 01:30:00+00	2025-09-18 02:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
777d1dcd-9c6b-4355-a085-e997f54ec2b5	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 02:00:00+00	2025-09-18 02:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
3a1c20a5-214f-4f8d-9ad1-44689dccf006	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 02:30:00+00	2025-09-18 03:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
a8342c17-df66-4a21-8838-4842d6bcf77b	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
44a07a7a-1e71-46ab-96c1-e5bdcf79132a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
da828b64-baa3-4044-9ae3-b6ee4a0b5950	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
b0d55ab0-70b9-4cd5-9af7-37364a197478	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
144fcf4b-9353-4518-98c6-3118d573ff3e	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
59f3c576-f474-4901-9257-50e7f372210c	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
137f99f9-16fc-4483-af4a-5ace97148ac5	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
08526f7e-9e13-4c6e-abc8-df1882da6d92	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
bdb69b40-1af9-4d9d-a7e3-981131cb661a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
dde8e38f-153a-4a88-8739-fd18668b1011	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
06e6c7a4-3c7f-4f24-a169-2202f052a643	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
6071e189-9ea1-4dfd-b903-ab7d04beffe1	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
28f544f1-dcbd-44c5-9c17-fb755e31cfd2	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
3bca50d9-0291-4649-a80f-92ba59c236f1	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
bb655315-8c49-4963-a9dc-026d0ca1d9f0	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
04ed7e9b-d8e5-479c-b51c-c836702c864d	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
8ec9d98a-9379-485d-bcca-69f7a82ef4dc	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
7e881787-d8f9-470d-aa03-d60f4f24ea67	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
e08f9a47-0a18-4b1b-89fe-92a62f884cbb	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
c0a0a5b5-f268-451f-b525-d255273f3c3a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
a8597b11-54d6-4de9-a43b-33b3381af83a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
3fcaf351-96ef-47b5-8927-e9655eed5710	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
bf1ff043-c56a-43ea-b3b8-9c43bf64aa4b	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
460fb24a-750c-4c89-a908-363000be1a73	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
05101e87-660b-4c82-b56c-1660867765fc	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
e8e3c9f2-580a-4546-aa5c-c0d69a77dd29	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
4ecc17f6-edfe-4054-9493-ce55cf303730	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
47d517f6-fac9-4121-8f33-8851d65b8638	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
b6f6343a-f6ad-4be2-934c-47716ad9b7e0	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
52954589-1fb5-4317-94d0-503de28509ac	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 01:24:22.403678+00
2990b6d3-dbdc-490a-b137-f12dd8a96a8e	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 03:00:00+00	2025-09-18 03:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
3908c15b-ce59-4cee-a6bc-35046c03a685	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 03:30:00+00	2025-09-18 04:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
1a6efec6-fc53-48db-8645-2b44c00d4bc1	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 04:00:00+00	2025-09-18 04:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
0264b4c3-b4ed-41ea-87b9-907248ed3191	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
e8b233d9-c0ff-47fa-b249-1aa8b519cc53	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
1cd9c2df-fcc9-4d5e-8117-b5034c0f3de4	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
5424859b-c39d-4809-8ed0-a1ede0e49113	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
7cf3e245-2dfe-4fbc-a585-e40882ce7e63	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
d8fd8153-ee99-4305-80ed-a8ad084971ad	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
a1457cd5-a9a9-44b2-ae08-934d434b8aa0	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
34bd0cef-c88f-4e8d-a114-0e553287b8d4	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
44c45dd1-44a5-40c2-9bfb-0d511dea3f27	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
96dde691-72a3-45e3-ac1a-1fb68ae564dc	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
41bd68f9-a3ee-41b3-a70d-7e5093e7633a	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
e0e72e73-cad0-46b3-9c8f-a925b767009b	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
8cd3f409-c270-483f-b578-ad8c82c5dc34	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
08d15b1c-ebd2-4d09-b6e5-3af392af489e	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
fc3b4d41-c8c7-43cf-91f5-6bcfa3fec9b5	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
d68d62ca-6e0d-4107-957b-bcb5e68c38ca	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
93ce4754-1c57-47f2-89b1-924129cecb71	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
0f7e6f40-3145-4405-b947-6a77f7dd0de5	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
b88fdb21-65b0-4ab8-9e49-1ef5e5ae0008	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
760b8c0a-9709-45b7-98a4-320f130f39ee	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
96e1f6fa-d5f3-4580-ac4c-bfe4e9459f10	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
f4ffdafc-deec-423d-9d0f-7f4ecfbfe1ed	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
681ff257-7cb1-4443-a3f3-ab500cbd258b	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
475f3831-fa7a-40da-8fbb-54cf37dd5bdd	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
24b282da-d40f-455e-9eea-377ad9272ee3	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
83349601-6495-4240-b947-a6d22aff2ee8	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
fc4040f5-961a-4536-8f2d-b1c3f2dfedeb	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 03:08:02.607351+00
5051cb1b-d1d6-4d74-a013-808b3c2bde89	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 04:30:00+00	2025-09-18 05:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
06d466af-bfe9-42cf-8d8d-9a192953d6f4	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 05:00:00+00	2025-09-18 05:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
e1c5a816-d658-486f-b114-bbb131b18cc9	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 05:30:00+00	2025-09-18 06:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
9c848f26-46e1-4346-94a2-b0e21a95fcc0	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 06:00:00+00	2025-09-18 06:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
36820dee-37c9-4586-952f-cea8a70652dc	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 06:30:00+00	2025-09-18 07:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
73c6c493-c568-4800-9953-5da8dcc7a8ae	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 07:00:00+00	2025-09-18 07:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
9fe0f641-1841-4afa-a4c2-cbafe1af6949	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 07:30:00+00	2025-09-18 08:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
ca85301f-28bc-40d1-9b4b-96f4ecf47516	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 08:00:00+00	2025-09-18 08:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
051240ee-c887-41e6-9489-f69dc2404db4	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 08:30:00+00	2025-09-18 09:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
5154bb42-db06-4b80-9f01-4d3a2c303182	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 09:00:00+00	2025-09-18 09:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
d3e30fab-490f-4bb1-a2da-8d32af674c2b	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 09:30:00+00	2025-09-18 10:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
afef3a4a-82e5-456f-b362-260b74880668	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
30013112-f74c-4a73-9750-2b98539a2785	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 10:30:00+00	2025-09-18 11:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
d299c214-ea86-4da3-b5c3-1d485974410b	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 11:00:00+00	2025-09-18 11:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
69467a83-90ec-40ec-bb17-e98aeabb69f3	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
407026a9-532d-4df9-bd7b-2db409fcbd0b	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
19b541c6-0c8e-4a5b-a0b4-2cc621029e81	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
9b27185a-7cb9-418d-acd9-f10cd65267c6	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
4c291b58-2105-48d1-8b89-d62cc2c36eac	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
b3bb8217-f143-40cf-bbea-78674c496ec0	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
32a062d6-3842-4496-8c6b-56d1ac0012a4	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
a1884c85-939c-4354-be0c-4e2922a8d740	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
dd0215cb-bc1a-4c7b-a7b9-4c11922f2f4f	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
2e2b7ab3-c111-4cfc-b114-690241190652	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
a8d5f9f2-ad59-464f-8031-ae5f376e90b0	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
88d7e2f2-8ddf-495a-80d6-77857c0087ab	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
6f24a41c-ace6-4a17-b38c-1b3a9796f398	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
e347e93e-860e-40e7-a4b2-3d212e342951	963e79ac-b111-400d-873c-50e5d6c97858	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-18 04:38:48.448031+00	2025-09-18 04:38:48.448031+00
89f8c980-b003-4c5b-a164-3ded53b2cd4b	51b89dcb-0dd1-4765-be11-850f9c647e67	2025-09-18 10:00:00+00	2025-09-18 10:30:00+00	booked	6b1106f0-490d-47d7-a41b-1803d7702e2b	\N	\N	2025-09-18 03:08:02.607351+00	2025-09-18 07:40:31.449357+00
a45e4401-f495-41cf-8b4e-b21a48958f09	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	booked	bed7a9a9-62cc-4048-815c-848261d9dc4f	\N	\N	2025-09-18 01:24:22.403678+00	2025-09-18 10:36:15.97366+00
bdfb2539-f0b5-4e47-9b75-7802b8be4ef2	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 11:30:00+00	2025-09-18 12:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
ab4b5398-992e-4df8-b43b-8b3b6ce2ad0e	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 12:00:00+00	2025-09-18 12:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
535e0945-9522-4a2e-b0d9-4a4032ccdfea	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 12:30:00+00	2025-09-18 13:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
a2dc33b9-9c88-4b92-bd34-aa3962031035	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 13:00:00+00	2025-09-18 13:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
d1884959-3da6-44a3-8c91-4fd0229ea8a9	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 13:30:00+00	2025-09-18 14:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
f8b25811-b6ab-42ce-a660-6767121a21ec	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 14:00:00+00	2025-09-18 14:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
894c0b0e-d7bf-4579-9427-2e954fa90509	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 14:30:00+00	2025-09-18 15:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
89dc4fac-fdfc-4e88-a774-6ef6eb207543	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 15:00:00+00	2025-09-18 15:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
ac8a301b-7f31-4b2d-ac03-9f02f6cb7880	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 15:30:00+00	2025-09-18 16:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
8aa68309-fd4f-4d1b-8614-d6fcdd1a922d	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 16:00:00+00	2025-09-18 16:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
4fd63b26-6421-455b-8d8c-1e4cb4bf23e4	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 16:30:00+00	2025-09-18 17:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
620b5c48-4d44-40ee-b767-3e5a306d402d	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 17:00:00+00	2025-09-18 17:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
8a75874c-ecfb-4afb-830e-7c2f1660243a	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 17:30:00+00	2025-09-18 18:00:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
d366674f-9bed-4948-9b14-dc650058d065	f8323476-ee6d-4a67-aeb3-f51ba3b5e17e	2025-09-18 18:00:00+00	2025-09-18 18:30:00+00	available	\N	\N	\N	2025-09-18 11:30:33.287488+00	2025-09-18 11:30:33.287488+00
0d8c5d93-7a07-4487-b879-093a41245214	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-19 21:30:00+00	2025-09-19 22:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
9ae3800f-2a74-449d-abf7-ec502779dc0b	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-19 22:00:00+00	2025-09-19 22:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
812d730d-f1e0-4a43-8c55-fd5f2d97223a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-19 22:30:00+00	2025-09-19 23:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
f65048c9-c3d2-4199-a0ae-bffbdb482a94	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-19 23:00:00+00	2025-09-19 23:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
69fcda1d-4978-4e46-b561-3f9cd776a122	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-19 23:30:00+00	2025-09-20 00:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
15451148-a4d0-4d5f-9f07-398569131f4f	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 00:00:00+00	2025-09-20 00:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
1b2ea783-8c33-462e-81db-761bc288861b	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 00:30:00+00	2025-09-20 01:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
a0c8fe23-a373-4a4b-98e1-8d6ccf29fe45	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 01:00:00+00	2025-09-20 01:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
d2e98c65-cec1-4d7f-bc7c-ea9c9ffbda5a	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 01:30:00+00	2025-09-20 02:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
6f745d75-e4b1-48c7-ba51-0a77561e7fba	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 02:00:00+00	2025-09-20 02:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
504fbe88-d07f-4b0b-be5b-c3b6abb756c9	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 02:30:00+00	2025-09-20 03:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
3acc6cf3-3dfa-4bc4-8bca-aead7125ebef	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 03:00:00+00	2025-09-20 03:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
ff217baf-a6c5-4dfb-90ba-efb18f6414b7	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 03:30:00+00	2025-09-20 04:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
7e02027b-1e09-44f2-8a5e-a93af029931c	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 04:00:00+00	2025-09-20 04:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
3e69bb7c-a4e5-4cc3-91be-6b36bea81942	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 04:30:00+00	2025-09-20 05:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
174f4619-d2c0-4a66-ae04-4597211ef763	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 05:00:00+00	2025-09-20 05:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
9687cef2-cf28-4e93-a9fb-17f02c0e1ba7	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 05:30:00+00	2025-09-20 06:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
43b8a03b-ebb8-43f6-bbd4-c2a228802298	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 06:00:00+00	2025-09-20 06:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
8807cf9f-28e6-48c2-8029-6c96f6944c6d	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 06:30:00+00	2025-09-20 07:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
eb1e1a67-cf7b-40be-bab5-8c74b74d46ab	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 07:00:00+00	2025-09-20 07:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
49e30fbe-248a-40cb-93a8-761e1fbb0488	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 07:30:00+00	2025-09-20 08:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
e040244c-fcd3-43a6-8306-d0ec405bafd5	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 08:00:00+00	2025-09-20 08:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
a86179a0-330b-4378-a3ff-cc1891a1279d	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 08:30:00+00	2025-09-20 09:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
b0360990-41b5-4329-aa6e-5317dcec5d1e	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 09:00:00+00	2025-09-20 09:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
6823138d-258c-4cba-85c9-d865bab66f59	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 09:30:00+00	2025-09-20 10:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
50a62573-ce92-4bb4-b15a-3ab9b41ab7c2	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 10:00:00+00	2025-09-20 10:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
cc482f10-8e23-4731-a198-82e75a8e3314	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 10:30:00+00	2025-09-20 11:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
d54aa31c-65de-4c88-8791-065f208942a5	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 11:00:00+00	2025-09-20 11:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
9da323df-01eb-42a4-bb3e-803deb66fb21	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 11:30:00+00	2025-09-20 12:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
72a5b9ab-f1c7-41fd-bfbe-2924d0e1eb37	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 12:00:00+00	2025-09-20 12:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
563c05cb-5c0e-4f41-aaaa-31253edb5c35	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 12:30:00+00	2025-09-20 13:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
d123952f-9132-4ef2-a0ad-8964a0b01c42	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 13:00:00+00	2025-09-20 13:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
923b6f23-702d-424c-b1f3-9b56ef8d1886	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 13:30:00+00	2025-09-20 14:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
f68179e2-c884-4b9c-a9b9-1fbe5c40bbb6	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 14:00:00+00	2025-09-20 14:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
cd101d17-a08e-4102-9c91-919742db1bc4	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 14:30:00+00	2025-09-20 15:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
7b26972f-e62c-4eff-a598-ed977e059dff	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 15:00:00+00	2025-09-20 15:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
7f88ccb1-7a93-46f1-8473-6f0031efa70f	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 15:30:00+00	2025-09-20 16:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
50154666-cc96-4cba-b76e-b2d79a7bb257	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 16:00:00+00	2025-09-20 16:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
541f2070-c1bf-4b09-9580-101acf1a6211	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 16:30:00+00	2025-09-20 17:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
5fdbaec7-776f-496c-8308-220152532b10	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 17:00:00+00	2025-09-20 17:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
b242abcc-f5e5-457c-8c3e-72fca88d9100	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 17:30:00+00	2025-09-20 18:00:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
604a62b3-48b9-489f-a808-2b1c878eb02b	fe509eba-32af-4941-92f8-6d65deb6fc3c	2025-09-20 18:00:00+00	2025-09-20 18:30:00+00	available	\N	\N	\N	2025-09-19 21:40:59.509918+00	2025-09-19 21:40:59.509918+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (email, password_hash, first_name, last_name, phone, is_admin, is_active, id, created_at, updated_at, total_spent) FROM stdin;
admin@smartparking.com	$2b$12$1Nw8zfprnUUhQYMphENqse3gdJfZfPjydMHWbFK88c4A8stfMhbim	Admin	User	+1234567890	t	t	ac1ef1d8-d27e-43b3-9e96-d5ba839628fc	2025-09-16 11:29:29.472298+00	2025-09-16 11:29:29.472298+00	0.00
user@example.com	$2b$12$tmY3QTsAdIIzGqM8J5KRpOpJNeB8BrgpSBx5WNswsTIO7.r4z.G6u	User	LastName	+1234567890	f	t	2307bee9-d3eb-4d2c-ba37-d0acd4f5de76	2025-09-16 13:20:21.91516+00	2025-09-16 13:20:21.91516+00	0.00
john.doe@example.com	$2b$12$Bo6nmcN62yqLoiIdr93TY.wmpTpgpzFduqQaLpOfKZeZOj4W8dSpe	John	Doe	+1234567890	f	t	3a22cbff-7448-4af0-8289-ea7bf4b98dd1	2025-09-16 11:28:32.610937+00	2025-09-16 13:22:43.264951+00	0.00
md@example.com	$2b$12$cAOroXXL2Sy6.IZld5fP3OvtKx/pEvAd7O.BFYIn3VlUOahxdjIMC	MM	DDD	+1234567892	t	t	8fdf35c0-bdcf-48c0-b684-4b830348174c	2025-09-16 11:32:40.943009+00	2025-09-16 13:34:54.004222+00	0.00
testuser@example.com	$2b$12$UpMpQqOubzlOVFbSPqTZsuMS.HQ6P3UYhXoklU6aRu2iANqDW9.u.	Test	User	+1234567890	f	t	0722ba41-40ec-4473-81f6-94fd5fb5cd61	2025-09-16 14:25:36.969555+00	2025-09-16 14:25:36.969555+00	0.00
test@example.com	$2b$12$WEdqjoT4IzqT14Wn/tj90O8NcLv8wCttKGULBkoviXpnGnhYqve3u	Test	User	1234567890	f	t	7fc2584a-e44f-4556-b1bd-3bc4eb76c232	2025-09-16 18:08:35.256959+00	2025-09-16 18:08:35.256959+00	0.00
duser@example.com	$2b$12$X6KZ4oEJPh0ZGgtqRkzc3.TfSm.RaFgAViCUIy9fv6959LHOnLvVG	Dummy	User	\N	f	t	e5b8cb69-e70b-4910-a9b8-39d1d8a767cd	2025-09-16 18:10:01.728783+00	2025-09-16 18:10:01.728783+00	0.00
admin@parking.com	$2b$12$H0Qz/saT/8FXHuJeXFIB4OiTyNX3/BRhBjBZQIlPngIh1kYOiE9hW	Admin	User	9999999999	f	t	b6b6b87e-370e-4c00-afb3-5307390ddf3c	2025-09-16 20:35:26.001972+00	2025-09-16 20:35:26.001972+00	0.00
user@parking.com	$2b$12$rCY/wPucYKN3uXvFFK435Oe1cJ9I5TiMsvkbqHKx446B9zCfQwLxi	Test	User	1234567890	f	t	95af85f1-b3fd-4df7-8e49-abcce35db1fc	2025-09-16 20:36:10.130113+00	2025-09-16 20:36:10.130113+00	0.00
testadmin@example.com	$2b$12$jLMaDWt3GxmqG9JHBEkhP.IPR9RTTZfY.9kJc3mruIQCFLQz8wZWi	Test	Admin	5555551234	f	t	01e30074-e0c6-48d2-91d9-62abc7902719	2025-09-16 20:39:04.582204+00	2025-09-16 20:39:04.582204+00	0.00
newuser@test.com	$2b$12$5p1vIk71Ai532Hu1ezhujOyvLVROzdNJQPQRgTT17GVbkR6Z9ZmjO	New	User	\N	f	t	8f013d1e-67bb-48f2-b70e-57d29a1f02c1	2025-09-16 21:46:11.898945+00	2025-09-16 21:46:11.898945+00	0.00
test3@test.com	$2b$12$YJ2AQEusjIesaE1Wrn808uiD1./8tCV33P5WnZoqkQrbAVgo49w62	Test	User	\N	f	t	e81f3f97-6634-4ac2-aed3-bd38a9fd94ac	2025-09-16 21:46:50.717338+00	2025-09-16 21:46:50.717338+00	0.00
test4@test.com	$2b$12$WZXqpFdP9PZosdFuLrmCQuNiUnmjczLcIWV9AhgLU6u/Hjf/E2JRK	Test	User	\N	f	t	143b1a0c-e700-45c6-89df-3e7165f3580b	2025-09-16 21:47:36.080689+00	2025-09-16 21:47:36.080689+00	0.00
test5@test.com	$2b$12$sJesSe.VwtRaUfJsJx1tAu8s0JNAoyd865ftbcibqprLbr7NQ7Wpy	Test	User	\N	f	t	c6a172a9-741a-48b8-8401-c9bef86676a4	2025-09-16 21:47:47.641824+00	2025-09-16 21:47:47.641824+00	0.00
duser1@example.com	$2b$12$YHnbTI14mH/CwAe1m8CI/ejEd4kQLPwqbwE.XPCsBz7ApmP1So5q.	Dummy	User	\N	f	t	5d8778c7-67dc-46ee-94ca-672899a28862	2025-09-16 21:49:13.594903+00	2025-09-16 21:49:13.594903+00	0.00
test6@test.com	$2b$12$req.1rkVQ7vjZozvTMfbQOMekS9fRA53w.ZgAu8OEjCBrui26PLBC	Test	User	\N	f	t	2622634a-2e07-41cd-a476-dd7d47363cd7	2025-09-16 21:49:40.470633+00	2025-09-16 21:49:40.470633+00	0.00
testuser@test.com	$2b$12$Hd0z/GAq1CANOPOHqfNlxeJGIMZtd8sUBNAW3TXEgMvJ1r0Ua2.7q	Test	User	\N	f	t	c1842768-eeb5-468b-beb6-4e356bc66a62	2025-09-16 21:58:06.522753+00	2025-09-16 21:58:06.522753+00	0.00
duser2@example.com	$2b$12$XUbIxp0jkjCHybVNaqgVmeaq8cmIS.bS6oj/XdX/9h8JlPMzMtXnW	Dummy	User	duser@example.com	f	t	9f5402f7-1a3d-4f0c-9227-b7a808a64055	2025-09-16 22:08:25.266566+00	2025-09-16 22:45:41.086899+00	11.51
testuser_utc@test.com	$2b$12$02XWO4FgmGZ75spF28EJse87jtSltpB9HdODVndi1FcFqdiFZE3ii	UTC	Test	+1234567890	f	t	a31b1f6f-5893-4d3c-a92c-e79894e3a493	2025-09-17 17:48:06.124432+00	2025-09-17 17:48:06.124432+00	0.00
demo@example.com	$2b$12$NcCNPUKCx6EH1Fu7s0ZlkOlAx8MlhQP3uWC8boua.2XWKHPQw0uQq	Demo	User		f	t	af99f3e6-84eb-42d7-8d10-c80ad4138e4e	2025-09-16 21:42:17.052543+00	2025-09-17 17:53:53.348895+00	101.47
user@smartparking.com	$2b$12$kVWSpjF5lKxG1yxF2HbpAuDD4u0VrRerveezqTVJWatTVf.wcw/3e	Test	User	+919876543210	f	t	5b0c9625-bf8a-4e7c-81b4-903c34465157	2025-09-18 08:10:27.479995+00	2025-09-18 08:10:27.479995+00	0.00
priya.sharma@example.com	$2b$12$a/wV7fid88SjPC7FM9GG0.1u6poe4eyppbyv3ZUMhuM2KAb9Rsv5u	Priya	Sharma	+919876543212	f	t	4d781bdf-0fbc-4266-bee5-be2a7552d332	2025-09-18 08:10:27.479995+00	2025-09-18 08:10:27.479995+00	0.00
admin.manager@smartparking.com	$2b$12$Ad39xFdGx85ACcHYAU5hc.8X0pUEfPT8qQdShejRZINUAqhempquy	Admin	Manager	+919876543213	t	t	885cf30a-43a0-41b7-9c10-6096a8421a30	2025-09-18 08:10:27.479995+00	2025-09-18 08:10:27.479995+00	0.00
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: bookings bookings_booking_reference_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_booking_reference_key UNIQUE (booking_reference);


--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: parking_lots parking_lots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parking_lots
    ADD CONSTRAINT parking_lots_pkey PRIMARY KEY (id);


--
-- Name: parking_slots parking_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parking_slots
    ADD CONSTRAINT parking_slots_pkey PRIMARY KEY (id);


--
-- Name: payment_cards payment_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_cards
    ADD CONSTRAINT payment_cards_pkey PRIMARY KEY (id);


--
-- Name: payment_transactions payment_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payments payments_transaction_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_transaction_id_key UNIQUE (transaction_id);


--
-- Name: pricing_rules pricing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT pricing_rules_pkey PRIMARY KEY (id);


--
-- Name: slot_allocations slot_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_allocations
    ADD CONSTRAINT slot_allocations_pkey PRIMARY KEY (id);


--
-- Name: slot_time_chunks slot_time_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_time_chunks
    ADD CONSTRAINT slot_time_chunks_pkey PRIMARY KEY (id);


--
-- Name: parking_slots unique_lot_slot; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parking_slots
    ADD CONSTRAINT unique_lot_slot UNIQUE (lot_id, slot_number);


--
-- Name: pricing_rules unique_pricing_rule; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT unique_pricing_rule UNIQUE (lot_id, vehicle_type, start_time, end_time, rule_type);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_allocation_booking; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_allocation_booking ON public.slot_allocations USING btree (booking_id);


--
-- Name: idx_allocation_slot; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_allocation_slot ON public.slot_allocations USING btree (slot_id);


--
-- Name: idx_allocation_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_allocation_type ON public.slot_allocations USING btree (allocation_type);


--
-- Name: idx_booking_lot_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_lot_id ON public.bookings USING btree (lot_id);


--
-- Name: idx_booking_reference; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_reference ON public.bookings USING btree (booking_reference);


--
-- Name: idx_booking_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_status ON public.bookings USING btree (status);


--
-- Name: idx_booking_time_range; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_time_range ON public.bookings USING btree (start_time, end_time);


--
-- Name: idx_booking_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_user_id ON public.bookings USING btree (user_id);


--
-- Name: idx_booking_vehicle; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_booking_vehicle ON public.bookings USING btree (vehicle_number);


--
-- Name: idx_bookings_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bookings_session ON public.bookings USING btree (session_id);


--
-- Name: idx_no_overlapping_chunks; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_no_overlapping_chunks ON public.slot_time_chunks USING btree (slot_id, start_time, end_time) WHERE ((status)::text = ANY ((ARRAY['booked'::character varying, 'temp_reserved'::character varying])::text[]));


--
-- Name: idx_notifications_booking_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_booking_id ON public.notifications USING btree (booking_id);


--
-- Name: idx_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at);


--
-- Name: idx_notifications_is_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: idx_notifications_scheduled_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_scheduled_at ON public.notifications USING btree (scheduled_at);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_type ON public.notifications USING btree (type);


--
-- Name: idx_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: idx_notifications_user_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_read ON public.notifications USING btree (user_id, is_read);


--
-- Name: idx_parking_lot_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parking_lot_active ON public.parking_lots USING btree (is_active);


--
-- Name: idx_parking_lot_location; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parking_lot_location ON public.parking_lots USING btree (latitude, longitude);


--
-- Name: idx_payment_booking_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_booking_id ON public.payments USING btree (booking_id);


--
-- Name: idx_payment_card_default; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_card_default ON public.payment_cards USING btree (user_id, is_default);


--
-- Name: idx_payment_card_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_card_token ON public.payment_cards USING btree (card_token);


--
-- Name: idx_payment_card_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_card_user_id ON public.payment_cards USING btree (user_id);


--
-- Name: idx_payment_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_created_at ON public.payments USING btree (created_at);


--
-- Name: idx_payment_gateway_transaction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_gateway_transaction_id ON public.payments USING btree (gateway_transaction_id);


--
-- Name: idx_payment_processed_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_processed_at ON public.payments USING btree (processed_at);


--
-- Name: idx_payment_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_status ON public.payments USING btree (status);


--
-- Name: idx_payment_transaction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_transaction_id ON public.payments USING btree (transaction_id);


--
-- Name: idx_payment_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payment_user_id ON public.payments USING btree (user_id);


--
-- Name: idx_pricing_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_active ON public.pricing_rules USING btree (is_active);


--
-- Name: idx_pricing_lot_vehicle; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_lot_vehicle ON public.pricing_rules USING btree (lot_id, vehicle_type);


--
-- Name: idx_pricing_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_priority ON public.pricing_rules USING btree (priority);


--
-- Name: idx_pricing_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_time ON public.pricing_rules USING btree (start_time, end_time);


--
-- Name: idx_slot_availability; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_availability ON public.parking_slots USING btree (is_occupied, is_reserved, status);


--
-- Name: idx_slot_chunks_availability; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_chunks_availability ON public.slot_time_chunks USING btree (slot_id, start_time, end_time, status);


--
-- Name: idx_slot_chunks_booking; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_chunks_booking ON public.slot_time_chunks USING btree (booking_id);


--
-- Name: idx_slot_chunks_reserved_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_chunks_reserved_by ON public.slot_time_chunks USING btree (reserved_by, reserved_at);


--
-- Name: idx_slot_lot_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_lot_type ON public.parking_slots USING btree (lot_id, slot_type);


--
-- Name: idx_slot_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_slot_status ON public.parking_slots USING btree (status);


--
-- Name: idx_transaction_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_created_at ON public.payment_transactions USING btree (created_at);


--
-- Name: idx_transaction_payment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_payment_id ON public.payment_transactions USING btree (payment_id);


--
-- Name: idx_transaction_processed_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_processed_at ON public.payment_transactions USING btree (processed_at);


--
-- Name: idx_transaction_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_status ON public.payment_transactions USING btree (status);


--
-- Name: idx_transaction_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_type ON public.payment_transactions USING btree (transaction_type);


--
-- Name: idx_user_email_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_email_active ON public.users USING btree (email, is_active);


--
-- Name: idx_user_phone; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_phone ON public.users USING btree (phone);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: bookings bookings_lot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_lot_id_fkey FOREIGN KEY (lot_id) REFERENCES public.parking_lots(id) ON DELETE CASCADE;


--
-- Name: bookings bookings_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_slot_id_fkey FOREIGN KEY (slot_id) REFERENCES public.parking_slots(id) ON DELETE SET NULL;


--
-- Name: bookings bookings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id);


--
-- Name: notifications notifications_lot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_lot_id_fkey FOREIGN KEY (lot_id) REFERENCES public.parking_lots(id);


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: parking_slots parking_slots_lot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parking_slots
    ADD CONSTRAINT parking_slots_lot_id_fkey FOREIGN KEY (lot_id) REFERENCES public.parking_lots(id) ON DELETE CASCADE;


--
-- Name: payment_cards payment_cards_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_cards
    ADD CONSTRAINT payment_cards_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: payment_transactions payment_transactions_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES public.payments(id) ON DELETE CASCADE;


--
-- Name: payments payments_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE CASCADE;


--
-- Name: payments payments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: pricing_rules pricing_rules_lot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT pricing_rules_lot_id_fkey FOREIGN KEY (lot_id) REFERENCES public.parking_lots(id) ON DELETE CASCADE;


--
-- Name: slot_allocations slot_allocations_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_allocations
    ADD CONSTRAINT slot_allocations_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE CASCADE;


--
-- Name: slot_allocations slot_allocations_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_allocations
    ADD CONSTRAINT slot_allocations_slot_id_fkey FOREIGN KEY (slot_id) REFERENCES public.parking_slots(id) ON DELETE CASCADE;


--
-- Name: slot_time_chunks slot_time_chunks_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_time_chunks
    ADD CONSTRAINT slot_time_chunks_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE SET NULL;


--
-- Name: slot_time_chunks slot_time_chunks_reserved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_time_chunks
    ADD CONSTRAINT slot_time_chunks_reserved_by_fkey FOREIGN KEY (reserved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: slot_time_chunks slot_time_chunks_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slot_time_chunks
    ADD CONSTRAINT slot_time_chunks_slot_id_fkey FOREIGN KEY (slot_id) REFERENCES public.parking_slots(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict hNne62o1fMzeiE6vvXxMadeSoQGYOh3juVUTwqGAUjp9ogLvWzaHaWLt2fB9CN4

