import re
import pandas as pd
from typing import Dict, Any, List

class ArabicRealEstateAgent:
    def __init__(self, properties_df: pd.DataFrame, dialect: str = "egyptian"):
        self.properties_df = properties_df
        self.current_dialect = dialect
        self.session_state = {
            "preferences": {
                "type": None,
                "location": None,
                "bedrooms": None,
                "budget": None,
                "other_features": []
            },
            "conversation_stage": "greeting",
            "shown_properties": [],
            "current_property": None,
            "negotiation_attempts": 0
        }
        self.patterns = {
            "type_patterns": {
                "شقة": ["شقة", "شقه", "apartment", "flat"],
                "فيلا": ["فيلا", "فيلة", "villa", "house"],
                "مكتب": ["مكتب", "office", "workspace"],
                "أرض": ["أرض", "ارض", "قطعة أرض", "land", "plot"]
            },
            "budget_patterns": {"money": r"(\d+(?:,\d+)*)\s*(جنيه|دولار|ريال|درهم|الف|ألف|مليون)?"},
            "bedroom_patterns": {"count": r"(\d+)\s*(غرفة|غرف)"}
        }
        self.phrases = {
            "egyptian": {
                "greeting": "أهلاً وسهلاً! أنا هنا لمساعدتك في العثور على العقار المناسب.",
                "ask_type": "تحب تدور على شقة ولا فيلا ولا نوع تاني؟",
                "ask_location": "في أنهي منطقة حابب تدور؟",
                "ask_bedrooms": "كام أوضة نوم بتحتاج؟",
                "ask_budget": "ميزانيتك قد إيه؟",
                "recommendation": "دي أنسب حاجة لقيتها ليك:",
                "refine_question": "تحب تعدل في المعايير؟",
                "adjust_budget": "ميزانيتك ممكن تكون قليلة شوية..."
            },
            "khaleeji": {
                "greeting": "هلا والله! أنا هني أساعدك تلقى العقار المناسب لك.",
                "ask_type": "تبي شقة ولا فيلا ولا شي ثاني؟",
                "ask_location": "في أي منطقة تبي تسكن؟",
                "ask_bedrooms": "كم غرفة نوم تحتاج؟",
                "ask_budget": "كم ميزانيتك؟",
                "recommendation": "هذا أنسب شي لقيته لك:",
                "refine_question": "تبي تغير المعايير؟",
                "adjust_budget": "ميزانيتك يمكن تكون شوي قليلة..."
            },
            "msa": {
                "greeting": "أهلاً وسهلاً! أنا هنا لمساعدتك في العثور على العقار المناسب لك.",
                "ask_type": "هل تبحث عن شقة أم فيلا أم نوع آخر من العقارات؟",
                "ask_location": "في أي منطقة ترغب بالسكن؟",
                "ask_bedrooms": "كم عدد غرف النوم التي تحتاجها؟",
                "ask_budget": "ما هي ميزانيتك المتاحة؟",
                "recommendation": "هذا أفضل عقار مناسب لطلبك:",
                "refine_question": "هل ترغب في تعديل معايير البحث؟",
                "adjust_budget": "قد تكون ميزانيتك منخفضة قليلاً..."
            }
        }
    
    def get_current_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session state.
        
        Returns:
            Dictionary with summary of current state
        """
        return {
            "preferences": self.session_state["preferences"],
            "conversation_stage": self.session_state["conversation_stage"],
            "properties_shown": len(self.session_state["shown_properties"]),
            "current_dialect": self.current_dialect
        }
    
    def reset_session(self) -> None:
        """Reset the session state to start a new conversation."""
        self.session_state = {
            "preferences": {
                "type": None,
                "location": None,
                "bedrooms": None,
                "budget": None,
                "other_features": []
            },
            "conversation_stage": "greeting",
            "shown_properties": [],
            "current_property": None,
            "negotiation_attempts": 0
        }
    
    def get_available_dialects(self) -> List[str]:
        """
        Get list of available Arabic dialects.
        
        Returns:
            List of supported dialect names
        """
        return list(self.phrases.keys())

    def get_property_types(self) -> List[str]:
        """
        Get list of available property types.
        
        Returns:
            List of property types in the database
        """
        return list(self.patterns["type_patterns"].keys())
    
    def get_greeting(self) -> str:
        """
        Get initial greeting message.
        
        Returns:
            Greeting message in current dialect
        """
        return self.get_phrase("greeting")
    
    def get_phrase(self, key: str) -> str:
        """Get a phrase in the current dialect."""
        return self.phrases.get(self.current_dialect, {}).get(key, "")
    
    def switch_dialect(self, dialect: str) -> str:
        """
        Switch to a different Arabic dialect.
        
        Args:
            dialect: The dialect to switch to ('egyptian', 'khaleeji', or 'msa')
            
        Returns:
            Confirmation message in the new dialect
        """
        return self.set_dialect(dialect)
    
    def set_dialect(self, dialect):
        if dialect in self.phrases:
            self.current_dialect = dialect
            if dialect == "egyptian":
                return "تم التغيير للهجة المصرية!"
            elif dialect == "khaleeji":
                return "تم التغيير للهجة الخليجية!"
            else:  # MSA
                return "تم التغيير للغة العربية الفصحى!"
        else:
            return "اللهجة غير متوفرة. اللهجات المتاحة هي: مصري (egyptian)، خليجي (khaleeji)، فصحى (msa)."
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and respond accordingly based on conversation stage.
        
        Args:
            user_input: The user's input text in Arabic
            
        Returns:
            Agent's response in the current dialect
        """
        # Log current session state for debugging
        print(f"[DEBUG] Process input with state: {self.session_state}")
        
        # Ensure session_state has the expected structure
        if not isinstance(self.session_state, dict):
            print(f"[ERROR] session_state is not a dictionary: {type(self.session_state)}")
            # Initialize with default values
            self.session_state = {
                "conversation_stage": "greeting",
                "preferences": {
                    "type": None,
                    "location": None,
                    "bedrooms": None,
                    "budget": None
                },
                "shown_properties": [],
                "current_property": None,
                "negotiation_attempts": 0
            }
        
        # Check if preferences is missing or not a dictionary
        if "preferences" not in self.session_state or not isinstance(self.session_state["preferences"], dict):
            print(f"[ERROR] preferences missing or invalid in session_state")
            self.session_state["preferences"] = {
                "type": None,
                "location": None,
                "bedrooms": None,
                "budget": None
            }
        
        # Extract information from user input
        self._extract_information(user_input)
        
        # Print updated state after extraction
        print(f"[DEBUG] State after extraction: {self.session_state}")
        
        # Determine next action based on conversation stage
        if self.session_state["conversation_stage"] == "greeting":
            # Move to clarification stage and ask first question
            self.session_state["conversation_stage"] = "clarifying"
            print(f"[INFO] Moving from greeting to clarifying stage")
            return self._clarify_next_preference()
        
        elif self.session_state["conversation_stage"] == "clarifying":
            # Continue asking questions until we have enough information
            print(f"[INFO] In clarifying stage, continuing to ask questions")
            return self._clarify_next_preference()
        
        elif self.session_state["conversation_stage"] == "recommending":
            # Process user feedback on recommendation
            if any(word in user_input.lower() for word in ["لا", "مش", "غير", "تاني", "آخر", "no", "other"]):
                # User wants another recommendation
                return self._make_recommendation()
            elif any(word in user_input.lower() for word in ["نعم", "أيوة", "تمام", "حلو", "yes", "good"]):
                # User is satisfied, move to closing
                self.session_state["conversation_stage"] = "closing"
                return "هل ترغب في تحديد موعد لمشاهدة العقار؟"
            else:
                # Unclear response, ask for clarification
                return "هل أعجبك هذا العقار؟ أم تريد اقتراحاً آخر؟"
        
        elif self.session_state["conversation_stage"] == "refining":
            # Update preferences based on refinement
            # Then go back to recommending
            self.session_state["conversation_stage"] = "recommending"
            return self._make_recommendation()
        
        elif self.session_state["conversation_stage"] == "closing":
            # Closing the deal
            if any(word in user_input.lower() for word in ["نعم", "أيوة", "تمام", "حلو", "yes"]):
                # User wants to schedule a viewing
                return "ممتاز! سأتواصل معك قريبًا لتحديد الموعد المناسب. هل لديك أسئلة أخرى؟"
            else:
                # User not ready yet
                self.session_state["conversation_stage"] = "recommending"
                return "حسنًا، هل تريد مشاهدة عقارات أخرى؟"
        
        else:
            # Default response
            return self.get_phrase("greeting")
    
    def _extract_information(self, user_input: str) -> None:
        """
        Extract relevant information from user input (property type, budget, location, etc.)
        and update the session state.
        
        Args:
            user_input: The user's input text in Arabic
        """
        # Ensure preferences exist and are initialized properly
        if "preferences" not in self.session_state:
            print("[ERROR] preferences key missing in session_state during extraction")
            self.session_state["preferences"] = {
                "type": None,
                "location": None,
                "bedrooms": None,
                "budget": None
            }
        elif not isinstance(self.session_state["preferences"], dict):
            print(f"[ERROR] preferences is not a dictionary: {type(self.session_state['preferences'])}")
            self.session_state["preferences"] = {
                "type": None,
                "location": None,
                "bedrooms": None,
                "budget": None
            }
            
        # Check that all required preference fields exist
        required_prefs = ["type", "location", "bedrooms", "budget"]
        for pref in required_prefs:
            if pref not in self.session_state["preferences"]:
                print(f"[ERROR] Missing preference field: {pref}")
                self.session_state["preferences"][pref] = None
                
        # Extract property type
        if self.session_state["preferences"]["type"] is None:
            for prop_type, patterns in self.patterns["type_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["type"] = prop_type
                    print(f"[INFO] Detected property type: {prop_type}")
                    break
        
        # Extract budget
        if self.session_state["preferences"]["budget"] is None:
            budget_match = re.search(self.patterns["budget_patterns"]["money"], user_input)
            if budget_match:
                amount = budget_match.group(1).replace(',', '')
                currency = budget_match.group(2) if budget_match.group(2) else ""
                
                # Convert to float
                try:
                    amount = float(amount)
                    
                    # Apply multiplier for thousands/millions
                    if "الف" in currency or "ألف" in currency:
                        amount *= 1000
                    elif "مليون" in currency:
                        amount *= 1000000
                    
                    self.session_state["preferences"]["budget"] = amount
                except ValueError:
                    pass
        
        # Extract bedroom count
        if self.session_state["preferences"]["bedrooms"] is None:
            bedroom_match = re.search(self.patterns["bedroom_patterns"]["count"], user_input)
            if bedroom_match:
                try:
                    bedrooms = int(bedroom_match.group(1))
                    self.session_state["preferences"]["bedrooms"] = bedrooms
                except ValueError:
                    pass
        
        # Extract location (check if the location exists in our properties dataset or directly match common values)
        if self.session_state["preferences"]["location"] is None:
            print(f"[INFO] Trying to extract location from: '{user_input}'")
            
            # Direct matching for common Arabic locations
            common_locations = {
                "التجمع": "التجمع", 
                "الرحاب": "الرحاب",
                "مدينتي": "مدينتي",
                "الشيخ زايد": "الشيخ زايد",
                "6 اكتوبر": "6 اكتوبر",
                "المعادي": "المعادي",
                "مصر الجديدة": "مصر الجديدة",
                "القاهرة الجديدة": "القاهرة الجديدة"
            }
            
            # First check direct matches for common locations
            user_input_lower = user_input.lower()
            for location_key, location_value in common_locations.items():
                if location_key.lower() in user_input_lower:
                    print(f"[INFO] Matched common location: {location_value}")
                    self.session_state["preferences"]["location"] = location_value
                    return  # Exit early if we found a match
            
            # Get unique locations from dataset for matching
            try:
                unique_locations = self.properties_df["location"].unique()
                for location in unique_locations:
                    if isinstance(location, str) and location.lower() in user_input_lower:
                        print(f"[INFO] Matched dataset location: {location}")
                        self.session_state["preferences"]["location"] = location
                        break
            except Exception as e:
                print(f"[ERROR] Failed to match location from dataset: {str(e)}")
                
            # If we're still here with no match, just use the direct input if it's short enough
            if self.session_state["preferences"]["location"] is None and len(user_input) < 20:
                print(f"[INFO] Using direct input as location: {user_input}")
                self.session_state["preferences"]["location"] = user_input
    
    def _clarify_next_preference(self) -> str:
        """
        Determine which preference to ask about next and generate the appropriate question.
        
        Returns:
            Question about the next preference to clarify
        """
        # Print current state for debugging
        print(f"[DEBUG] _clarify_next_preference with preferences: {self.session_state['preferences']}")
        
        # Check which preferences are still missing
        preferences = self.session_state["preferences"]
        
        # If we have enough information, move to recommendation
        if (preferences["type"] is not None and 
            preferences["location"] is not None and 
            (preferences["bedrooms"] is not None or preferences["type"] not in ["شقة", "فيلا"]) and
            preferences["budget"] is not None):
            
            print(f"[INFO] All preferences satisfied, moving to recommendation stage")
            self.session_state["conversation_stage"] = "recommending"
            return self._make_recommendation()
        
        # Otherwise, ask about missing preferences
        if preferences["type"] is None:
            print(f"[INFO] Missing property type, asking for it")
            return self.get_phrase("ask_type")
        elif preferences["location"] is None:
            print(f"[INFO] Missing location, asking for it")
            return self.get_phrase("ask_location")
        elif preferences["bedrooms"] is None and preferences["type"] in ["شقة", "فيلا"]:
            print(f"[INFO] Missing bedrooms for residential property, asking for it")
            return self.get_phrase("ask_bedrooms")
        elif preferences["budget"] is None:
            print(f"[INFO] Missing budget, asking for it")
            return self.get_phrase("ask_budget")
        else:
            # We should have enough information to make a recommendation
            print(f"[INFO] Ready to make recommendation with preferences: {preferences}")
            self.session_state["conversation_stage"] = "recommending"
            return self._make_recommendation()
    
    def _make_recommendation(self) -> str:
        """
        Generate a property recommendation based on user preferences.
        
        Returns:
            Recommendation text with property details
        """
        preferences = self.session_state["preferences"]
        
        # Filter properties based on preferences
        filtered_df = self.properties_df.copy()
        
        if preferences["type"] is not None:
            filtered_df = filtered_df[filtered_df["type"] == preferences["type"]]
        
        if preferences["location"] is not None:
            filtered_df = filtered_df[filtered_df["location"] == preferences["location"]]
        
        if preferences["bedrooms"] is not None:
            filtered_df = filtered_df[filtered_df["bedrooms"] == preferences["bedrooms"]]
        
        if preferences["budget"] is not None:
            # Add a 20% buffer to the budget
            budget_with_buffer = preferences["budget"] * 1.2
            filtered_df = filtered_df[filtered_df["price"] <= budget_with_buffer]
        
        # Filter out properties already shown
        filtered_df = filtered_df[~filtered_df["id"].isin(self.session_state["shown_properties"])]
        
        # If no properties match, suggest criteria adjustment
        if len(filtered_df) == 0:
            return self._suggest_criteria_adjustment()
        
        # Select the best matching property (for simplicity, just take the first one)
        selected_property = filtered_df.iloc[0]
        self.session_state["current_property"] = selected_property.to_dict()
        
        # Add to shown properties
        self.session_state["shown_properties"].append(selected_property["id"])
        
        # Create recommendation text
        recommendation = self.get_phrase("recommendation") + "\n\n"
        
        # Format price with commas for readability
        price_formatted = f"{int(selected_property['price']):,}"
        currency = selected_property.get('currency', 'EGP')
        
        # Build the recommendation details based on property type
        if selected_property["type"] == "شقة" or selected_property["type"] == "Apartment":
            recommendation += f"شقة {selected_property['bedrooms']} غرف في {selected_property['location']}"
            if 'neighborhood' in selected_property:
                recommendation += f"، {selected_property['neighborhood']}"
            recommendation += f"\nالسعر: {price_formatted} {currency}"
            recommendation += f"\nالمساحة: {selected_property['area_m2']} متر مربع"
            recommendation += f"\nالحمامات: {selected_property['bathrooms']}"
            
        elif selected_property["type"] == "فيلا" or selected_property["type"] == "Villa":
            recommendation += f"فيلا {selected_property['bedrooms']} غرف في {selected_property['location']}"
            if 'neighborhood' in selected_property:
                recommendation += f"، {selected_property['neighborhood']}"
            recommendation += f"\nالسعر: {price_formatted} {currency}"
            recommendation += f"\nالمساحة: {selected_property['area_m2']} متر مربع"
            recommendation += f"\nالحمامات: {selected_property['bathrooms']}"
            if 'garden_area' in selected_property:
                recommendation += f"\nمساحة الحديقة: {selected_property['garden_area']} متر مربع"
            
        elif selected_property["type"] == "مكتب" or selected_property["type"] == "Office":
            recommendation += f"مكتب في {selected_property['location']}"
            if 'neighborhood' in selected_property:
                recommendation += f"، {selected_property['neighborhood']}"
            recommendation += f"\nالسعر: {price_formatted} {currency}"
            recommendation += f"\nالمساحة: {selected_property['area_m2']} متر مربع"
            
        elif selected_property["type"] == "أرض" or selected_property["type"] == "Land":
            recommendation += f"قطعة أرض في {selected_property['location']}"
            if 'neighborhood' in selected_property:
                recommendation += f"، {selected_property['neighborhood']}"
            recommendation += f"\nالسعر: {price_formatted} {currency}"
            recommendation += f"\nالمساحة: {selected_property['area_m2']} متر مربع"
        
        # Add description if available
        if 'description' in selected_property and selected_property['description']:
            recommendation += f"\n\nوصف العقار: {selected_property['description']}"
        
        # Add question about the property
        recommendation += "\n\nهل هذا العقار يناسبك؟"
        
        return recommendation
    
    def _suggest_criteria_adjustment(self) -> str:
        """
        Suggest adjusting search criteria when no matching properties are found.
        Performs reasoning about which criteria to adjust based on the dataset.
        
        Returns:
            Suggestion text for adjusting criteria
        """
        preferences = self.session_state["preferences"]
        all_properties = self.properties_df.copy()
        
        suggestion = "لم أجد عقارات تتطابق مع جميع متطلباتك. إليك بعض الاقتراحات لتعديل البحث:\n"
        
        # Check type restriction
        if preferences["type"] is not None:
            type_count = len(all_properties[all_properties["type"] == preferences["type"]])
            if type_count < 5:  # Arbitrary threshold
                suggestion += "- نوع العقار الذي اخترته قليل في قاعدة البيانات لدينا، ربما تريد تجربة نوع آخر؟\n"
        
        # Check location restriction
        if preferences["location"] is not None:
            location_count = len(all_properties[all_properties["location"] == preferences["location"]])
            if location_count < 5:  # Arbitrary threshold
                suggestion += "- عدد العقارات في المنطقة التي اخترتها قليل جداً، ربما تريد توسيع نطاق البحث لمناطق أخرى؟\n"
        
        # Check budget restriction
        if preferences["budget"] is not None:
            budget_properties = all_properties[all_properties["price"] <= preferences["budget"]]
            if len(budget_properties) < 5:  # Arbitrary threshold
                # Calculate a suggested budget
                suggested_budget = round(all_properties["price"].quantile(0.3) * 1.1, -3)  # Round to nearest thousand
                formatted_budget = f"{int(suggested_budget):,}"
                currency = all_properties.get('currency', 'EGP').iloc[0] if 'currency' in all_properties else 'EGP'
                suggestion += f"- ميزانيتك قد تكون منخفضة، ربما تحتاج إلى زيادتها إلى حوالي {formatted_budget} {currency}؟\n"
        
        # Check bedroom restriction
        if preferences["bedrooms"] is not None and preferences["type"] in ["شقة", "فيلا", "Apartment", "Villa"]:
            bedroom_count = len(all_properties[all_properties["bedrooms"] == preferences["bedrooms"]])
            if bedroom_count < 5:  # Arbitrary threshold
                suggestion += "- عدد غرف النوم الذي طلبته قد يكون غير متوفر بكثرة، ربما تريد زيادة أو تقليل العدد بغرفة واحدة؟\n"
        
        # Move back to clarification stage
        self.session_state["conversation_stage"] = "clarifying"
        
        # Reset one of the preferences to force re-asking
        if preferences["budget"] is not None and "ميزانيتك" in suggestion:
            self.session_state["preferences"]["budget"] = None
        elif preferences["location"] is not None and "المنطقة" in suggestion:
            self.session_state["preferences"]["location"] = None
        elif preferences["type"] is not None and "نوع العقار" in suggestion:
            self.session_state["preferences"]["type"] = None
        
        suggestion += "\nدعنا نعيد ضبط بعض المعايير. " + self._clarify_next_preference()
        
        return suggestion

def create_real_estate_agent(properties_df: pd.DataFrame, dialect: str = "egyptian") -> ArabicRealEstateAgent:
    """
    Factory function to create a new real estate agent instance.
    
    Args:
        properties_df: DataFrame with property listings
        dialect: The dialect to use (default: 'egyptian')
        
    Returns:
        Configured ArabicRealEstateAgent instance
    """
    return ArabicRealEstateAgent(properties_df, dialect)