#!/bin/bash

# Dynamically determine onion address to serve monerod on tor network

hidden_service=(
    monerod
    monerod-rpc
)
for i in "${hidden_service[@]}"; do
    tries=0
    until [ -f /var/lib/tor/"${i}"/hostname ]; do
        if [ $tries -ge 5 ]; then
            echo "[+] Failed to generate ${i} onion address"
            exit 1
        fi
        tries=$((tries+1))
        echo -e "[${tries}] Waiting for ${i} onion address to be generated"
        sleep 1
    done
    onion=$(cat "/var/lib/tor/${i}/hostname")
    echo -e "[+] Generated /var/lib/tor/${i}/hostname\n${onion}\n"
done

export ONION_ADDRESS=$(cat /var/lib/tor/monerod-rpc/hostname)
export P2P_ONION_ADDRESS=$(cat /var/lib/tor/monerod/hostname)

echo "=========================================="
echo "Your Monero RPC Onion address is: ${ONION_ADDRESS}"
echo "Your Monero P2P Onion address is: ${P2P_ONION_ADDRESS}"
echo "=========================================="

sleep 3

# Well-connected public stagenet nodes kept as permanent peers. With ordinary peers the sync crawled through the heavy
# blocks around height 1.58M (0.23 blocks/s); with these it ran at 1-126 blocks/s. PRIORITY_NODES overrides the list
# (space-separated host:port); "none" disables it.
PRIORITY_NODES=${PRIORITY_NODES:-"node.sethforprivacy.com:38080 node.monerodevs.org:38080 node2.monerodevs.org:38080 stagenet.xmr-tw.org:38080"}
priority=()
if [ "${PRIORITY_NODES}" != "none" ]; then
    for n in ${PRIORITY_NODES}; do priority+=("--add-priority-node=${n}"); done
fi

monerod \
    --stagenet \
    --data-dir=/data \
    --p2p-bind-ip=0.0.0.0 \
    --p2p-bind-port=38080 \
    --rpc-restricted-bind-ip=0.0.0.0 \
    --rpc-restricted-bind-port=38089 \
    --zmq-rpc-bind-ip=0.0.0.0 \
    --zmq-rpc-bind-port=38082 \
    --confirm-zmq-rpc-external-bind \
    --rpc-bind-ip=0.0.0.0 \
    --rpc-bind-port=38081 \
    --non-interactive \
    --confirm-external-bind \
    --public-node \
    --log-level=0 \
    --rpc-ssl=disabled \
    --ban-list=/ban_list.txt \
    --anonymous-inbound=${P2P_ONION_ADDRESS}:38084,0.0.0.0:38084,24 \
    --tx-proxy=tor,172.31.255.250:9050,disable_noise,24 \
    --tx-proxy=i2p,172.31.255.251:4447,disable_noise,24 \
    "${priority[@]}"
