#!/usr/bin/expect -f

set contract [lindex $argv 0];
set account [lindex $argv 1];
set password [lindex $argv 2];
set network [lindex $argv 3];

spawn npm run deploy $contract $account -- --network $network
expect "Enter password for \"$account\":"
send "$password\n"
expect "$ "