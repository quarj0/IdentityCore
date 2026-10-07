package io.identitycore;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.identitycore.models.GeneratedModels;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GeneratedModelsTest {
    @Test
    void enumUsesWireValueAndRejectsUnknownValues() throws Exception {
        var mapper = new ObjectMapper();
        var value = GeneratedModels.ManualReviewDecisionRequestDecision.Verified;
        assertEquals("\"verified\"", mapper.writeValueAsString(value));
        assertEquals(value, mapper.readValue("\"verified\"", GeneratedModels.ManualReviewDecisionRequestDecision.class));
        assertThrows(com.fasterxml.jackson.databind.JsonMappingException.class,
            () -> mapper.readValue("\"invalid\"", GeneratedModels.ManualReviewDecisionRequestDecision.class));
    }
}
