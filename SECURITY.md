# Security

Please report vulnerabilities in private, with **Report a vulnerability** in the Security tab of the repository, and not
in a public issue. Only the latest version gets fixes.

## What to know

- **Plain FTP is not encrypted**: the user and password can be read on the way. This is how game server hosts offer it.
  Use a password you do not use elsewhere.
- The password is never written to disk. It can come from `ACC_FTP_PASSWORD` or be typed.
- The address, port and user of the last server are saved as plain text on your computer.
- The cache has result files as the server saved them, with player ids. `race.json`, the charts and the summary do not.
- Never put result files with real players, addresses or passwords in an issue.
