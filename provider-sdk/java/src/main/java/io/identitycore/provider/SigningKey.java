package io.identitycore.provider;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.util.Set;

public record SigningKey(
    String keyId,
    @JsonIgnore String secret,
    String tenantId,
    String environment,
    Set<String> capabilities) {
  public SigningKey {
    capabilities = Set.copyOf(capabilities);
  }

  @Override
  public String toString() {
    return "SigningKey(" + keyId + ")";
  }
}
