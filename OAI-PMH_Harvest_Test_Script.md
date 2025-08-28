# OAI-PMH Harvest Test Script

Script: `apps/shfa/test_oai.sh`  
Purpose: Iteratively harvest all OAI-PMH records (ListRecords) following `resumptionToken`s and store each response.

## Prerequisites
- bash
- curl
- xmlstarlet (`brew install xmlstarlet` or `apt-get install xmlstarlet`)

## Usage
```bash
chmod +x apps/shfa/test_oai.sh
./apps/shfa/test_oai.sh BASE_URL [metadataPrefix] [setSpec]
```

Examples:
```bash
./apps/shfa/test_oai.sh https://example.org/oai                # default metadataPrefix=oai_dc
./apps/shfa/test_oai.sh https://example.org/oai oai_dc         # explicit
./apps/shfa/test_oai.sh https://example.org/oai oai_dc my:set  # restricted to a set
```

## Output
- XML pages saved under `oai_dump/` (override with `OUT_DIR=custom_dir ./...`).
- Files named `page-0001.xml`, `page-0002.xml`, etc.
- Logs show each requested URL and warnings if `<error>` elements are present.

## Quick Validation
Count records:
```bash
grep -c "<record>" oai_dump/page-*.xml
```
Check last token (should be empty on completion):
```bash
grep -H "<resumptionToken" oai_dump/page-*.xml | tail
```
Validate XML well-formedness:
```bash
xmlstarlet val --well-formed oai_dump/page-*.xml
```

## Environment Variables
| Variable  | Purpose                       | Default   |
|-----------|------------------------------|-----------|
| OUT_DIR   | Destination directory        | oai_dump  |

## Common Issues
- 400 with `badArgument`: missing `metadataPrefix`.
- Empty harvest: server returns `<error code="noRecordsMatch">`.
- Token with special chars failing: adjust `build_token_url` to use `curl -G --data-urlencode` if needed.

## Cleanup
```bash
rm -rf oai_dump
```

## Exit Codes
- 0 success
- 1 missing dependency or curl failure
- 2 non-200 HTTP