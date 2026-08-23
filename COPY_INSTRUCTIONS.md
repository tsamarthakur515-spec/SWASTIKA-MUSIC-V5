# Full code copy — no PC needed (not a fork)

Target repo: https://github.com/tsamarthakur515-spec/Swastika-Music-V5
Source: SWASTIKA-MUSICV4

## Phone se (recommended)

### Method 1 — Download ZIP + Upload
1. Open SWASTIKA-MUSICV4 on GitHub (phone browser)
2. **Code → Download ZIP**
3. Unzip on phone (Files app / ZArchiver)
4. Open **Swastika-Music-V5** on GitHub
5. **Add file → Upload files** → saari folders/files select karo → Commit

### Method 2 — GitHub Codespaces (easiest full push)
1. SWASTIKA-MUSICV4 → **Code → Codespaces → Create codespace on main**
2. Terminal open karo, ye likho:

```bash
git remote add v5 https://github.com/tsamarthakur515-spec/Swastika-Music-V5.git
git push v5 HEAD:main --force
```

Isse V4 ka **poora code** V5 pe aa jayega — **fork nahi**, seedha copy.

### Method 3 — VPS / bot host terminal
Agar bot kisi VPS pe chal raha hai, wahan:

```bash
cd /path/to/SWASTIKA-MUSICV4
git remote add v5 https://github.com/tsamarthakur515-spec/Swastika-Music-V5.git
git push v5 main --force
```

## Note
`Config.env` mein secrets mat commit karo. VPS pe alag se set karo.
