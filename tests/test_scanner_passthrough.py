"""Tests for pass-through directory skipping (Epic 19 Story 19.5).

Pass-through directories are those with:
1. No code files of their own (only subdirectories)
2. Exactly one subdirectory (pure pass-through)

This avoids redundant README_AI.md generation in deep directory structures
like Java Maven: src/main/java/com/zcyl/module/
"""

from codeindex.config import Config
from codeindex.scanner import is_pass_through


class TestIsPassThrough:
    """Test the is_pass_through function."""

    def test_no_code_single_subdir_is_passthrough(self, tmp_path):
        """Directory with no code files and single subdir is pass-through."""
        child = tmp_path / "child"
        child.mkdir()
        (child / "code.py").write_text("x = 1\n")

        config = Config(languages=["python"])
        assert is_pass_through(tmp_path, config) is True

    def test_has_code_files_not_passthrough(self, tmp_path):
        """Directory with code files is NOT pass-through (even with single subdir)."""
        (tmp_path / "code.py").write_text("x = 1\n")
        child = tmp_path / "child"
        child.mkdir()

        config = Config(languages=["python"])
        assert is_pass_through(tmp_path, config) is False

    def test_no_code_multiple_subdirs_not_passthrough(self, tmp_path):
        """Directory with multiple subdirs is NOT pass-through (has navigation value)."""
        (tmp_path / "child_a").mkdir()
        (tmp_path / "child_b").mkdir()

        config = Config(languages=["python"])
        assert is_pass_through(tmp_path, config) is False

    def test_no_code_no_subdirs_not_passthrough(self, tmp_path):
        """Empty directory is NOT pass-through (no subdirs)."""
        config = Config(languages=["python"])
        assert is_pass_through(tmp_path, config) is False

    def test_excluded_subdirs_not_counted(self, tmp_path):
        """Excluded subdirectories should not be counted."""
        (tmp_path / "__pycache__").mkdir()
        child = tmp_path / "child"
        child.mkdir()

        config = Config(languages=["python"], exclude=["**/__pycache__/**"])
        assert is_pass_through(tmp_path, config) is True

    def test_non_code_files_ignored(self, tmp_path):
        """Non-code files (e.g., .txt, .md) should not prevent pass-through."""
        (tmp_path / "README.md").write_text("# Readme\n")
        child = tmp_path / "child"
        child.mkdir()

        config = Config(languages=["python"])
        assert is_pass_through(tmp_path, config) is True

    def test_java_extensions_checked(self, tmp_path):
        """Java files should be checked for Java language config."""
        (tmp_path / "Main.java").write_text("public class Main {}\n")
        child = tmp_path / "child"
        child.mkdir()

        config = Config(languages=["java"])
        assert is_pass_through(tmp_path, config) is False


class TestDirectoryTreePassthrough:
    """Test that DirectoryTree skips pass-through directories."""

    def test_java_maven_structure_skips_intermediates(self, tmp_path):
        """Java Maven src/main/java/com/zcyl/gateway/ should skip intermediates."""
        from codeindex.directory_tree import DirectoryTree

        # Create Maven-like structure
        leaf = tmp_path / "src" / "main" / "java" / "com" / "zcyl" / "gateway"
        leaf.mkdir(parents=True)
        (leaf / "GatewayApp.java").write_text("public class GatewayApp {}\n")

        config = Config(
            languages=["java"],
            include=["src/"],
            exclude=[],
        )
        tree = DirectoryTree(tmp_path, config)
        dirs = tree.get_processing_order()

        # Only the leaf directory with code should be processed
        assert len(dirs) == 1
        assert dirs[0] == leaf.resolve()

    def test_python_flat_structure_no_skip(self, tmp_path):
        """Python flat structure - dirs with code files are never skipped."""
        from codeindex.directory_tree import DirectoryTree

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("def main(): pass\n")

        models = src / "models"
        models.mkdir()
        (models / "user.py").write_text("class User: pass\n")

        config = Config(
            languages=["python"],
            include=["src/"],
            exclude=[],
        )
        tree = DirectoryTree(tmp_path, config)
        dirs = tree.get_processing_order()

        # Both directories have code files, neither should be skipped
        resolved_dirs = [d.resolve() for d in dirs]
        assert src.resolve() in resolved_dirs
        assert models.resolve() in resolved_dirs

    def test_dir_with_multiple_subdirs_kept(self, tmp_path):
        """Directory with multiple subdirs has navigation value and is kept."""
        from codeindex.directory_tree import DirectoryTree

        # src/ has no code but 2 subdirs -> navigation value -> kept
        src = tmp_path / "src"
        src.mkdir()

        module_a = src / "module_a"
        module_a.mkdir()
        (module_a / "a.py").write_text("x = 1\n")

        module_b = src / "module_b"
        module_b.mkdir()
        (module_b / "b.py").write_text("y = 2\n")

        config = Config(
            languages=["python"],
            include=["src/"],
            exclude=[],
        )
        tree = DirectoryTree(tmp_path, config)
        dirs = tree.get_processing_order()

        resolved_dirs = [d.resolve() for d in dirs]
        # src/ has 2 children so it should be kept (navigation value)
        assert src.resolve() in resolved_dirs
        assert module_a.resolve() in resolved_dirs
        assert module_b.resolve() in resolved_dirs

    def test_deep_passthrough_chain_all_skipped(self, tmp_path):
        """Multiple levels of pass-through should all be skipped."""
        from codeindex.directory_tree import DirectoryTree

        # com/zcyl/service/impl/ServiceImpl.java
        # com/, zcyl/, service/ are all pass-throughs (1 child, no code)
        impl = tmp_path / "com" / "zcyl" / "service" / "impl"
        impl.mkdir(parents=True)
        (impl / "ServiceImpl.java").write_text("public class ServiceImpl {}\n")

        config = Config(
            languages=["java"],
            include=["."],
            exclude=[],
        )
        tree = DirectoryTree(tmp_path, config)
        dirs = tree.get_processing_order()

        # Only impl/ should be in the processing list
        assert len(dirs) == 1
        assert dirs[0] == impl.resolve()
