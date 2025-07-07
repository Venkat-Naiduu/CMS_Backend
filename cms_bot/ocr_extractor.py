import os
import base64
from dotenv import load_dotenv
from openai import AzureOpenAI
from PIL import Image


def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the image: {e}")
        return None


def extract_ocr_details(image_path):

    load_dotenv()

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if not all([api_key, endpoint, deployment_name, api_version]):
        print("Error: Please make sure all environment variables are set in your .env file.")
        print("Required variables: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION")
        return

    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return

    try:
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that helps people extract information from documents. You will be provided with an image of an patient claiming insurance. Your task is to extract the following details: Provider , Patient , Sex , Hospital discharge procedures , History of present illness , hospital discharge physical findings , hospital discharge studies summary , hospital course , hospital discharge followup "
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Please extract the details (mention the details) from this image."
                        }
                    ]
                }
            ],
            max_tokens=2000
        )

        if response.choices:
            extracted_content = response.choices[0].message.content
            print("--- Extracted Patients Details ---")
            print("The extracted content was printed")
            print("--------------------------------")
            return extracted_content
        else:
            print("Could not extract details from the image. The response was empty.")

    except Exception as e:
        print(f"An error occurred while calling the Azure OpenAI API: {e}")


if __name__ == "__main__":

    ocr_image_file = "ocr.jpg" 
    
    if not os.path.exists(ocr_image_file):
         print(f"Error: The image file '{ocr_image_file}' was not found in the current directory.")
    else:
        extracted_text = extract_ocr_details(ocr_image_file) 
        if extracted_text:
            os.makedirs("extracted", exist_ok=True)
            with open("extracted/claim_001.txt", "w", encoding="utf-8") as f:
                f.write(extracted_text)

        
