INSERT INTO "user" (username, email, hashed_password, first_name, last_name, role_id, is_active, created_at, updated_at) 
VALUES ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EQVGkYuFLVDe', 'Admin', 'User', 1, true, NOW(), NOW())
ON CONFLICT (username) DO NOTHING;
