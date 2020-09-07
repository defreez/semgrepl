#!/bin/bash

ID="$1"
REPO="$2"
SEMGREPL_CMD="$3"

if [ -z "$REPO" ]; then
	echo "Usage: batch.sh ID REPO SEMGREPL_CMD"
	exit 1
fi

git clone --depth 1 $REPO /tmp/repo
cd /root
CMD="import pickle; import semgrepl.main as sm; config = sm.init('/tmp/repo'); result = $SEMGREPL_CMD; pickle.dump(result, open('$ID.p', 'wb'))"
echo $CMD
ipython3 -c "$CMD"

aws s3 cp $ID.p s3://semgrepl/pickles/
