# filepath: /Users/xkaria/GRIDH/diana-backend/apps/shfa/test_oai.sh
#!/usr/bin/env bash
# Fetch all OAI-PMH records via resumptionToken paging.
# Usage: ./test_oai.sh https://your.host/oai endpoint_metadataPrefix [setSpec]

set -euo pipefail

if ! command -v xmlstarlet >/dev/null 2>&1; then
  echo "xmlstarlet is required" >&2
  exit 1
fi

SERVER="${1:-}"
METADATA_PREFIX="${2:-oai_dc}"
SET_SPEC="${3:-}"          # optional
OUT_DIR="${OUT_DIR:-oai_dump}"

if [[ -z "$SERVER" ]]; then
  echo "Usage: $0 BASE_URL [metadataPrefix] [setSpec]" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Extract resumptionToken and also pretty-save full response
extract_token() {
  local in_file="$1"
  xmlstarlet sel -N oai="http://www.openarchives.org/OAI/2.0/" \
    --template \
    --match "/oai:OAI-PMH/oai:ListRecords/oai:resumptionToken" \
    --value-of "."
}

fetch_page() {
  local url="$1"
  local idx="$2"
  local out_xml="$OUT_DIR/page-$(printf "%04d" "$idx").xml"
  echo "[INFO $(timestamp)] GET $url"
  http_code=$(curl -w '%{http_code}' -sS -g -H 'Accept: application/xml' \
    -H 'User-Agent: OAI-Test-Script/1.0' \
    "$url" -o "$out_xml") || {
      echo "[ERROR] curl failed for $url" >&2
      return 1
    }
  if [[ "$http_code" != 200 ]]; then
    echo "[ERROR] HTTP $http_code for $url" >&2
    return 2
  fi
  # Basic protocol error check
  if grep -q "<error " "$out_xml"; then
    echo "[WARN] OAI-PMH error element found in page $idx:"
    grep "<error " "$out_xml"
  fi
  extract_token "$out_xml"
}

build_initial_url() {
  local base="$SERVER?verb=ListRecords&metadataPrefix=$METADATA_PREFIX"
  if [[ -n "$SET_SPEC" ]]; then
    base="$base&set=$SET_SPEC"
  fi
  echo "$base"
}

build_token_url() {
  local token="$1"
  # Use --get & URL-encode via curl -G + --data-urlencode (safer if token has +/=/:)
  printf "%s" "$SERVER?verb=ListRecords&resumptionToken=$token"
}

echo "[INFO] Starting OAI-PMH harvest"
page=1
initial_url=$(build_initial_url)
token=$(fetch_page "$initial_url" "$page" || echo "")

while [[ -n "${token// /}" ]]; do
  ((page++))
  # URL may need encoding if token contains special chars; safer approach:
  # Use curl -G --data-urlencode in fetch_page, but we inlined simple build here.
  token_url=$(build_token_url "$token")
  token=$(fetch_page "$token_url" "$page" || echo "")
done

echo "[INFO] Completed. Pages: $page Output dir: $OUT_DIR"