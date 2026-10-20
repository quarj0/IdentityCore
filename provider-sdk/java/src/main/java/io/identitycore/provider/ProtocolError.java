package io.identitycore.provider;

/** Stable, value-free protocol failure. Never include received content in messages. */
public final class ProtocolError extends RuntimeException {
  public ProtocolError(String message) {
    super(message, null, false, false);
  }
}
