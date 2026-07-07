CREATE TABLE IF NOT EXISTS queue (

    -- Internal identifier
    id SERIAL PRIMARY KEY,

    -- Merchant's order number
    order_id TEXT UNIQUE NOT NULL,

    -- Original Shopify webhook
    raw_payload JSONB NOT NULL,

    -- Processed order after all business rules
    warehouse_payload JSONB,

    -- Current lifecycle status
    status VARCHAR(30) NOT NULL,

    -- Retry information
    retry_count INTEGER DEFAULT 0,

    -- Generated CSV filename
    csv_filename TEXT,

    -- Uploaded filename on warehouse server
    warehouse_filename TEXT,

    -- Returned from warehouse
    tracking_number TEXT,

    carrier TEXT,

    -- Human readable failure
    failure_reason TEXT,

    -- Audit timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    csv_generated_at TIMESTAMP,

    uploaded_at TIMESTAMP,

    tracking_received_at TIMESTAMP,

    completed_at TIMESTAMP

);