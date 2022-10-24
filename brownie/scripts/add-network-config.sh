#!/bin/bash

brownie networks delete substrate-subnet-network-A
brownie networks delete substrate-subnet-network-B
rm -rf brownie/build/deployments
brownie networks import ./network-config.yaml
