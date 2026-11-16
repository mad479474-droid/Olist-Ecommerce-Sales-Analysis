# Olist Track A: direct CSV -> 8 pre-created SQL Server tables.
# Usage (PowerShell in project root):
# powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\import_olist_sqlserver.ps1 -DataFolder "C:\Users\Dell\Desktop\project bi\Dataset" -Server "."
# Uses Windows Authentication and built-in .NET libraries. No SSMS import wizard, Python or ODBC driver required.
param(
    [Parameter(Mandatory=$true)][string]$DataFolder,
    [string]$Server = '.',
    [string]$Database = 'OlistTrackA',
    [int]$BatchSize = 2000
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName 'System.Data'
Add-Type -AssemblyName 'Microsoft.VisualBasic'
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$tables = @(
    @{File='olist_customers_dataset.csv';Table='customers';Expected=99441},
    @{File='olist_orders_dataset.csv';Table='orders';Expected=99441},
    @{File='olist_order_items_dataset.csv';Table='order_items';Expected=112650},
    @{File='olist_products_dataset.csv';Table='products';Expected=32951},
    @{File='olist_sellers_dataset.csv';Table='sellers';Expected=3095},
    @{File='olist_order_payments_dataset.csv';Table='order_payments';Expected=103886},
    @{File='olist_order_reviews_dataset.csv';Table='order_reviews';Expected=99224},
    @{File='product_category_name_translation.csv';Table='category_translation';Expected=71}
)
$connString = "Server=$Server;Database=$Database;Integrated Security=True;TrustServerCertificate=True;Connection Timeout=15;"
$conn = [System.Data.SqlClient.SqlConnection]::new($connString)
$conn.Open()
try {
    $command = $conn.CreateCommand()
    $command.CommandText = "SELECT DB_NAME(), @@SERVERNAME"
    $reader = $command.ExecuteReader(); $reader.Read() | Out-Null
    Write-Host ("CONNECTED: database={0} server={1}" -f $reader.GetString(0),$reader.GetString(1)) -ForegroundColor Cyan
    $reader.Close()
    foreach ($item in $tables) {
        $table = [string]$item.Table
        $path = Join-Path $DataFolder $item.File
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing CSV: $path" }
        $check = $conn.CreateCommand()
        $check.CommandText = "SELECT OBJECT_ID(N'dbo.$table', N'U'), (SELECT COUNT_BIG(*) FROM [dbo].[$table])"
        $checkReader = $check.ExecuteReader()
        $null = $checkReader.Read()
        if ($checkReader.IsDBNull(0)) { throw "Table dbo.$table not found. Run sql/01_schema.sql first." }
        $oldCount = [int64]$checkReader.GetValue(1)
        $checkReader.Close()
        if ($oldCount -eq $item.Expected) {
            Write-Host "SKIP $table ($oldCount rows already present)" -ForegroundColor Green
            continue
        }
        if ($oldCount -gt 0) { throw "STOP: dbo.$table has $oldCount rows, expected either 0 or $($item.Expected). No data were deleted. Resolve existing rows before retry." }
        $parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new($path,[System.Text.Encoding]::UTF8)
        try {
            $parser.TextFieldType = [Microsoft.VisualBasic.FileIO.FieldType]::Delimited
            $parser.SetDelimiters(',')
            $parser.HasFieldsEnclosedInQuotes = $true
            $parser.TrimWhiteSpace = $false
            $headers = $parser.ReadFields()
            $schemaCmd = $conn.CreateCommand()
            $schemaCmd.CommandText = "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=@t"
            $null = $schemaCmd.Parameters.Add('@t',[System.Data.SqlDbType]::NVarChar,128)
            $schemaCmd.Parameters['@t'].Value=$table
            $schemaRdr=$schemaCmd.ExecuteReader()
            $colTypes=@{}
            while ($schemaRdr.Read()) { $colTypes[$schemaRdr.GetString(0)]=$schemaRdr.GetString(1) }
            $schemaRdr.Close()
            $dt = New-Object System.Data.DataTable
            foreach ($header in $headers) {
                if (-not $colTypes.ContainsKey($header)) { throw "CSV column '$header' missing from dbo.$table" }
                $type=[string]$colTypes[$header]
                $dotnetType = switch ($type) {
                    {$_ -in @('int','smallint','tinyint')} { [int];break }
                    'bigint' {[long];break}
                    {$_ -in @('decimal','numeric','money','smallmoney')} {[decimal];break}
                    {$_ -in @('datetime','datetime2','date','smalldatetime')} {[datetime];break}
                    default {[string];break}
                }
                $null=$dt.Columns.Add($header,$dotnetType)
            }
            $bulk = [System.Data.SqlClient.SqlBulkCopy]::new($conn,[System.Data.SqlClient.SqlBulkCopyOptions]::KeepNulls,$null)
            $bulk.DestinationTableName="[dbo].[$table]"
            $bulk.BatchSize=$BatchSize
            $bulk.BulkCopyTimeout=180
            foreach ($header in $headers) { $null=$bulk.ColumnMappings.Add($header,$header) }
            try {
                $processed=0
                while (-not $parser.EndOfData) {
                    $values=$parser.ReadFields()
                    if ($values.Length -ne $headers.Length) {throw "Wrong field count at CSV record $($processed+2) in $($item.File)"}
                    $row=$dt.NewRow()
                    for ($i=0; $i -lt $headers.Length; $i++) {
                        $name=$headers[$i];$v=$values[$i];$typ=[string]$colTypes[$name]
                        if ($null -eq $v -or $v -eq '') {
                            $row[$name]=[DBNull]::Value
                        } else {
                            switch ($typ) {
                                {$_ -in @('int','smallint','tinyint')} {$row[$name]=[int]::Parse($v,$culture);break}
                                'bigint' {$row[$name]=[long]::Parse($v,$culture);break}
                                {$_ -in @('decimal','numeric','money','smallmoney')} {$row[$name]=[decimal]::Parse($v,[System.Globalization.NumberStyles]::Number,$culture);break}
                                {$_ -in @('datetime','datetime2','date','smalldatetime')} {$row[$name]=[datetime]::Parse($v,$culture);break}
                                default {$row[$name]=$v;break}
                            }
                        }
                    }
                    $dt.Rows.Add($row)
                    $processed++
                    if ($dt.Rows.Count -ge $BatchSize) {
                        $bulk.WriteToServer($dt)
                        $dt.Clear()
                    }
                }
                if ($dt.Rows.Count -gt 0) {$bulk.WriteToServer($dt);$dt.Clear()}
            } finally {$bulk.Close();$dt.Dispose()}
        } finally {$parser.Close()}
        $cmd = $conn.CreateCommand()
        $cmd.CommandText="SELECT COUNT_BIG(*) FROM [dbo].[$table]"
        $count=[int64]$cmd.ExecuteScalar()
        if ($count -ne $item.Expected) {throw "INVALID COUNT for ${table}: expected $($item.Expected), found $count. STOP and investigate before continuing."}
        Write-Host "OK $table : $count rows" -ForegroundColor Green
    }
    Write-Host 'ALL EIGHT TABLES IMPORTED AND COUNTS VERIFIED.' -ForegroundColor Green
    Write-Host 'Next in SSMS: sql/02_validation.sql, then sql/00_views.sql, then sql/03_analysis.sql.' -ForegroundColor Cyan
} finally {$conn.Close()}


