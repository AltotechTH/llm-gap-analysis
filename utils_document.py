import openai
import requests
import PyPDF2  # Add this import
from pathlib import Path  # Add this import
import json


def extract_data_from_pdf(pdf_file_path: str) -> str:
    def read_pdf(file_path: str) -> str:
        """
        Reads a PDF file and returns its text content.
        """
        try:
            pdf_file = open(file_path, 'rb')
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            pdf_file.close()
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    # Define available functions
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_pdf",
                "description": "Read and extract text from a PDF file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the PDF file"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]

    client = openai.OpenAI(api_key='sk-WsXHCAvUutHKsx3i1p355ovzAWbp4dzQmcxKJtawNgT3BlbkFJY19N9IP0z22LG48EI71zVVneoCeF9w4wMtMZBWHQMA')

    PDF_FILE_PATH = "./2023 CHILLER PLANT AUDIT REPORT.pdf"
    USER_PROMPT = """
    Please extract the following data from the PDF file `./2023 CHILLER PLANT AUDIT REPORT.pdf`
    Only return a JSON object with the following structure without any other text messages:
    {
        "site_meta_data": {
            "how_many_chiller": int,  # How Many Chiller
            "how_many_total_pchp": int,  # How Many PCHP
            "how_many_vsd_pchp": int,  # How Many PCHP with VSD
            "how_many_total_schp": int,  # How Many SCHP
            "how_many_vsd_schp": int,  # How Many SCHP with VSD
            "how_many_total_cdp": int,  # How Many CDP
            "how_many_vsd_cdp": int,  # How Many CDP with VSD
            "how_many_cooling_tower": int,  # How Many Cooling Tower
            "operation_hour": str,  # Operation Hour
        },
        "technical_data": {
            "average_ton": float,  # Average Ton
            "average_kw": float,  # Average kW
            "average_kw_per_ton": float,  # Average kW/Ton
            "each_chiller_chs_temp": list[float],  # Each Chiller CHS Temp
            "each_chiller_chr_temp": list[float],  # Each Chiller CHR Temp
            "each_chiller_chwdelta_temp": list[float],  # Each Chiller CHWdeltaT Temp
            "each_chiller_cds_temp": list[float],  # Each Chiller CDS Temp
            "each_chiller_cdr_temp": list[float],  # Each Chiller CDR Temp
            "each_chiller_cdwdelta_temp": list[float],  # Each Chiller CDWdeltaT Temp
            "each_chiller_setpoint": list[float],  # Each Chiller Setpoint
            "site_wetbulb_temperature": float,  # Site Wetbulb temperature
        }
    }
    """

    # Update your completion call to include function calling
    completion = client.chat.completions.create(
        model="gpt-4",  # Make sure you're using a model that supports function calling
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT
            }
        ],
        tools=tools,
        tool_choice="auto"
    )

    # Handle the response
    response_message = completion.choices[0].message

    # Check if the model wants to call a function
    if response_message.tool_calls:
        # Process each tool call
        for tool_call in response_message.tool_calls:
            print(f"tool_call: {tool_call}")
            if tool_call.function.name == "read_pdf":
                # Parse the function arguments
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the function
                pdf_content = read_pdf(function_args["file_path"])
                
                # Send the function result back to the model
                second_completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "user",
                            "content": USER_PROMPT
                            # "content": "Please read and summarize the content of example.pdf"
                        },
                        response_message,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "read_pdf",
                            "content": pdf_content
                        }
                    ]
                )
                return second_completion.choices[0].message.content
    else:
        return response_message.content
