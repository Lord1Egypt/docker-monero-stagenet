# Official XMRig release (static x64). The sha256 is from the release's SHA256SUMS, whose GPG signature was verified
# against XMRig's key 9AC4 CEA8 E66E 35A5 C7CD DC1B 446A 5363 8BE9 4409 (doc/gpg_keys/xmrig.asc in the XMRig repo).
FROM debian:bookworm-slim
ARG XMRIG_VERSION=6.26.0
ARG XMRIG_SHA256=fc6f8ae5f64e4f17481f7e3be29a1c56949f216a998414188003eae1db20c9e5
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
 && curl -fsSL -o /tmp/xmrig.tar.gz "https://github.com/xmrig/xmrig/releases/download/v${XMRIG_VERSION}/xmrig-${XMRIG_VERSION}-linux-static-x64.tar.gz" \
 && echo "${XMRIG_SHA256}  /tmp/xmrig.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/xmrig.tar.gz -C /tmp && install -m 0755 /tmp/xmrig-${XMRIG_VERSION}/xmrig /usr/local/bin/xmrig \
 && rm -rf /tmp/xmrig* && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && useradd -r -u 1000 miner
USER miner
ENTRYPOINT ["/bin/sh", "-c", "if [ \"${MINE_HOURS:-6}\" = 0 ]; then exec xmrig \"$@\"; else exec timeout \"${MINE_HOURS:-6}h\" xmrig \"$@\"; fi", "--"]
