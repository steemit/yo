#!/bin/bash

if [ ! -f ./pubkey.txt ]; then
    pushd scripts/
   ./gen_webpush_keys.sh
   popd
fi

./scripts/delayed_run.sh ./scripts/create_test_user.sh &

LOG_LEVEL=DEBUG make run-without-docker
