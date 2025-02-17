#sh gitPartClone.sh <branch_name> <number_of_commits>
branch="$1"
d=$2
mkdir PartRepo
cd PartRepo
git clone --filter=blob:none --origin upstream --sparse https://ATTD@dev.azure.com/ATTD/HDMT_Prod/_git/HDMTOS -b $branch --depth $(($d + 1))
cd HDMTOS
git sparse-checkout set I2L TAL HAL Validation/iVal/HBI Validation/iVal/HDMT Validation/iVal/ValidationCode/TestClasses Validation/iVal/ValidationCode/UserFunctions Validation/iVal/BuildScripts
git diff --name-only HEAD~$d > ../../changedFileName.txt
cd ..