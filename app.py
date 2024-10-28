import os
import json
import dotenv
import openai
from swarm import Swarm, Agent
from swarm.core import Result

from utils_document import extract_data_from_pdf

# Load environment variables
dotenv.load_dotenv()

# Setup OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

data_extraction_status = False
data_storage = dict()

# Setup Swarm client
client = Swarm()


# Setup functions
def transfer_to_agent_processor():
    """Transfer to the Data Processor Agent."""
    return agent_data_processor

def transfer_to_agent_validator():
    """Transfer to the Data Validator Agent."""
    return agent_data_validator


def required_data_format():
    """Return the required datapoints that the `Data Processor Agent` needs to extract from the uploaded document.

    Args: None
    """
    return {
        "site_meta_data": {
            "how_many_chiller": int,
            "how_many_total_pchp": int,
            "how_many_vsd_pchp": int,
            "how_many_total_schp": int,
            "how_many_vsd_schp": int,
            "how_many_total_cdp": int,
            "how_many_vsd_cdp": int,
            "how_many_cooling_tower": int,
            "operation_hour": str,
        },
        "technical_data": {
            "average_ton": float,
            "average_kw": float,
            "average_kw_per_ton": float,
            "each_chiller_chs_temp": list[float],
            "each_chiller_chr_temp": list[float],
            "each_chiller_chwdelta_temp": list[float],
            "each_chiller_cds_temp": list[float],
            "each_chiller_cdr_temp": list[float],
            "each_chiller_cdwdelta_temp": list[float],
            "each_chiller_setpoint": list[float],
            "site_wetbulb_temperature": float,
        }
    }


def data_processor_function(document_path: str, error_message: str = None):
    """Read the document and extract the data in the required format.
    
    Args:
        document_path (str): Path to the PDF document.
        error_message (str): Error message explaining why the data is not valid (optional)
      
    Returns:
        dict: Dictionary containing the processed data including `site_meta_data` and `technical_data`
    """
    print("\nProcessing data...")
    
    # TODO: Implement the data processing logic here
    site_meta_data = dict()
    technical_data = dict()
    
    response: str = extract_data_from_pdf(document_path)
    response = response.replace("None", '"None"')
    print(response)
    # parse json to dict
    if isinstance(response, str):
        response_dict = json.loads(response)
        site_meta_data = response_dict["site_meta_data"]
        technical_data = response_dict["technical_data"]
    else:
        site_meta_data = response["site_meta_data"]
        technical_data = response["technical_data"]

    payload = {"site_meta_data": site_meta_data, "technical_data": technical_data}
    print("results: ", payload)

    return payload


