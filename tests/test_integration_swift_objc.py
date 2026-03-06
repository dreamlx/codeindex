"""Integration tests for mixed Swift/Objective-C projects (Story 3.5).

This test file validates end-to-end parsing of mixed language projects:
- Parsing both Swift and Objective-C files together
- .h/.m file association accuracy
- Category file handling in mixed projects
- Bridging header integration
- Performance with realistic file counts
- Real-world project structure scenarios

Epic: #23
Story: 3.5
"""

from textwrap import dedent

import pytest

from codeindex.objc_association import (
    calculate_association_accuracy,
    find_objc_pairs,
    merge_objc_results,
    parse_objc_pair,
)
from codeindex.parser import parse_file


class TestMixedProjectParsing:
    """Test parsing mixed Swift/Objective-C projects."""

    def test_parse_swift_and_objc_together(self, tmp_path):
        """Should parse both Swift and Objective-C files in same directory."""
        # Swift file
        swift_file = tmp_path / "ViewController.swift"
        swift_file.write_text(dedent("""
            import UIKit

            class ViewController: UIViewController {
                override func viewDidLoad() {
                    super.viewDidLoad()
                }
            }
        """).strip() + "\n")

        # Objective-C header
        h_file = tmp_path / "AudioManager.h"
        h_file.write_text(dedent("""
            @interface AudioManager : NSObject
            - (void)playSound;
            @end
        """).strip() + "\n")

        # Objective-C implementation
        m_file = tmp_path / "AudioManager.m"
        m_file.write_text(dedent("""
            @implementation AudioManager
            - (void)playSound {
                // Implementation
            }
            @end
        """).strip() + "\n")

        # Parse all files
        try:
            swift_result = parse_file(swift_file)
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # All should parse without errors
        assert swift_result.error is None
        assert h_result.error is None
        assert m_result.error is None

        # Swift should find class
        swift_classes = [s for s in swift_result.symbols if s.kind == "class"]
        assert len(swift_classes) >= 1

        # Objective-C should find class
        objc_classes = [s for s in h_result.symbols if s.kind == "class"]
        assert len(objc_classes) >= 1

    def test_bridging_header_with_swift(self, tmp_path):
        """Should handle bridging header exposing Objective-C to Swift."""
        # Objective-C class
        h_file = tmp_path / "LegacyHelper.h"
        h_file.write_text(dedent("""
            @interface LegacyHelper : NSObject
            - (NSString *)helpMessage;
            @end
        """).strip() + "\n")

        m_file = tmp_path / "LegacyHelper.m"
        m_file.write_text(dedent("""
            @implementation LegacyHelper
            - (NSString *)helpMessage {
                return @"Help!";
            }
            @end
        """).strip() + "\n")

        # Bridging header
        bridging_file = tmp_path / "MyApp-Bridging-Header.h"
        bridging_file.write_text(dedent("""
            #import "LegacyHelper.h"
        """).strip() + "\n")

        # Swift file using Objective-C
        swift_file = tmp_path / "SwiftClass.swift"
        swift_file.write_text(dedent("""
            import Foundation

            class SwiftClass {
                let helper = LegacyHelper()

                func getMessage() -> String {
                    return helper.helpMessage()
                }
            }
        """).strip() + "\n")

        try:
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
            bridging_result = parse_file(bridging_file)
            swift_result = parse_file(swift_file)
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # All should parse
        assert h_result.error is None
        assert m_result.error is None
        assert bridging_result.error is None
        assert swift_result.error is None

        # Bridging header should have import
        assert len(bridging_result.imports) >= 1
        assert any("LegacyHelper" in imp.module for imp in bridging_result.imports)


