# symlink this as ~/.bash_aliases to pull in all the *.rc scripts here

if [ -d ~/rattatouille/etc ]; then
  echo -n "Importing rattatouille:" 
  for rc in ~/rattatouille/etc/bashrc.*rc; do
    echo -n " ${rc##*bashrc.}"
    source $rc
  done
  echo " "
fi
