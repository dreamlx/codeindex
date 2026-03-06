"""Tests for test smells detection.

This module tests the detection of test code anti-patterns like:
- Skipped tests (it.skip, xit, @skip, etc.)
- Giant test files (>1000 lines)
"""



from codeindex.test_smells import SmellType, TestSmellDetector


class TestSkippedTestsDetection:
    """Test detection of skipped tests across different frameworks."""

    def test_detect_jest_skip(self, tmp_path):
        """Should detect Jest's it.skip() pattern."""
        test_file = tmp_path / "test.spec.js"
        test_file.write_text(
            """
            describe('User service', () => {
                it('should create user', () => {
                    expect(true).toBe(true);
                });

                it.skip('should delete user', () => {
                    // Skipped test
                });
            });
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert smells[0].type == SmellType.SKIPPED_TEST
        assert smells[0].file_path == test_file
        assert "it.skip" in smells[0].details

    def test_detect_xit(self, tmp_path):
        """Should detect xit() (disabled test in Jest/Mocha)."""
        test_file = tmp_path / "test.spec.ts"
        test_file.write_text(
            """
            xit('should handle edge case', () => {
                expect(false).toBe(true);
            });
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert smells[0].type == SmellType.SKIPPED_TEST
        assert "xit" in smells[0].details

    def test_detect_describe_skip(self, tmp_path):
        """Should detect describe.skip() pattern."""
        test_file = tmp_path / "auth.test.js"
        test_file.write_text(
            """
            describe.skip('Authentication', () => {
                it('should login', () => {});
            });
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert "describe.skip" in smells[0].details

    def test_detect_pytest_skip(self, tmp_path):
        """Should detect pytest @skip decorator."""
        test_file = tmp_path / "test_auth.py"
        test_file.write_text(
            """
            import pytest

            @pytest.mark.skip(reason="Not implemented yet")
            def test_oauth_login():
                assert True

            def test_basic_login():
                assert True
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert smells[0].type == SmellType.SKIPPED_TEST
        assert "@pytest.mark.skip" in smells[0].details

    def test_detect_unittest_skip(self, tmp_path):
        """Should detect unittest @skip decorator."""
        test_file = tmp_path / "test_service.py"
        test_file.write_text(
            """
            import unittest

            class TestService(unittest.TestCase):
                @unittest.skip("Temporarily disabled")
                def test_feature_a(self):
                    pass
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert "@unittest.skip" in smells[0].details or "@skip" in smells[0].details

    def test_detect_junit_ignore(self, tmp_path):
        """Should detect JUnit @Ignore annotation."""
        test_file = tmp_path / "ServiceTest.java"
        test_file.write_text(
            """
            import org.junit.Ignore;
            import org.junit.Test;

            public class ServiceTest {
                @Test
                @Ignore("Broken test")
                public void testFeature() {
                    // Test code
                }
            }
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert "@Ignore" in smells[0].details

    def test_detect_junit5_disabled(self, tmp_path):
        """Should detect JUnit 5 @Disabled annotation."""
        test_file = tmp_path / "UserTest.java"
        test_file.write_text(
            """
            import org.junit.jupiter.api.Disabled;
            import org.junit.jupiter.api.Test;

            @Disabled("Feature not ready")
            class UserTest {
                @Test
                void testUser() {}
            }
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 1
        assert "@Disabled" in smells[0].details

    def test_no_skipped_tests(self, tmp_path):
        """Should return empty list when no skipped tests found."""
        test_file = tmp_path / "test_clean.py"
        test_file.write_text(
            """
            def test_feature_a():
                assert True

            def test_feature_b():
                assert True
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 0

    def test_multiple_skipped_tests(self, tmp_path):
        """Should detect multiple skipped tests in one file."""
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text(
            """
            import pytest

            @pytest.mark.skip
            def test_a():
                pass

            def test_b():
                pass

            @pytest.mark.skip
            def test_c():
                pass
            """
        )

        detector = TestSmellDetector()
        smells = detector.detect_skipped_tests(test_file)

        assert len(smells) == 2


class TestGiantTestFileDetection:
    """Test detection of overly large test files."""

    def test_detect_giant_test_file(self, tmp_path):
        """Should detect test files larger than threshold."""
        from codeindex.parser import ParseResult

        test_file = tmp_path / "test_giant.py"
        # Simulate a giant test file
        parse_result = ParseResult(
            path=test_file,
            file_lines=1500,  # Over 1000 line threshold
            symbols=[],
            imports=[],
        )

        detector = TestSmellDetector()
        smells = detector.detect_giant_test_file(parse_result)

        assert len(smells) == 1
        assert smells[0].type == SmellType.GIANT_TEST_FILE
        assert smells[0].metric_value == 1500

    def test_normal_test_file(self, tmp_path):
        """Should not flag normal-sized test files."""
        from codeindex.parser import ParseResult

        test_file = tmp_path / "test_normal.py"
        parse_result = ParseResult(
            path=test_file,
            file_lines=500,  # Under threshold
            symbols=[],
            imports=[],
        )

        detector = TestSmellDetector()
        smells = detector.detect_giant_test_file(parse_result)

        assert len(smells) == 0

    def test_non_test_file_not_checked(self, tmp_path):
        """Should not check non-test files for giant test file smell."""
        from codeindex.parser import ParseResult

        regular_file = tmp_path / "service.py"  # Not a test file
        parse_result = ParseResult(
            path=regular_file,
            file_lines=2000,  # Large, but not a test file
            symbols=[],
            imports=[],
        )

        detector = TestSmellDetector()
        smells = detector.detect_giant_test_file(parse_result)

        # Should not flag non-test files
        assert len(smells) == 0


class TestTestSmellDetectorIntegration:
    """Integration tests for TestSmellDetector."""

    def test_analyze_file_with_multiple_smells(self, tmp_path):
        """Should detect multiple types of test smells in one analysis."""
        from codeindex.parser import ParseResult

        test_file = tmp_path / "test_problematic.spec.js"
        # Create a file with skipped tests
        test_file.write_text(
            """
            describe('Feature', () => {
                it('works', () => { expect(true).toBe(true); });
                it.skip('broken test', () => {});
                xit('another broken', () => {});
            });
            """ * 200  # Repeat to make it >1000 lines
        )

        # Create ParseResult for the file
        content = test_file.read_text()
        parse_result = ParseResult(
            path=test_file,
            file_lines=len(content.splitlines()),
            symbols=[],
            imports=[],
        )

        detector = TestSmellDetector()
        all_smells = detector.analyze_test_file(test_file, parse_result)

        # Should detect both skipped tests AND giant test file
        assert len(all_smells) >= 2
        smell_types = {s.type for s in all_smells}
        assert SmellType.SKIPPED_TEST in smell_types
        assert SmellType.GIANT_TEST_FILE in smell_types
