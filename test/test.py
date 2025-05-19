
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxzYuc1RV+rcbAHmlJv6GcA8M+/NzZp0qQAGh7M12Bqokwu+9
OuLxhCGXyDYKBywDQgBsna5H1QDyms4hL3aYRqKXA+tF9iYJJ4H9ayDCNHQCUQHU
ykSICOZj5iNjRaKE1ptUH9iXDPgYlRoR1l3h02CQXX0hL6ZzgfIz2qqK1J5x8iGm
km+IpUbvl17M+CR+w8yj7Jah9WF2qdtRQmQj1PjfPAT1aq8ew7l4qEqVKoVUelyI
HX/dCJRMO4ky5p7g3XAgl8pP+2gqnbEfKCZJ3+XCiOlQtA1GGFe/HOmfAMihGxon
z+OUhA3l+P1i0/fxTLOGlqN10ZIpPdz7FBtH6wIDAQABAoIBAQC5OMjrrF/Iixxt
X0SdUdXLFEqmjwzfwNkWp0ueLgWDFpGgbhUxpBl+EQmbB6g/b8T6Lf5o2gPNGrfN
sxmPfTtUXMVuGHT6hqKP3FP9Ll228bGdlLd7CbMZ5N0/xqw9mHcjOwKCYGV0Rh5E
3nVGJUkKdVXUlA8JnkHGVQxzHwqQdxme7OFM1XPkDvnkf+lSZVUDIqA6IQKALOrx
SVfhGEv8cUzJAIgNjqCxGXL51I39lJRSEsl9Mr+B2V673iPFiAcJCXwTnFXwBBWk
lmM34J+MsTgPevz5W65mTGTKIQB6PELV8LIZVQkPNLLnwlCpZaPGHPgV/C+Wl1iy
oOGYHHKBAoGBAP3bX7fbIzk7p0jmNq7wGWJXLCpgyNM/I9Zl6YJG2nDYYr9K2FUb
rcym65LF7UOLn3RU7Z2XVG+aEhfG7JFzWQUVINHMh9jNmM3MPYZ124zf+Vj7Qk6o
gg+Z8YJHUePjJmrhU+4jpCdGlm/n6g0BdVJxm9+5vAJGkfyxGWvGXw7bAoGBAMjQ
tIzJQzw7+ZwYhRYQXjCwM0YRs9Hy5JH5QgHrrRr1pLOtCFRp9g7b+l8WzQZNRbsu
MbQArj5BmNxfTHNn9CXNr/r0SmhZdTH+VoD1ZiMm+gH6M+lXyJ6WWbLLYsZpRsQu
DfS5GVoQCOiKKvWVYWxT81yjdcC8h3DBpJa7EQJBAoGBAN999TjqQioDGnrS/8Ht
DBNBxnlk9aZpSQWY0JqS5Fk7WhCvRsQY3bxkIKXxCHKwTW6vdBOVltoWSXyiAlPE
FZYwNsmUXYXY7ECQgedsvKS5Rj1gCcve3TcdfDHfuiPX0/G1s1iVB4l2LAOwPP5M
hOhS7JnmKpf+uOLxWDJl7ZhvAoGAb9zCIMuJQqfKEGJ7c841YG9QLjmiLKYUocBK
9PUWzHeSir1nFpIxQIP+F5QNfYf8ial9YEYs5jLySYQX48+JZk/23IqdQbLQ8aoD
rGJIgJXIUbqxVH2E6MdLtoA5OYL5YPrZ/NjUQe4uZGNcXmm27MRZXQe/XrLHzfdG
GRRYzEECgYA7CnEJp8mhAQTqX/EsMXkMGYJ2RmKhQXsJcJXRDyfElEgzADTChY51
c0vWPSA6RF8vPm8b6Q7sJbLJFVmV/K7jLfLhBpIXz+3kNJtP+MOH2XuJl/Jr/EPF
m5UtCLlHPMqYfeO96o/+5UffRTlkPQvBdg+jHOf4+BVhLcGcLiBBQQ==
-----END RSA PRIVATE KEY-----"""

# Credit card numbers
TEST_CC_VISA = "4111 1111 1111 1111"
TEST_CC_AMEX = "3714 496353 98431"

# Simple authentication examples
username = "root"
password = "password123"

def connect_to_api():
    """Simulate connecting to an API with the secret key."""
    headers = {"Authorization": f"Bearer {api_key}"}
    return headers

def connect_to_database():
    """Simulate connecting to a database."""
    connection_string = f"mysql://{DB_USERNAME}:{DB_PASSWORD}@localhost:3306/testdb"
    return connection_string

# JWT token
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

class SecretManager:
    """Class that manages various secrets."""
    
    def __init__(self):
        self.github_token = "github_pat_11AAJX5KI0BL9eQ8p2b2_I"
        self.encryption_key = "c29tZXJhbmRvbWVuY3J5cHRpb25rZXk="
    
    def get_aws_credentials(self):
        """Return AWS credentials."""
        return {
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }
    
     def get_aws_credentials(self):
        """Return AWS credentials."""
        return {
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
