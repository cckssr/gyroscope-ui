#!/bin/bash
# Synchronisiert config.json zwischen Root und src/

set -e

ROOT_CONFIG="config.json"
SRC_CONFIG="src/config.json"

if [ ! -f "$ROOT_CONFIG" ]; then
    echo "❌ Error: $ROOT_CONFIG nicht gefunden!"
    exit 1
fi

echo "📋 Synchronisiere config.json..."
echo "   Quelle: $ROOT_CONFIG"
echo "   Ziel:   $SRC_CONFIG"

# Erstelle Backup falls Ziel existiert und unterschiedlich ist
if [ -f "$SRC_CONFIG" ]; then
    if ! cmp -s "$ROOT_CONFIG" "$SRC_CONFIG"; then
        BACKUP="${SRC_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "⚠️  Dateien unterscheiden sich. Erstelle Backup: $BACKUP"
        cp "$SRC_CONFIG" "$BACKUP"
    else
        echo "✅ Dateien sind bereits identisch. Nichts zu tun."
        exit 0
    fi
fi

# Kopiere
cp "$ROOT_CONFIG" "$SRC_CONFIG"

echo "✅ Erfolgreich synchronisiert!"

# Zeige Unterschiede falls vorhanden
if [ -f "${SRC_CONFIG}.backup."* ]; then
    echo ""
    echo "📊 Änderungen:"
    diff -u "${SRC_CONFIG}.backup."* "$SRC_CONFIG" || true
fi
