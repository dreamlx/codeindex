"""
Business Semantic Extractor

Story 4.4: Extract business semantics from directory structure
Task 4.4.1: Foundation (Day 1-2)

This module extracts meaningful business descriptions from code directories,
replacing generic descriptions like "Module directory" with semantic insights.
"""
from dataclasses import dataclass
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
    description: str        # Business description (e.g., "后台管理系统：用户和权限")
    purpose: str           # Main purpose
    key_components: List[str]  # Key components/features


class SemanticExtractor:
    """
    Extract business semantics from directory context

    Supports two modes:
    - Heuristic mode: Rule-based pattern matching (fast, offline)
    - AI mode: LLM-powered semantic understanding (accurate, requires API)
    """

    def __init__(self, use_ai: bool = False):
        """
        Initialize SemanticExtractor

        Args:
            use_ai: If True, use AI for extraction; if False, use heuristic rules
        """
        self.use_ai = use_ai

        # Heuristic keyword mappings (Chinese + English)
        self.keyword_mappings = {
            "Controller": {
                "description": "控制器目录：处理HTTP请求和业务逻辑路由",
                "purpose": "处理用户请求，调用相应的业务逻辑",
                "components": ["请求处理", "路由分发"]
            },
            "Model": {
                "description": "数据模型目录：封装数据库操作和业务规则",
                "purpose": "管理数据访问层，封装业务数据逻辑",
                "components": ["数据访问", "业务规则"]
            },
            "View": {
                "description": "视图模板目录：前端页面渲染和展示",
                "purpose": "负责前端页面的渲染和用户界面展示",
                "components": ["页面渲染", "模板引擎"]
            },
            "Service": {
                "description": "服务层目录：业务逻辑封装和服务编排",
                "purpose": "封装复杂业务逻辑，提供服务接口",
                "components": ["业务逻辑", "服务编排"]
            },
            "Repository": {
                "description": "数据访问层：数据库操作和查询封装",
                "purpose": "封装数据库访问，提供统一的数据操作接口",
                "components": ["数据查询", "持久化"]
            },
            "Util": {
                "description": "工具类目录：通用辅助功能和帮助方法",
                "purpose": "提供通用的辅助功能和工具方法",
                "components": ["辅助方法", "通用功能"]
            },
            "Helper": {
                "description": "辅助类目录：通用帮助函数和工具方法",
                "purpose": "提供辅助功能和帮助方法",
                "components": ["帮助方法", "工具函数"]
            },
            "Common": {
                "description": "公共模块：共享代码和通用功能",
                "purpose": "提供项目共享的通用功能",
                "components": ["共享代码", "通用模块"]
            },
            "Admin": {
                "description": "后台管理模块：系统管理和配置功能",
                "purpose": "提供系统后台管理功能",
                "components": ["系统管理", "配置管理"]
            },
            "Api": {
                "description": "API接口目录：对外接口和服务端点",
                "purpose": "提供外部API接口和服务",
                "components": ["接口定义", "服务端点"]
            }
        }

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
        1. If use_ai=True, call AI for extraction (not implemented in Day 1)
        2. Otherwise, use heuristic rules based on:
           - Directory path keywords (Controller, Model, etc.)
           - Symbol names (UserController → user-related)
           - File names
        """
        if self.use_ai:
            # AI mode (to be implemented in Day 2)
            return self._ai_extract(context)
        else:
            # Heuristic mode
            return self._heuristic_extract(context)

    def _heuristic_extract(self, context: DirectoryContext) -> BusinessSemantic:
        """
        Extract semantic using heuristic rules

        Strategy (improved - combine path and symbols):
        1. Check if path has architectural keywords (Controller, Model, etc.)
        2. If yes, check symbols for business domain info
        3. Combine architectural + business info for precise description
        4. Otherwise, infer from symbols/files, or fallback

        Args:
            context: Directory context

        Returns:
            BusinessSemantic with heuristic-based description
        """
        path_lower = context.path.lower()

        # Step 1: Check for architectural keywords in path
        arch_keyword = None
        arch_mapping = None

        for keyword, mapping in self.keyword_mappings.items():
            if keyword.lower() in path_lower:
                arch_keyword = keyword
                arch_mapping = mapping
                break

        # Step 2: Get business domain from symbols (if any)
        business_domain = self._extract_business_domain(context)

        # Step 3: Combine architectural + business info
        if arch_keyword and business_domain:
            # Best case: we have both architectural and business context
            # Example: "Controller" + "User" → "用户管理控制器"
            description = f"{business_domain}相关的{arch_mapping['description'].split('：')[0]}"
            purpose = f"处理{business_domain}相关的业务逻辑"
            components = [business_domain, arch_mapping['components'][0]]

            return BusinessSemantic(
                description=description,
                purpose=purpose,
                key_components=components
            )

        # Step 4: If only architectural keyword (no business domain)
        if arch_keyword:
            return BusinessSemantic(
                description=arch_mapping["description"],
                purpose=arch_mapping["purpose"],
                key_components=arch_mapping["components"]
            )

        # Step 5: If only business domain (no architectural keyword)
        if business_domain:
            return BusinessSemantic(
                description=f"{business_domain}相关功能模块",
                purpose=f"处理{business_domain}相关的业务逻辑",
                key_components=[business_domain, "业务逻辑"]
            )

        # Step 6: Infer from file names
        inferred = self._infer_from_files(context)
        if inferred:
            return inferred

        # Step 7: Fallback to generic (but better than "Module directory")
        return self._generic_description(context)

    def _extract_business_domain(self, context: DirectoryContext) -> Optional[str]:
        """
        Extract business domain from symbols (helper method)

        Returns just the domain keyword (e.g., "用户管理", "商品管理")
        not a full BusinessSemantic.

        Args:
            context: Directory context

        Returns:
            Business domain string if found, None otherwise
        """
        if not context.symbols:
            return None

        # Common business domain keywords
        domain_keywords = {
            "user": "用户管理",
            "auth": "认证授权",
            "product": "商品管理",
            "order": "订单处理",
            "payment": "支付",
            "cart": "购物车",
            "role": "角色权限",
            "permission": "权限管理"
        }

        # Check symbols for domain keywords
        symbols_lower = ' '.join(context.symbols).lower()

        for keyword, domain in domain_keywords.items():
            if keyword in symbols_lower:
                return domain

        return None

    def _infer_from_symbols(self, context: DirectoryContext) -> Optional[BusinessSemantic]:
        """
        Infer semantic from symbol names

        Look for patterns in symbol names:
        - UserController, UserModel → user management
        - ProductController → product-related
        - AuthService → authentication

        Args:
            context: Directory context

        Returns:
            BusinessSemantic if inference successful, None otherwise
        """
        if not context.symbols:
            return None

        # Common business domain keywords
        domain_keywords = {
            "user": "用户管理相关功能",
            "auth": "认证和授权功能",
            "product": "商品管理相关功能",
            "order": "订单处理相关功能",
            "payment": "支付相关功能",
            "cart": "购物车相关功能",
            "role": "角色和权限管理",
            "permission": "权限管理功能"
        }

        # Check symbols for domain keywords
        symbols_lower = ' '.join(context.symbols).lower()

        for keyword, description in domain_keywords.items():
            if keyword in symbols_lower:
                return BusinessSemantic(
                    description=f"{description}模块",
                    purpose=f"处理{description}相关的业务逻辑",
                    key_components=[description.replace("功能", ""), "业务逻辑"]
                )

        return None

    def _infer_from_files(self, context: DirectoryContext) -> Optional[BusinessSemantic]:
        """
        Infer semantic from file names

        Args:
            context: Directory context

        Returns:
            BusinessSemantic if inference successful, None otherwise
        """
        if not context.files:
            return None

        # Similar to symbol inference but from file names
        files_str = ' '.join(context.files).lower()

        if "controller" in files_str:
            count = sum(1 for f in context.files if "controller" in f.lower())
            return BusinessSemantic(
                description=f"控制器目录：包含{count}个控制器文件",
                purpose="处理HTTP请求和业务逻辑",
                key_components=["请求处理", "业务调用"]
            )

        if "model" in files_str:
            count = sum(1 for f in context.files if "model" in f.lower())
            return BusinessSemantic(
                description=f"数据模型目录：包含{count}个模型文件",
                purpose="管理数据访问和业务数据",
                key_components=["数据访问", "业务数据"]
            )

        return None

    def _generic_description(self, context: DirectoryContext) -> BusinessSemantic:
        """
        Generate generic but meaningful description

        Args:
            context: Directory context

        Returns:
            BusinessSemantic with generic description
        """
        # Extract directory name from path
        dir_name = context.path.split('/')[-1]

        # Count files and subdirs
        file_count = len(context.files)
        subdir_count = len(context.subdirs)

        if file_count > 0 and subdir_count > 0:
            description = f"{dir_name} 模块：包含{file_count}个文件和{subdir_count}个子目录"
        elif file_count > 0:
            description = f"{dir_name} 模块：包含{file_count}个代码文件"
        elif subdir_count > 0:
            description = f"{dir_name} 目录：包含{subdir_count}个子模块"
        else:
            description = f"{dir_name} 目录"

        return BusinessSemantic(
            description=description,
            purpose="代码组织和模块划分",
            key_components=[dir_name]
        )

    def _ai_extract(self, context: DirectoryContext) -> BusinessSemantic:
        """
        Extract semantic using AI (to be implemented in Day 2)

        Args:
            context: Directory context

        Returns:
            BusinessSemantic with AI-generated description
        """
        # TODO: Implement in Task 4.4.1 Day 2
        raise NotImplementedError(
            "AI extraction not implemented yet. "
            "This will be implemented in Task 4.4.1 Day 2."
        )
