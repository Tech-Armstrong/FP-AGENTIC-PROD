Objective
Create a Python agent named education_fees_scrapper within the file education_fees_scrapper.py. This agent's primary function is to replace the hardcoded fee calculations in the education_fees_calculation node (from child_education_nodes.py) with dynamically scraped and processed data from the web.

The agent will generate two separate pickle files: one for graduation fees and one for post-graduation fees.

Context
The current system uses predefined, static values for college fees. This agent will introduce a dynamic data pipeline by scraping real-world fee information, processing it, and storing it in a structured format that the education_fees_calculation node can consume.

Required Tools
The agent must utilize the following tools:

tavily: For web searches, specifically to find college fees and the latest currency conversion rates.

currency_conversion: To convert fees from foreign currencies (GBP) to Indian Rupees (INR).

calculate_overall_fees: To compute the total course fees based on the annual fee and course duration.

A Structured LLM (Pydantic integration): To ensure the final output strictly adheres to the specified data schema.

Data Structure and Schema
The final output for each category (graduation and post-graduation) must be a list of Pydantic models, which will then be saved to a pickle file.

1. Graduation Fees Schema:
json
[
  {
    "graduation_destination": "International",
    "graduation_stream": "Engineering",
    "current_fees_of_graduation": 2488640
  },
  ...
]
2. Post-Graduation Fees Schema:
json
[
  {
    "post_graduation_destination": "International",
    "post_graduation_stream": "MBA",
    "current_fees_of_post_graduation": 5748390
  },
  ...
]
Agent Workflow
The agent must execute the following steps for both graduation and post-graduation courses separately.

Scrape Annual College Fees:

For each predefined destination (International, Domestic) and stream (e.g., Engineering, MBA):

Use the tavily tool to search for the annual fees of the top 10 colleges for that specific stream and destination.

Destination Rule:

If destination is International, search for colleges exclusively in the UK.

If destination is Domestic, search for colleges exclusively in India.

Calculate the average of these top 10 annual fees.

Sanitize Fee Data:

Ensure the resulting average annual fee is a clean numerical value (float or integer) and contains no commas (e.g., 345532.45).

Perform Currency Conversion:

If the fees were scraped from UK colleges (and are in GBP), they must be converted to INR.

First, use the tavily tool to fetch the latest GBP to INR conversion rate.

Next, use the currency_conversion tool, providing the annual fee and the fetched conversion rate, to get the amount in INR.

Calculate Overall Course Fees:

Use the calculate_overall_fees tool to determine the total cost of the entire course. This tool will take the annual fee (in INR) and the standard duration of the course stream as input.

Structure the Final Output:

After calculating the final average overall fee (in INR) for a destination-stream pair, pass this data to a structured LLM integrated with a Pydantic model.

This step is critical to ensure the output is formatted correctly into a dictionary matching the schemas defined above.

Store Data in Pickle File:

Collect the structured dictionaries for all destination-stream combinations into a single list.

Serialize and save this final list into a dedicated pickle file (graduation_fees.pkl or post_graduation_fees.pkl).