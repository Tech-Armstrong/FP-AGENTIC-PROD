"""Fallback fee tables when pickle files are not present."""

DEFAULT_GRADUATION_FEES = [
    {
        "graduation_destination": "Domestic",
        "graduation_stream": "Engineering",
        "current_fees_of_graduation": 1_200_000,
    },
    {
        "graduation_destination": "Domestic",
        "graduation_stream": "Medical",
        "current_fees_of_graduation": 2_500_000,
    },
    {
        "graduation_destination": "Domestic",
        "graduation_stream": "Commerce",
        "current_fees_of_graduation": 600_000,
    },
    {
        "graduation_destination": "Domestic",
        "graduation_stream": "General",
        "current_fees_of_graduation": 800_000,
    },
    {
        "graduation_destination": "International",
        "graduation_stream": "B.Tech",
        "current_fees_of_graduation": 4_000_000,
    },
    {
        "graduation_destination": "International",
        "graduation_stream": "MBA",
        "current_fees_of_graduation": 5_000_000,
    },
]

DEFAULT_POST_GRADUATION_FEES = [
    {
        "post_graduation_destination": "Domestic",
        "post_graduation_stream": "MBA",
        "current_fees_of_post_graduation": 1_500_000,
    },
    {
        "post_graduation_destination": "Domestic",
        "post_graduation_stream": "Medical",
        "current_fees_of_post_graduation": 3_000_000,
    },
    {
        "post_graduation_destination": "International",
        "post_graduation_stream": "MBA",
        "current_fees_of_post_graduation": 4_500_000,
    },
]