def data_validation_function(site_meta_data: dict, technical_data: dict):
    """Validate the data structure and format.
    
    Args:
        site_meta_data (dict): Dictionary containing site metadata like equipment counts and operation hours
        technical_data (dict): Dictionary containing technical measurements and parameters
        
    Returns:
        Result: A Result object containing:
            - value: "Done" if validation passes
            - agent: Reference to data validator agent
            - context_variables: Dict with validated data and any error messages
    """
    print("\nValidating data...")
    
    # Implement the data validation logic here
    error_message = None
    
    # validate site_meta_data
    required_site_meta_data_keys = required_data_format()["site_meta_data"].keys()
    # required_site_meta_data_keys = ['how_many_chiller', 'how_many_total_pchp', 'how_many_vsd_pchp', 'how_many_total_schp', 'how_many_vsd_schp', 'how_many_total_cdp', 'how_many_vsd_cdp', 'how_many_cooling_tower', 'operation_hour']
    missing_site_meta_data_keys = []
    for key in required_site_meta_data_keys:
        if key not in site_meta_data.keys():
            missing_site_meta_data_keys.append(key)

    
    # technical_data
    required_technical_data = required_data_format()["technical_data"].keys()
    # required_technical_data = ['average_ton', 'average_kw', 'average_kw_per_ton', 'each_chiller_chs_temp', 'each_chiller_chr_temp', 'each_chiller_chwdelta_temp', 'each_chiller_cds_temp', 'each_chiller_cdr_temp', 'each_chiller_cdwdelta_temp', 'each_chiller_setpoint', 'site_wetbulb_temperature']
    missing_technical_data_keys = []
    for key in required_technical_data:
        if key not in technical_data.keys():
            missing_technical_data_keys.append(key)
    
    incomplete_chiller_data_keys = []
    for key in ['each_chiller_chs_temp', 'each_chiller_chr_temp', 'each_chiller_chwdelta_temp', 'each_chiller_cds_temp', 'each_chiller_cdr_temp', 'each_chiller_cdwdelta_temp', 'each_chiller_setpoint']:
        if len(technical_data.get(key)) != site_meta_data.get('how_many_chiller'):
            incomplete_chiller_data_keys.append(key)
    
    if (len(missing_site_meta_data_keys) > 0) or (len(missing_technical_data_keys) > 0) or (len(incomplete_chiller_data_keys) > 0):
        error_message = "There is missing datapoint in extracted data. Please check these following datapoints and try again."
    if len(missing_site_meta_data_keys) > 0:
        error_message += f"\nMissing site meta data keys: {missing_site_meta_data_keys}"
    if len(missing_technical_data_keys) > 0:
        error_message += f"\nMissing technical data keys: {missing_technical_data_keys}"
    if len(incomplete_chiller_data_keys) > 0:
        error_message += f"\nIncomplete chiller data keys: {incomplete_chiller_data_keys}"
    
    data_extraction_status = True  # TODO: need to remove later
    data_storage = {"site_meta_data": site_meta_data, "technical_data": technical_data}
    if error_message is not None:
        return Result(
            value="Error",
            agent=agent_data_validator,
            context_variables={"error_message": error_message}
        )
    
    data_extraction_status = True
    data_storage = {"site_meta_data": site_meta_data, "technical_data": technical_data}
    return Result(
       value="Done",
       agent=agent_data_validator,
       context_variables={"site_meta_data": site_meta_data, "technical_data": technical_data, "data_extraction_status": "completed"}
   )


# Setup agents
agent_data_processor = Agent(
    name="Data Processor Agent",
    model="gpt-4o",
    instructions="""
    You are a helpful data processor agent. You will be given a document and you need to extract the data and return it in a structured format.
    You will always required to call the `Data Validator Agent` to ensure the data is valid.
    """,
    functions=[
        required_data_format,
        data_processor_function,
        transfer_to_agent_validator
    ]
)

agent_data_validator = Agent(
    name="Data Validator Agent",
    model="gpt-4o",
    instructions="""
    You are a helpful Data Validator Agent. You will be given a document and you need to validate the data structure and format.
    You will work continuously together with the `Data Processor Agent` to ensure the data is valid.
    If the data is not valid or missing, you need to return an error message with the reason why the data is not valid. 
    Then ask the user to provide the missing data and try again.
    """,
    functions=[
        required_data_format,
        data_validation_function,
        transfer_to_agent_processor
    ]
)

if __name__ == "__main__":
    messages = [
            {"role": "system", "content": """
                You are a helpful data processor agent. You will be given a document and you need to extract the data and return it in a structured format. 
                You will always required to call the `Data Validator Agent` to ensure the data is valid.
                You could access document path by using the `document_path` context variable.
                """},
            {"role": "user", "content": "I have provided a document with the data of a cooling plant. Please extract the data and return it in a structured format."}
        ]
    
    print("Hello, I'm Building Energy Gap Analysis agent. Please upload a document with the data of a cooling plant.")
    while True:
        _input = input("\nINPUT:")

        if data_extraction_status is False:
            # Step 1: Handle the uploaded document in a structured format. Using validation to ensure the data is in the required format.
            response = client.run(
                agent=agent_data_processor,
                context_variables={"document_path": "./2023 CHILLER PLANT AUDIT REPORT.pdf", "data_extraction_status": "not complete"},
                messages=messages
            )
            print(response.messages[-1]["content"])
            messages.append({"role": "assistant", "context": response.messages[-1]["content"]})
            data_extraction_status = True
            print("eiei")
            print(data_storage)

        # Step 2: Process Gap Analysis on Energy Saving opportunities of the Cooling Plant.
        # TODO: Implement the Gap Analysis logic here
        if data_extraction_status is True:
            print("Providing Gap Analysis ...")

            site_meta_data = data_storage["site_meta_data"]
            technical_data = data_storage["technical_data"]
            print(site_meta_data, technical_data)
            average_kw_per_ton = technical_data["average_kw_per_ton"]
            print(average_kw_per_ton)
