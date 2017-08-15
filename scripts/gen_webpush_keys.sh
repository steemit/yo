#!/bin/sh

echo if this fails, install web-push first:
echo    npm install -g web-push

TMPFILE=`mktemp`

web-push generate-vapid-keys >$TMPFILE
grep -A1 "Public Key" $TMPFILE  | tail -1 >../pubkey.txt
grep -A1 "Private Key" $TMPFILE | tail -1 >../privkey.txt

rm $TMPFILE

echo "Keys are in ../pubkey.txt and ../privkey.txt - don't share the private key (obviously)"

