#!/bin/bash

list_of_files=$(ls -la | awk '{print $9}')
for file in $list_of_files; do
        if [[ -f $file ]]; then
                name_of_file=$file 
                if [[ $name_of_file == "test.sh" ]]; then
                        continue
                fi
                mv "$name_of_file" "${name_of_file:3:1000}";
        fi
done