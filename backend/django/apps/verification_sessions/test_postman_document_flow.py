import io
import json
import re
import subprocess
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APITestCase

from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.uploads.models import Upload, UploadStatus
from apps.verification_sessions import tests as fixtures


class PostmanDocumentFlowTests(APITestCase):
    setUp = fixtures.VerificationSessionPortalTests.setUp

    def collection(self):
        root = Path(__file__).resolve().parents[4]
        data = json.loads(
            (root / "postman/IdentityCore.postman_collection.json").read_text()
        )
        return {
            item["name"]: item
            for group in data["item"]
            for item in group.get("item", [])
        }

    def test_national_id_request_includes_front_and_back(self):
        request = self.collection()["Submit Document"]["request"]
        payload = json.loads(request["body"]["raw"])
        self.assertEqual(payload["country_code"], "GH")
        self.assertEqual(payload["document_type"], "national_id")
        self.assertEqual(
            {capture["side"] for capture in payload["captures"]}, {"front", "back"}
        )
        self.assertEqual(
            len({capture["upload_id"] for capture in payload["captures"]}), 2
        )

    def test_upload_creation_uses_bound_session_credentials(self):
        items = self.collection()
        for name in [
            "Create Document Upload",
            "Create Back Document Upload",
            "Create Selfie Upload",
            "Create Liveness Upload",
        ]:
            with self.subTest(name=name):
                headers = {
                    h["key"]: h["value"] for h in items[name]["request"]["header"]
                }
                self.assertEqual(headers["Authorization"], "Bearer {{session_token}}")
                self.assertEqual(headers["X-Session-Id"], "{{verification_session_id}}")
                self.assertNotIn("X-Client-Id", headers)

    def resolve(self, value):
        return re.sub(r"\{\{(.*?)\}\}", lambda m: str(self.values[m[1]]), value)

    def request_item(self, name, *, content=None):
        item = self.items[name]
        request = item["request"]
        url = self.resolve(request["url"])
        headers = {
            "HTTP_" + h["key"].upper().replace("-", "_"): self.resolve(h["value"])
            for h in request["header"]
            if h["key"] != "Content-Type"
        }
        if request["method"] == "GET":
            response = self.client.get(url, **headers)
        elif content is not None:
            self.assertEqual(request["body"]["mode"], "formdata")
            self.assertEqual(request["body"]["formdata"][0]["key"], "file")
            self.assertFalse(any(h["key"] == "Content-Type" for h in request["header"]))
            response = self.client.post(
                url,
                {
                    "file": SimpleUploadedFile(
                        "synthetic.jpg", content, content_type="image/jpeg"
                    )
                },
                format="multipart",
                **headers
            )
        else:
            body = json.loads(self.resolve(request["body"]["raw"]))
            response = self.client.post(url, body, format="json", **headers)
        self.assertEqual(
            response.status_code,
            201 if name.startswith("Create ") else 200,
            (name, response.data),
        )
        scripts = [
            line for event in item.get("event", []) for line in event["script"]["exec"]
        ]
        if scripts:
            # Execute the actual collection scripts, including the notice export loop.
            runner = """const [script,payload,values]=process.argv.slice(1).map(JSON.parse);
const pm={response:{json:()=>payload},environment:{set:(key,value)=>values[key]=value},
 test:(name,fn)=>fn(),expect:(obj)=>({to:{have:{property:(key)=>{if(!(key in obj))throw Error(key)}}}})};
new Function('pm',script)(pm);process.stdout.write(JSON.stringify(values));"""
            self.values = json.loads(
                subprocess.check_output(
                    [
                        "node",
                        "-e",
                        runner,
                        json.dumps("\n".join(scripts)),
                        json.dumps(response.json()),
                        json.dumps(self.values),
                    ],
                    text=True,
                )
            )
        return response

    @patch("apps.uploads.views.put_object_bytes")
    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_collection_uploads_both_sides_and_selfie_through_session_transfer(
        self, _publish, _storage
    ):
        self.items = self.collection()
        self.values = {
            "baseUrl": "",
            "restBase": "/api/v1",
            "session_token": self.raw_session_token,
            "verification_session_id": self.session.public_id,
        }
        self.request_item("Session Detail")
        self.request_item("Accept Consent")
        image = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(image, format="JPEG")
        content = image.getvalue()
        for create, transfer, prefix in [
            ("Create Document Upload", "Transfer Front Document", "document"),
            ("Create Back Document Upload", "Transfer Back Document", "document_back"),
        ]:
            self.values[prefix + "_file_size_bytes"] = len(content)
            self.request_item(create)
            self.request_item(transfer, content=content)
            upload = Upload.objects.get(public_id=self.values[prefix + "_upload_id"])
            self.assertEqual(upload.status, UploadStatus.UPLOADED)
            self.assertEqual(upload.verification_session_id, self.session.pk)
            self.assertTrue(upload.capture_receipt)
        self.request_item("Submit Document")
        document = IdentityDocument.objects.get(
            public_id=self.values["identity_document_id"]
        )
        self.assertEqual(
            set(document.captures.values_list("side", flat=True)), {"front", "back"}
        )
        document.status = IdentityDocumentStatus.PROCESSED
        document.save(update_fields=["status", "updated_at"])
        self.verification.status = "awaiting_selfie"
        self.verification.save(update_fields=["status", "updated_at"])
        self.values["selfie_file_size_bytes"] = len(content)
        self.request_item("Create Selfie Upload")
        self.request_item("Transfer Selfie", content=content)
        self.request_item("Submit Selfie")
        self.assertTrue(self.values["selfie_capture_id"])
