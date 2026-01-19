# ADR 002: 外部 AI CLI 集成策略

## 状态
已采纳 (Accepted)

## 背景
codeindex 需要调用 AI 来生成高质量的代码文档。主要考虑以下方案：

1. **内置 AI SDK**: 直接集成 Anthropic/OpenAI SDK
2. **外部 AI CLI**: 调用用户本地的 AI CLI 工具
3. **API Gateway**: 搭建中间代理服务

## 决策
采用 **外部 AI CLI** 调用策略。

## 理由

### 优势
1. **灵活性**: 用户可以使用任何 AI CLI（claude, opencode, gemini 等）
2. **无 API 密钥管理**: 不需要在工具中存储敏感信息
3. **用户选择权**: 用户可以选择喜欢的 AI 提供商
4. **降低依赖**: 不绑定特定 AI SDK 版本
5. **简化部署**: 不需要处理 API 限流、重试等复杂逻辑

### 劣势
1. **需要用户预先安装**: 用户必须安装并配置 AI CLI
2. **错误处理复杂**: 不同 CLI 的输出格式不同
3. **性能开销**: 多一层进程调用

### 为什么不内置 SDK
- 强制依赖特定 AI 提供商
- 需要管理 API 密钥
- 版本耦合，难以升级

### 为什么不用 API Gateway
- 增加系统复杂度
- 需要额外的部署和维护

## 实现细节

### 配置格式
```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
```

### Prompt 注入
通过字符串替换 `{prompt}` 占位符。

### 超时控制
默认 120 秒，可配置：
```yaml
ai_timeout: 120  # seconds
```

### Fallback 模式
如果没有 AI CLI，提供基础文档生成：
```bash
codeindex scan ./src --fallback
```

### 安全考虑
- Prompt 内容进行 shell 转义
- 不执行来自 AI 的代码
- 输出长度限制（防止内存溢出）

## 后果

### 积极影响
- 用户可以自由选择 AI 工具
- 不依赖特定 AI 提供商
- 简化了工具的部署和维护

### 消极影响
- 用户需要额外配置 AI CLI
- 不同 AI 的输出质量可能不一致

## 替代方案（未来可能）
如果社区强烈需求，可以提供 Plugin 系统：
```python
# 插件接口
class AIProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

# 内置插件
providers = {
    'anthropic': AnthropicProvider,
    'openai': OpenAIProvider,
}
```

## 参考
- [Claude CLI](https://github.com/anthropics/claude-cli)
- [OpenAI CLI](https://github.com/openai/openai-python)
