#!/bin/sh
echo "Configuring runtime environment..."

cat > /usr/share/app/env.js <<EOF
window.env = {
  VITE_API_BASE: '${VITE_API_BASE:-http://localhost:8000}'
};
EOF

if [ -f /usr/share/app/index.html ]; then
    sed -i 's|</head>|  <script src="/env.js"></script>\n  </head>|' /usr/share/app/index.html
fi

exec serve -s /usr/share/app -l 8080
