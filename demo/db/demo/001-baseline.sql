CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name VARCHAR,
  image_url VARCHAR
);

CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  log VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE
);