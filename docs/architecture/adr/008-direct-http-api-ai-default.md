# ADR 008: Direct HTTP API 作默认 AI backend(部分反转 ADR-002)

## Status

Accepted — 部分反转 ADR-002(「不内置 SDK」决策)。

## Context

ADR-002 选择外部 AI CLI 作唯一 transport,理由:不绑定 provider / 不管理
API key / 无 SDK 版本耦合。`codeindex init` 默认 seed
`ai_command = 'claude -p "{prompt}" --model haiku --allowedTools "Read"'`。

2026 年中 Anthropic 大范围封号,`claude` CLI 对大量用户失效。codeindex 默认
AI 路径一夜不可用,且 codeindex 侧无法修(依赖外部账号)。ADR-002 的前提
(claude CLI 稳定可用)失效。

## Decision

加内置 OpenAI 兼容 HTTP client(httpx,**非 vendor SDK**)作**默认** AI
backend,DeepSeek(`deepseek-chat`)作 seed provider。外部 CLI 路径
(`ai_command`)**保留**作显式 escape hatch。

Precedence(每个 call site,`invoker.resolve_ai_backend`):
`ai_command`(CLI)> `ai.api_key`(API)> error。已用 `ai_command` 的用户
零行为变化。

`ai.api_key` 解析:env `CODEINDEX_AI_API_KEY`(provider 无关,主)优先,`DEEPSEEK_API_KEY`(backcompat)次,yaml `ai.api_key` fallback。
(`AIConfig.resolved_api_key`)。

## 反转 ADR-002 哪些

- 「不内置 SDK」:**部分反转**。默认路径加内置 HTTP client(httpx)。
- 「不管理 API key」:**反转**(API 路径)。key 经 env 优先,yaml fallback。

## 保留 ADR-002 哪些

- **CLI 路径不删**。用户若有可用 claude/opencode/gemini CLI,设
  `ai_command` 继续用。
- **无 vendor SDK**。用 httpx 打 OpenAI 兼容 `/chat/completions`,非
  openai/anthropic SDK。换 provider 只改 `base_url`,无 SDK 版本耦合。

## Consequences

+ 默认路径设 `CODEINDEX_AI_API_KEY` 即用(out-of-box)。
+ 现有 `ai_command` 用户零变化。
+ 复用 GH-97 transient retry 框架(`_retry_transient`,两 backend 共享;
  HTTP 429/5xx/timeout/connection error 复用现有 `_TRANSIENT_ERROR_PATTERNS`,
  零新 pattern)。401/402/403 非 transient → fast-fail(避免 hammer 坏 key)。
- 新核心依赖:httpx(~300KB,lazy import,非 AI 用户零 import 成本)。
- 用户需管理 API key(缓解:env 优先于 yaml;template 把 `api_key:` 注释掉)。

## 为什么 seed DeepSeek

OpenAI 兼容 API、低成本、广可用 — Anthropic 账号可用性不确定期间的稳定
默认。`base_url` / `model` 可配;**非 DeepSeek lock-in**。换 OpenAI / 别的
兼容 provider 只改 `ai.base_url` + `ai.model`。

## Scope notes

- 核心路径(`scan --ai` / `scan-all --ai`)走 `invoke_ai(config)` dispatch
  (cli_scan.py + semantic_extractor + docstring_processor 全 reroute)。
- `init --yes`(非交互)seed `ai:` section;`init` 交互 wizard 的 Step 6
  (backend 选择)重构 deferred — wizard 选 "no CLI" 仍得 `ai:` section,
  选 CLI 仍得 `ai_command`(过渡可接受,follow-up 改 wizard 问 backend)。

## References

- [ADR-002](002-external-ai-cli-integration.md)(被部分反转)
- GH #97(transient retry 框架,两 backend 复用)
- CHANGELOG v0.17.0(「agent-CLI stays the only transport」— 现为两 backend 之一)
