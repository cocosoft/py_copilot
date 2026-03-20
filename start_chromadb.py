import chromadb

# 配置chromadb - 使用新的配置方式
chroma_client = chromadb.PersistentClient(
    path="./chromadb_data"
)

# 启动服务
print("Chromadb服务已启动，数据存储在 ./chromadb_data 目录")
print("客户端初始化成功:", chroma_client)

# 创建一个测试集合
test_collection = chroma_client.create_collection(name="test_collection")
print("创建测试集合成功")

# 添加一些测试数据
test_collection.add(
    documents=["这是测试文档1", "这是测试文档2"],
    metadatas=[{"source": "test1"}, {"source": "test2"}],
    ids=["1", "2"]
)
print("添加测试数据成功")

# 测试查询
results = test_collection.query(
    query_texts=["测试文档"],
    n_results=2
)
print("查询结果:", results)

print("\nChromadb服务运行正常！")
print("要停止服务，请按 Ctrl+C")

# 保持服务运行
import time
while True:
    time.sleep(1)
