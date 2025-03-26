#!/bin/bash

set -e

if test -z $1
then
	echo "Usage: migrate.sh {data_dir}"
	exit 1
fi

data_dir=$1
sed_dir=`dirname $0`

echo "Migration started"
sed -i -E -f ${sed_dir}/uni-migration.sed ${data_dir}/*.json

if test -f ${data_dir}/C_modules_all_ages.json
then
	sed -i -E -f ${sed_dir}/C_modules_all_ages.sed ${data_dir}/C_modules_all_ages.json
fi

echo "Edits applied"

for f in ${data_dir}/*.json
do
	rpft sheets-to-uni $f $f
	echo "File migrated, path=$f"
done

echo "Migration completed"
