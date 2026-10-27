# Security Vulnerability Audit - PyStreamPDF

**Audit Date:** 2026-10-27
**Repository:** /Users/georgimullassery/Desktop/Projects/PyStreamPDF
**Total Findings:** 12

## Summary
- **Critical:** 12

## Findings

### 1. [Critical] Insecure Deserialization
- **File:** CHANGELOG.md:268
- **Description:** pickle load/dumps
- **Evidence (Line):** ``pickle.load()` on unverified bytes. Every cache entry is now HMAC-SHA256`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 2. [Critical] Insecure Deserialization
- **File:** docs/AUDIT_FINDINGS.md:20
- **Description:** pickle load/dumps
- **Evidence (Line):** `verified before `pickle.loads()`, cache directory `0700`, key `0600`.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 3. [Critical] Hardcoded Secret
- **File:** examples/mcp_pystreampdf.py:25
- **Description:** Token Assignment detected
- **Evidence (Line):** `#     auth_token="replace-with-a-long-random-token",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 4. [Critical] Insecure Deserialization
- **File:** python/pystreampdf/cache.py:111
- **Description:** pickle load/dumps
- **Evidence (Line):** `used to HMAC-sign every L2 (disk) cache entry, so that `pickle.load()``
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 5. [Critical] Insecure Deserialization
- **File:** python/pystreampdf/cache.py:270
- **Description:** pickle load/dumps
- **Evidence (Line):** ``pickle.load()` ever runs on the bytes; a missing or invalid`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 6. [Critical] Insecure Deserialization
- **File:** python/pystreampdf/cache.py:290
- **Description:** pickle load/dumps
- **Evidence (Line):** `data = pickle.loads(payload)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 7. [Critical] Hardcoded Secret
- **File:** tests/conftest.py:75
- **Description:** Password Assignment detected
- **Evidence (Line):** `ENCRYPTED_PDF_CORRECT_PASSWORD = "correct-horse-battery-staple"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 8. [Critical] Hardcoded Secret
- **File:** tests/conftest.py:76
- **Description:** Password Assignment detected
- **Evidence (Line):** `ENCRYPTED_PDF_WRONG_PASSWORD = "wrong-password-123"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 9. [Critical] Hardcoded Secret
- **File:** tests/conftest.py:88
- **Description:** Password Assignment detected
- **Evidence (Line):** `ownerPassword="owner-secret-password",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 10. [Critical] Hardcoded Secret
- **File:** tests/conftest.py:112
- **Description:** Password Assignment detected
- **Evidence (Line):** `ownerPassword="owner-secret-password",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 11. [Critical] Hardcoded Secret
- **File:** tests/test_mcp_auth.py:23
- **Description:** Token Assignment detected
- **Evidence (Line):** `TOKEN = "test-bearer-token-0123456789"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 12. [Critical] Hardcoded Secret
- **File:** tests/test_mcp_tls.py:30
- **Description:** Token Assignment detected
- **Evidence (Line):** `TOKEN = "test-bearer-token-tls-0123456789"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High
