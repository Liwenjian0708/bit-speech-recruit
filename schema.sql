-- 用户表（新生）
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    pwd TEXT NOT NULL,
    name TEXT NOT NULL,
    grade TEXT NOT NULL,
    college TEXT NOT NULL,
    major TEXT NOT NULL,
    time_slot TEXT NOT NULL,  -- 日常空闲时段，逗号分隔
    busy_week TEXT NOT NULL,  -- 忙碌周，逗号分隔
    activity_pre TEXT NOT NULL,  -- 活动参与偏好
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 测评答案表
CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    answers TEXT NOT NULL,  -- 答案向量，字典转字符串
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 匹配报告表
CREATE TABLE IF NOT EXISTS report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    data TEXT NOT NULL,  -- 报告数据，字典转字符串
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 报名信息表
CREATE TABLE IF NOT EXISTS apply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    grade TEXT NOT NULL,
    college TEXT NOT NULL,
    major TEXT NOT NULL,
    team1 TEXT NOT NULL,  -- 第一志愿
    team2 TEXT,           -- 第二志愿
    intro TEXT,           -- 自我介绍
    specialty TEXT,       -- 语言特长
    status TEXT DEFAULT '待审核',  -- 待审核/初试通过/复试通知/录取成功
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 标杆成员画像表
CREATE TABLE IF NOT EXISTS benchmark (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team TEXT NOT NULL,  -- speech/host/debate/dubbing
    name TEXT NOT NULL,  -- 标杆成员姓名
    answers TEXT NOT NULL,  -- 标杆答案向量
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 队伍活动时间表
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team TEXT NOT NULL,  -- speech/host/debate/dubbing
    name TEXT NOT NULL,  -- 活动名称
    time_slot TEXT NOT NULL,  -- 活动时段
    week TEXT NOT NULL,  -- 活动周次
    priority TEXT NOT NULL,  -- 高/中/低
    form TEXT NOT NULL,  -- 线上/线下
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 管理员/队长表（初始账号：admin/123456；各队长账号：captain1-4/123456）
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT UNIQUE NOT NULL,
    pwd TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,  -- admin/captain
    team TEXT,  -- speech/host/debate/dubbing（admin为NULL）
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入初始管理员和队长账号
INSERT OR IGNORE INTO admin (account, pwd, name, role, team) VALUES
('admin', '123456', '超级管理员', 'admin', NULL),
('captain1', '123456', '杨伊瑞', 'captain', 'speech'),
('captain2', '123456', '林皓宇', 'captain', 'host'),
('captain3', '123456', '顾泽轩', 'captain', 'debate'),
('captain4', '123456', '苏晚晴', 'captain', 'dubbing');