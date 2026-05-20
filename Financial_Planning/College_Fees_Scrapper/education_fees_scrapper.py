"""
Education Fees Web Scrapper - Dynamic Fee Data Collection

What this file does:
This script implements an agentic web scrapper that dynamically collects college fee data
from the web, processes it, and stores structured data in pickle files for consumption
by the education_fees_calculation node.

What this file contains:
- Stream-duration mappings for different courses
- scrape_fees_for_stream: Scrapes and averages fees from top 10 colleges for a stream-destination pair
- convert_currency_if_needed: Fetches GBP to INR conversion rate and converts fees
- calculate_total_course_fees: Computes total course fees using annual fee and duration
- scrape_graduation_fees: Orchestrates scraping for all graduation stream-destination combinations
- scrape_post_graduation_fees: Orchestrates scraping for all post-graduation combinations
- generate_fee_pickles: Main execution function that generates pickle files
"""

import os
import pickle
import re
import json
from datetime import date
from typing import List, Literal
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from Financial_Planning.Agent.agent import Agent
from Financial_Planning.Models.llm_schemas import GraduationFee, PostGraduationFee, fees_list
from Financial_Planning.Toools.custom_tools import (calculate_overall_fees, currency_conversion, avg_fees)
from Financial_Planning.Toools.standard_tools import (tavily_tool)

# file='C:/Users/Aakash/projects/armstrong_v3/Financial_Planning/College_Fees_Scrapper/post_graduation_fees.pkl'
# #file='Financial_Planning/College_Fees_Scrapper.graduation_fees.pkl/post_graduation_fees.pkl'
# with open (file, 'rb') as f:
#     graduation_details=pickle.load(f)
# list(graduation_details)

# graduation_info=[]
# for info in graduation_details: 
#     graduation_destination=info.post_graduation_destination
#     graduation_stream=info.post_graduation_stream
#     current_fees_of_graduation=info.current_fees_of_post_graduation
#     graduation_info.append({'graduation_destination': graduation_destination, 'graduation_stream': graduation_stream, 'current_fees_of_graduation': current_fees_of_graduation})

# with open(file, 'wb') as f:
#     pickle.dump(graduation_details,f)

# import pickle
# file='C:/Users/Aakash/projects/armstrong_v3/Financial_Planning/College_Fees_Scrapper/default_graduation_fees.pkl'
# with open(file, "rb") as f:
#     post_grad=pickle.load(f)

# graduation_details=[{'graduation_destination': 'International', 'graduation_stream': 'B.tech', 'current_fees_of_graduation': 10826849.5}, 
# {'graduation_destination': 'International', 'graduation_stream': 'MBBS', 'current_fees_of_graduation': 17615234.87}, 
# {'graduation_destination': 'International', 'graduation_stream': 'B.com / BBA', 'current_fees_of_graduation': 10968112.54}, 
# {'graduation_destination': 'International', 'graduation_stream': 'Other', 'current_fees_of_graduation': 7200561}, 
# {'graduation_destination': 'Domestic', 'graduation_stream': 'B.Tech', 'current_fees_of_graduation': 1282600}, 
# {'graduation_destination': 'Domestic', 'graduation_stream': 'MBBS', 'current_fees_of_graduation': 4156100.1}, 
# {'graduation_destination': 'Domestic', 'graduation_stream': 'B.com / BBA', 'current_fees_of_graduation': 225849}, 
# {'graduation_destination': 'Domestic', 'graduation_stream': 'Other', 'current_fees_of_graduation': 657418}]

# file='C:/Users/Aakash/projects/armstrong_v3/Financial_Planning/College_Fees_Scrapper/default_graduation_fees.pkl'
# with open(file, "wb") as f:
#     pickle.dump(graduation_details, f)

# Load environment variables
load_dotenv()

AZURE_API_KEY = os.getenv('AZURE_API_KEY')
AZURE_API_BASE = os.getenv('AZURE_API_BASE')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')
AZURE_DEPLOYMENT_NAME = os.getenv('AZURE_DEPLOYMENT_NAME')

