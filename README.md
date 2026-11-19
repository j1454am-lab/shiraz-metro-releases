# Shiraz Metro — Android Releases

مخزن عمومی انتشار اپلیکیشن **غیررسمی** راهنمای مترو شیراز؛ مستقل از اپراتور رسمی. سورس، Keystore و Secretهای امضا در مخزن خصوصی نگهداری می‌شوند.

## وضعیت

نسخه 1.0.18 (کد 19) مبنای آزمون موفق OTA روی گوشی است. انتشارها فعلاً **technical pre-release** هستند؛ بخشی از داده‌های خدمات اطراف ایستگاه‌ها هنوز تأیید نشده‌اند. این وضعیت به معنی انتشار نهایی در فروشگاه یا تأیید رسمی داده‌ها نیست.

- APK امضاشده و SHA256SUMS.txt در قسمت [Releases](https://github.com/j1454am-lab/shiraz-metro-releases/releases).
- latest.json فقط پس از اعتبارسنجی فایل عمومی و ادغام درخواست فعال‌سازی برنامه، تغییر می‌کند.
- دریافت و نصب نسخه جدید نیازمند تأیید کاربر است. VPS لازم نیست.

## Separated Build & Release Architecture v1.0

1. Private repository `j1454am-lab/shiraz-metro`: approved release request → Android CI/runtime → signing and pinned certificate → verified artifacts → draft release with APK, checksum and candidate.json → repository_dispatch type metro-signed-candidate-v1.
2. Public repo: `.github/workflows/ota-publish.yml` admits the draft only on protected main. It independently verifies actual package/version, APK SHA-256, v2 signature and signer against the immutable known-good 1.0.18 APK digest. The public job does not have signing secrets or the private source repository.
3. Public job publishes the verified technical pre-release, downloads its APK without authentication, compares bytes, then prepares activate/vX.Y.Z branch changing ONLY latest.json. It attempts to open an activation PR; if GitHub's Actions permission prevents this, use the compare link in the run summary.
4. Owner reviews activation PR and requires **Manifest gate** (workflow Public OTA manifest validation) before merging. That check independently verifies the public APK and compares candidate version with base latest.json; the candidate PR cannot change verifier or workflow code together with the feed.
5. The merge into main activates app updates. This explicit final approval is intentional. Do not bypass PR or modify main latest.json directly.

### Owner settings (not applied by these commits)
- Public main protection: require pull requests, require Manifest gate (with branches up to date), conversation resolution, prohibit force pushes/deletion and bypass. Select actual check name after first successful workflow. For single-maintainer workflow an additional reviewer is not required unless another authorized reviewer is available.
- Optionally allow Actions to create PRs under repository Actions settings; owner might have to approve the workflow run or create PR manually for required checks. Never enable automatic approval of an activation by CI.
- The existing cross-repo fine-grained token remains in private repo only. It can create a draft and dispatch; enforce public main protection before testing publish. Public workflow uses only its own GITHUB_TOKEN.

### Failure recovery
If draft admission or public byte verification fails, do not advance latest.json. If release becomes public but PR fails, reconcile already-published asset and create a manifest-only PR after independent verification; do not overwrite a signed APK/tag. Keep v1.0.18 trust-anchor asset available. Keep the private source branch access restricted: public protection is not private source protection.
