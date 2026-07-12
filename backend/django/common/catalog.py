DOCUMENT_TYPES = [
    {"code": "national_id", "name": "National ID"},
    {"code": "passport", "name": "Passport"},
    {"code": "driver_license", "name": "Driver License"},
    {"code": "health_id", "name": "Health ID"},
    {"code": "voter_id", "name": "Voter ID"},
]

COUNTRY_PROFILES = [
    {
        "code": "GH",
        "name": "Ghana",
        "supported_document_types": [
            {"document_type": "national_id", "local_name": "NATIONAL IDENTIFICATION CARD"},
            {"document_type": "passport", "local_name": "PASSPORT"},
            {"document_type": "driver_license", "local_name": "DRIVER LICENSE"},
            {"document_type": "health_id", "local_name": "NHIS CARD"},
            {"document_type": "voter_id", "local_name": "VOTER CARD"},
        ],
    }
]
