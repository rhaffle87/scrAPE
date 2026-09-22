"""
tests/storage/test_cas_key_validation.py

Adversarial property and fuzz testing for Content-Addressable Storage (CAS) key validation (AC2.3).
Proves that validate_cas_key() only accepts canonical 64-char lowercase hex SHA-256 strings
and rejects all directory traversal payloads, uppercase hex, invalid lengths, and control chars.
"""

import hashlib
import random
import string
import pytest
from common.security import validate_cas_key


class TestCASKeyValidation:
    """AC2.3: CAS key validation must reject non-conforming inputs and traversal attempts."""

    @pytest.mark.parametrize(
        "valid_key",
        [
            hashlib.sha256(b"hello world").hexdigest(),
            hashlib.sha256(b"").hexdigest(),
            hashlib.sha256(b"scrAPE v0.30.0 cloud cas sync").hexdigest(),
            "0" * 64,
            "f" * 64,
            "0123456789abcdef" * 4,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ],
    )
    def test_valid_cas_keys_accepted(self, valid_key):
        """Valid 64-character lowercase hex strings must return unchanged."""
        assert validate_cas_key(valid_key) == valid_key

    @pytest.mark.parametrize(
        "traversal_payload",
        [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "../../../../cas/00/11/22",
            "%2e%2e/%2e%2e/secret.json",
            "cas/../../00/11/22",
            "..",
            "../",
            "..\\",
            "../" * 32,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852/etc",
            "/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\\",
        ],
    )
    def test_path_traversal_payloads_rejected(self, traversal_payload):
        """Directory traversal attempts in CAS key must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CAS key"):
            validate_cas_key(traversal_payload)

    @pytest.mark.parametrize(
        "invalid_chars",
        [
            "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",  # uppercase
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85G",  # 'G' is non-hex
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85z",  # 'z' is non-hex
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85-",  # '-' symbol
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85_",  # '_' symbol
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85.",  # '.' symbol
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8\x00\x00",  # null byte
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8\n\n",  # newline
        ],
    )
    def test_invalid_characters_rejected(self, invalid_chars):
        """Uppercase hex, symbols, control chars, and non-hex characters must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CAS key"):
            validate_cas_key(invalid_chars)

    @pytest.mark.parametrize(
        "wrong_length",
        [
            "",
            "a",
            "a" * 32,  # MD5 length
            "a" * 40,  # SHA-1 length
            "a" * 63,  # 1 char short
            "a" * 65,  # 1 char long
            "a" * 128,  # SHA-512 length
        ],
    )
    def test_wrong_length_rejected(self, wrong_length):
        """Strings not exactly 64 characters in length must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CAS key"):
            validate_cas_key(wrong_length)

    @pytest.mark.parametrize(
        "bad_type",
        [
            None,
            123456789,
            b"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
            {"key": "value"},
        ],
    )
    def test_non_string_types_raise_value_error(self, bad_type):
        """Non-string inputs must raise ValueError."""
        with pytest.raises(ValueError, match="CAS key must be a string"):
            validate_cas_key(bad_type)

    def test_fuzz_corpus_mutation(self):
        """
        Fuzz testing with 250 programmatic mutations (insertions, deletions, substitutions,
        special characters, path separators). Assert that only canonical 64-char lowercase hex passes.
        """
        rng = random.Random(42)  # Seed for reproducibility
        canonical = hashlib.sha256(b"seed").hexdigest()
        assert len(canonical) == 64

        chars_to_inject = string.punctuation + string.ascii_uppercase + "ghijklmnopqrstuvwxyz\x00\r\n\t "

        for _ in range(250):
            mutation_type = rng.choice(["insert", "delete", "replace", "prefix", "suffix"])
            mutated = list(canonical)
            idx = rng.randint(0, len(mutated) - 1)
            bad_char = rng.choice(chars_to_inject)

            if mutation_type == "insert":
                mutated.insert(idx, bad_char)
            elif mutation_type == "delete":
                del mutated[idx]
            elif mutation_type == "replace":
                mutated[idx] = bad_char
            elif mutation_type == "prefix":
                mutated = [bad_char] + mutated
            elif mutation_type == "suffix":
                mutated = mutated + [bad_char]

            payload = "".join(mutated)
            # If the mutation somehow produced a valid 64-char lowercase hex string, it would pass,
            # but our injected chars are non-hex/uppercase/separators or alter the length != 64.
            with pytest.raises(ValueError):
                validate_cas_key(payload)
