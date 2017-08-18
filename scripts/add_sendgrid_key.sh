#!/bin/bash

# If the sendgrid private key is set in environment already, skip reading it
if [ -z "${SENDGRID_PRIV_KEY}" ]; then
	read -s -p "Paste sendgrid private key and hit enter:" SENDGRID_PRIV_KEY
	echo
fi

# Write key to .txt file
echo $SENDGRID_PRIV_KEY >../sendgrid_privkey.txt
