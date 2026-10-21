#!/usr/bin/env bash
# Build and push the multi-arch (linux/amd64 + linux/arm64) stagenet images to Docker Hub.
# Needs `docker login` and Buildx with QEMU for the foreign architecture.
#   ./release.sh monero|exporter|nodemapper|tor|i2p|explorer|all [DOCKERHUB_USER]
set -euo pipefail

IMAGE=${1:?usage: ./release.sh monero|exporter|nodemapper|tor|i2p|explorer|all [user]}
DH_USER=${2:-lord1egypt}
PLATFORMS=linux/amd64,linux/arm64
MONERO_VERSION=v0.18.5.4            # must match dockerfiles/files/monerod/hashes.txt (GPG-verified at build time)
VERSION=1.0.0
EXPLORER_UPSTREAM=lalanza808/moneroexplorer:v1.0.0

build() {   # build NAME TAG DOCKERFILE
    docker buildx build --platform "$PLATFORMS" -t "${DH_USER}/$1:$2" -t "${DH_USER}/$1:latest" -f "$3" . --push
}

case "$IMAGE" in
    monero)     build monero-stagenet "$MONERO_VERSION" dockerfiles/monero ;;
    exporter)   build monero-stagenet-exporter "$VERSION" dockerfiles/exporter ;;
    nodemapper) build monero-stagenet-nodemapper "$VERSION" dockerfiles/nodemapper ;;
    tor)        build monero-stagenet-tor "$VERSION" dockerfiles/tor ;;
    i2p)        build monero-stagenet-i2p "$VERSION" dockerfiles/i2p ;;
    explorer)   # network-agnostic upstream explorer, pinned under this namespace (both architectures copied as-is)
                docker buildx imagetools create -t "${DH_USER}/monero-stagenet-explorer:${VERSION}" -t "${DH_USER}/monero-stagenet-explorer:latest" "$EXPLORER_UPSTREAM" ;;
    all)        for i in monero exporter nodemapper tor i2p explorer; do "$0" "$i" "$DH_USER"; done ;;
    *)          echo "unknown image $IMAGE"; exit 2 ;;
esac
