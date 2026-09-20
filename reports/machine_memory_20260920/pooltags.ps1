# Read-only: asks the kernel for its per-tag pool accounting (what poolmon shows), twice, and prints what is largest and what is growing.
# Nothing is changed on the system. Usage: powershell -NoProfile -ExecutionPolicy Bypass -File pooltags.ps1 [-Seconds 60]
param([int]$Seconds = 60)
$code = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class PoolTags {
    [DllImport("ntdll.dll")]
    static extern int NtQuerySystemInformation(int cls, IntPtr buffer, int length, out int returned);
    public class Row { public string Tag; public long NonPagedUsed; public long PagedUsed; public long NonPagedAllocs; public long NonPagedFrees; }
    public static List<Row> Query() {
        int size = 1 << 20;
        for (int attempt = 0; attempt < 8; attempt++) {
            IntPtr buffer = Marshal.AllocHGlobal(size);
            try {
                int returned;
                int status = NtQuerySystemInformation(22, buffer, size, out returned);   // 22 = SystemPoolTagInformation
                if (status == unchecked((int)0xC0000004)) { size *= 2; continue; }        // buffer too small
                if (status != 0) throw new Exception("NtQuerySystemInformation failed: 0x" + status.ToString("X8"));
                int count = Marshal.ReadInt32(buffer);
                var rows = new List<Row>(count);
                int offset = 8;                                                           // ULONG Count + padding on x64
                for (int i = 0; i < count; i++) {
                    byte[] tag = new byte[4];
                    Marshal.Copy(new IntPtr(buffer.ToInt64() + offset), tag, 0, 4);
                    var row = new Row();
                    row.Tag = System.Text.Encoding.ASCII.GetString(tag);
                    row.PagedUsed = Marshal.ReadInt64(buffer, offset + 16);
                    row.NonPagedAllocs = (uint)Marshal.ReadInt32(buffer, offset + 24);
                    row.NonPagedFrees = (uint)Marshal.ReadInt32(buffer, offset + 28);
                    row.NonPagedUsed = Marshal.ReadInt64(buffer, offset + 32);
                    rows.Add(row);
                    offset += 40;                                                         // sizeof(SYSTEM_POOLTAG) on x64
                }
                return rows;
            } finally { Marshal.FreeHGlobal(buffer); }
        }
        throw new Exception("pool tag table did not fit");
    }
}
'@
Add-Type -TypeDefinition $code
$first = [PoolTags]::Query()
$firstAt = Get-Date
"sample 1: {0} tags, nonpaged total {1:N0} MB" -f $first.Count, (($first | Measure-Object NonPagedUsed -Sum).Sum / 1MB)
Start-Sleep -Seconds $Seconds
$second = [PoolTags]::Query()
$minutes = ((Get-Date) - $firstAt).TotalMinutes
"sample 2: {0} tags, nonpaged total {1:N0} MB, after {2:N1} min" -f $second.Count, (($second | Measure-Object NonPagedUsed -Sum).Sum / 1MB), $minutes
$before = @{}
foreach ($row in $first) { $before[$row.Tag] = $row }
$rows = foreach ($row in $second) {
    $old = $before[$row.Tag]
    $delta = if ($old) { $row.NonPagedUsed - $old.NonPagedUsed } else { $row.NonPagedUsed }
    [pscustomobject]@{ Tag = $row.Tag; NonPagedMB = [math]::Round($row.NonPagedUsed / 1MB, 1); GrowthMBperMin = [math]::Round(($delta / 1MB) / $minutes, 2);
                       Outstanding = $row.NonPagedAllocs - $row.NonPagedFrees; PagedMB = [math]::Round($row.PagedUsed / 1MB, 1) }
}
"--- largest nonpaged tags"
$rows | Sort-Object NonPagedMB -Descending | Select-Object -First 14 | Format-Table -AutoSize | Out-String
"--- fastest growing nonpaged tags"
$rows | Sort-Object GrowthMBperMin -Descending | Select-Object -First 8 | Format-Table -AutoSize | Out-String
