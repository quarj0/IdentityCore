package io.identitycore;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.identitycore.models.GeneratedModels;
import java.util.ArrayList;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GovernedResourcesTest {
    @Test void projectPurposeAndDisclosureHeaderSurviveEncoding() {
        var urls = new ArrayList<String>(); var headers = new ArrayList<Map<String,String>>(); var bodies = new ArrayList<String>();
        var client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("recipient").clientSecret("synthetic-secret")
            .transport((method, url, head, body, timeout) -> {urls.add(url.toString()); headers.add(head); bodies.add(body); return new IdentityCoreClient.RawResponse(200,"{\"success\":true,\"data\":{\"ok\":true}}");}).build();
        client.governed.getEvidence("evd_one/../../claims?x=y", Map.of("project_id","prj_one","purpose","address & employment"));
        assertTrue(urls.get(0).contains("evd_one%2F..%2F..%2Fclaims%3Fx%3Dy")); assertTrue(urls.get(0).contains("address%20%26%20employment"));
        client.governed.redeemClaimDisclosure("dcl_one",new ObjectMapper().createObjectNode().put("project_id","prj_one"),"once",Map.of(),"synthetic-capability");
        assertEquals("synthetic-capability",headers.get(1).get("X-Disclosure-Token"));assertEquals("once",headers.get(1).get("Idempotency-Key"));
        assertFalse(urls.get(1).contains("synthetic-capability"));assertFalse(bodies.get(1).contains("synthetic-capability"));
    }
    @Test void humanApprovalUsesUserJwtAndNoClientIdentity() {
        var client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").accessToken("synthetic-user-jwt")
            .transport((method,url,headers,body,timeout)->{assertEquals("Bearer synthetic-user-jwt",headers.get("Authorization"));assertFalse(headers.containsKey("X-Client-Id"));return new IdentityCoreClient.RawResponse(200,"{\"success\":true,\"data\":{}}");}).build();
        client.governed.approvePurposeAuthorization("paz_one",new ObjectMapper().createObjectNode(),null,Map.of());
    }
    @Test void numericAndHyphenatedWireEnumsRequireExactStrings() throws Exception {
        var mapper=new ObjectMapper();var contract=GeneratedModels.ProviderCertificationOperationContract.IcProviderOperationsV1;
        assertEquals("\"ic-provider-operations-v1\"",mapper.writeValueAsString(contract));
        assertEquals(contract,mapper.readValue("\"ic-provider-operations-v1\"",GeneratedModels.ProviderCertificationOperationContract.class));
        assertEquals("\"1\"",mapper.writeValueAsString(GeneratedModels.ProviderCertificationContractVersion.Value1));
        assertThrows(com.fasterxml.jackson.databind.JsonMappingException.class,()->mapper.readValue("0",GeneratedModels.ProviderCertificationContractVersion.class));
    }
}
