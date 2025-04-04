#!/usr/bin/env python3
"""Test file with dummy secrets to test the pre-push hook."""

# API Keys (these are fake but should trigger detection)
API_KEY = "sk_live_51LzUQHK8tQhPM6TyumgmeyV8cZ"
STRIPE_SECRET_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
AWS_API_KEY = "AKIAIOSFODNN7EXAMPLE"

# Database credentials
DB_PASSWORD = "super_secure_password123!"
DATABASE_CONNECTION = "postgresql://admin:verystrongpassword@localhost:5432/database"

# OAuth and access tokens
GITHUB_TOKEN = "ghp_kBHjU8LoNSQK6ugMvp7jSavHhXsZG40jzzmM"
OAUTH_TOKEN = "ya29.a0AfB_byAK1qr4xVXM-OmII_W9nkQh9sdJ7TLcpyoNs"

# Private key (this is a fake one)
PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxzYuc1RV+rcbAHmlJv6GcA8hPQQhHvQAYPnrGcwwPFOVKUJA
hvUKicS5ZBvpk+kfL5NzjWNUw+NFnbPZ/F7ykgVx3Ps3QJUQwt5OCaAM4H+kYF0d
djQQK5GL3+t4Q7ej2yQe+jkDUjWdvmWGnAi/0nCoq/wjcL7mxpSm7H56jd1vjiQu
8IF1ni7JGP8MZ4xtU3/yoK1hGvl3uY+dYa3pyXj5S/9tPgDd5JF2lXLKY7BnTXda
gSxJE+wl1ET8tLT+zk2K8cPRUTm9/wOYJJCj0+6Ld5PGTz9/qZ0QKrnG7GZqUGTK
KuA7NBnNTEBsF2lGizTcm5+0o5qYeULrV4K6XQIDAQABAoIBAQDG0DpkTTnPiQbO
q5lQkLQJPcCCLmRmVNWbDQZuKjZzRwlEfW1ImSYkFhyKVX8YfFSQn+T3W/dUWwlM
TXwNwPbLH0uJ+/0kd9o8BAICvUh7XsLy/RXlDnzQFLe3F9UJbdF/tNt0zc6vFILO
VGbv/JVeKIAWuGHXNMGrCcRHYLmPHgYRL32KPsbgM3iYmRWU0QkSUzZEaSkLKF3B
k0zGE2+KUWDlDPhc9TvE07lLJwtYbDjBUwTHCAtgRjPQ/k4aJQ3MbVG8KfSN3Tyl
4zJrr32QXnRV+Lmty6j0TXWZx7xO7IJaKvt8UE1oWQIwOHt2i71g4MXAxY4+v7Hv
5zHu7QjBAoGBAOZOKNS2KHh3my9GFgEZUQvO5gPz1XhdWtwb+DHO7A51oQpwtYXZ
bDxrYkYjYTvMCTnFbMbGQ9owVYm6cKJJN8vGm3AcwHjqYUCQmAFmZPMcx/EAqK8R
V7W5W+crGLaWTKFLpydaqCJO4YH7o7+rGPLu3ARLR8l9vJ+XPrpIAXutAoGBAN2Y
u0WWSHg9EYKnbYUjjYZAl+Ve8W5XS3mXZ7m5QBj9D+cA8xby8SD1ak7gxNKwT6Kc
vgaf3NyILUlDrPqWGo3P8nKg4mihsVNF5a8Ch4RV2IRRF2a+5JpiBEHQdR5+dHYK
KWWKQQXDECnWbIMv/hZaFtXtXK6xjfzPlQoGfODhAoGAW+41S1oFvxLkrgOJHNbj
Lv6MjDQN5qvvA1MgpKy9uGXsUi/TbbA8YqHb9WdgsSNXkWz+wJHxlJO+Qs0h7sK7
lXaW3K7c+g+WJrRDb+RhCZ0xOKMZrDX1cWXreLMB3RDM0JgfJUMzGYR2jcMjXRdl
XZ4dVY2E+QVdVE/O+/F1zIECgYEAylLfwJvnUUPjR1Gb9ki+TOXoQnhqnz1BMN6m
pHpZwAMOsTcZQ4nwcbTEVHMXlDTnWzs5QEjljzbpHIgrm5y9+VKcyK5s/LC8nFnc
G68zFypv7XRDJr/QYjY3fXMJ2B6fOQg6yI5L8qbbYMDjVpMNJKD+ZGmHjQVL06QO
/t0sHiECgYBQkfSxQjGk0JcVc483nx6yrWN9ZBDrm2+4y5cjRqhY3HBP/+QUerIX
dYnzRF+K/aOS0FbMk0Kyz8DXzXLjuDpR+IP8e2ozjwLQxfwST3M3ZaOdFtDvVw3S
aWvYbCbG7JqjMEkO3nBycMHNMV8gPQ9HaPfwOcpIKbX5H1NUZ2RiLQ==
-----END RSA PRIVATE KEY-----
"""

# JWT token
JWT_SECRET = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# This shouldn't trigger detection (regular variable)
regular_variable = "This is just a normal string"

def main():
    """Print some of the secrets (for testing purposes only)."""
    print(f"API Key: {API_KEY[:5]}...")
    print(f"Database Password: {DB_PASSWORD[:5]}...")
    
if __name__ == "__main__":
    main() 