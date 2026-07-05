DOCUMENT_TYPES = [
    {"code": "national_id", "name": "National ID"},
    {"code": "passport", "name": "Passport"},
    {"code": "driver_license", "name": "Driver License"},
    {"code": "health_id", "name": "Health ID"},
]

COUNTRY_PROFILES = [
    {
        "code": "GH",
        "name": "Ghana",
        "supported_document_types": [
            {"document_type": "national_id", "local_name": "Ghana Card"},
            {"document_type": "passport", "local_name": "Passport"},
            {"document_type": "driver_license", "local_name": "Driver License"},
            {"document_type": "health_id", "local_name": "NHIS Card"},
        ],
    }
]
