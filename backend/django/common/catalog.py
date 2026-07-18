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
            {"document_type": "national_id", "local_name": "National ID"},
            {"document_type": "passport", "local_name": "Passport"},
            {"document_type": "driver_license", "local_name": "Driver License"},
            {"document_type": "health_id", "local_name": "Health ID"},
            {"document_type": "voter_id", "local_name": "Voter ID"},
        ],
    },
    {
        "code": "NG",
        "name": "Nigeria",
        "supported_document_types": [
            {"document_type": "passport", "local_name": "Passport"},
        ],
    },
    {
        "code": "SN",
        "name": "Senegal",
        "supported_document_types": [
            {"document_type": "passport", "local_name": "Passeport"},
        ],
    },
    {
        "code": "TG",
        "name": "Togo",
        "supported_document_types": [
            {"document_type": "passport", "local_name": "Passeport"},
        ],
    },
    {
        "code": "CI",
        "name": "Côte d’Ivoire",
        "supported_document_types": [
            {"document_type": "passport", "local_name": "Passeport"},
        ],
    },
]
