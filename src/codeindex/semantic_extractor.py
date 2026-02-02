"""
Business Semantic Extractor

Story 4.4: Extract business semantics from directory structure
Task 4.4.5: KISS Universal Description Generator

This module provides universal, language-agnostic code directory descriptions.
No domain knowledge assumptions, no translations, just objective information extraction.
"""
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class DirectoryContext:
    """
    Context information about a directory

    Used to collect information for semantic extraction.
    """
    path: str
    files: List[str]
    subdirs: List[str]
    symbols: List[str]  # Class names, function names
    imports: List[str]  # Import statements


@dataclass
class BusinessSemantic:
    """
    Business semantic information

    Extracted description of what a directory does.
    """
    # Description (e.g., "Admin/Controller: 15 controllers (AdminJurUsers, Permission, ...)")
    description: str
    purpose: str  # Main purpose
    key_components: List[str]  # Key components/features


class SimpleDescriptionGenerator:
    """
    Universal description generator: zero assumptions, zero semantic understanding

    Only extracts objective information, no subjective judgments.
    Supports all languages, all architectures.
    """

    def generate(self, context: DirectoryContext) -> str:
        """
        Generate description: {path} {pattern} ({symbols})

        Strategy:
        1. Extract path context (last 1-2 levels)
        2. Identify symbol pattern (common suffix)
        3. List key symbols (sorted, deduplicated, truncated)
        4. Simple concatenation
        """
        # 1. Path context (keep original, no interpretation)
        path_context = self._extract_path_context(context.path)

        # 2. Symbol pattern analysis
        pattern = self._analyze_symbol_pattern(context.symbols)

        # 3. Extract entity names (remove common suffixes)
        entities = self._extract_entity_names(context.symbols)

        # 4. Sort, deduplicate, truncate
        entities = sorted(set(entities))
        entity_count = len(entities)
        entity_sample = entities[:5]

        # 5. Concatenate description
        if entity_count == 0:
            return f"{path_context} (empty directory)"

        entity_str = ", ".join(entity_sample)
        if entity_count > 5:
            entity_str += f", ... ({entity_count} total)"

        return f"{path_context}: {entity_count} {pattern} ({entity_str})"

    def _extract_path_context(self, path: str) -> str:
        """Extract path context (last 1-2 levels)"""
        parts = Path(path).parts
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        elif len(parts) == 1:
            return parts[-1]
        else:
            return "."

    def _analyze_symbol_pattern(self, symbols: List[str]) -> str:
        """
        Analyze symbol pattern (identify common suffix)

        Universal suffix mapping (language-agnostic):
        - Controller/Controllers → "controllers"
        - Service/Services → "services"
        - Model/Models → "models"
        - Util/Utils/Helper/Helpers → "utilities"
        - Manager/Managers → "managers"
        - Handler/Handlers → "handlers"
        - Provider/Providers → "providers"
        - Repository/Repositories → "repositories"
        - No obvious pattern → "modules/classes/functions"
        """
        if not symbols:
            return "items"

        # Count suffixes
        suffix_count = defaultdict(int)
        common_suffixes = [
            "Controller", "Service", "Model", "Manager",
            "Handler", "Provider", "Repository", "Util",
            "Helper", "Factory", "Builder", "Strategy",
            "Observer", "Listener", "Adapter", "Facade",
            "Test", "Spec"
        ]

        for symbol in symbols:
            for suffix in common_suffixes:
                if symbol.endswith(suffix):
                    suffix_count[suffix] += 1
                    break

        if not suffix_count:
            return "modules"

        # Find most common suffix
        dominant_suffix, count = max(suffix_count.items(), key=lambda x: x[1])

        # If >50% of symbols have this suffix, use plural form
        if count / len(symbols) > 0.5:
            return self._pluralize(dominant_suffix)
        else:
            return "modules"

    def _pluralize(self, suffix: str) -> str:
        """Convert to plural (simple rules)"""
        mapping = {
            "Controller": "controllers",
            "Service": "services",
            "Model": "models",
            "Manager": "managers",
            "Handler": "handlers",
            "Provider": "providers",
            "Repository": "repositories",
            "Util": "utilities",
            "Helper": "helpers",
            "Factory": "factories",
            "Strategy": "strategies",
            "Observer": "observers",
            "Adapter": "adapters",
            "Test": "tests",
            "Spec": "specs",
        }
        return mapping.get(suffix, suffix.lower() + "s")

    def _extract_entity_names(self, symbols: List[str]) -> List[str]:
        """
        Extract entity names (remove common suffixes)

        "AdminJurUsersController" → "AdminJurUsers"
        "UserRoleService" → "UserRole"
        "ProductModel" → "Product"
        """
        entities = []
        common_suffixes = [
            "Controller", "Service", "Model", "Manager",
            "Handler", "Provider", "Repository", "Util",
            "Helper", "Factory", "Builder", "Strategy",
            "Observer", "Listener", "Adapter", "Facade",
            "Test", "Spec"
        ]

        for symbol in symbols:
            entity = symbol
            for suffix in common_suffixes:
                if entity.endswith(suffix):
                    entity = entity[:-len(suffix)]
                    break

            # Remove Interface/Abstract prefix
            if entity.startswith("I") and len(entity) > 1 and entity[1].isupper():
                entity = entity[1:]
            if entity.startswith("Abstract"):
                entity = entity[8:]

            if entity:  # Prevent empty strings
                entities.append(entity)

        return entities