# Initialize Azure LLM
llm_azure = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_API_BASE,
    api_version=AZURE_API_VERSION,
    deployment_name=AZURE_DEPLOYMENT_NAME,
    temperature=0
)

# ======================== CONSTANTS ========================

# Maximum fee limits (to prevent outlier contamination)
MAX_ANNUAL_FEE_DOMESTIC = 1500000  # 50 lakhs INR
MAX_ANNUAL_FEE_INTERNATIONAL = 50000  # 50K GBP
MAX_TOTAL_COURSE_FEE = 30000000  # 3 crore INR

# Course duration mappings (in years)
GRADUATION_DURATION = {
    'B.Tech': 4,
    'MBBS': 4,
    'B.Com / BBA': 3,
    'Other': 3
}

POST_GRADUATION_DURATION = {
    'MBA': 2,
    'M.Tech': 2,
    'MD': 2,
    'Other': 2
}

# Stream combinations to scrape
GRADUATION_STREAMS = ['B.Tech', 'MBBS', 'B.Com / BBA', 'Other']
POST_GRADUATION_STREAMS = ['MBA', 'M.Tech', 'MD', 'Other']
DESTINATIONS = ['International', 'Domestic']

# ======================== HELPER FUNCTIONS ========================

def scrape_fees_for_stream(destination: Literal['International', 'Domestic'], stream: str, education_level: Literal['graduation', 'post-graduation']):
    """
    Scrape annual fees for top 10 colleges for a given destination and stream.

    Args:
        destination: 'International' (UK) or 'Domestic' (India)
        stream: Stream of study (e.g., 'Engineering', 'MBA')
        education_level: 'graduation' or 'post-graduation'

    Returns:
        Average annual fee in the local currency (GBP for UK, INR for India)
    """
    # Construct search query based on destination
    location = "UK" if destination == "International" else "India"

    search_query = f"top 5 {stream} colleges in {location} annual tuition fees"

    print(f"\nSearching for: {search_query}")

    # Use Tavily to search
    search_results = tavily_tool.invoke({"query": search_query})

    # Create an agent to extract fee information
    # Set realistic fee bounds based on destination
    if location == "India":
        min_fee, max_fee = 10000, MAX_ANNUAL_FEE_DOMESTIC
    else:  # UK
        min_fee, max_fee = 10000, MAX_ANNUAL_FEE_INTERNATIONAL

    system_prompt = f"""You are a financial data extraction expert. Your task is to:
    1. Analyze the search results provided
    2. Extract annual tuition fees for approximately 10 top colleges for {stream} in {location} for education level {education_level}
    3. Return ONLY numeric values representing ANNUAL tuition fees (no currency symbols, no commas)
    4. If fees are given as ranges, use the average
    5. Return a list of fee values

    IMPORTANT VALIDATION RULES: 
    - ONLY extract annual tuition fee numbers (not years like 2025, not total program costs, not percentages)
    - Each fee should be between {min_fee:,} and {max_fee:,} (local currency)
    - Exclude any numbers that don't represent annual tuition fees
    - Exclude scientific notation or extremely large outlier values
    - If you find total program costs, divide by typical duration to get annual fee

    Search results: {search_results}

    Extract the annual fees and return them as a comma-separated list of numbers.
    Example format: 25000, 28000, 30000, 27500, 26000, 29000, 31000, 28500, 27000, 26500
    """

    # Use LLM to extract fees
    extraction_agent = Agent(
        model=llm_azure,
        tools=[],
        system=system_prompt
    )
     
    result = extraction_agent.graph.invoke({
        "messages": [HumanMessage(content=f"Extract annual tuition fees for top {stream} colleges in {location} from the search results.")]
    })

    # Parse the extracted fees
    fee_text = result['messages'][-1].content

    fees_list_llm=llm_azure.with_structured_output(fees_list)
    fees=fees_list_llm.invoke(f"Represent the provided data in list of floats format: {fee_text} \n **DO ENSURE THAT THE FEES ARE IN NUMERIC FORMAT IN FLOAT TYPE AND DOES NOT CONTAIN ANY COMMA BETWEEN THEM**").fee_list

    fees = [float(f) for f in fees]

    # Filter outliers using IQR method and apply max fee substitution
    if len(fees) >= 4:
        fees_sorted = sorted(fees)
        q1_idx = len(fees_sorted) // 4
        q3_idx = 3 * len(fees_sorted) // 4
        q1, q3 = fees_sorted[q1_idx], fees_sorted[q3_idx]
        iqr = q3 - q1
        lower_bound = max(min_fee, q1 - 1.5 * iqr)
        upper_bound = min(max_fee, q3 + 1.5 * iqr)

        # Process fees: filter within bounds OR substitute max_fee if exceeded
        fees_processed = []
        max_fee_substitutions = 0

        for f in fees:
            if f < lower_bound:
                fees_processed.append(max_fee/2)
                max_fee_substitutions += 1
            elif f > max_fee:
                # Substitute with max_fee if upper limit exceeded
                fees_processed.append(max_fee/1.5)
                max_fee_substitutions += 1

        # Use processed fees if we have at least 5 valid values
        if len(fees_processed) >= 5:
            fees = fees_processed[:10]
            if max_fee_substitutions > 0:
                print(f"⚠️  {max_fee_substitutions} fees exceeded max limit, substituted with {max_fee:,.0f}")
            filtered_count = len(fees) - len(fees_processed)
            if filtered_count > 0:
                print(f"Filtered {filtered_count} outliers. Valid range: {lower_bound:.0f}-{upper_bound:.0f}")

    # Take first 10 values
    fees = fees[:10]

    # If we don't have 10 values, pad with the median of what we have
    if len(fees) < 10 and len(fees) > 0:
        median_fee = sorted(fees)[len(fees) // 2]
        fees.extend([median_fee] * (10 - len(fees)))
    elif len(fees) == 0:
        # Fallback: use midpoint of expected range
        fallback_fee = (min_fee + max_fee) / 2
        fees = [fallback_fee] * 10
        print(f"⚠️  No valid fees found, using fallback: {fallback_fee:.0f}")

    # Calculate average using custom tool
    average_fee = avg_fees.invoke({"colleges": fees})
    print(f"Average annual fee for {stream} in {location}: {average_fee}")
    return average_fee


def convert_currency_if_needed(amount: float, destination: Literal['International', 'Domestic']) -> float:
    """
    Convert currency from GBP to INR if destination is International (UK).

    Args:
        amount: Amount in local currency
        destination: 'International' or 'Domestic'

    Returns:
        Amount in INR
    """
    if destination == 'Domestic':
        return amount  # Already in INR

    # Fetch latest GBP to INR conversion rate
    search_query = "GBP to INR conversion rate latest 2025"
    print(f"\nFetching conversion rate: {search_query}")

    search_results = tavily_tool.invoke({"query": search_query})

    # Extract conversion rate using LLM
    system_prompt = f"""You are a currency conversion expert. Extract the latest GBP to INR conversion rate from the search results.

    Search results: {search_results}

    Return ONLY the numeric conversion rate (e.g., if 1 GBP = 105.25 INR, return 105.25).
    """

    extraction_agent = Agent(
        model=llm_azure,
        tools=[],
        system=system_prompt
    )

    result = extraction_agent.graph.invoke({
        "messages": [HumanMessage(content="Extract the GBP to INR conversion rate.")]
    })

    rate_text = result['messages'][-1].content
    conversion_rate = float(re.findall(r'\d+(?:\.\d+)?', rate_text)[0])

    print(f"GBP to INR rate: {conversion_rate}")

    # Convert using custom tool
    amount_in_inr = currency_conversion.invoke({
        "amount_to_convert": amount,
        "conversion_ratio": conversion_rate
    })

    print(f"Converted {amount} GBP to {amount_in_inr} INR")

    return float(amount_in_inr)


def calculate_total_course_fees(
    annual_fee_inr: float,
    stream: str,
    education_level: Literal['graduation', 'post-graduation']
) -> float:
    """
    Calculate total course fees using annual fee and course duration.

    Args:
        annual_fee_inr: Annual fee in INR
        stream: Stream of study
        education_level: 'graduation' or 'post-graduation'

    Returns:
        Total course fees in INR
    """
    # Get duration for the stream
    if education_level == 'graduation':
        duration = GRADUATION_DURATION.get(stream, 3)
    else:
        duration = POST_GRADUATION_DURATION.get(stream, 2)

    # Calculate total fees using custom tool
    total_fees = calculate_overall_fees.invoke({
        "annual_fees": annual_fee_inr,
        "duration": duration
    })

    print(f"Total {education_level} fees for {stream} ({duration} years): {total_fees} INR")

    return float(total_fees)


# ======================== MAIN SCRAPING FUNCTIONS ========================

def scrape_graduation_fees() -> List[GraduationFee]:
    """
    Scrape graduation fees for all destination-stream combinations.

    Returns:
        List of GraduationFee objects with structured data
    """ 
    graduation_fees = []
    structured_llm = llm_azure.with_structured_output(GraduationFee)

    print("\n" + "="*60)
    print("SCRAPING GRADUATION FEES")
    print("="*60) 

    for destination in DESTINATIONS:
        for stream in GRADUATION_STREAMS:
            print(f"\n--- Processing: {destination} - {stream} ---")

            try:
                # Step 1: Scrape annual fees
                annual_fee = scrape_fees_for_stream(destination, stream, 'graduation')

                # Step 2: Convert to INR if needed
                annual_fee_inr = convert_currency_if_needed(annual_fee, destination)

                # Step 3: Calculate total course fees
                total_fees = calculate_total_course_fees(annual_fee_inr, stream, 'graduation')

                # Step 3.5: Validate total fees before structuring
                if total_fees >= MAX_TOTAL_COURSE_FEE:
                    print(f"⚠️  WARNING: Total fees {total_fees:.2e} exceeds max limit for {destination} {stream}")
                    print(f"   Using maximum allowed fee: {MAX_TOTAL_COURSE_FEE:,} INR")
                    total_fees = MAX_TOTAL_COURSE_FEE
                elif total_fees <= 0:
                    print(f"⚠️  ERROR: Invalid fee value {total_fees} for {destination} {stream}")
                    print(f"   Using fallback fee calculation")
                    # Use midpoint of expected range based on duration
                    duration = GRADUATION_DURATION.get(stream, 3)
                    total_fees = (50000 + MAX_ANNUAL_FEE_DOMESTIC) / 2 * duration

                # Step 4: Structure output using LLM
                prompt = f"""Create a structured graduation fee record with the following data:
                - Destination: {destination}
                - Stream: {stream}
                - Total Fees (INR): {total_fees}

                Ensure the fees value is a clean float with no commas or currency symbols.
                """

                structured_data = structured_llm.invoke(prompt)
                graduation_fees.append(structured_data)

                print(f" Successfully processed {destination} - {stream}")

            except Exception as e:
                print(f" Error processing {destination} - {stream}: {str(e)}")
                # Create fallback record to ensure we always have complete data
                print(f"   Using fallback: MAX_TOTAL_COURSE_FEE")
                try:
                    fallback_prompt = f"""Create a structured graduation fee record with the following data:
                    - Destination: {destination}
                    - Stream: {stream}
                    - Total Fees (INR): {MAX_TOTAL_COURSE_FEE}

                    Ensure the fees value is a clean float with no commas or currency symbols.
                    """
                    fallback_data = structured_llm.invoke(fallback_prompt)
                    graduation_fees.append(fallback_data)
                    print(f"✓ Created fallback record for {destination} - {stream}")
                except Exception as fallback_error:
                    # Last resort: manually create record
                    print(f"⚠️  Fallback LLM failed, creating manual record: {fallback_error}")
                    manual_record = GraduationFee(
                        graduation_destination=destination,
                        graduation_stream=stream,
                        current_fees_of_graduation=float(MAX_TOTAL_COURSE_FEE)
                    )
                    graduation_fees.append(manual_record)
                    print(f"✓ Created manual fallback record for {destination} - {stream}")

    return graduation_fees


def scrape_post_graduation_fees():
    """
    Scrape post-graduation fees for all destination-stream combinations.

    Returns: 
        List of PostGraduationFee objects with structured data
    """
    post_graduation_fees = []
    structured_llm = llm_azure.with_structured_output(PostGraduationFee)

    print("\n" + "="*60)
    print("SCRAPING POST-GRADUATION FEES")
    print("="*60)

    for destination in DESTINATIONS:
        for stream in POST_GRADUATION_STREAMS:
            print(f"\n--- Processing: {destination} - {stream} ---")

            try:
                # Step 1: Scrape annual fees
                annual_fee = scrape_fees_for_stream(destination, stream, 'post-graduation')

                # Step 2: Convert to INR if needed
                annual_fee_inr = convert_currency_if_needed(annual_fee, destination)

                # Step 3: Calculate total course fees
                total_fees = calculate_total_course_fees(annual_fee_inr, stream, 'post-graduation')

                # Step 3.5: Validate total fees before structuring
                if total_fees >= MAX_TOTAL_COURSE_FEE:
                    print(f"⚠️  WARNING: Total fees {total_fees:.2e} exceeds max limit for {destination} {stream}")
                    print(f"   Using maximum allowed fee: {MAX_TOTAL_COURSE_FEE:,} INR")
                    total_fees = MAX_TOTAL_COURSE_FEE
                elif total_fees <= 0:
                    print(f"⚠️  ERROR: Invalid fee value {total_fees} for {destination} {stream}")
                    print(f"   Using fallback fee calculation")
                    # Use midpoint of expected range based on duration
                    duration = POST_GRADUATION_DURATION.get(stream, 2)
                    total_fees = (50000 + MAX_ANNUAL_FEE_DOMESTIC) / 2 * duration

                # Step 4: Structure output using LLM
                prompt = f"""Create a structured post-graduation fee record with the following data:
                - Destination: {destination}
                - Stream: {stream}
                - Total Fees (INR): {total_fees}

                Ensure the fees value is a clean float with no commas or currency symbols.
                """

                structured_data = structured_llm.invoke(prompt)
                post_graduation_fees.append(structured_data)

                print(f" Successfully processed {destination} - {stream}")

            except Exception as e:
                print(f" Error processing {destination} - {stream}: {str(e)}")
                # Create fallback record to ensure we always have complete data
                print(f"   Using fallback: MAX_TOTAL_COURSE_FEE")
                try:
                    fallback_prompt = f"""Create a structured post-graduation fee record with the following data:
                    - Destination: {destination}
                    - Stream: {stream}
                    - Total Fees (INR): {MAX_TOTAL_COURSE_FEE}

                    Ensure the fees value is a clean float with no commas or currency symbols.
                    """
                    fallback_data = structured_llm.invoke(fallback_prompt)
                    post_graduation_fees.append(fallback_data)
                    print(f"✓ Created fallback record for {destination} - {stream}")
                except Exception as fallback_error:
                    # Last resort: manually create record
                    print(f"⚠️  Fallback LLM failed, creating manual record: {fallback_error}")
                    manual_record = PostGraduationFee( 
                        post_graduation_destination=destination,
                        post_graduation_stream=stream,
                        current_fees_of_post_graduation=float(MAX_TOTAL_COURSE_FEE)
                    ) 
                    post_graduation_fees.append(manual_record)
                    print(f"✓ Created manual fallback record for {destination} - {stream}")

    return post_graduation_fees

# ======================== MAIN EXECUTION ========================

def generate_fee_pickles():
    """
    Main execution function that generates both pickle files.
    """
    print("\n" + "="*60)
    print("EDUCATION FEES SCRAPPER")
    print("="*60)

    # Get the directory where this script is located
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = 'Financial_Planning/College_Fees_Scrapper'
    try:
        # Scrape graduation fees
        print("\n[1/2] Scraping graduation fees...")
        graduation_fees = scrape_graduation_fees()
        #print(f"graduation fees: {graduation_fees}")

        # Validate graduation fees count (2 destinations × 4 streams = 8 records)
        EXPECTED_GRADUATION_RECORDS = len(DESTINATIONS) * len(GRADUATION_STREAMS)
        if len(graduation_fees) != EXPECTED_GRADUATION_RECORDS:
            print(f"⚠️  WARNING: Expected {EXPECTED_GRADUATION_RECORDS} graduation records, got {len(graduation_fees)}")
        else:
            print(f"✓ Validated: {len(graduation_fees)} graduation records (complete)")

        graduation_info=[]
        for info in graduation_fees: 
            graduation_destination=info.graduation_destination
            graduation_stream=info.graduation_stream
            current_fees_of_graduation=info.current_fees_of_graduation
            graduation_info.append({'graduation_destination': graduation_destination, 'graduation_stream': graduation_stream,'current_fees_of_graduation': current_fees_of_graduation })
        
        print(f"graduation_fees: {graduation_info}")
        graduation_pkl_path = os.path.join(script_dir, 'graduation_fees.pkl')
        with open(graduation_pkl_path, 'wb') as f:
            pickle.dump(graduation_info, f) 
        print(f"\n Saved graduation fees to: {graduation_pkl_path}")
        print(f"  Total records: {len(graduation_fees)}")

        # Scrape post-graduation fees
        print("\n[2/2] Scraping post-graduation fees...")
        post_graduation_fees = scrape_post_graduation_fees()
        print(f"post graduation fees: {post_graduation_fees}")

        # Validate post-graduation fees count (2 destinations × 5 streams = 10 records)
        EXPECTED_POST_GRADUATION_RECORDS = len(DESTINATIONS) * len(POST_GRADUATION_STREAMS)
        if len(post_graduation_fees) != EXPECTED_POST_GRADUATION_RECORDS:
            print(f"⚠️  WARNING: Expected {EXPECTED_POST_GRADUATION_RECORDS} post-graduation records, got {len(post_graduation_fees)}")
        else:
            print(f"✓ Validated: {len(post_graduation_fees)} post-graduation records (complete)")

        post_graduation_info=[]
        for info in post_graduation_fees: 
            post_graduation_destination=info.post_graduation_destination
            post_graduation_stream=info.post_graduation_stream
            current_fees_of_post_graduation=info.current_fees_of_post_graduation
            post_graduation_info.append({'post_graduation_destination': post_graduation_destination, 'post_graduation_stream': post_graduation_stream,'current_fees_of_post_graduation': current_fees_of_post_graduation })

        print(f"post_graduation_fees: {post_graduation_fees}")
        # Save to pickle
        post_graduation_pkl_path = os.path.join(script_dir, 'post_graduation_fees.pkl')
        with open(post_graduation_pkl_path, 'wb') as f:
            pickle.dump(post_graduation_info, f) 
        print(f"\n Saved post-graduation fees to: {post_graduation_pkl_path}")
        print(f"  Total records: {len(post_graduation_fees)}")

        print("\n" + "="*60)
        print("SCRAPING COMPLETED SUCCESSFULLY")
        print("="*60)

        # Display summary
        print("\n📊 SUMMARY:")
        print(f"  Graduation records: {len(graduation_fees)}")
        print(f"  Post-graduation records: {len(post_graduation_fees)}")
        print(f"\n  Files generated:")
        print(f"    - {graduation_pkl_path}")
        print(f"    - {post_graduation_pkl_path}")

    except Exception as e:
        print(f"\n ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

file='C:/Users/Aakash/projects/armstrong_v3/Financial_Planning/College_Fees_Scrapper/last_update.pkl'
with open(file, 'rb') as f: 
    picl=pickle.load(f)

current_date=date.today()

if abs(current_date.month-picl[0])>3:
    generate_fee_pickles()

    with open(file, 'wb') as f: 
        pickle.dump([current_date.month], f)

if __name__ == "__main__":
    generate_fee_pickles()