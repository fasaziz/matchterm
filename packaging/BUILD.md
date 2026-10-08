# Windows installer build

Target repository: https://github.com/fasaziz/matchterm

The workflow runs on a Windows GitHub Actions runner. It tests the application, bundles Python and dependencies with PyInstaller, then creates a per-user Inno Setup installer. Installer output stays in a private workflow artifact; this workflow does not create a public release or submit a WinGet package.

1. Upload this source tree to the root of the private repository, including `.github/workflows/windows-build.yml`.
2. Open the repository's Actions tab and select **Build Windows installer**.
3. Run the workflow on main, or let the initial main push trigger it.
4. After success, download **MATCHTERM-Windows-installer** from the workflow run.
5. Extract it and run the setup executable on Windows 11.

No Python or uv is required on the laptop for this standalone installer. App files install under `%LOCALAPPDATA%\Programs\MATCHTERM`; saves remain under `%LOCALAPPDATA%\MATCHTERM`. A Start menu shortcut and user PATH entry are added. Uninstall removes the program PATH entry and leaves saves intact. Open a new PowerShell session after installation to use `matchterm` by name; the installer's Launch option starts directly.

An existing uv installation can remain on disk; PATH precedence may depend on the session. For testing the standalone build, use its Start menu shortcut or full executable path. After confirming it works, `uv tool uninstall matchterm` removes the older uv-managed copy while keeping saves.

The installer is unsigned in this first build. Code signing and a public, stable versioned download URL remain future release steps. The installer has not yet been built or executed by the preparing Linux environment. GitHub Actions logs and an actual Windows install/upgrade/uninstall test must confirm it works before any WinGet submission.

The WinGet manifest is deliberately not included yet: it needs the final hosted installer URL and its actual SHA256 after a successful Windows build.