class TestFileAssociationAccuracy:
    """Test .h/.m file association accuracy."""

    def test_high_association_accuracy(self, tmp_path):
        """Should achieve ≥95% .h/.m association in realistic project."""
        # Create 20 complete pairs (40 files)
        for i in range(20):
            class_name = f"Class{i}"
            h_file = tmp_path / f"{class_name}.h"
            m_file = tmp_path / f"{class_name}.m"

            h_file.write_text(f"@interface {class_name} : NSObject\n@end\n")
            m_file.write_text(f"@implementation {class_name}\n@end\n")

        # Create 1 header-only file (protocol)
        protocol_file = tmp_path / "Protocol.h"
        protocol_file.write_text("@protocol MyProtocol\n@end\n")

        # Find pairs
        pairs = find_objc_pairs(tmp_path)

        # Calculate accuracy
        accuracy = calculate_association_accuracy(pairs)

        # Should have 21 total pairs (20 complete + 1 header-only)
        assert len(pairs) == 21

        # Accuracy should be ≥95% (20/21 = 95.2%)
        assert accuracy >= 95.0

    def test_category_association_accuracy(self, tmp_path):
        """Should achieve ≥90% category association."""
        # Create base classes
        for i in range(10):
            class_name = f"BaseClass{i}"
            h_file = tmp_path / f"{class_name}.h"
            m_file = tmp_path / f"{class_name}.m"
            h_file.write_text(f"@interface {class_name} : NSObject\n@end\n")
            m_file.write_text(f"@implementation {class_name}\n@end\n")

        # Create 9 category pairs (18 files)
        for i in range(9):
            h_file = tmp_path / f"NSString+Util{i}.h"
            m_file = tmp_path / f"NSString+Util{i}.m"

            h_file.write_text(dedent(f"""
                @interface NSString (Util{i})
                - (BOOL)isValid{i};
                @end
            """).strip() + "\n")

            m_file.write_text(dedent(f"""
                @implementation NSString (Util{i})
                - (BOOL)isValid{i} {{
                    return YES;
                }}
                @end
            """).strip() + "\n")

        # Create 1 category header without implementation
        h_file = tmp_path / "NSString+Extra.h"
        h_file.write_text(dedent("""
            @interface NSString (Extra)
            - (NSString *)extra;
            @end
        """).strip() + "\n")

        # Find pairs
        pairs = find_objc_pairs(tmp_path)

        # Should have 10 base class pairs + 9 complete category pairs + 1 header-only category
        # Total = 20 pairs
        assert len(pairs) == 20

        # Calculate accuracy (19 complete / 20 total = 95%)
        accuracy = calculate_association_accuracy(pairs)
        assert accuracy >= 90.0


class TestRealisticProjectStructure:
    """Test realistic mixed project structures."""

    def test_nested_directory_structure(self, tmp_path):
        """Should handle nested directory structure like real apps."""
        # Create realistic directory structure
        controllers_dir = tmp_path / "Controllers"
        controllers_dir.mkdir()

        models_dir = tmp_path / "Models"
        models_dir.mkdir()

        utils_dir = tmp_path / "Utils"
        utils_dir.mkdir()

        # Controllers (Swift)
        (controllers_dir / "MainViewController.swift").write_text(dedent("""
            import UIKit

            class MainViewController: UIViewController {
                override func viewDidLoad() {
                    super.viewDidLoad()
                }
            }
        """).strip() + "\n")

        # Models (Objective-C)
        (models_dir / "User.h").write_text(dedent("""
            @interface User : NSObject
            @property (nonatomic, copy) NSString *name;
            @end
        """).strip() + "\n")

        (models_dir / "User.m").write_text(dedent("""
            @implementation User
            @end
        """).strip() + "\n")

        # Utils (Objective-C categories)
        (utils_dir / "NSString+Validation.h").write_text(dedent("""
            @interface NSString (Validation)
            - (BOOL)isValidEmail;
            @end
        """).strip() + "\n")

        (utils_dir / "NSString+Validation.m").write_text(dedent("""
            @implementation NSString (Validation)
            - (BOOL)isValidEmail {
                return [self containsString:@"@"];
            }
            @end
        """).strip() + "\n")

        # Parse files from each directory
        try:
            swift_result = parse_file(controllers_dir / "MainViewController.swift")
            h_result = parse_file(models_dir / "User.h")
            m_result = parse_file(models_dir / "User.m")
            cat_h = parse_file(utils_dir / "NSString+Validation.h")
            cat_m = parse_file(utils_dir / "NSString+Validation.m")
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # All should parse
        assert swift_result.error is None
        assert h_result.error is None
        assert m_result.error is None
        assert cat_h.error is None
        assert cat_m.error is None

        # Check pair association in models directory
        model_pairs = find_objc_pairs(models_dir)
        assert len(model_pairs) == 1
        assert model_pairs[0].is_complete

        # Check pair association in utils directory
        util_pairs = find_objc_pairs(utils_dir)
        assert len(util_pairs) == 1
        assert util_pairs[0].is_complete

    def test_multiple_classes_per_file(self, tmp_path):
        """Should handle files with multiple class declarations."""
        h_file = tmp_path / "Models.h"
        h_file.write_text(dedent("""
            @interface Person : NSObject
            @property (nonatomic, copy) NSString *name;
            @end

            @interface Address : NSObject
            @property (nonatomic, copy) NSString *street;
            @end

            @interface Company : NSObject
            @property (nonatomic, copy) NSString *companyName;
            @end
        """).strip() + "\n")

        m_file = tmp_path / "Models.m"
        m_file.write_text(dedent("""
            @implementation Person
            @end

            @implementation Address
            @end

            @implementation Company
            @end
        """).strip() + "\n")

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
            merged = merge_objc_results(pair)
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # Should find all 3 classes
        classes = [s for s in merged.symbols if s.kind == "class"]
        assert len(classes) >= 3

        class_names = {c.name for c in classes}
        assert "Person" in class_names
        assert "Address" in class_names
        assert "Company" in class_names


