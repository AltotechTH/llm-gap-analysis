import os
import dotenv
import openai
from swarm import Swarm, Agent
from swarm.core import Result

# Load environment variables
dotenv.load_dotenv()

# Setup OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
            "how_many_pchp": int,
            "how_many_vsd_pchp": int,
            "how_many_schp": int,
            "how_many_vsd_schp": int,
            "how_many_cdp": int,
            "how_many_vsd_cdp": int,
            "how_many_cooling_tower": int,
            "operation_hour": int,
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
    print("Processing data...")
    
    # TODO: Implement the data processing logic here
    required_data_format_dict = required_data_format()
    site_meta_data = dict()
    technical_data = dict()

    return {"site_meta_data": site_meta_data, "technical_data": technical_data}


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
    print("Validating data...")
    
    # TODO: Implement the data validation logic here
    error_message = None
    
    return Result(
       value="Done",
       agent=agent_data_validator,
       context_variables={"site_meta_data": site_meta_data, "technical_data": technical_data, "error_message": error_message}
   )


# Setup agents
agent_data_processor = Agent(
    name="Data Processor Agent",
    model="gpt-4o",
    instructions="""
    You are a helpful data processor agent. You will be given a document and you need to extract the data and return it in a structured format.
    You will work continuously together with the `Data Validator Agent` to ensure the data is valid.
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
    If the data is not valid, you should return an error message with the reason why the data is not valid. 
    Then, the `Data Processor Agent` will try to extract the requireddata again.
    """,
    functions=[
        required_data_format,
        data_validation_function,
        transfer_to_agent_processor
    ]
)

# Step 1: Handle the uploaded document in a structured format. Using validation to ensure the data is in the required format.
response = client.run(
    agent=agent_data_processor,
    context_variables={"document_path": "2023 CHILLER PLANT AUDIT REPORT.pdf"},
    messages=[{"role": "user", "content": "I have provided a document with the data of a cooling plant. Please extract the data and return it in a structured format."}],
)
print(response.messages[-1]["content"])

# Step 2: Process Gap Analysis on Energy Saving opportunities of the Cooling Plant.
# TODO: Implement the Gap Analysis logic here
