import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('py_copilot.db')
cursor = conn.cursor()

# Create tables
print("Creating database tables...")

# 1. Create model_categories table
cursor.execute('''
CREATE TABLE IF NOT EXISTS model_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category_type VARCHAR(20) DEFAULT "main" NOT NULL,
    parent_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    logo TEXT,
    default_parameters JSON DEFAULT '{}',
    FOREIGN KEY (parent_id) REFERENCES model_categories (id)
)
''')
print("✓ model_categories table created")

# 2. Create suppliers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    api_endpoint VARCHAR(255),
    api_key_required BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    logo VARCHAR(255),
    category VARCHAR(100),
    website VARCHAR(255),
    api_docs VARCHAR(255),
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
)
''')
print("✓ suppliers table created")

# 3. Create parameter_templates table
cursor.execute('''
CREATE TABLE IF NOT EXISTS parameter_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    level VARCHAR(50) NOT NULL,
    parent_id INTEGER,
    level_id INTEGER,
    parameters JSON NOT NULL,
    version VARCHAR(50) DEFAULT "1.0.0",
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (parent_id) REFERENCES parameter_templates (id) ON DELETE SET NULL
)
''')
print("✓ parameter_templates table created")

# 4. Create models table
cursor.execute('''
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(200) NOT NULL,
    description TEXT,
    supplier_id INTEGER NOT NULL,
    model_type_id INTEGER,
    context_window INTEGER,
    max_tokens INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    logo VARCHAR(255),
    parameter_template_id INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE CASCADE,
    FOREIGN KEY (model_type_id) REFERENCES model_categories (id),
    FOREIGN KEY (parameter_template_id) REFERENCES parameter_templates (id) ON DELETE SET NULL
)
''')
print("✓ models table created")

# 5. Create model_parameters table
cursor.execute('''
CREATE TABLE IF NOT EXISTS model_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_type VARCHAR(50) NOT NULL,
    parameter_value TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    description TEXT,
    parameter_source VARCHAR(50) DEFAULT "model",
    is_override BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE
)
''')
print("✓ model_parameters table created")

# 6. Create model_category_associations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS model_category_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES model_categories (id) ON DELETE CASCADE
)
''')
print("✓ model_category_associations table created")

# 7. Create model_capabilities table
cursor.execute('''
CREATE TABLE IF NOT EXISTS model_capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    capability_type VARCHAR(50) DEFAULT "standard" NOT NULL,
    input_types TEXT,
    output_types TEXT,
    domain VARCHAR(50) DEFAULT "nlp" NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    logo TEXT
)
''')
print("✓ model_capabilities table created")

# 8. Create model_capability_associations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS model_capability_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    capability_id INTEGER NOT NULL,
    config VARCHAR(255),
    config_json TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE,
    FOREIGN KEY (capability_id) REFERENCES model_capabilities (id) ON DELETE CASCADE
)
''')
print("✓ model_capability_associations table created")

# Insert sample data
print("\nInserting sample data...")

# Insert a default supplier
cursor.execute('''
INSERT OR IGNORE INTO suppliers (name, display_name, description, is_active)
VALUES ("openai", "OpenAI", "OpenAI供应商", TRUE)
''')
supplier_id = cursor.lastrowid
print("✓ Sample supplier inserted")

# Insert a default model category
cursor.execute('''
INSERT OR IGNORE INTO model_categories (name, display_name, category_type, is_system, is_active)
VALUES ("llm", "大语言模型", "main", TRUE, TRUE)
''')
model_type_id = cursor.lastrowid
print("✓ Sample model category inserted")

# Insert a system parameter template
cursor.execute('''
INSERT OR IGNORE INTO parameter_templates (name, level, parameters, is_active)
VALUES ("System Default Template", "system", '{"temperature": 0.7, "top_p": 0.9}', TRUE)
''')
system_template_id = cursor.lastrowid
print("✓ System parameter template inserted")

# Insert a model parameter template
cursor.execute('''
INSERT OR IGNORE INTO parameter_templates (name, level, parent_id, parameters, is_active)
VALUES ("GPT-4 Template", "model", ?, '{"temperature": 0.5, "top_p": 0.8}', TRUE)
''', (system_template_id,))
model_template_id = cursor.lastrowid
print("✓ Model parameter template inserted")

# Insert a sample model
cursor.execute('''
INSERT OR IGNORE INTO models (model_id, model_name, description, supplier_id, model_type_id, parameter_template_id, is_active)
VALUES ("gpt-4", "GPT-4", "OpenAI GPT-4模型", ?, ?, ?, TRUE)
''', (supplier_id, model_type_id, model_template_id))
model_id = cursor.lastrowid
print("✓ Sample model inserted")

# Insert sample model parameters
cursor.execute('''
INSERT OR IGNORE INTO model_parameters (model_id, parameter_name, parameter_type, parameter_value, is_default)
VALUES (?, "temperature", "float", "0.7", TRUE)
''', (model_id,))

cursor.execute('''
INSERT OR IGNORE INTO model_parameters (model_id, parameter_name, parameter_type, parameter_value, is_default)
VALUES (?, "max_tokens", "integer", "4096", TRUE)
''', (model_id,))
print("✓ Sample model parameters inserted")

# Create model-category association
cursor.execute('''
INSERT OR IGNORE INTO model_category_associations (model_id, category_id)
VALUES (?, ?)
''', (model_id, model_type_id))
print("✓ Model-category association inserted")

# Insert sample model capabilities
cursor.execute('''
INSERT OR IGNORE INTO model_capabilities (name, display_name, description, capability_type, input_types, output_types, domain, is_active, is_system)
VALUES 
    ("text_generation", "文本生成", "生成文本内容的能力", "standard", '["text"]', '["text"]', "nlp", TRUE, TRUE),
    ("image_generation", "图像生成", "生成图像内容的能力", "standard", '["text"]', '["image"]', "cv", TRUE, TRUE),
    ("speech_recognition", "语音识别", "将语音转换为文本的能力", "standard", '["audio"]', '["text"]', "audio", TRUE, TRUE),
    ("text_summarization", "文本摘要", "将长文本总结为短文本的能力", "standard", '["text"]', '["text"]', "nlp", TRUE, TRUE),
    ("translation", "翻译", "将文本从一种语言翻译为另一种语言的能力", "standard", '["text"]', '["text"]', "nlp", TRUE, TRUE)
''')
print("✓ Sample model capabilities inserted")

# Get the text_generation capability id
cursor.execute('SELECT id FROM model_capabilities WHERE name = "text_generation"')
text_generation_id = cursor.fetchone()[0]

# Create model-capability association
cursor.execute('''
INSERT OR IGNORE INTO model_capability_associations (model_id, capability_id, is_default)
VALUES (?, ?, TRUE)
''', (model_id, text_generation_id))
print("✓ Model-capability association inserted")

# Commit changes
conn.commit()
print("\n✓ All tables created and sample data inserted successfully!")

# Close connection
conn.close()