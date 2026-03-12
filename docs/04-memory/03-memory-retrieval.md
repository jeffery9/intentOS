# 记忆检索

> 记忆检索支持按标签检索、全文搜索、语义搜索等多种方式，帮助用户快速找到所需信息。

---

## 1. 标签检索

### 1.1 设置标签

```python
await manager.set_long_term(
    key="report:q3_sales",
    value={"title": "Q3 销售报告", "content": "..."},
    tags=["report", "sales", "q3"],
)
```

### 1.2 按标签检索

```python
# 获取所有带 "report" 标签的记忆
entries = await manager.get_by_tag("report")

for entry in entries:
    print(f"{entry.key}: {entry.value}")
```

### 1.3 标签组合

```python
# 与运算：同时有 report 和 sales 标签
entries = await manager.get_by_tags(["report", "sales"], op="and")

# 或运算：有 report 或 sales 标签
entries = await manager.get_by_tags(["report", "sales"], op="or")
```

---

## 2. 全文搜索

### 2.1 基本搜索

```python
# 搜索包含关键词的记忆
results = await manager.search("销售")

for r in results:
    print(f"{r.key}: {r.value}")
```

### 2.2 搜索范围

```python
# 指定搜索字段
results = await manager.search(
    query="销售",
    fields=["key", "value", "tags"],  # 搜索键、值、标签
)
```

### 2.3 高亮显示

```python
results = await manager.search(
    query="销售",
    highlight=True,  # 启用高亮
    highlight_prefix="<em>",
    highlight_suffix="</em>",
)

# 结果中包含高亮标记
for r in results:
    print(r.highlighted_text)  # "...本季度<em>销售</em>增长..."
```

---

## 3. 语义搜索

### 3.1 向量嵌入

```python
class SemanticSearch:
    def __init__(self, embedding_model: str = "text-embedding-ada-002"):
        self.model = embedding_model
    
    def embed(self, text: str) -> list[float]:
        """生成向量嵌入"""
        # 调用 LLM API 生成嵌入
        response = await llm.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
```

### 3.2 相似度计算

```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot_product / (norm_a * norm_b)
```

### 3.3 语义搜索实现

```python
async def semantic_search(
    self,
    query: str,
    threshold: float = 0.7,
    limit: int = 10,
) -> list[SearchResult]:
    """语义搜索"""
    # 生成查询向量
    query_embedding = self.embed(query)
    
    results = []
    
    # 遍历所有记忆
    async for entry in self._iterate_all():
        # 获取记忆的向量（预先计算并存储）
        entry_embedding = entry.metadata.get("embedding")
        
        if entry_embedding:
            similarity = cosine_similarity(query_embedding, entry_embedding)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    entry=entry,
                    similarity=similarity,
                ))
    
    # 按相似度排序
    results.sort(key=lambda r: r.similarity, reverse=True)
    
    return results[:limit]
```

---

## 4. 索引优化

### 4.1 标签索引

```python
class TagIndex:
    def __init__(self):
        self._tag_to_keys: dict[str, set[str]] = defaultdict(set)
        self._key_to_tags: dict[str, set[str]] = {}
    
    def add(self, key: str, tags: list[str]) -> None:
        """添加索引"""
        # 移除旧标签
        if key in self._key_to_tags:
            for tag in self._key_to_tags[key]:
                self._tag_to_keys[tag].discard(key)
        
        # 添加新标签
        self._key_to_tags[key] = set(tags)
        for tag in tags:
            self._tag_to_keys[tag].add(key)
    
    def get_by_tag(self, tag: str) -> set[str]:
        """获取标签对应的所有键"""
        return self._tag_to_keys.get(tag, set())
```

### 4.2 全文索引

```python
class FullTextIndex:
    def __init__(self):
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
    
    def index(self, key: str, text: str) -> None:
        """建立全文索引"""
        # 分词
        words = self._tokenize(text)
        
        # 添加到倒排索引
        for word in words:
            self._inverted_index[word].add(key)
    
    def search(self, query: str) -> set[str]:
        """搜索"""
        query_words = self._tokenize(query)
        
        if not query_words:
            return set()
        
        # 取所有词的交集
        result = self._inverted_index[query_words[0]].copy()
        for word in query_words[1:]:
            result &= self._inverted_index[word]
        
        return result
```

---

## 5. 使用示例

### 5.1 标签检索

```python
from intentos import create_memory_manager

manager = await create_and_initialize_memory_manager()

# 设置带标签的记忆
await manager.set_long_term(
    key="doc:1",
    value="文档 1 内容",
    tags=["doc", "important"],
)
await manager.set_long_term(
    key="doc:2",
    value="文档 2 内容",
    tags=["doc", "archive"],
)

# 按标签检索
entries = await manager.get_by_tag("doc")
print(f"找到 {len(entries)} 篇文档")

entries = await manager.get_by_tag("important")
print(f"找到 {len(entries)} 篇重要文档")
```

### 5.2 全文搜索

```python
# 搜索包含关键词的记忆
results = await manager.search("销售报告")

print(f"找到 {len(results)} 条结果:")
for r in results:
    print(f"  {r.key}: {r.value[:50]}...")
```

### 5.3 组合搜索

```python
# 先按标签过滤，再全文搜索
entries = await manager.get_by_tag("report")

results = []
for entry in entries:
    if "销售" in str(entry.value):
        results.append(entry)

print(f"找到 {len(results)} 篇销售相关报告")
```

---

## 6. 总结

记忆检索的核心功能：

1. **标签检索**: 快速分类查找
2. **全文搜索**: 关键词匹配
3. **语义搜索**: 理解含义
4. **索引优化**: 提高检索速度

---

**下一篇**: [过期策略](04-expiry-policy.md)

**上一篇**: [分布式记忆同步](02-distributed-sync.md)
