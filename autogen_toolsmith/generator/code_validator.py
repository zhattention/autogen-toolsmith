import io
import os
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Tuple, Union

import pytest

class CodeValidator:
    """Validator for generated code."""
    
    @staticmethod
    def validate_syntax(code: str) -> bool:
        """Check if the code has valid Python syntax.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code has valid syntax, False otherwise.
        """
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            return False
    
    @staticmethod
    def validate_security(code: str) -> Tuple[bool, str]:
        """Check if the code has potential security issues.
        
        Args:
            code: The code to validate.
            
        Returns:
            Tuple[bool, str]: A tuple of (is_safe, reason).
        """
        # This is a very basic check and should be expanded for production use
        import re
        dangerous_patterns = [
            (r"os\.system\(", "Direct system command execution"),
            (r"subprocess\.", "Subprocess execution"),
            (r"eval\(", "Code evaluation"),
            (r"exec\(", "Code execution"),
            (r"__import__\(", "Dynamic imports"),
            (r"open\(.+,\s*['\"]w['\"]", "File writing")
        ]
        
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, code):
                return False, f"Security issue: {reason}"
        
        return True, ""
    
    @staticmethod
    def run_tests(tool_file: Union[str, Path], test_file: Union[str, Path]) -> Tuple[bool, str]:
        """Run tests for the generated tool.
        
        Args:
            tool_file: Path to the tool file.
            test_file: Path to the test file.
            
        Returns:
            Tuple[bool, str]: A tuple of (passed, test_output).
        """
        tool_file_path = Path(tool_file)
        test_file_path = Path(test_file)
        
        if not tool_file_path.exists():
            return False, f"Tool file not found: {tool_file_path}"
        
        if not test_file_path.exists():
            return False, f"Test file not found: {test_file_path}"
        
        # Add the tool file's directory to the Python path
        tool_dir = tool_file_path.parent
        sys.path.insert(0, str(tool_dir))
        
        try:
            # Capture the output from pytest using a temporary file
            import tempfile
            import os
            
            # Create a temporary file to capture pytest output
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
                temp_file_path = temp_file.name
            
            try:
                # Run pytest with output redirected to the temporary file
                # -v: verbose, --no-header: remove header, --no-summary: remove summary
                # -s: don't capture stdout/stderr (let it go to our file)
                result = pytest.main([
                    "-vvs",  # Very verbose, don't capture stdout/stderr
                    f"--tb=long",  # Long traceback format
                    f"--capture=tee-sys",  # Capture output and also show it
                    f"--junitxml={temp_file_path}.xml",  # Save results in JUnit XML format
                    str(test_file_path)
                ])
                
                # Read the captured output from the temporary file
                full_output = ""
                
                # Try to read the JUnit XML file for structured test results
                try:
                    tree = ET.parse(f"{temp_file_path}.xml")
                    root = tree.getroot()
                    
                    # Extract test case results
                    for testcase in root.findall('.//testcase'):
                        test_name = testcase.get('name')
                        class_name = testcase.get('classname')
                        
                        # Check if the test failed
                        failure = testcase.find('failure')
                        error = testcase.find('error')
                        
                        if failure is not None:
                            full_output += f"\nFAILED: {class_name}::{test_name}\n"
                            full_output += f"Reason: {failure.get('message')}\n"
                            full_output += f"{failure.text}\n"
                            full_output += "-" * 60 + "\n"
                        elif error is not None:
                            full_output += f"\nERROR: {class_name}::{test_name}\n"
                            full_output += f"Reason: {error.get('message')}\n"
                            full_output += f"{error.text}\n"
                            full_output += "-" * 60 + "\n"
                except Exception as xml_error:
                    # If we can't parse the XML, just note it
                    full_output += f"Note: Could not parse detailed test results: {str(xml_error)}\n"
                
                # Capture stdout/stderr directly as well
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()
                
                # Run the tests again with output redirection to get console output
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    pytest.main(["-vvs", str(test_file_path)])
                
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                # Add the console output to our full output
                if not full_output.strip():  # If we didn't get anything from XML
                    full_output = stdout_output + "\n" + stderr_output
                
                # Pytest exit codes: 0 = success, 1 = tests failed, 2 = errors, others = other errors
                success = result == 0
                
                # Create a detailed message with the exit code and full output
                message = f"Tests {'passed' if success else 'failed'} with exit code {result}\n\n"
                message += "=== Test Output ===\n"
                message += full_output
                
                return success, message
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_file_path)
                    if os.path.exists(f"{temp_file_path}.xml"):
                        os.unlink(f"{temp_file_path}.xml")
                except Exception:
                    pass  # Ignore cleanup errors
                
        except Exception as e:
            return False, f"Test execution error: {str(e)}\n{traceback.format_exc()}"
        finally:
            # Remove the directory from the Python path
            if str(tool_dir) in sys.path:
                sys.path.remove(str(tool_dir))

    def validate_tool(self, code: str) -> bool:
        """Validate the tool code.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validate_syntax(code):
            return False
        
        # Check security
        is_safe, _ = self.validate_security(code)
        if not is_safe:
            return False
        
        return True
        
    def validate_test(self, code: str) -> bool:
        """Validate the test code.
        
        Args:
            code: The code to validate.
            
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Check syntax
        if not self.validate_syntax(code):
            return False
        
        # Check security
        is_safe, _ = self.validate_security(code)
        if not is_safe:
            return False
        
        return True 