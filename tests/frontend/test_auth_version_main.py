import pytest
from cli.auth import perform_interactive_login

def test_auth_imports():
    assert callable(perform_interactive_login)
