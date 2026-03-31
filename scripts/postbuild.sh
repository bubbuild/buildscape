#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
INDEX_HTML="${BUILD_DIR}/index.html"

cp "${ROOT_DIR}/theme/custom.css" "${BUILD_DIR}/custom.css"
cp "${ROOT_DIR}/theme/custom.js" "${BUILD_DIR}/custom.js"

if ! grep -q 'custom.css' "${INDEX_HTML}"; then
  perl -0pi -e 's#</head>#  <link rel="stylesheet" href="./custom.css">\n    </head>#' "${INDEX_HTML}"
fi

if ! grep -q 'custom.js' "${INDEX_HTML}"; then
  perl -0pi -e 's#</body>#        <script src="./custom.js"></script>\n    </body>#' "${INDEX_HTML}"
fi
