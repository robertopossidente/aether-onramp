FROM aetherproject/ocudu:rel-1.0.0

LABEL org.opencontainers.image.title="Aether O-DU" \
      org.opencontainers.image.description="Dedicated O-DU (Distributed Unit) for Aether MOCN Orchestrated" \
      org.opencontainers.image.version="1.0.0"

# Remove non-DU binaries to specialize the image for O-DU role
RUN rm -f /usr/local/bin/ocu /usr/local/bin/gnb*

CMD ["/usr/local/bin/odu", "-c", "/opt/du_config.yaml"]

