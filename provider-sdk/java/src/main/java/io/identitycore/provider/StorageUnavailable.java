package io.identitycore.provider;

public final class StorageUnavailable extends RuntimeException {
  public StorageUnavailable() {
    super("Provider operation storage is unavailable.", null, false, false);
  }
}
