#!/usr/bin/env bash

i=0
while IFS= read -d $'\0' -r file ; do
        echo $file
        printf 'File found: %s\n' "$file"
        python3 ./main_collect_ml_api_type_Inference.py $file '68013171' $i
        true $(( i++ ))
done < <(find PATH_FOLDER -iname '*py' -print0)
