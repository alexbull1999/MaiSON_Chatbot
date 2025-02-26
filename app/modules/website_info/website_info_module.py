import json
import os
from typing import Dict, Optional
from ..llm import LLMClient


class WebsiteInfoModule:
    """Module for handling website functionality and company information queries."""

    def __init__(self):
        self.llm_client = LLMClient()
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        print(f"Data directory path: {self.data_dir}")
        print(f"Data directory exists: {os.path.exists(self.data_dir)}")
        
        # List files in the data directory
        if os.path.exists(self.data_dir):
            print(f"Files in data directory: {os.listdir(self.data_dir)}")
        
        self._website_features = self._load_json_data("website_features.json")
        self._user_journey = self._load_json_data("user_journey.json")
        self._company_info = self._load_json_data("company_info.json")
        
        # Print loaded data sizes
        print(f"Loaded website_features.json: {len(self._website_features)} items")
        print(f"Loaded user_journey.json: {len(self._user_journey)} items")
        print(f"Loaded company_info.json: {len(self._company_info)} items")

    def _load_json_data(self, filename: str) -> Dict:
        """Load data from a JSON file in the data directory."""
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            # For test cases, only print one message
            if not os.path.exists(file_path):
                print(f"Warning: {filename} not found in {self.data_dir}")
                return {}
            
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    print(f"Successfully loaded {filename}")
                    return data
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}\nTraceback: {__import__('traceback').format_exc()}")
                return {}
                
        except Exception as e:
            print(f"Unexpected error with {filename}: {str(e)}")
            return {}

    async def handle_website_functionality(
        self, message: str, context: Optional[Dict] = None
    ) -> str:
        """Handle queries about website functionality and user journey."""
        try:
            # Check if we have the data
            if not self._website_features:
                print("Warning: No website features data available")
                return ("I apologize, but I don't have information about our website features at the moment." 
                        "Please contact our support team for assistance.")
            
            # Create a simplified version of the website features
            simplified_features = {}
            for key, feature in list(self._website_features.items())[:3]:  # Take only first 3 features
                if isinstance(feature, dict):
                    simplified_features[key] = {
                        "name": feature.get("name", ""),
                        "description": feature.get("description", "")
                    }
            
            # Convert JSON to string and escape curly braces to avoid format string issues
            features_json = json.dumps(simplified_features, indent=2).replace("{", "{{").replace("}", "}}")
            
            # Create prompt for the LLM
            prompt = (
                "You are an assistant for MaiSON-AI, a platform that helps people buy and sell homes "
                "without traditional estate agents. The user has asked a question about how to use "
                "the MaiSON website or about the steps in the buyer/seller journey.\n\n"
                "Here is information about our website features:\n\n"
                f"{features_json}\n\n"
                "User question: {0}\n\n"
                "Please provide a helpful response based on the information provided. "
                "If the information doesn't cover the user's question, provide general guidance "
                "about using the MaiSON platform and suggest they contact support for more specific help."
            )

            # Format the prompt with the user's message
            formatted_prompt = prompt.format(message)
            print(f"Debug - Formatted prompt length: {len(formatted_prompt)}")
            
            # Generate response using LLM
            try:
                response = await self.llm_client.generate_response(
                    messages=[{"role": "user", "content": formatted_prompt}],
                    temperature=0.7,
                    module_name="website_info",
                )
                return response
            except Exception as llm_error:
                print(f"LLM error in website functionality: {str(llm_error)}")
                # Make sure to return an error message that contains "apologize" and "error"
                return ("I apologize, but I encountered an error processing your question about our website. " 
                        "Please try again or contact our support team for assistance.")

        except Exception as e:
            import traceback
            print(f"Error handling website functionality query: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return ("I apologize, but I encountered an error processing your question about our website. " 
                    "Please try again or contact our support team for assistance.")

    async def handle_company_information(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle queries about company information, history, team, etc."""
        try:
            # Check if we have the data
            if not self._company_info:
                print("Warning: No company information data available")
                return "I apologize, but I don't have information about our company at the moment. Please visit our website for more information."
            
            # Create a simplified version of the company information
            simplified_info = {}
            
            # Include basic company info if available
            if "company" in self._company_info:
                simplified_info["company"] = self._company_info["company"]
            
            # Include leadership info if available and relevant
            if "team" in self._company_info and "leadership" in self._company_info["team"]:
                simplified_info["leadership"] = self._company_info["team"]["leadership"]
            
            # Convert JSON to string and escape curly braces to avoid format string issues
            company_json = json.dumps(simplified_info, indent=2).replace("{", "{{").replace("}", "}}")
            
            # Create prompt for the LLM
            prompt = (
                "You are an assistant for MaiSON-AI, a platform that helps people buy and sell homes "
                "without traditional estate agents. The user has asked a question about the MaiSON "
                "company, its history, mission, team, or other company-specific information.\n\n"
                "Here is information about our company:\n\n"
                f"{company_json}\n\n"
                "User question: {0}\n\n"
                "Please provide a helpful response based on the information provided. "
                "If the information doesn't cover the user's question, acknowledge the limitation "
                "and suggest they visit our website or contact us for more information."
            )

            # Format the prompt with the user's message
            formatted_prompt = prompt.format(message)
            print(f"Debug - Formatted company info prompt length: {len(formatted_prompt)}")
            
            # Generate response using LLM
            try:
                response = await self.llm_client.generate_response(
                    messages=[{"role": "user", "content": formatted_prompt}],
                    temperature=0.7,
                    module_name="website_info",
                )
                return response
            except Exception as llm_error:
                print(f"LLM error in company information: {str(llm_error)}")
                # Make sure to return an error message that contains "apologize" and "error"
                return ("I apologize, but I encountered an error processing your question about our company. " 
                        "Please try again or visit our website for more information.")

        except Exception as e:
            import traceback
            print(f"Error handling company information query: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return ("I apologize, but I encountered an error processing your question about our company. " 
                    "Please try again or visit our website for more information.")
