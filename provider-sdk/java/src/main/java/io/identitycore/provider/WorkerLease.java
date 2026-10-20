package io.identitycore.provider;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.databind.node.ObjectNode;

public record WorkerLease(
    String operationId,
    long generation,
    @JsonIgnore String owner,
    @JsonIgnore ObjectNode binding,
    @JsonIgnore ObjectNode inputs) {
  @Override
  public String toString() {
    return "WorkerLease(" + operationId + ", generation=" + generation + ")";
  }
}
