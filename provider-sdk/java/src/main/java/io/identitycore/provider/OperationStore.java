package io.identitycore.provider;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;

/** Implement with a shared transactional database for multi-host deployments. */
public interface OperationStore {
  boolean claimNonce(String digest, long expiresAt);

  ObjectNode admit(ObjectNode binding, ObjectNode inputs, Instant deadline);

  ObjectNode poll(ObjectNode binding);

  WorkerLease claimJob(int leaseSeconds);

  boolean renew(WorkerLease lease, int leaseSeconds);

  ObjectNode complete(WorkerLease lease, ObjectNode result);

  ObjectNode control(ObjectNode binding, String action);
}
