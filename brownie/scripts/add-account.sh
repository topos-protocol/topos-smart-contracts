#!/usr/bin/expect -f

set id [lindex $argv 0];
set privateKey [lindex $argv 1];
set password [lindex $argv 2];

spawn brownie accounts new $id
expect "Enter the private key you wish to add:" 
send "$privateKey\n"
expect "Enter the password to encrypt this account with:" 
send "$password\n"
expect "$ "
