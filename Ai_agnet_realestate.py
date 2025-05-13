import re
import pandas as pd
import random
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
                "bathrooms": None,
                "budget": None,
                "area_m2": None,
                "floor": None,
                "purpose": None,  # For rent or sale
                "compound": None, # In a compound or not
                "finishing": None, # Finishing type
                "finishing_type": None, # Type of finishing if applicable
                "services": [],    # Additional services
                "other_features": []
            },
            "user_info": {
                "name": None,
                "phone": None,
                "email": None
            },
            "conversation_stage": "greeting",
            "shown_properties": [],
            "current_property": None,
            "selected_property_index": 0,  # Index of the property the user selected (1 or 2)
            "negotiation_attempts": 0,
            "question_flow_index": 0, # To control the flow of questions
            "asked_finishing_type": False, # Track if finishing type question was asked
            "asked_services": False, # Track if services question was asked
            "last_question_asked": None, # Track the last question asked
            "sales_pitch_stage": 0,  # Track which sales pitch stage we're in
            "used_sales_arguments": []  # Track which sales arguments have been used
        }
        
        # Define the order of questions to ask
        self.question_flow = [
            "location", "purpose", "type", "compound", "area_m2", 
            "finishing", "finishing_type", "services", "floor", 
            "budget", "bedrooms", "bathrooms"
        ]
        
        # Keywords that indicate buying/renting intent
        self.buying_intent_keywords = [
            "هشتري", "هاخده", "عايز اشتري", "أشتري", "اشتري", "هشتريه", "أخده", "اخده", "اتفقنا",
            "موافق", "تمام", "حلو", "مناسب", "عجبني", "خلاص", "اوك", "okay", "ok", "buy", "deal", 
            "ماشي", "اتفقنا", "أوافق", "اوافق", "أقبل", "اقبل", "قبلت", "حجزت", "احجز", "أحجز"
        ]
        
        # Sales arguments for varied persuasion
        self.sales_arguments = [
            # Location benefits
            "الموقع استراتيجي جداً وده من أهم العوامل اللي بتزود قيمة العقار مع الوقت. المنطقة دي من أكتر المناطق المرغوبة وطلب السكن فيها بيزيد باستمرار.",
            "مش هتلاقي عقار في الموقع ده بالسعر ده تاني. المنطقة دي بتتطور بسرعة والأسعار مرشحة للزيادة 20% خلال السنة الجاية.",
            
            # Investment value
            "العقار ده يعتبر استثمار ممتاز. الأسعار في المنطقة دي بتزيد بشكل سنوي بنسبة 15-20%، يعني لو اشتريته دلوقتي، قيمته هتزيد بشكل كبير في السنين الجاية.",
            "لو حسبناها كاستثمار، العقار ده هيرجعلك استثمارك في خلال 7-10 سنين لو أجرته، وبعد كده كله مكسب صافي.",
            
            # Features and amenities
            "المميزات والخدمات اللي فيه هتخليك مبسوط جداً بالاختيار ده. كمان المساحة مثالية والتقسيم الداخلي عملي جداً.",
            "جودة التشطيب عالية جداً، هتوفر عليك وقت ومجهود وفلوس. تقدر تنتقل على طول من غير أي تعديلات.",
            
            # Urgency creation
            "وصدقني، العقارات في الموقع ده بتتباع بسرعة كبيرة، فرصة زي دي مش هتتكرر كتير. الوقت دلوقتي مناسب جداً للشراء قبل ما الأسعار تزيد أكتر.",
            "فيه عميل تاني بيفكر في العقار ده وممكن يحجزه النهاردة، لو انت عاجبك فعلاً يبقى لازم نتحرك بسرعة.",
            
            # Negotiation opportunity
            "ممكن أحاول أتفاوض مع المالك على خصم بسيط لو أكدت رغبتك في الشراء دلوقتي. ممكن نوصل لتخفيض ١-٣٪ من السعر.",
            "المالك مُستعد يتنازل عن جزء من السعر لو الدفع هيكون كاش ومباشر.",
            
            # Long-term benefits
            "العقار ده تم تصميمه بشكل يوفر في استهلاك الكهرباء والمياه، هتلاحظ فرق كبير في فواتيرك الشهرية.",
            "تخيل نفسك وانت بتستقبل ضيوفك في المكان ده، هيكون انطباعهم إزاي عن ذوقك واختيارك!"
        ]
        
        self.patterns = {
            "type_patterns": {
                "شقة": ["شقة", "شقه", "apartment", "flat", "شقق", "شق"],
                "فيلا": ["فيلا", "فيلة", "villa", "house", "فيل", "منزل", "بيت"],
                "مكتب": ["مكتب", "office", "workspace", "مكاتب", "عمل", "مكتبي", "تجاري", "إداري", "اداري"],
                "أرض": ["أرض", "ارض", "قطعة أرض", "land", "plot", "قطع"]
            },
            "purpose_patterns": {
                "للشراء": ["شراء", "تمليك", "بيع", "buy", "purchase", "امتلاك", "مشتري", "اشتري", "يشتري"],
                "للإيجار": ["ايجار", "إيجار", "استئجار", "rent", "rental", "أجار", "مستأجر", "استأجر", "يستأجر"]
            },
            "compound_patterns": {
                "نعم": ["كمباوند", "مجمع", "مغلق", "compound", "كومباوند", "نعم", "ايوة", "أيوة", "اه", "آه"],
                "لا": ["لا", "مش محتاج", "عادي", "مش ضروري", "غير مهم", "no", "not important"]
            },
            "finishing_patterns": {
                "متشطب": ["متشطب", "تشطيب", "نهائي", "finished", "كامل", "super", "super lux", "سوبر", "لوكس", "الترا", "ultra"],
                "نص تشطيب": ["نص", "half", "غير كامل", "بدون", "not finished", "غير متشطب", "نصف"]
            },
            "finishing_type_patterns": {
                "سوبر لوكس": ["سوبر", "super", "super lux", "سوبر لوكس"],
                "الترا لوكس": ["الترا", "ultra", "ultra lux", "الترا لوكس", "فاخر", "luxury", "لاكشري"],
                "عادي": ["عادي", "normal", "standard", "بسيط", "regular", "مش فارق", "غير مهم", "أي حاجة"]
            },
            "services_patterns": {
                "أمن": ["أمن", "امن", "security", "حراسة", "حارس", "سكيورتي"],
                "جراج": ["جراج", "garage", "موقف", "باركينج", "parking", "عربية", "سيارة"],
                "نادي": ["نادي", "club", "gym", "جيم", "رياضة", "مسبح", "حمام سباحة", "pool", "swimming"],
                "مول": ["مول", "سوق", "تسوق", "mall", "shopping", "سنتر", "محلات", "مركز تجاري", "مول تجاري"]
            },
            "budget_patterns": {"money": r"(\d+(?:,\d+)*)\s*(جنيه|دولار|ريال|درهم|الف|ألف|مليون)?"},
            "bedroom_patterns": {"count": r"(\d+)(?:\s*)(غرفة|غرف|اوض|أوض|room|bedroom)?"},
            "bathroom_patterns": {"count": r"(\d+)(?:\s*)(حمام|toilet|bathroom|bath)?"},
            "area_patterns": {"area": r"(\d+)(?:\s*)(متر|م2|m2|square meter|sqm)?"},
            "floor_patterns": {"floor": r"(\d+)(?:\s*)(دور|طابق|floor)?"},
            "contact_patterns": {
                "name": r"(?:اسمي|انا|my name|i am)\s+([A-Za-zأ-ي\s]+)",
                "phone": r"(\+?\d{8,15})|(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4,6})",
                "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
            }
        }
        
        self.phrases = {
            "egyptian": {
                "greeting": "أهلاً وسهلاً! أنا وكيل العقارات الذكي. ازاي ممكن أساعدك؟",
                "ask_location": "ممكن أعرف في أي منطقة بتدور على العقار؟ 📍",
                "ask_purpose": "حضرتك بتدور على عقار للإيجار ولا للشراء؟ 🏢",
                "ask_type": "تمام، تحب يكون العقار ده شقة، فيلا، ولا إداري/تجاري؟",
                "ask_compound": "طيب، تفضل العقار يكون في كمباوند ولا لا؟",
                "ask_area": "تحب المساحة تكون تقريباً قد إيه بالمتر المربع؟",
                "ask_finishing": "العقار يكون متشطب ولا نص تشطيب؟",
                "ask_finishing_type": "ولو متشطب، تحب نوع التشطيب يكون سوبر لوكس، ألترا لوكس، ولا مش فارق معاك؟",
                "ask_services": "فيه خدمات معينة محتاجها في العقار؟ زي أمن، جراج، نادي، مول تجاري قريب؟ 🛍️🏬",
                "ask_floor": "تحب العقار يكون في الدور الكام تقريبًا؟",
                "ask_budget": "إيه هي ميزانيتك أو السعر اللي حابب تدفعه؟ ولو في حدود، قوللي مثلًا \"من كذا لكذا\". 💵",
                "ask_bedrooms": "محتاج كام غرفة نوم؟",
                "ask_bathrooms": "محتاج كام حمام؟",
                "recommendation": "دي أنسب حاجة لقيتها ليك:",
                "refine_question": "تحب تعدل في المعايير؟",
                "adjust_budget": "ميزانيتك ممكن تكون قليلة شوية...",
                "summary_intro": "تمام، بناءً على اللي فهمته:",
                "summary_confirm": "كدة تمام ولا حابب تعدل اي حاجة؟",
                "suggestions_intro": "تمام، عندي لك اقتراحين مناسبين:",
                "sales_pitch_intro": "الاختيار ده ممتاز وأنا حاسس إنه مناسب جداً ليك. خليني أقولك ليه:",
                "sales_pitch_location": "الموقع استراتيجي جداً وده من أهم العوامل اللي بتزود قيمة العقار مع الوقت. المنطقة دي من أكتر المناطق المرغوبة وطلب السكن فيها بيزيد باستمرار.",
                "sales_pitch_investment": "العقار ده يعتبر استثمار ممتاز. الأسعار في المنطقة دي بتزيد بشكل سنوي بنسبة 15-20%، يعني لو اشتريته دلوقتي، قيمته هتزيد بشكل كبير في السنين الجاية.",
                "sales_pitch_amenities": "المميزات والخدمات اللي فيه هتخليك مبسوط جداً بالاختيار ده. كمان المساحة مثالية والتقسيم الداخلي عملي جداً.",
                "sales_pitch_limited": "وصدقني، العقارات في الموقع ده بتتباع بسرعة كبيرة، فرصة زي دي مش هتتكرر كتير. الوقت دلوقتي مناسب جداً للشراء قبل ما الأسعار تزيد أكتر.",
                "sales_pitch_closing": "تحب نحدد معاد لمعاينة العقار؟ يمكن بكرة او بعده لو مناسب ليك؟",
                "ask_contact": "ممتاز! ممكن أعرف اسمك ورقم موبايلك عشان أقدر أتواصل معاك لتحديد التفاصيل؟",
                "confirm_appointment": "تمام جداً {name}! هتواصل معاك على {phone} لتحديد ميعاد معاينة العقار. أنا متأكد انك هتحب العقار أكتر لما تشوفه. هل تحب تعرف أي تفاصيل تانية عن العقار أو المنطقة؟",
                "ask_more_options": "عندي عقارات تانية ممكن تكون مناسبة ليك. تحب أعرضها عليك؟",
                "property_comparison": "العقار ده أفضل من غيره بكتير من ناحية السعر والمساحة والموقع. بالمقارنة مع العقارات المشابهة، هتلاقيه أوفر بحوالي 10-15%.",
                "discount_offer": "ممكن أحاول أتفاوض مع المالك على خصم بسيط لو أكدت رغبتك في الشراء دلوقتي. ممكن نوصل لتخفيض ١-٣٪ من السعر.",
                "higher_discount": "بما إنك عميل مميز، هحاول أوصل للمالك وأشوف لو ممكن يديك خصم 5-7%، بس لازم تأكدلي إنك موافق مبدئياً."
            },
            "khaleeji": {
                "greeting": "هلا والله! أنا هني أساعدك تلقى العقار المناسب لك.",
                "ask_location": "ممكن تخبرني في أي منطقة تبحث عن العقار؟ 📍",
                "ask_purpose": "تبحث عن عقار للإيجار أو للشراء؟ 🏢",
                "ask_type": "زين، تفضل العقار شقة، فيلا، أو تجاري/إداري؟",
                "ask_compound": "هل تفضل العقار يكون في مجمع سكني؟",
                "ask_area": "شنو المساحة المناسبة لك بالمتر المربع؟",
                "ask_finishing": "تبي العقار يكون مشطب أو نص تشطيب؟",
                "ask_finishing_type": "إذا مشطب، تفضل التشطيب سوبر لوكس، ألترا لوكس، أو ما يهمك؟",
                "ask_services": "في خدمات معينة تبيها في العقار؟ مثل أمن، موقف سيارات، نادي، مجمع تجاري قريب؟ 🛍️🏬",
                "ask_floor": "أي دور تفضل للعقار؟",
                "ask_budget": "ما هي الميزانية أو السعر اللي تبيه؟ وإذا في حدود، قولي مثلاً \"من كذا إلى كذا\". 💵",
                "ask_bedrooms": "كم غرفة نوم تحتاج؟",
                "ask_bathrooms": "كم حمام تحتاج؟",
                "recommendation": "هذا أنسب شي لقيته لك:",
                "refine_question": "تبي تغير المعايير؟",
                "adjust_budget": "ميزانيتك يمكن تكون شوي قليلة...",
                "summary_intro": "تمام، بناءً على اللي فهمته منك:",
                "summary_confirm": "هذا مناسب أو تبي تعدل أي شي؟",
                "suggestions_intro": "زين، عندي لك اختيارين مناسبين:",
                "sales_pitch_intro": "هالاختيار ممتاز وأشوف إنه مناسب لك جداً. خلني أقولك ليش:",
                "sales_pitch_location": "الموقع استراتيجي جداً وهذا من أهم العوامل اللي تزيد قيمة العقار مع الوقت. المنطقة هذي من أكثر المناطق المرغوبة والطلب على السكن فيها يزيد باستمرار.",
                "sales_pitch_investment": "العقار هذا يعتبر استثمار ممتاز. الأسعار في المنطقة هذي تزيد بشكل سنوي بنسبة 15-20%، يعني لو اشتريته الحين، قيمته بتزيد بشكل كبير في السنوات الجاية.",
                "sales_pitch_amenities": "المميزات والخدمات اللي فيه بتخليك مبسوط جداً بالاختيار هذا. المساحة بعد مثالية والتقسيم الداخلي عملي جداً.",
                "sales_pitch_limited": "وصدقني، العقارات في الموقع هذا تنباع بسرعة كبيرة، فرصة مثل هذي ما تتكرر وايد. الوقت الحين مناسب جداً للشراء قبل ما تزيد الأسعار أكثر.",
                "sales_pitch_closing": "تبي نحدد موعد لمعاينة العقار؟ يمكن باچر أو اللي بعده إذا مناسب لك؟",
                "ask_contact": "ممتاز! ممكن أعرف اسمك ورقم موبايلك عشان أقدر أتواصل معاك لتحديد التفاصيل؟",
                "confirm_appointment": "زين جداً {name}! بتواصل معاك على {phone} لتحديد موعد معاينة العقار. أنا متأكد إنك بتحب العقار أكثر لما تشوفه. تبي تعرف أي تفاصيل ثانية عن العقار أو المنطقة؟",
                "ask_more_options": "عندي عقارات ثانية ممكن تكون مناسبة لك. تبي أعرضها عليك؟",
                "property_comparison": "العقار هذا أفضل من غيره وايد من ناحية السعر والمساحة والموقع. بالمقارنة مع العقارات المشابهة، بتلقاه أوفر بحوالي 10-15%.",
                "discount_offer": "ممكن أحاول أتفاوض مع المالك على خصم بسيط لو أكدت رغبتك في الشراء الحين. ممكن نوصل لتخفيض ١-٣٪ من السعر.",
                "higher_discount": "بما إنك عميل مميز، بحاول أوصل للمالك وأشوف إذا ممكن يعطيك خصم 5-7%، بس لازم تأكد لي إنك موافق مبدئياً."
            },
            "msa": {
                "greeting": "أهلاً وسهلاً! أنا هنا لمساعدتك في العثور على العقار المناسب لك.",
                "ask_location": "هل يمكنني معرفة المنطقة التي تبحث فيها عن العقار؟ 📍",
                "ask_purpose": "هل تبحث عن عقار للإيجار أم للشراء؟ 🏢",
                "ask_type": "حسناً، هل تفضل أن يكون العقار شقة، فيلا، أم تجاري/إداري؟",
                "ask_compound": "هل تفضل أن يكون العقار داخل مجمع سكني؟",
                "ask_area": "ما هي المساحة التقريبية التي ترغب بها بالمتر المربع؟",
                "ask_finishing": "هل تفضل العقار متشطباً أم نصف تشطيب؟",
                "ask_finishing_type": "إذا كان متشطباً، هل تفضل تشطيب سوبر لوكس، ألترا لوكس، أم ليس مهماً بالنسبة لك؟",
                "ask_services": "هل هناك خدمات معينة ترغب بتوفرها في العقار؟ مثل أمن، موقف سيارات، نادي، مركز تجاري قريب؟ 🛍️🏬",
                "ask_floor": "في أي طابق تفضل أن يكون العقار؟",
                "ask_budget": "ما هي ميزانيتك أو السعر الذي ترغب بدفعه؟ وإذا كان هناك حدود، فضلاً أخبرني مثلاً \"من كذا إلى كذا\". 💵",
                "ask_bedrooms": "كم عدد غرف النوم التي تحتاجها؟",
                "ask_bathrooms": "كم عدد الحمامات التي تحتاجها؟",
                "recommendation": "هذا أفضل عقار مناسب لطلبك:",
                "refine_question": "هل ترغب في تعديل معايير البحث؟",
                "adjust_budget": "قد تكون ميزانيتك منخفضة قليلاً...",
                "summary_intro": "حسناً، بناءً على ما فهمته منك:",
                "summary_confirm": "هل هذا مناسب أم ترغب في تعديل أي من هذه المعلومات؟",
                "suggestions_intro": "حسناً، لدي اقتراحين مناسبين لك:",
                "sales_pitch_intro": "هذا الاختيار ممتاز وأرى أنه مناسب جداً لك. دعني أخبرك لماذا:",
                "sales_pitch_location": "الموقع استراتيجي للغاية وهذا من أهم العوامل التي تزيد قيمة العقار مع مرور الوقت. هذه المنطقة من أكثر المناطق المرغوبة والطلب على السكن فيها يزداد باستمرار.",
                "sales_pitch_investment": "يعتبر هذا العقار استثماراً ممتازاً. ترتفع الأسعار في هذه المنطقة بنسبة سنوية تتراوح بين 15-20%، مما يعني أنك إذا اشتريته الآن، ستزداد قيمته بشكل كبير في السنوات القادمة.",
                "sales_pitch_amenities": "الميزات والخدمات المتوفرة فيه ستجعلك سعيداً جداً بهذا الاختيار. كما أن المساحة مثالية والتقسيم الداخلي عملي للغاية.",
                "sales_pitch_limited": "وصدقني، العقارات في هذا الموقع تُباع بسرعة كبيرة، فرصة مثل هذه لا تتكرر كثيراً. الوقت الحالي مناسب جداً للشراء قبل أن ترتفع الأسعار أكثر.",
                "sales_pitch_closing": "هل ترغب في تحديد موعد لمعاينة العقار؟ ربما غداً أو بعد غد إذا كان ذلك مناسباً لك؟",
                "ask_contact": "ممتاز! هل يمكنني معرفة اسمك ورقم هاتفك حتى أتمكن من التواصل معك لتحديد التفاصيل؟",
                "confirm_appointment": "جيد جداً {name}! سأتواصل معك على {phone} لتحديد موعد معاينة العقار. أنا متأكد أنك ستحب العقار أكثر عندما تراه. هل تود معرفة أي تفاصيل أخرى عن العقار أو المنطقة؟",
                "ask_more_options": "لدي عقارات أخرى قد تكون مناسبة لك. هل ترغب في الاطلاع عليها؟",
                "property_comparison": "هذا العقار أفضل من غيره بكثير من حيث السعر والمساحة والموقع. بالمقارنة مع العقارات المماثلة، ستجده أوفر بحوالي 10-15%.",
                "discount_offer": "يمكنني محاولة التفاوض مع المالك على خصم بسيط إذا أكدت رغبتك في الشراء الآن. يمكننا الوصول إلى تخفيض ١-٣٪ من السعر.",
                "higher_discount": "بما أنك عميل مميز، سأحاول التواصل مع المالك لأرى إذا كان بإمكانه منحك خصم 5-7%، لكن يجب أن تؤكد لي أنك موافق مبدئياً."
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
                "bathrooms": None,
                "budget": None,
                "area_m2": None,
                "floor": None,
                "purpose": None,
                "compound": None,
                "finishing": None,
                "finishing_type": None,
                "services": [],
                "other_features": []
            },
            "user_info": {
                "name": None,
                "phone": None,
                "email": None
            },
            "conversation_stage": "greeting",
            "shown_properties": [],
            "current_property": None,
            "selected_property_index": 0,
            "negotiation_attempts": 0,
            "question_flow_index": 0,
            "asked_finishing_type": False,
            "asked_services": False,
            "last_question_asked": None,
            "sales_pitch_stage": 0,
            "used_sales_arguments": []
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
                    "bathrooms": None,
                    "budget": None,
                    "area_m2": None,
                    "floor": None,
                    "purpose": None,
                    "compound": None,
                    "finishing": None,
                    "finishing_type": None,
                    "services": [],
                    "other_features": []
                },
                "user_info": {
                    "name": None,
                    "phone": None,
                    "email": None
                },
                "shown_properties": [],
                "current_property": None,
                "selected_property_index": 0,
                "negotiation_attempts": 0,
                "question_flow_index": 0,
                "asked_finishing_type": False,
                "asked_services": False,
                "last_question_asked": None,
                "sales_pitch_stage": 0,
                "used_sales_arguments": []
            }
        
        # Check if preferences is missing or not a dictionary
        if "preferences" not in self.session_state or not isinstance(self.session_state["preferences"], dict):
            print(f"[ERROR] preferences missing or invalid in session_state")
            self.session_state["preferences"] = {
                "type": None,
                "location": None,
                "bedrooms": None,
                "bathrooms": None,
                "budget": None,
                "area_m2": None,
                "floor": None,
                "purpose": None,
                "compound": None,
                "finishing": None,
                "finishing_type": None,
                "services": [],
                "other_features": []
            }
        
        # Extract contact information if applicable
        self._extract_contact_info(user_input)
        
        # Extract information from user input
        self._extract_information(user_input)
        
        # Print updated state after extraction
        print(f"[DEBUG] State after extraction: {self.session_state}")
        
        # Check for buying intent to bypass recommendation loops
        if self._check_buying_intent(user_input) and self.session_state["conversation_stage"] in ["recommending", "sales_pitch"]:
            print("[INFO] Detected buying intent, moving to contact collection stage")
            self.session_state["conversation_stage"] = "contact_collection"
            return self.get_phrase("ask_contact")
        
        # Check for higher discount request
        if (("خصم" in user_input or "تخفيض" in user_input or "discount" in user_input) and 
            ("أكبر" in user_input or "أكثر" in user_input or "أعلى" in user_input or "زيادة" in user_input or "higher" in user_input)):
            print("[INFO] User requesting higher discount")
            self.session_state["negotiation_attempts"] += 1
            return self.phrases[self.current_dialect]["higher_discount"]
        
        # Check for numeric-only inputs - treat them as answers to current questions
        if user_input.strip().isdigit():
            num_value = int(user_input.strip())
            
            # Handle direct numeric responses based on conversation stage
            if self.session_state["conversation_stage"] == "clarifying":
                last_question = self.session_state["last_question_asked"]
                
                if last_question == "ask_bedrooms":
                    self.session_state["preferences"]["bedrooms"] = num_value
                    print(f"[INFO] Set bedrooms from direct numeric input: {num_value}")
                    # Increment question flow
                    self.session_state["question_flow_index"] += 1
                
                elif last_question == "ask_bathrooms":
                    self.session_state["preferences"]["bathrooms"] = num_value
                    print(f"[INFO] Set bathrooms from direct numeric input: {num_value}")
                    # Increment question flow
                    self.session_state["question_flow_index"] += 1
                
                elif last_question == "ask_area":
                    self.session_state["preferences"]["area_m2"] = num_value
                    print(f"[INFO] Set area from direct numeric input: {num_value}")
                    # Increment question flow
                    self.session_state["question_flow_index"] += 1
                
                elif last_question == "ask_floor":
                    self.session_state["preferences"]["floor"] = num_value
                    print(f"[INFO] Set floor from direct numeric input: {num_value}")
                    # Increment question flow
                    self.session_state["question_flow_index"] += 1
                
                elif last_question == "ask_budget":
                    # Treat as thousands by default if small number
                    if num_value < 1000:
                        num_value *= 1000000  # Treat as millions
                    elif num_value < 100000:
                        num_value *= 1000  # Treat as thousands
                    
                    self.session_state["preferences"]["budget"] = float(num_value)
                    print(f"[INFO] Set budget from direct numeric input: {num_value}")
                    # Increment question flow
                    self.session_state["question_flow_index"] += 1
        
        # Determine next action based on conversation stage
        if self.session_state["conversation_stage"] == "greeting":
            # Move to clarification stage and ask first question
            self.session_state["conversation_stage"] = "clarifying"
            print(f"[INFO] Moving from greeting to clarifying stage")
            return self._ask_next_question()
        
        elif self.session_state["conversation_stage"] == "clarifying":
            # Continue asking questions
            return self._ask_next_question()
        
        elif self.session_state["conversation_stage"] == "summarizing":
            # Check if user confirms the summary
            if any(word in user_input.lower() for word in ["نعم", "أيوة", "ايوه", "تمام", "صح", "مظبوط", "yes", "correct"]):
                # User confirms summary, move to recommendation
                self.session_state["conversation_stage"] = "recommending"
                return self._make_recommendation()
            else:
                # User wants to adjust something
                if any(word in user_input.lower() for word in ["منطقة", "location", "مكان"]):
                    self.session_state["preferences"]["location"] = None
                    return self.get_phrase("ask_location")
                elif any(word in user_input.lower() for word in ["نوع", "type"]):
                    self.session_state["preferences"]["type"] = None
                    return self.get_phrase("ask_type")
                elif any(word in user_input.lower() for word in ["غرف", "اوض", "bedrooms", "room"]):
                    self.session_state["preferences"]["bedrooms"] = None
                    return self.get_phrase("ask_bedrooms")
                elif any(word in user_input.lower() for word in ["ميزانية", "سعر", "فلوس", "budget", "price"]):
                    self.session_state["preferences"]["budget"] = None
                    return self.get_phrase("ask_budget")
                elif any(word in user_input.lower() for word in ["مساحة", "متر", "area", "size"]):
                    self.session_state["preferences"]["area_m2"] = None
                    return self.get_phrase("ask_area")
                else:
                    # Unclear what to adjust, move to recommendation
                    self.session_state["conversation_stage"] = "recommending"
                    return self._make_recommendation()
        
        elif self.session_state["conversation_stage"] == "recommending":
            # Process user feedback on recommendation
            if any(word in user_input.lower() for word in ["لا", "مش", "غير", "تاني", "آخر", "no", "other"]):
                # User wants another recommendation
                return self._make_recommendation()
            elif "١" in user_input or "1" in user_input or "الأول" in user_input or "اول" in user_input or "الاول" in user_input:
                # User selected option 1
                self.session_state["selected_property_index"] = 0
                self.session_state["conversation_stage"] = "sales_pitch"
                self.session_state["sales_pitch_stage"] = 0
                return self._get_adaptive_sales_pitch()
            elif "٢" in user_input or "2" in user_input or "الثاني" in user_input or "تاني" in user_input or "التاني" in user_input:
                # User selected option 2
                self.session_state["selected_property_index"] = 1
                self.session_state["conversation_stage"] = "sales_pitch"
                self.session_state["sales_pitch_stage"] = 0
                return self._get_adaptive_sales_pitch()
            elif any(word in user_input.lower() for word in ["نعم", "أيوة", "تمام", "حلو", "yes", "good", "اعجبني", "عجبني", "يعجبني"]):
                # User is generally satisfied, move to sales pitch with the first property
                self.session_state["selected_property_index"] = 0
                self.session_state["conversation_stage"] = "sales_pitch"
                self.session_state["sales_pitch_stage"] = 0
                return self._get_adaptive_sales_pitch()
            else:
                # Unclear response, ask for clarification
                return "أي من هذه العقارات أعجبك؟ العقار الأول أم الثاني؟ أم تريد اقتراحات أخرى؟"
        
        elif self.session_state["conversation_stage"] == "sales_pitch":
            # Handle responses in the sales pitch stage
            if any(word in user_input.lower() for word in ["سعر", "خصم", "ميزانية", "price", "discount", "budget", "تخفيض"]):
                # User is discussing price - engage in negotiation
                self.session_state["negotiation_attempts"] += 1
                
                # Vary the discount offer based on negotiation attempts
                if self.session_state["negotiation_attempts"] <= 1:
                    return self.get_phrase("discount_offer")
                else:
                    return self.phrases[self.current_dialect]["higher_discount"]
                    
            elif self._check_buying_intent(user_input):
                # User agrees to proceed, move to contact info collection
                self.session_state["conversation_stage"] = "contact_collection"
                return self.get_phrase("ask_contact")
                
            elif any(word in user_input.lower() for word in ["لا", "مش", "غير", "تاني", "no", "other", "another"]):
                # User not convinced, try another property
                self.session_state["conversation_stage"] = "recommending"
                return self.get_phrase("ask_more_options")
            else:
                # Continue with adaptive sales pitches
                return self._get_adaptive_sales_pitch()
        
        elif self.session_state["conversation_stage"] == "contact_collection":
            # Extract name and contact info
            user_info = self.session_state["user_info"]
            
            # If we have name and contact info, move to appointment confirmation
            if user_info["name"] and (user_info["phone"] or user_info["email"]):
                self.session_state["conversation_stage"] = "closing"
                
                # Format closing message with name and phone
                name = user_info["name"]
                phone = user_info["phone"] or "الرقم الذي قدمته"
                closing_phrase = self.phrases[self.current_dialect]["confirm_appointment"]
                return closing_phrase.format(name=name, phone=phone)
            else:
                # Still need more info
                if not user_info["name"]:
                    return "ممكن أعرف اسم حضرتك؟"
                elif not user_info["phone"]:
                    return "ممكن رقم موبايلك عشان نقدر نتواصل معاك؟"
        
        elif self.session_state["conversation_stage"] == "refining":
            # Handle refinement input
            print(f"[INFO] Processing refinement input: {user_input}")
            
            # Look for keywords to determine what to refine
            if any(word in user_input.lower() for word in ["ميزانية", "سعر", "فلوس", "budget", "price"]):
                # Reset budget preference
                self.session_state["preferences"]["budget"] = None
                return self.get_phrase("ask_budget")
            elif any(word in user_input.lower() for word in ["منطقة", "مكان", "location", "area"]):
                # Reset location preference
                self.session_state["preferences"]["location"] = None
                return self.get_phrase("ask_location")
            elif any(word in user_input.lower() for word in ["غرف", "اوض", "bedrooms", "room"]):
                # Reset bedrooms preference
                self.session_state["preferences"]["bedrooms"] = None
                return self.get_phrase("ask_bedrooms")
            elif any(word in user_input.lower() for word in ["حمام", "bathroom", "toilet"]):
                # Reset bathrooms preference
                self.session_state["preferences"]["bathrooms"] = None
                return self.get_phrase("ask_bathrooms")
            elif any(word in user_input.lower() for word in ["نوع", "type"]):
                # Reset property type preference
                self.session_state["preferences"]["type"] = None
                return self.get_phrase("ask_type")
            elif any(word in user_input.lower() for word in ["مساحة", "متر", "area", "size"]):
                # Reset area preference
                self.session_state["preferences"]["area_m2"] = None
                return self.get_phrase("ask_area")
            elif any(word in user_input.lower() for word in ["نعم", "أيوة", "yes", "ok", "تمام"]):
                # User agrees to refine, ask which criterion
                return "ما هو المعيار الذي تريد تعديله؟ (النوع، المنطقة، عدد الغرف، المساحة، الميزانية)"
            else:
                # Try to make recommendation with current preferences
                self.session_state["conversation_stage"] = "recommending"
                return self._make_recommendation()
        
        elif self.session_state["conversation_stage"] == "closing":
            # Closing the deal
            if any(word in user_input.lower() for word in ["شكراً", "شكرا", "ممتاز", "أشكرك", "thank", "thanks", "good"]):
                # User is thankful
                return "العفو! سعدت جداً بمساعدتك. أتمنى أن تكون سعيداً بالعقار الجديد. سنتواصل معك قريباً لإتمام التفاصيل. هل هناك أي استفسارات أخرى؟"
            elif any(word in user_input.lower() for word in ["نعم", "أيوة", "تمام", "حلو", "yes", "اوك", "موافق"]):
                # User confirms
                return "ممتاز! سنتواصل معك قريباً لإتمام التفاصيل. شكراً لاختيارك التعامل معنا، ونتطلع إلى مساعدتك في العثور على منزل أحلامك!"
            elif any(word in user_input.lower() for word in ["معلومات", "تفاصيل", "اسأل", "سؤال", "استفسار", "info", "question", "details"]):
                # User asks for more information
                return "بكل سرور، العقار يقع في منطقة راقية مع خدمات متكاملة. التشطيبات عالية الجودة، والمرافق والخدمات العامة قريبة جداً. هل هناك أي معلومات محددة ترغب في معرفتها؟"
            elif any(word in user_input.lower() for word in ["وقت", "تاريخ", "ساعة", "يوم", "date", "time", "tomorrow", "today"]):
                # User suggests another time
                return "تم تسجيل الموعد المطلوب. سأؤكد لك التفاصيل عبر الهاتف. هل هناك أي استفسارات أخرى لديك؟"
            else:
                # General closing response
                return "شكراً لاهتمامك! سنتواصل معك قريباً على الرقم الذي قدمته لتحديد موعد المعاينة وإتمام باقي التفاصيل. نسعد دائماً بخدمتك!"
        
        else:
            # Default response
            return self.get_phrase("greeting")
    
    def _check_buying_intent(self, user_input: str) -> bool:
        """
        Check if user input indicates intent to buy/rent property
        Only detect clear buying intent phrases, not general interest
        """
        # Skip short messages - they're unlikely to contain real buying intent
        if len(user_input.strip()) < 10:
            return False
            
        # Define very specific buying intent phrases
        clear_intent_phrases = [
            "عايز اشتري", "هشتري", "أريد شراء", "موافق على الشراء",
            "أقبل العرض", "اتفقنا", "اخدت قراري", "أوافق على السعر",
            "نروح نشوفها امتى", "متى أستطيع رؤيتها"
        ]
        
        # Check for these specific phrases
        user_input_lower = user_input.lower()
        for phrase in clear_intent_phrases:
            if phrase in user_input_lower:
                print(f"[INFO] Detected clear buying intent with phrase: {phrase}")
                return True
                
        # If we're in sales_pitch stage and user replies positively to viewing question
        if self.session_state["conversation_stage"] == "sales_pitch" and self.session_state["sales_pitch_stage"] >= 4:
            positive_responses = ["نعم", "أيوة", "تمام", "موافق", "اوك", "خلاص", "ماشي", "ok", "yes", "sure"]
            
            # If user responds positively to viewing question
            if any(response in user_input_lower for response in positive_responses):
                print(f"[INFO] Detected positive response to viewing question")
                return True
                
        return False
    
    def _extract_contact_info(self, user_input: str) -> None:
        """Extract contact information from user input"""
        user_info = self.session_state["user_info"]
        
        # Extract name
        if user_info["name"] is None:
            name_match = re.search(self.patterns["contact_patterns"]["name"], user_input)
            if name_match:
                user_info["name"] = name_match.group(1).strip()
                print(f"[INFO] Extracted name: {user_info['name']}")
            elif len(user_input.split()) <= 3 and self.session_state["conversation_stage"] == "contact_collection":
                # If we're in contact collection mode and this is a short response
                # It's likely just the name
                user_info["name"] = user_input.strip()
                print(f"[INFO] Using input as name: {user_info['name']}")
                
        # Extract phone number
        if user_info["phone"] is None:
            phone_match = re.search(self.patterns["contact_patterns"]["phone"], user_input)
            if phone_match:
                phone = phone_match.group(0).strip()
                user_info["phone"] = phone
                print(f"[INFO] Extracted phone: {user_info['phone']}")
                
        # Extract email
        if user_info["email"] is None:
            email_match = re.search(self.patterns["contact_patterns"]["email"], user_input)
            if email_match:
                user_info["email"] = email_match.group(0).strip()
                print(f"[INFO] Extracted email: {user_info['email']}")
    
    def _extract_information(self, user_input: str) -> None:
        """
        Extract relevant information from user input.
        
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
                "bathrooms": None,
                "budget": None,
                "area_m2": None,
                "floor": None,
                "purpose": None,
                "compound": None,
                "finishing": None,
                "finishing_type": None,
                "services": [],
                "other_features": []
            }
                
        # Extract property type
        if self.session_state["preferences"]["type"] is None:
            for prop_type, patterns in self.patterns["type_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["type"] = prop_type
                    print(f"[INFO] Detected property type: {prop_type}")
                    break
        
        # Extract purpose (buy/rent)
        if self.session_state["preferences"]["purpose"] is None:
            for purpose, patterns in self.patterns["purpose_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["purpose"] = purpose
                    print(f"[INFO] Detected purpose: {purpose}")
                    break
        
        # Extract compound preference
        if self.session_state["preferences"]["compound"] is None:
            for answer, patterns in self.patterns["compound_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["compound"] = answer
                    print(f"[INFO] Detected compound preference: {answer}")
                    break
        
        # Extract finishing
        if self.session_state["preferences"]["finishing"] is None:
            for finishing, patterns in self.patterns["finishing_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["finishing"] = finishing
                    print(f"[INFO] Detected finishing: {finishing}")
                    break
        
        # Extract finishing type
        if self.session_state["preferences"]["finishing"] == "متشطب" and self.session_state["preferences"].get("finishing_type") is None:
            for finish_type, patterns in self.patterns["finishing_type_patterns"].items():
                if any(pattern in user_input.lower() for pattern in patterns):
                    self.session_state["preferences"]["finishing_type"] = finish_type
                    print(f"[INFO] Detected finishing type: {finish_type}")
                    break
        
        # Extract services
        services = self.session_state["preferences"]["services"]
        for service, patterns in self.patterns["services_patterns"].items():
            if any(pattern in user_input.lower() for pattern in patterns) and service not in services:
                services.append(service)
                print(f"[INFO] Detected service: {service}")
        
        # Extract budget
        if self.session_state["preferences"]["budget"] is None:
            # First try the specific pattern
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
                    
                    # Sanity check for real estate pricing
                    if amount < 1000:
                        amount *= 1000000  # Assume it's in millions
                    elif amount < 100000:
                        amount *= 1000  # Assume it's in thousands
                    
                    self.session_state["preferences"]["budget"] = amount
                    print(f"[INFO] Extracted budget: {amount}")
                except ValueError:
                    pass
            
            # Try to find budget range (from X to Y)
            elif any(phrase in user_input.lower() for phrase in ["من", "الى", "إلى", "حتى", "لغاية", "to", "بين"]):
                numbers = re.findall(r'\d+(?:,\d+)*', user_input)
                if len(numbers) >= 2:
                    try:
                        # Take the higher number as the budget
                        amounts = [float(num.replace(',', '')) for num in numbers]
                        max_amount = max(amounts)
                        
                        # Apply heuristics based on magnitude
                        if max_amount < 1000:
                            max_amount *= 1000000  # Assume it's in millions
                        elif max_amount < 100000:
                            max_amount *= 1000  # Assume it's in thousands
                        
                        self.session_state["preferences"]["budget"] = max_amount
                        print(f"[INFO] Extracted budget from range: {max_amount}")
                    except ValueError:
                        pass
        
        # Extract bedroom count
        if self.session_state["preferences"]["bedrooms"] is None:
            bedroom_match = re.search(self.patterns["bedroom_patterns"]["count"], user_input)
            if bedroom_match:
                try:
                    bedrooms = int(bedroom_match.group(1))
                    self.session_state["preferences"]["bedrooms"] = bedrooms
                    print(f"[INFO] Extracted bedrooms: {bedrooms}")
                except ValueError:
                    pass
        
        # Extract bathroom count
        if self.session_state["preferences"]["bathrooms"] is None:
            bathroom_match = re.search(self.patterns["bathroom_patterns"]["count"], user_input)
            if bathroom_match:
                try:
                    bathrooms = int(bathroom_match.group(1))
                    self.session_state["preferences"]["bathrooms"] = bathrooms
                    print(f"[INFO] Extracted bathrooms: {bathrooms}")
                except ValueError:
                    pass
        
        # Extract area
        if self.session_state["preferences"]["area_m2"] is None:
            area_match = re.search(self.patterns["area_patterns"]["area"], user_input)
            if area_match:
                try:
                    area = int(area_match.group(1))
                    self.session_state["preferences"]["area_m2"] = area
                    print(f"[INFO] Extracted area: {area}")
                except ValueError:
                    pass
        
        # Extract floor
        if self.session_state["preferences"]["floor"] is None:
            floor_match = re.search(self.patterns["floor_patterns"]["floor"], user_input)
            if floor_match:
                try:
                    floor = int(floor_match.group(1))
                    self.session_state["preferences"]["floor"] = floor
                    print(f"[INFO] Extracted floor: {floor}")
                except ValueError:
                    pass
        
        # Extract location
        if self.session_state["preferences"]["location"] is None:
            print(f"[INFO] Trying to extract location from: '{user_input}'")
            
            # First check for locations from our dataset
            try:
                user_input_lower = user_input.lower()
                
                # Try to match location from dataset first
                for location in self.properties_df["location"].unique():
                    if isinstance(location, str) and location.lower() in user_input_lower:
                        print(f"[INFO] Matched dataset location: {location}")
                        self.session_state["preferences"]["location"] = location
                        return  # Exit early if we found a match
                
                # Direct matching for common Arabic locations as fallback
                common_locations = {
                    "التجمع": "Cairo", 
                    "الرحاب": "Cairo",
                    "مدينتي": "Cairo",
                    "الشيخ زايد": "Giza",
                    "6 اكتوبر": "Giza",
                    "أكتوبر": "Giza",
                    "المعادي": "Cairo",
                    "مصر الجديدة": "Cairo",
                    "القاهرة الجديدة": "Cairo",
                    "الإسكندرية": "Alexandria",
                    "اسكندرية": "Alexandria",
                    "الجيزة": "Giza",
                    "جيزة": "Giza",
                    "القاهرة": "Cairo",
                    "أسيوط": "Assiut",
                    "المنصورة": "Mansoura",
                }
                
                # Check common locations
                for location_key, location_value in common_locations.items():
                    if location_key.lower() in user_input_lower:
                        print(f"[INFO] Matched common location: {location_value}")
                        self.session_state["preferences"]["location"] = location_value
                        return  # Exit early if we found a match
                
                # For the case where we're specifically asking for location and we get a one-word answer
                if self.session_state["conversation_stage"] == "clarifying" and len(user_input.split()) <= 2:
                    # Use the input directly as a location if it's short
                    cleanInput = user_input.strip()
                    # Check if it exists in our dataset first
                    for location in self.properties_df["location"].unique():
                        if cleanInput.lower() == location.lower():
                            self.session_state["preferences"]["location"] = location
                            print(f"[INFO] Matched exact location: {location}")
                            return
                            
                    # If not found, just use as is
                    print(f"[INFO] Using direct input as location: {cleanInput}")
                    self.session_state["preferences"]["location"] = cleanInput
                
            except Exception as e:
                print(f"[ERROR] Failed to match location from dataset: {str(e)}")
    
    def _get_adaptive_sales_pitch(self) -> str:
        """
        Generate varied and persuasive sales pitches that build desire for the current property
        
        Returns:
            A persuasive sales argument
        """
        # Get a different sales pitch each time
        used_arguments = self.session_state.get("used_sales_arguments", [])
        property_data = self.session_state.get("current_property", {})
        
        # Filter out arguments we've already used
        available_arguments = [arg for arg in self.sales_arguments if arg not in used_arguments]
        
        # If we've used all arguments, reset
        if not available_arguments:
            self.session_state["used_sales_arguments"] = []
            available_arguments = self.sales_arguments
        
        # Choose a random argument
        pitch = random.choice(available_arguments)
        
        # Enhance pitch with property-specific details if available
        if property_data:
            try:
                # Add property details to personalize the pitch
                if "neighborhood" in property_data and "location" in property_data:
                    pitch = pitch.replace("المنطقة دي", f"منطقة {property_data['neighborhood']} في {property_data['location']}")
                
                # Add price comparison if available
                if "price" in property_data:
                    price = int(property_data["price"])
                    pitch += f"\n\nالسعر ({price:,}) أقل من متوسط أسعار العقارات المماثلة في المنطقة بنسبة 5-10%."
            except:
                # If any error occurs during personalization, just use the original pitch
                pass
        
        # Update used arguments
        used_arguments.append(pitch)
        self.session_state["used_sales_arguments"] = used_arguments
        
        return pitch
    
    def _ask_next_question(self) -> str:
        """
        Ask the next question in the flow based on current state
        
        Returns:
            The next question to ask
        """
        # If we've asked all questions, move to summary
        if self.session_state["question_flow_index"] >= len(self.question_flow):
            return self._generate_summary()
        
        # Get the next question type
        question_type = self.question_flow[self.session_state["question_flow_index"]]
        
        # Check if we should skip compound question for non-residential properties
        if question_type == "compound" and self.session_state["preferences"]["type"] not in ["شقة", "فيلا"]:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
            
        # Check if we should skip finishing type question for non-fully-finished properties
        if question_type == "finishing_type":
            if self.session_state["preferences"]["finishing"] != "متشطب" or self.session_state["asked_finishing_type"]:
                self.session_state["question_flow_index"] += 1
                return self._ask_next_question()
            self.session_state["asked_finishing_type"] = True
            
        # Check if we already asked services question
        if question_type == "services" and self.session_state["asked_services"]:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
            
        # Check if we already have an answer for this question
        preferences = self.session_state["preferences"]
        
        if question_type == "location" and preferences["location"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "purpose" and preferences["purpose"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "type" and preferences["type"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "compound" and preferences["compound"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "area_m2" and preferences["area_m2"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "finishing" and preferences["finishing"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "floor" and preferences["floor"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "budget" and preferences["budget"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "bedrooms" and preferences["bedrooms"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        elif question_type == "bathrooms" and preferences["bathrooms"] is not None:
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
        
        # Ask the appropriate question
        if question_type == "location":
            self.session_state["last_question_asked"] = "ask_location"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_location")
        elif question_type == "purpose":
            self.session_state["last_question_asked"] = "ask_purpose"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_purpose")
        elif question_type == "type":
            self.session_state["last_question_asked"] = "ask_type"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_type")
        elif question_type == "compound":
            self.session_state["last_question_asked"] = "ask_compound"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_compound")
        elif question_type == "area_m2":
            self.session_state["last_question_asked"] = "ask_area"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_area")
        elif question_type == "finishing":
            self.session_state["last_question_asked"] = "ask_finishing"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_finishing")
        elif question_type == "finishing_type":
            self.session_state["last_question_asked"] = "ask_finishing_type"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_finishing_type")
        elif question_type == "services":
            self.session_state["last_question_asked"] = "ask_services"
            self.session_state["asked_services"] = True
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_services")
        elif question_type == "floor":
            self.session_state["last_question_asked"] = "ask_floor"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_floor")
        elif question_type == "budget":
            self.session_state["last_question_asked"] = "ask_budget"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_budget")
        elif question_type == "bedrooms":
            self.session_state["last_question_asked"] = "ask_bedrooms"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_bedrooms")
        elif question_type == "bathrooms":
            self.session_state["last_question_asked"] = "ask_bathrooms"
            self.session_state["question_flow_index"] += 1
            return self.get_phrase("ask_bathrooms")
        else:
            # Increment index and try next question
            self.session_state["question_flow_index"] += 1
            return self._ask_next_question()
    
    def _generate_summary(self) -> str:
        """Generate a summary of collected preferences"""
        preferences = self.session_state["preferences"]
        
        # Move to summarizing stage
        self.session_state["conversation_stage"] = "summarizing"
        
        # Create the summary based on dialect
        if self.current_dialect == "egyptian":
            summary = f"{self.get_phrase('summary_intro')}\n\n"
            
            if preferences["type"]:
                summary += f"• نوع العقار: {preferences['type']}\n"
            
            if preferences["location"]:
                summary += f"• منطقة البحث: {preferences['location']}\n"
            
            if preferences["purpose"]:
                summary += f"• الغرض: {preferences['purpose']}\n"
            
            if preferences["budget"]:
                summary += f"• الميزانية: {int(preferences['budget']):,} جنيه\n"
            
            if preferences["area_m2"]:
                summary += f"• المساحة: {preferences['area_m2']} متر مربع\n"
            
            if preferences["bedrooms"]:
                summary += f"• عدد الغرف: {preferences['bedrooms']}\n"
            
            if preferences["bathrooms"]:
                summary += f"• عدد الحمامات: {preferences['bathrooms']}\n"
            
            if preferences["finishing"]:
                summary += f"• التشطيب: {preferences['finishing']}"
                if preferences.get("finishing_type"):
                    summary += f" ({preferences['finishing_type']})\n"
                else:
                    summary += "\n"
            
            if preferences["floor"]:
                summary += f"• الطابق المطلوب: {preferences['floor']}\n"
            
            if len(preferences["services"]) > 0:
                summary += f"• الخدمات المطلوبة: {', '.join(preferences['services'])}\n"
            
            summary += f"\n{self.get_phrase('summary_confirm')}"
        
        elif self.current_dialect == "khaleeji":
            summary = f"{self.get_phrase('summary_intro')}\n\n"
            
            if preferences["type"]:
                summary += f"• نوع العقار: {preferences['type']}\n"
            
            if preferences["location"]:
                summary += f"• منطقة البحث: {preferences['location']}\n"
            
            if preferences["purpose"]:
                summary += f"• الغرض: {preferences['purpose']}\n"
            
            if preferences["budget"]:
                summary += f"• الميزانية: {int(preferences['budget']):,} ريال\n"
            
            if preferences["area_m2"]:
                summary += f"• المساحة: {preferences['area_m2']} متر مربع\n"
            
            if preferences["bedrooms"]:
                summary += f"• عدد الغرف: {preferences['bedrooms']}\n"
            
            if preferences["bathrooms"]:
                summary += f"• عدد الحمامات: {preferences['bathrooms']}\n"
            
            if preferences["finishing"]:
                summary += f"• التشطيب: {preferences['finishing']}"
                if preferences.get("finishing_type"):
                    summary += f" ({preferences['finishing_type']})\n"
                else:
                    summary += "\n"
            
            if preferences["floor"]:
                summary += f"• الطابق المطلوب: {preferences['floor']}\n"
            
            if len(preferences["services"]) > 0:
                summary += f"• الخدمات المطلوبة: {', '.join(preferences['services'])}\n"
            
            summary += f"\n{self.get_phrase('summary_confirm')}"
        
        else:  # MSA
            summary = f"{self.get_phrase('summary_intro')}\n\n"
            
            if preferences["type"]:
                summary += f"• نوع العقار: {preferences['type']}\n"
            
            if preferences["location"]:
                summary += f"• منطقة البحث: {preferences['location']}\n"
            
            if preferences["purpose"]:
                summary += f"• الغرض: {preferences['purpose']}\n"
            
            if preferences["budget"]:
                summary += f"• الميزانية: {int(preferences['budget']):,} وحدة نقدية\n"
            
            if preferences["area_m2"]:
                summary += f"• المساحة: {preferences['area_m2']} متر مربع\n"
            
            if preferences["bedrooms"]:
                summary += f"• عدد الغرف: {preferences['bedrooms']}\n"
            
            if preferences["bathrooms"]:
                summary += f"• عدد الحمامات: {preferences['bathrooms']}\n"
            
            if preferences["finishing"]:
                summary += f"• التشطيب: {preferences['finishing']}"
                if preferences.get("finishing_type"):
                    summary += f" ({preferences['finishing_type']})\n"
                else:
                    summary += "\n"
            
            if preferences["floor"]:
                summary += f"• الطابق المطلوب: {preferences['floor']}\n"
            
            if len(preferences["services"]) > 0:
                summary += f"• الخدمات المطلوبة: {', '.join(preferences['services'])}\n"
            
            summary += f"\n{self.get_phrase('summary_confirm')}"
        
        return summary
    
    def _make_recommendation(self) -> str:
        """
        Generate a property recommendation based on user preferences.
        
        Returns:
            Recommendation text with property details
        """
        preferences = self.session_state["preferences"]
        
        # Filter properties based on preferences
        filtered_df = self.properties_df.copy()
        
        # Apply loose filtering when we can't find exact matches
        if preferences["type"] is not None:
            try:
                filtered_df = filtered_df[filtered_df["type"] == preferences["type"]]
                # If no results, don't filter by type
                if len(filtered_df) == 0:
                    print(f"[INFO] No properties match the type {preferences['type']}, ignoring type filter")
                    filtered_df = self.properties_df.copy()
            except Exception as e:
                print(f"[ERROR] Error filtering by type: {str(e)}")
        
        if preferences["location"] is not None and len(filtered_df) > 0:
            try:
                exact_match_df = filtered_df[filtered_df["location"] == preferences["location"]]
                # If no exact matches, try loose matching
                if len(exact_match_df) == 0:
                    print(f"[INFO] No exact location matches for {preferences['location']}, trying loose matching")
                    # Don't apply location filter if can't find match
                else:
                    filtered_df = exact_match_df
            except Exception as e:
                print(f"[ERROR] Error filtering by location: {str(e)}")
        
        if preferences["bedrooms"] is not None and len(filtered_df) > 0:
            try:
                exact_match_df = filtered_df[filtered_df["bedrooms"] == preferences["bedrooms"]]
                # If no exact matches, try nearby bedroom counts
                if len(exact_match_df) == 0:
                    print(f"[INFO] No exact bedroom matches for {preferences['bedrooms']}, trying nearby counts")
                    # Look for properties with bedrooms +/- 1
                    nearby_df = filtered_df[
                        (filtered_df["bedrooms"] >= preferences["bedrooms"] - 1) & 
                        (filtered_df["bedrooms"] <= preferences["bedrooms"] + 1)
                    ]
                    if len(nearby_df) > 0:
                        filtered_df = nearby_df
                else:
                    filtered_df = exact_match_df
            except Exception as e:
                print(f"[ERROR] Error filtering by bedrooms: {str(e)}")
        
        if preferences["bathrooms"] is not None and len(filtered_df) > 0:
            try:
                exact_match_df = filtered_df[filtered_df["bathrooms"] == preferences["bathrooms"]]
                # If no exact matches, try nearby bathroom counts
                if len(exact_match_df) == 0:
                    print(f"[INFO] No exact bathroom matches for {preferences['bathrooms']}, trying nearby counts")
                    # Look for properties with bathrooms +/- 1
                    nearby_df = filtered_df[
                        (filtered_df["bathrooms"] >= preferences["bathrooms"] - 1) & 
                        (filtered_df["bathrooms"] <= preferences["bathrooms"] + 1)
                    ]
                    if len(nearby_df) > 0:
                        filtered_df = nearby_df
                else:
                    filtered_df = exact_match_df
            except Exception as e:
                print(f"[ERROR] Error filtering by bathrooms: {str(e)}")
        
        if preferences["budget"] is not None and len(filtered_df) > 0:
            try:
                # Add a 20% buffer to the budget
                budget_with_buffer = preferences["budget"] * 1.2
                budget_filtered_df = filtered_df[filtered_df["price"] <= budget_with_buffer]
                
                # If no properties within budget, try up to 50% over budget
                if len(budget_filtered_df) == 0:
                    print(f"[INFO] No properties within budget {preferences['budget']}, extending buffer")
                    extended_budget = preferences["budget"] * 1.5
                    budget_filtered_df = filtered_df[filtered_df["price"] <= extended_budget]
                
                # If still no matches, just get the cheapest options
                if len(budget_filtered_df) == 0:
                    print(f"[INFO] No properties within extended budget, finding cheapest options")
                    budget_filtered_df = filtered_df.nsmallest(3, "price")
                
                filtered_df = budget_filtered_df
            except Exception as e:
                print(f"[ERROR] Error filtering by budget: {str(e)}")
        
        # Filter out properties already shown, if possible
        try:
            if len(self.session_state["shown_properties"]) > 0:
                not_shown_df = filtered_df[~filtered_df["id"].isin(self.session_state["shown_properties"])]
                # Only apply this filter if we still have properties left
                if len(not_shown_df) > 0:
                    filtered_df = not_shown_df
        except Exception as e:
            print(f"[ERROR] Error filtering out shown properties: {str(e)}")
        
        # If after all filtering we have no properties, suggest criteria adjustment
        if len(filtered_df) == 0:
            return self._suggest_criteria_adjustment()
        
        # Present two options as requested
        try:
            # Sort by price to get the best matches within budget
            filtered_df = filtered_df.sort_values(by="price")
            
            # Get up to 2 properties to recommend
            best_properties = []
            for i in range(min(2, len(filtered_df))):
                property_data = filtered_df.iloc[i]
                
                # Add to shown properties
                property_id = int(property_data["id"]) if "id" in property_data else -1
                if property_id >= 0 and property_id not in self.session_state["shown_properties"]:
                    self.session_state["shown_properties"].append(property_id)
                
                if i == 0:
                    self.session_state["current_property"] = property_data.to_dict()
                
                best_properties.append(property_data)
            
            # Generate recommendations text
            recommendation = self._format_multiple_recommendations(best_properties)
            return recommendation
            
        except Exception as e:
            print(f"[ERROR] Error selecting best properties: {str(e)}")
            return "عذراً، حدثت مشكلة في اختيار العقار المناسب. هل يمكننا تعديل معايير البحث؟"
    
    def _format_multiple_recommendations(self, properties):
        """Format multiple property recommendations"""
        try:
            if self.current_dialect == "egyptian":
                recommendation = f"{self.get_phrase('suggestions_intro')}\n\n"
                
                for i, property_data in enumerate(properties):
                    recommendation += f"✨ الاقتراح رقم {i+1}:\n"
                    recommendation += f"🏠 {property_data['type']} في {property_data['location']}, حي {property_data['neighborhood']}\n"
                    recommendation += f"💰 السعر: {int(property_data['price']):,} {property_data['currency']}\n"
                    recommendation += f"🛏️ عدد الغرف: {int(property_data['bedrooms'])}\n"
                    recommendation += f"🚿 عدد الحمامات: {int(property_data['bathrooms'])}\n"
                    recommendation += f"📏 المساحة: {int(property_data['area_m2'])} متر مربع\n"
                    recommendation += f"{property_data['description']}\n\n"
                
                recommendation += "أي من هذه العقارات تفضل؟ رقم 1 أم رقم 2؟ أم تريد اقتراحات أخرى؟"
            
            elif self.current_dialect == "khaleeji":
                recommendation = f"{self.get_phrase('suggestions_intro')}\n\n"
                
                for i, property_data in enumerate(properties):
                    recommendation += f"✨ الاقتراح رقم {i+1}:\n"
                    recommendation += f"🏠 {property_data['type']} في {property_data['location']}, حي {property_data['neighborhood']}\n"
                    recommendation += f"💰 السعر: {int(property_data['price']):,} {property_data['currency']}\n"
                    recommendation += f"🛏️ عدد الغرف: {int(property_data['bedrooms'])}\n"
                    recommendation += f"🚿 عدد الحمامات: {int(property_data['bathrooms'])}\n"
                    recommendation += f"📏 المساحة: {int(property_data['area_m2'])} متر مربع\n"
                    recommendation += f"{property_data['description']}\n\n"
                
                recommendation += "أي من هذه العقارات تفضل؟ رقم 1 أم رقم 2؟ أو تبي خيارات ثانية؟"
            
            else:  # MSA
                recommendation = f"{self.get_phrase('suggestions_intro')}\n\n"
                
                for i, property_data in enumerate(properties):
                    recommendation += f"✨ الاقتراح رقم {i+1}:\n"
                    recommendation += f"🏠 {property_data['type']} في {property_data['location']}, حي {property_data['neighborhood']}\n"
                    recommendation += f"💰 السعر: {int(property_data['price']):,} {property_data['currency']}\n"
                    recommendation += f"🛏️ عدد الغرف: {int(property_data['bedrooms'])}\n"
                    recommendation += f"🚿 عدد الحمامات: {int(property_data['bathrooms'])}\n"
                    recommendation += f"📏 المساحة: {int(property_data['area_m2'])} متر مربع\n"
                    recommendation += f"{property_data['description']}\n\n"
                
                recommendation += "أي من هذه العقارات تفضل؟ رقم 1 أم رقم 2؟ أم ترغب باقتراحات أخرى؟"
                
            return recommendation
        except Exception as e:
            print(f"[ERROR] Error formatting property recommendations: {str(e)}")
            return f"{self.get_phrase('recommendation')}\n\nلدي عقارات تناسب طلبك، ولكن حدثت مشكلة في عرض التفاصيل. هل ترغب في تعديل معايير البحث؟"
    
    def _suggest_criteria_adjustment(self) -> str:
        """
        Suggest adjusting search criteria when no matching properties are found.
        
        Returns:
            Suggestion text for adjusting criteria
        """
        preferences = self.session_state["preferences"]
        
        # Determine which criteria might be too restrictive
        problem_criteria = []
        
        # Check budget constraints
        if preferences["budget"] is not None:
            min_price = self.properties_df["price"].min()
            if min_price > preferences["budget"]:
                problem_criteria.append("budget_too_low")
        
        # Check location constraints
        if preferences["location"] is not None:
            try:
                available_locations = set(self.properties_df["location"].unique())
                if preferences["location"] not in available_locations:
                    problem_criteria.append("location_not_available")
            except Exception as e:
                print(f"[ERROR] Error checking location constraints: {str(e)}")
        
        # Check property type constraints
        if preferences["type"] is not None:
            try:
                type_count = len(self.properties_df[self.properties_df["type"] == preferences["type"]])
                if type_count == 0:
                    problem_criteria.append("type_not_available")
            except Exception as e:
                print(f"[ERROR] Error checking property type constraints: {str(e)}")
        
        # Check bedroom constraints
        if preferences["bedrooms"] is not None:
            try:
                bedroom_count = len(self.properties_df[self.properties_df["bedrooms"] == preferences["bedrooms"]])
                if bedroom_count == 0:
                    problem_criteria.append("bedrooms_not_available")
            except Exception as e:
                print(f"[ERROR] Error checking bedroom constraints: {str(e)}")
        
        # If no specific problems found, it's a combination issue
        if not problem_criteria:
            problem_criteria.append("combination")
        
        # Generate suggestion based on dialect and problems
        if self.current_dialect == "egyptian":
            if "budget_too_low" in problem_criteria:
                suggestion = "للأسف مفيش عقارات متاحة بالميزانية دي. ممكن نزود الميزانية شوية؟"
            elif "location_not_available" in problem_criteria:
                suggestion = "معلش، مفيش عقارات في المنطقة دي. ممكن نشوف مناطق تانية قريبة؟"
            elif "type_not_available" in problem_criteria:
                suggestion = "مفيش عقارات من النوع ده متاحة حالياً. ممكن نشوف نوع تاني؟"
            elif "bedrooms_not_available" in problem_criteria:
                suggestion = "مش لاقي عقارات بعدد الأوض ده. ممكن نشوف عدد أوض مختلف؟"
            else:
                suggestion = "المعايير اللي اخترتها مش متوفرة مع بعض. ممكن نغير واحد منهم؟"
        elif self.current_dialect == "khaleeji":
            if "budget_too_low" in problem_criteria:
                suggestion = "للأسف ما في عقارات متوفرة بهذي الميزانية. ممكن نزيد الميزانية شوي؟"
            elif "location_not_available" in problem_criteria:
                suggestion = "عذراً، ما في عقارات في هالمنطقة. نقدر نشوف مناطق ثانية قريبة؟"
            elif "type_not_available" in problem_criteria:
                suggestion = "ما في عقارات من هالنوع متوفرة حالياً. ممكن نشوف نوع ثاني؟"
            elif "bedrooms_not_available" in problem_criteria:
                suggestion = "ما حصلت عقارات بهالعدد من الغرف. ممكن نشوف عدد غرف مختلف؟"
            else:
                suggestion = "المعايير اللي اخترتها مو متوفرة مع بعض. ممكن نغير واحد منها؟"
        else:  # MSA
            if "budget_too_low" in problem_criteria:
                suggestion = "للأسف لا توجد عقارات متاحة بهذه الميزانية. هل يمكننا زيادة الميزانية قليلاً؟"
            elif "location_not_available" in problem_criteria:
                suggestion = "عذراً، لا توجد عقارات في هذه المنطقة. هل يمكننا البحث في مناطق أخرى قريبة؟"
            elif "type_not_available" in problem_criteria:
                suggestion = "لا توجد عقارات من هذا النوع متاحة حالياً. هل نبحث عن نوع آخر؟"
            elif "bedrooms_not_available" in problem_criteria:
                suggestion = "لم أجد عقارات بهذا العدد من الغرف. هل يمكننا النظر في عدد غرف مختلف؟"
            else:
                suggestion = "المعايير التي اخترتها غير متوفرة معاً. هل يمكننا تعديل أحدها؟"
                
        # Move to refining stage
        self.session_state["conversation_stage"] = "refining"
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
    return ArabicRealEstateAgent(properties_df, dialect=dialect)
