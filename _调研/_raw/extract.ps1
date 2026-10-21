param([string]$Url, [string]$Out)

$ProgressPreference = 'SilentlyContinue'
$r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 90
$bytes = $r.RawContentStream.ToArray()
$h = [System.Text.Encoding]::UTF8.GetString($bytes)

# keep a copy of raw html
$rawName = [System.IO.Path]::GetFileNameWithoutExtension($Out)
[System.IO.File]::WriteAllText("$PSScriptRoot\$rawName.html", $h, [System.Text.Encoding]::UTF8)

# remove non-content blocks
$h = [regex]::Replace($h, '(?is)<script.*?</script>', ' ')
$h = [regex]::Replace($h, '(?is)<style.*?</style>', ' ')
$h = [regex]::Replace($h, '(?is)<noscript.*?</noscript>', ' ')
$h = [regex]::Replace($h, '(?is)<svg.*?</svg>', ' ')
$h = [regex]::Replace($h, '(?is)<!--.*?-->', ' ')
# block level -> newline
$h = [regex]::Replace($h, '(?i)</(p|div|li|h1|h2|h3|h4|h5|h6|tr|section|article|br|td|th|ul|ol|table|header|footer|main)>', "`n")
$h = [regex]::Replace($h, '(?i)<br\s*/?>', "`n")
$h = [regex]::Replace($h, '(?s)<[^>]+>', ' ')
# entities
$h = $h -replace '&nbsp;', ' ' -replace '&amp;', '&' -replace '&lt;', '<' -replace '&gt;', '>' -replace '&quot;', '"' -replace '&#39;', "'"
# collapse whitespace per line
$lines = $h -split "`n" | ForEach-Object { ($_ -replace '\s+', ' ').Trim() } | Where-Object { $_ -ne '' }
$txt = ($lines -join "`n")

[System.IO.File]::WriteAllText($Out, $txt, [System.Text.Encoding]::UTF8)
Write-Output "$Url => lines=$($lines.Count) chars=$($txt.Length) out=$Out"
