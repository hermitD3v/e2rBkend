mkdir tempOldFiles
output_base_dir="tempOldFiles"
pushd ./PartRepo/HDMTOS
while IFS= read -r path; do
  echo "Processing: $path"
  
  # Create the directory structure in tempOldFiles
  output_path="../../$output_base_dir/$path"
  output_dir=$(dirname "$output_path")
  mkdir -p "$output_dir"
  
  # Run git show and redirect the output to the corresponding file in tempOldFiles
  git show HEAD~1:"$path" > "$output_path"
done < ../../changedFileName.txt

popd