"""Tests for PHP comment extraction (Epic 6, P2, Task 3.1)."""

from textwrap import dedent

from codeindex.parser import parse_file


class TestPHPCommentExtraction:
    """Test PHP PHPDoc comment extraction."""

    def test_extract_phpdoc_comment_from_method(self, tmp_path):
        """Should extract PHPDoc comment from PHP method."""
        # Arrange
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                /**
                 * 幸运抽奖
                 * @param $info
                 * @return array
                 */
                public function ImmediateLotteryDraw($info) {
                    return [];
                }
            }
            '''
            )
        )

        # Act
        result = parse_file(php_file)

        # Assert
        assert not result.error
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert "ImmediateLotteryDraw" in methods[0].name
        assert "幸运抽奖" in methods[0].docstring

    def test_extract_first_line_from_phpdoc(self, tmp_path):
        """Should extract first meaningful line from PHPDoc."""
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                /**
                 * Get user profile
                 * @param int $id User ID
                 * @return array User data
                 */
                public function getProfile($id) {
                    return [];
                }
            }
            '''
            )
        )

        result = parse_file(php_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert "Get user profile" in methods[0].docstring

    def test_extract_phpdoc_with_multiple_lines(self, tmp_path):
        """Should extract PHPDoc with description spanning multiple lines."""
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                /**
                 * This is a long description
                 * that spans multiple lines
                 * @param string $name
                 */
                public function process($name) {
                    // code
                }
            }
            '''
            )
        )

        result = parse_file(php_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        # Should preserve the description part
        assert "This is a long description" in methods[0].docstring

    def test_extract_phpdoc_skip_annotation_lines(self, tmp_path):
        """PHPDoc extraction should skip @param, @return lines."""
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                /**
                 * @param $info
                 * @return array
                 */
                public function noDescription($info) {
                    return [];
                }
            }
            '''
            )
        )

        result = parse_file(php_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        # Should be empty because only @annotations exist
        assert methods[0].docstring == ""

    def test_extract_phpdoc_from_class(self, tmp_path):
        """Should extract PHPDoc comment from PHP class."""
        php_file = tmp_path / "UserModel.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            /**
             * User model for managing user data
             * @package App\\Model
             */
            class UserModel {
                public function save() {}
            }
            '''
            )
        )

        result = parse_file(php_file)

        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) == 1
        assert "User model for managing user data" in classes[0].docstring

    def test_no_phpdoc_returns_empty_string(self, tmp_path):
        """Method without PHPDoc should have empty docstring."""
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                public function undocumented() {
                    return true;
                }
            }
            '''
            )
        )

        result = parse_file(php_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert methods[0].docstring == ""

    def test_single_line_phpdoc_comment(self, tmp_path):
        """Should extract single-line PHPDoc comment."""
        php_file = tmp_path / "TestController.php"
        php_file.write_text(
            dedent(
                '''
            <?php
            class TestController {
                /** Quick action */
                public function quick() {
                    return true;
                }
            }
            '''
            )
        )

        result = parse_file(php_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert "Quick action" in methods[0].docstring
