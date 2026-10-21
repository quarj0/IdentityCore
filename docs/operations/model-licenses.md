# Face-model provenance and commercial-use review

The OpenCV Zoo model directories explicitly license all files in each directory:

| Model | Selected file | Published license |
| --- | --- | --- |
| YuNet detector | `face_detection_yunet_2026may.onnx` | MIT |
| SFace embeddings | `face_recognition_sface_2021dec.onnx` | Apache 2.0 |

The candidate fetch script pins OpenCV Zoo commit
`48b10fa505aeb51fbd127fc60a5c660040e823b7`, verifies Git LFS content SHA-256 and
byte counts, and verifies/preserves the license texts. No weights are committed to
IdentityCore. Immutable upstream source and license records:

- [YuNet directory](https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet), including its MIT license.
- [SFace directory](https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface), including its Apache-2.0 license.

Retain upstream copyright and license notices when distributing assets. IdentityCore's
proprietary license does not replace third-party terms. Record the selected release,
notices and any additional contractual requirements in the deployment review.

The legacy InsightFace code is MIT, but its published trained weights, including
`buffalo_l`, are offered for non-commercial research. See its [upstream license
statement](https://github.com/deepinsight/insightface#license). Do not infer a commercial
weight license from the code license. An existing licensed customer may retain that
engine; new example configuration selects the OpenCV candidate.

Commercially permissive licensing is separate from model approval and demonstrated
performance. Replacing embeddings changes score distributions. Keep existing
thresholds until held-out calibration establishes an appropriate operating point;
never claim 99.99% accuracy from a model-card benchmark, self-match or smoke test.
