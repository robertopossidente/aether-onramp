FROM aetherproject/ocudu:rel-1.0.0

LABEL org.opencontainers.image.title="Aether O-CU" \
      org.opencontainers.image.description="Dedicated O-CU (Centralized Unit) for Aether MOCN Orchestrated" \
      org.opencontainers.image.version="1.0.0"

# Remove non-CU binaries to specialize the image for O-CU role
RUN rm -f /usr/local/bin/odu* /usr/local/bin/gnb* /usr/local/bin/ru_emulator

CMD ["/usr/local/bin/ocu", "-c", "/opt/cu_config.yaml"]