class TestPerformance:
    """Test parsing performance with realistic file counts."""

    def test_parse_many_files_quickly(self, tmp_path):
        """Should parse 50+ files in reasonable time."""
        import time

        # Create 50 Objective-C pairs (100 files total)
        for i in range(50):
            class_name = f"TestClass{i}"
            h_file = tmp_path / f"{class_name}.h"
            m_file = tmp_path / f"{class_name}.m"

            h_file.write_text(dedent(f"""
                @interface {class_name} : NSObject
                - (void)method{i};
                @end
            """).strip() + "\n")

            m_file.write_text(dedent(f"""
                @implementation {class_name}
                - (void)method{i} {{
                    // Implementation {i}
                }}
                @end
            """).strip() + "\n")

        # Measure parsing time
        start_time = time.time()

        try:
            pairs = find_objc_pairs(tmp_path)
            for pair in pairs:
                if pair.header_file:
                    parse_file(pair.header_file)
                if pair.implementation_file:
                    parse_file(pair.implementation_file)
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        elapsed = time.time() - start_time

        # Should parse 100 files in <5 seconds
        assert elapsed < 5.0
        assert len(pairs) == 50


class TestEdgeCases:
    """Test edge cases in mixed projects."""

    def test_mixed_naming_conventions(self, tmp_path):
        """Should handle different naming conventions."""
        # Objective-C style (PascalCase)
        (tmp_path / "AudioManager.h").write_text("@interface AudioManager : NSObject\n@end\n")
        (tmp_path / "AudioManager.m").write_text("@implementation AudioManager\n@end\n")

        # Swift style (also PascalCase but different patterns)
        (tmp_path / "NetworkService.swift").write_text(dedent("""
            class NetworkService {
                func fetch() {}
            }
        """).strip() + "\n")

        # Legacy C-style prefix
        (tmp_path / "ZCYLViewController.h").write_text("@interface ZCYLViewController : NSObject\n@end\n")
        (tmp_path / "ZCYLViewController.m").write_text("@implementation ZCYLViewController\n@end\n")

        try:
            pairs = find_objc_pairs(tmp_path)
            swift_result = parse_file(tmp_path / "NetworkService.swift")
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # Should find all pairs
        assert len(pairs) == 2  # AudioManager + ZCYLViewController

        # Swift should parse
        assert swift_result.error is None

    def test_empty_implementation_files(self, tmp_path):
        """Should handle empty .m files gracefully."""
        h_file = tmp_path / "EmptyClass.h"
        h_file.write_text(dedent("""
            @interface EmptyClass : NSObject
            - (void)someMethod;
            @end
        """).strip() + "\n")

        m_file = tmp_path / "EmptyClass.m"
        m_file.write_text(dedent("""
            @implementation EmptyClass
            @end
        """).strip() + "\n")

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
            merged = merge_objc_results(pair)
        except ImportError as e:
            pytest.skip(f"Parser not installed: {e}")

        # Should still parse
        assert merged.error is None

        # Should have class from header
        classes = [s for s in merged.symbols if s.kind == "class"]
        assert len(classes) >= 1
