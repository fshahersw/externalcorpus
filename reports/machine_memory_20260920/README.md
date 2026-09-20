# Kernel non-paged pool exhaustion: diagnosis and fix (2026-09-20)

## Symptom
Windows non-paged pool grew about 35 MB per minute until it held 12-15 GB of a 15.2 GB machine (2026-09-19). Every process was
paged out (about 170,000 pages/sec), the local server and the browser looked hung, and the machine had to be rebooted. After the
reboot the pool was back at 5.9 GB within three hours with none of this project's jobs running.

## Diagnosis (all read-only)
1. `pooltags.ps1` (in this folder) asks the kernel for its per-tag pool accounting (NtQuerySystemInformation class 22, the same
   numbers poolmon shows) twice and prints the largest and the fastest-growing tags.
   - `NtFC` (ntfs.sys, file-create path): 3.4 GB, 5.2 million outstanding allocations, +35 MB/min.
   - `FMsl` (fltMgr.sys, per-file contexts that file-system filter drivers such as antivirus attach): growing with it.
   - `cxbm` (netadaptercx.sys): 1.0 GB, static. This is the Wi-Fi adapter's receive-buffer pool, a fixed cost, not a leak.
2. Per-process counters (`\Process(*)\IO Other Operations/sec`): `git.exe` was performing about 155,000 file-system operations
   per second, continuously. Nothing else exceeded 6,500.
3. The git command lines were the desktop app's poll, `git ... ls-files --others --exclude-standard --full-name :/`
   (list every untracked file from the repository root), started about once a minute; each run took longer than a minute, so
   runs overlapped forever.
4. `git rev-parse --show-toplevel` from this project answers `C:/Users/firas`: the whole user profile is a git repository
   (2 commits, 71 tracked files from an old template project; created by accident). "Every untracked file" therefore meant the
   entire profile: Downloads, AppData, OneDrive, the 45 GB corpora. Millions of file opens per minute left NTFS and filter-manager
   structures in non-paged memory faster than Windows releases them.

So there is no faulty driver. The kernel memory was consumed by ntfs.sys on behalf of an endless directory walk.

## Fix applied
- One line, `/*`, appended to `C:\Users\firas\.git\info\exclude` (a local, uncommitted exclude list; backup beside it as
  `exclude.bak-20260920`). Untracked-file listings now prune the whole profile: the app's exact command went from never finishing
  to 0.06 s. Tracked files are unaffected. Undo: delete that line.
- The leftover runaway `git ls-files` processes were stopped.

## Result
`NtFC` growth 35 MB/min -> 0; `FMsl` draining; no git process running; paging about 100 pages/sec. The 3.5 GB already held under
`NtFC` is not returned while the machine stays up; a reboot reclaims it.

## Left to the owner (not done here)
- Reboot once to reclaim the 3.5 GB. Afterwards start the server with `reports/corpus_upgrade_20260919/start_server.ps1`.
- The accidental repository's `origin` address has a GitHub personal access token written into it in plain text, and that address
  was printed during this diagnosis. Revoke that token on GitHub and re-add the remote without a token. (The token is not
  recorded in this file or anywhere else in this project.)
- Decide whether the profile-level repository should exist at all. If not: rename `C:\Users\firas\.git` to something like
  `.git-accidental-backup`, and run `git init` inside the projects that should be versioned (this one included).
- Optional: the Killer Ethernet driver dates from 2023 and ships a traffic-shaping filter (KfeCo); it showed no growth in these
  samples, so nothing was changed.

## Check again at any time
    powershell -NoProfile -ExecutionPolicy Bypass -File reports\machine_memory_20260920\pooltags.ps1 -Seconds 60
