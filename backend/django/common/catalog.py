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
            {
                "document_type": "national_id",
                "local_name": "National ID",
                "capture_sides": ["front", "back"],
            },
            {
                "document_type": "passport",
                "local_name": "Passport",
                "capture_sides": ["single"],
            },
        ],
    },
    {
        "code": "NG",
        "name": "Nigeria",
        "supported_document_types": [
            {
                "document_type": "passport",
                "local_name": "Passport",
                "capture_sides": ["single"],
            },
        ],
    },
    {
        "code": "SN",
        "name": "Senegal",
        "supported_document_types": [
            {
                "document_type": "passport",
                "local_name": "Passeport",
                "capture_sides": ["single"],
            },
        ],
    },
    {
        "code": "TG",
        "name": "Togo",
        "supported_document_types": [
            {
                "document_type": "passport",
                "local_name": "Passeport",
                "capture_sides": ["single"],
            },
        ],
    },
    {
        "code": "CI",
        "name": "Côte d’Ivoire",
        "supported_document_types": [
            {
                "document_type": "passport",
                "local_name": "Passeport",
                "capture_sides": ["single"],
            },
        ],
    },
]