class SemanticExtractor:
    """
    Extract business semantics from directory context

    Supports two modes:
    - Heuristic mode: KISS universal description (fast, offline)
    - AI mode: LLM-powered semantic understanding (accurate, requires API)
    """

    def __init__(self, use_ai: bool = False, ai_command: Optional[str] = None):
        """
        Initialize SemanticExtractor

        Args:
            use_ai: If True, use AI for extraction; if False, use heuristic rules
            ai_command: AI command template (required if use_ai=True)
        """
        self.use_ai = use_ai
        self.ai_command = ai_command

        if use_ai and not ai_command:
            raise ValueError("ai_command is required when use_ai=True")

    def extract_directory_semantic(
        self,
        context: DirectoryContext
    ) -> BusinessSemantic:
        """
        Extract business semantic from directory context

        Args:
            context: Directory context information

        Returns:
            BusinessSemantic with description and purpose

        Strategy:
        - If use_ai=True, call AI for extraction
        - Otherwise, use KISS universal description
        """
        if self.use_ai:
            # AI mode
            return self._ai_extract(context)
        else:
            # Heuristic mode (KISS)
            return self._heuristic_extract(context)

    def _heuristic_extract(self, context: DirectoryContext) -> BusinessSemantic:
        """
        Extract semantic using KISS universal description

        Strategy:
        1. Use SimpleDescriptionGenerator for universal format
        2. No domain assumptions, no translations
        3. Just objective information extraction

        Args:
            context: Directory context

        Returns:
            BusinessSemantic with universal description
        """
        generator = SimpleDescriptionGenerator()
        description = generator.generate(context)

        # Extract entities for key_components
        entities = generator._extract_entity_names(context.symbols)
        key_components = sorted(set(entities))[:10]

        return BusinessSemantic(
            description=description,
            purpose=description,  # Simplified: purpose = description
            key_components=key_components
        )

    def _ai_extract(self, context: DirectoryContext) -> BusinessSemantic:
        """
        Extract semantic using AI (implemented in Day 2)

        Args:
            context: Directory context

        Returns:
            BusinessSemantic with AI-generated description
        """
        # Build the prompt
        prompt = self._build_ai_prompt(context)

        # Invoke AI CLI
        from codeindex.invoker import invoke_ai_cli

        result = invoke_ai_cli(
            command_template=self.ai_command,
            prompt=prompt,
            timeout=30
        )

        if not result.success:
            # Fallback to heuristic if AI fails
            return self._heuristic_extract(context)

        # Parse AI response
        try:
            semantic = self._parse_ai_response(result.output)
            return semantic
        except Exception:
            # Fallback to heuristic if parsing fails
            return self._heuristic_extract(context)

    def _build_ai_prompt(self, context: DirectoryContext) -> str:
        """
        Build AI prompt for semantic extraction

        Args:
            context: Directory context

        Returns:
            Formatted prompt string
        """
        # Prepare context information
        files_str = ", ".join(context.files[:10])  # Limit to first 10
        if len(context.files) > 10:
            files_str += f" (and {len(context.files) - 10} more)"

        subdirs_str = ", ".join(context.subdirs[:10])
        if len(context.subdirs) > 10:
            subdirs_str += f" (and {len(context.subdirs) - 10} more)"

        symbols_str = ", ".join(context.symbols[:20])
        if len(context.symbols) > 20:
            symbols_str += f" (and {len(context.symbols) - 20} more)"

        imports_str = ", ".join(context.imports[:10])
        if len(context.imports) > 10:
            imports_str += f" (and {len(context.imports) - 10} more)"

        prompt = f"""分析以下代码目录的业务语义，提供准确且有意义的描述。

目录路径: {context.path}

文件列表 ({len(context.files)} 个):
{files_str or "无"}

子目录 ({len(context.subdirs)} 个):
{subdirs_str or "无"}

代码符号 ({len(context.symbols)} 个):
{symbols_str or "无"}

导入模块 ({len(context.imports)} 个):
{imports_str or "无"}

请分析这个目录的业务含义，返回 JSON 格式：

{{
  "description": "业务描述（中文，简洁明确，避免通用化描述如'业务模块'）",
  "purpose": "主要用途（中文，说明这个目录的核心职责）",
  "key_components": ["组件1", "组件2", "组件3"]
}}

要求：
1. description 必须反映实际业务含义，不要使用"业务模块"、"代码目录"等通用描述
2. 结合路径名、文件名、符号名推断业务领域
3. 优先识别架构模式（Controller/Model/Service等）和业务领域（User/Product/Order等）
4. key_components 列举2-4个关键组成部分
5. 如果是PHP项目，识别ThinkPHP等框架的特定模式

只返回 JSON，不要其他解释。"""

        return prompt

    def _parse_ai_response(self, response: str) -> BusinessSemantic:
        """
        Parse AI response into BusinessSemantic

        Args:
            response: AI output string

        Returns:
            BusinessSemantic parsed from response

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response
        # AI might wrap JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in AI response")

        # Parse JSON
        data = json.loads(json_str)

        # Validate required fields
        if "description" not in data:
            raise ValueError("Missing 'description' field in AI response")

        return BusinessSemantic(
            description=data.get("description", ""),
            purpose=data.get("purpose", ""),
            key_components=data.get("key_components", [])
        )
