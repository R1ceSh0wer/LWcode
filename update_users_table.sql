-- 添加 created_at 字段到 users 表
ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- 为已存在的记录设置默认值
UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;