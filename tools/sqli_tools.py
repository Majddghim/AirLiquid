import re

class SQLInjectionTools:
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize user input to prevent SQL injection."""
        # Replace single quotes with double single quotes to escape them in SQL
        sanitized = input_string.replace("'", "''")
        return sanitized

    @staticmethod
    def is_suspected_injection(input_string):
        """Check if input contains suspicious SQL injection patterns."""
        # Define common SQL injection patterns (this is a simple example)
        injection_patterns = [
            r"(--|#)",  # Comments in SQL
            r"(\b(OR|AND|SELECT|UNION|INSERT|DELETE|DROP|UPDATE)\b)",  # SQL keywords
            r"(\b0x[0-9A-Fa-f]+\b)",  # Hexadecimal literals
            r"(';|--|/\*|\*/|\b--\b)"  # Various SQL injection tricks
        ]

        for pattern in injection_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True
        return False