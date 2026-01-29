# CORE_GENESIS Verifier (Sealed v1.1)

This folder contains the deterministic, stdlib-only verifier script for a pinned “Core Genesis Capsule” on Windows.

## Scheduled Task (robust)

Use an explicit Python interpreter path:

```bat
schtasks /Create /F ^
  /TN "CORE_GENESIS_Verifier" ^
  /TR "\"C:\Path\To\Python\python.exe\" \"C:\Governance\CoreGenesis\verify_core_genesis_capsule.py\"" ^
  /SC HOURLY ^
  /MO 1 ^
  /ST 00:07
```

## Pin + Sign (bootstrap)

1) Write the pinned hash file:

- `C:\Governance\CoreGenesis\pinned_capsule_hash.txt`

2) Create detached signature for the pinned hash file:

```bat
gpg --homedir "C:\Governance\CoreGenesis\gnupg_home" --batch --yes ^
  --detach-sign --armor ^
  --output "C:\Governance\CoreGenesis\pinned_capsule_signature.asc" ^
  "C:\Governance\CoreGenesis\pinned_capsule_hash.txt"
```

3) Verify once manually:

```bat
gpg --homedir "C:\Governance\CoreGenesis\gnupg_home" --batch --yes ^
  --verify "C:\Governance\CoreGenesis\pinned_capsule_signature.asc" ^
  "C:\Governance\CoreGenesis\pinned_capsule_hash.txt"
```
