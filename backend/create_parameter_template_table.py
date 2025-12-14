import sqlite3
import os
import json

# 获取数据库文件路径
db_path = os.path.join(os.getcwd(), 'py_copilot.db')

# 连接到SQLite数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查parameter_templates表是否存在
print("Checking parameter_templates table...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parameter_templates';")
if cursor.fetchone():
    print("parameter_templates table already exists.")
else:
    # 创建parameter_templates表
    print("Creating parameter_templates table...")
    create_table_sql = '''
    CREATE TABLE parameter_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        level VARCHAR(50) NOT NULL,
        parent_id INTEGER,
        level_id INTEGER,
        parameters JSON NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES parameter_templates (id) ON DELETE SET NULL
    );
    '''
    cursor.execute(create_table_sql)
    print("parameter_templates table created successfully.")

# 检查是否有激活的系统级参数模板
print("\nChecking for active system parameter template...")
cursor.execute("SELECT id FROM parameter_templates WHERE level='system' AND is_active=1;")
system_template = cursor.fetchone()
if system_template:
    print(f"Active system template already exists with ID: {system_template[0]}")
else:
    # 创建一个默认的系统级参数模板
    print("Creating default system parameter template...")
    default_parameters = [
        {
            "name": "temperature",
            "type": "float",
            "default_value": 0.7,
            "description": "控制生成文本的随机性",
            "required": False,
            "validation_rules": {
                "min": 0.0,
                "max": 1.0
            }
        },
        {
            "name": "top_p",
            "type": "float",
            "default_value": 1.0,
            "description": "控制核采样范围",
            "required": False,
            "validation_rules": {
                "min": 0.0,
                "max": 1.0
            }
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default_value": 2048,
            "description": "生成文本的最大token数",
            "required": False,
            "validation_rules": {
                "min": 1,
                "max": 4096
            }
        }
    ]
    
    insert_sql = '''
    INSERT INTO parameter_templates (name, level, parent_id, level_id, parameters, is_active)
    VALUES (?, ?, ?, ?, ?, ?);
    '''
    cursor.execute(insert_sql, (
        "Default System Template",
        "system",
        None,
        None,
        json.dumps(default_parameters),
        True
    ))
    print("Default system template created successfully.")

# 提交更改并关闭连接
conn.commit()
conn.close()
print("\nDatabase changes committed and connection closed.")