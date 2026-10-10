# Android release signing setup

One-time setup so tagged releases ship APKs signed with the FaraidFlow
upload key instead of a debug key.

## 1. Create the upload keystore (once)

```bash
keytool -genkeypair -v -keystore faraidflow-upload.jks -keyalg RSA \
  -keysize 2048 -validity 10950 -alias faraidflow
```

On Windows, base64-encode it for the secret step with:

```powershell
certutil -encode faraidflow-upload.jks faraidflow-upload.b64
```

(Get-Content faraidflow-upload.b64 | Select-String -Pattern '^-' -NotMatch
gives the single-line value to paste as the secret.)

Delete `faraidflow-upload.b64` right after pasting the secret value.

## 2. Add the four GitHub secrets

Repo Settings > Secrets and variables > Actions, then add:

| Secret name                | Value                                    |
| -------------------------- | ---------------------------------------- |
| `ANDROID_KEYSTORE_B64`     | base64 of `faraidflow-upload.jks`        |
| `ANDROID_KEYSTORE_PASSWORD`| the keystore password from step 1        |
| `ANDROID_KEY_ALIAS`        | `faraidflow` (or your chosen alias)      |
| `ANDROID_KEY_PASSWORD`     | the key password from step 1             |

Without these secrets the workflow still succeeds — APKs just fall back
to debug signing (testing and sharing only, not the Play Store).

## 3. Back up the keystore now

Copy `faraidflow-upload.jks` plus both passwords to offline storage
(USB drive, password manager). Losing them ends update continuity
forever: Google Play treats a new key as a new app, and installed
users could never update in place again.

## 4. Confirm it worked

After the next tag release, either install the APK over the previous
release (it installs as an *update*, no uninstall needed), or inspect
the certificate:

```bash
apksigner verify --print-certs out/ahli-waris-*-arm64-v8a.apk
```

The SHA digest must match the upload certificate, not the debug one.

## 5. Never commit the keystore

No keystore file ever enters git: `.gitignore` covers `*.jks` and
`*.keystore`. Secrets live only in GitHub Settings, mapped through
`env:` in the workflow — never pasted into code or logs.
