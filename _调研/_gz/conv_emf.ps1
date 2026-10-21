$ErrorActionPreference='Stop'
$src = "D:\Work\业务平台开发\_调研\_公租房图\image5.emf"
$tmpdoc = "D:\Work\业务平台开发\_调研\_gz\emf_tmp.docx"
$tmppdf = "D:\Work\业务平台开发\_调研\_gz\emf_tmp.pdf"
if (Test-Path $tmpdoc) { Remove-Item $tmpdoc -Force }
if (Test-Path $tmppdf) { Remove-Item $tmppdf -Force }
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Add()
# landscape big page to fit
$doc.PageSetup.Orientation = 1
$doc.PageSetup.PageWidth = 1500
$doc.PageSetup.PageHeight = 1100
$doc.PageSetup.TopMargin = 10
$doc.PageSetup.BottomMargin = 10
$doc.PageSetup.LeftMargin = 10
$doc.PageSetup.RightMargin = 10
$rng = $doc.Content
$shp = $doc.InlineShapes.AddPicture($src, $false, $true, $rng)
Write-Output ("EMF natural size (pt): " + $shp.Width + " x " + $shp.Height)
# scale to fit page width
$maxW = $doc.PageSetup.PageWidth - 10
$maxH = $doc.PageSetup.PageHeight - 10
$sx = $maxW / $shp.Width
$sy = $maxH / $shp.Height
$s = [Math]::Min($sx, $sy)
$shp.Width = $shp.Width * $s
$shp.Height = $shp.Height * $s
Write-Output ("scaled: " + $shp.Width + " x " + $shp.Height + " scale=" + $s)
$doc.SaveAs([ref]$tmpdoc, [ref]16)
$doc.ExportAsFixedFormat($tmppdf, 17)
$doc.Close(0)
$word.Quit()
Write-Output "done"
