#!/bin/sh

echo if this fails, install web-push first:
echo    npm install -g web-push

TMPFILE=`mktemp`

web-push generate-vapid-keys >$TMPFILE
grep -A1 "Public Key" $TMPFILE  | tail -1 | tr -d '\n' >../wwwpush_pubkey.txt
grep -A1 "Private Key" $TMPFILE | tail -1 | tr -d '\n' >../wwwpush_privkey.txt

rm $TMPFILE

echo "Keys are in wwwpush_pubkey.txt and wwwpush_privkey.txt - don't share the private key (obviously)"

