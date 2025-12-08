from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.model_management import Model, ModelSupplier

# 创建数据库连接
engine = create_engine('sqlite:///./py_copilot.db')
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = Session()

# 获取Ollama供应商
ollama_supplier = db.query(ModelSupplier).filter(ModelSupplier.name == "Ollama").first()

if not ollama_supplier:
    print("错误：未找到Ollama供应商！")
    db.close()
    exit()

# 实际可用的Ollama模型
available_models = [
    {"name": "deepseek-r1:1.5b", "display_name": "DeepSeek R1 1.5B", "model_type": "chat"},
    {"name": "ministral-3:3b", "display_name": "Ministral 3 3B", "model_type": "chat"}
]

# 更新或添加模型
for model_info in available_models:
    # 检查模型是否已存在
    existing_model = db.query(Model).filter(
        Model.name == model_info["name"],
        Model.supplier_id == ollama_supplier.id
    ).first()
    
    if existing_model:
        # 更新现有模型
        existing_model.display_name = model_info["display_name"]
        existing_model.model_type = model_info["model_type"]
        existing_model.is_active = True
        print(f"已更新模型：{model_info['name']}")
    else:
        # 添加新模型
        new_model = Model(
            name=model_info["name"],
            display_name=model_info["display_name"],
            supplier_id=ollama_supplier.id,
            model_type=model_info["model_type"],
            is_active=True
        )
        db.add(new_model)
        print(f"已添加模型：{model_info['name']}")

# 提交更改
db.commit()
print("\n模型更新完成！")

# 显示Ollama供应商下的所有模型
print("\nOllama供应商下的模型：")
ollama_models = db.query(Model).filter(Model.supplier_id == ollama_supplier.id).all()
for model in ollama_models:
    print(f"- {model.name} (显示名称：{model.display_name}，类型：{model.model_type}，状态：{model.is_active})")

db.close()