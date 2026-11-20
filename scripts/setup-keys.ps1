# Travel Hacking Toolkit - optional API key setup (Windows PowerShell).
# All keys are OPTIONAL. The toolkit is free-first: it works with none of them.
# Prompts for each optional key with masked input, validates it, and sets it as a
# persistent user environment variable. Never echoes the value back.

$keys = @(
  @{ Name = "SEATS_AERO_API_KEY"; Desc = "seats.aero Pro (live award search, >60 days, alerts)"; Min = 8 },
  @{ Name = "DUFFEL_API_KEY";     Desc = "Duffel (cleaner per-fare-class cash pricing)";          Min = 8 },
  @{ Name = "AWARDWALLET_API_KEY"; Desc = "AwardWallet (auto-pull balances)";                      Min = 8 },
  @{ Name = "AWARDWALLET_USER_ID"; Desc = "AwardWallet user id";                                   Min = 1 },
  @{ Name = "LITEAPI_API_KEY";    Desc = "LiteAPI (live hotel rates)";                             Min = 8 }
)

Write-Host "Travel Hacking Toolkit - optional key setup"
Write-Host "Every key is optional. Press Enter to skip any of them."
Write-Host ""

foreach ($k in $keys) {
  Write-Host ("{0}" -f $k.Desc)
  $secure = Read-Host -Prompt ("  {0}" -f $k.Name) -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

  if ([string]::IsNullOrEmpty($value)) { Write-Host "  skipped"; continue }
  if ($value.Length -lt $k.Min) { Write-Host ("  rejected: shorter than {0} characters" -f $k.Min); continue }

  [Environment]::SetEnvironmentVariable($k.Name, $value, "User")
  Write-Host "  saved"
}

Write-Host ""
Write-Host "Done. Open a new terminal for the variables to take effect."
Write-Host "The toolkit already works without any of these keys."
