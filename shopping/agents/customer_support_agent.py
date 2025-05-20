"""
Customer Support Agent for ShopperAI
Handles customer support operations including refunds, FAQ responses, and ticket escalations.
"""
from typing import Dict, Any, Optional, List, Union, Tuple
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import os
from pydantic import Field, ConfigDict, BaseModel
import asyncio
import uuid
import datetime
import json
from pathlib import Path
from difflib import get_close_matches
import logging
from dataclasses import dataclass
from enum import Enum
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of matches for FAQ searching"""
    EXACT = "exact"
    PARTIAL = "partial"
    KEYWORD = "keyword"
    NONE = "none"


@dataclass
class MatchScore:
    """Data class for storing match scores"""
    keyword_score: float
    similarity_score: float
    combined_score: float
    match_type: MatchType


class FAQResponse(BaseModel):
    """Pydantic model for FAQ response validation"""
    query: str
    found: bool
    timestamp: str
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    confidence_score: Optional[float] = None
    suggested_questions: List[str] = []
    helpful_links: List[str] = []
    related_topics: List[str] = []
    message: Optional[str] = None


class AztpConnection(BaseModel):
    """AZTP connection state"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Optional[Aztp] = None
    connection: Optional[SecureConnection] = None
    aztp_id: str = ""
    is_valid: bool = False
    is_initialized: bool = False


class CustomerSupportAgent(Agent):
    """Agent responsible for handling customer support operations"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    aztp: AztpConnection = Field(default_factory=AztpConnection)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    faq_data: Dict = Field(default={}, exclude=True)
    categories: Dict = Field(default={}, exclude=True)
    metadata: Dict = Field(default={}, exclude=True)
    openai_client: openai.OpenAI = Field(default=None, exclude=True)
    knowledge_base: str = Field(default="", exclude=True)

    def __init__(self):
        """Initialize the customer support agent with necessary tools"""
        super().__init__(
            role='Customer Support Agent',
            goal='Handle customer support operations including refunds, FAQs, and ticket escalations',
            backstory="""You are an expert customer support agent with extensive experience in 
            handling customer inquiries, processing refunds, and managing support tickets. You ensure 
            customer satisfaction while following company policies and procedures.""",
            verbose=True
        )

        try:
            # Initialize AZTP connection
            api_key = os.getenv("AZTP_API_KEY")
            if not api_key:
                raise ValueError("AZTP_API_KEY is not set")

            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set")

            self.aztpClient = Aztp(api_key=api_key)
            self.aztp = AztpConnection(
                client=Aztp(api_key=api_key)
            )
            self.iam_utils = IAMUtils()
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            self._load_faq_database()  # Load FAQ database during initialization

        except Exception as e:
            logger.error(f"Error initializing CustomerSupportAgent: {str(e)}")
            raise

    async def initialize(self):
        """Initialize the agent asynchronously"""
        if not self.is_initialized:
            print("\nInitializing Customer Support Agent...")
            try:
                # Establish secure connection
                self.aztp.connection = await self.aztpClient.secure_connect(
                    self,
                    "customer-support-agent",
                    {
                        "isGlobalIdentity": False,
                        "trustLevel": "high",
                        "department": "CustomerSupport"
                    }
                )

                # Store AZTP ID
                if self.aztp.connection and hasattr(self.aztp.connection, 'identity'):
                    self.aztp.aztp_id = self.aztp.connection.identity.aztp_id
                    print(
                        f"✅ Secured connection established. AZTP ID: {self.aztp.aztp_id}")

                # Verify identity
                self.aztp.is_valid = await self.aztpClient.verify_identity(self.aztp.connection)
                if not self.aztp.is_valid:
                    raise ValueError(
                        "Failed to verify identity for Customer Support Agent")

                # Verify customer support access
                await self.iam_utils.verify_access_or_raise(
                    agent_id=self.aztp.aztp_id,
                    action="customer_support",
                    policy_code="policy:9e9834d8cbea",
                    operation_name="Customer Support Operations"
                )

                self.aztp.is_initialized = True
                self.is_initialized = True
                print("✅ Customer Support Agent initialized successfully")

            except Exception as e:
                print(f"❌ Error initializing Customer Support Agent: {str(e)}")
                raise

    def _generate_ticket_id(self) -> str:
        """
        Generate a unique support ticket ID

        Returns:
            A unique ticket ID string
        """
        # Generate a UUID and take the first 8 characters
        ticket_id = str(uuid.uuid4())[:8].upper()
        # Add a timestamp component for additional uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        return f"TICKET-{ticket_id}-{timestamp}"

    async def process_refund(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund request for an order

        Args:
            order_details: Dictionary containing order information including transaction ID and refund reason

        Returns:
            Refund confirmation with details
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify refund processing access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="process_refund",
                policy_code="policy:9e9834d8cbea",
                operation_name="Refund Processing"
            )

            # Generate a refund ID
            refund_id = f"REF-{str(uuid.uuid4())[:8].upper()}"
            refund_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract order details
            transaction_id = order_details.get("transaction_id", "Unknown")
            refund_reason = order_details.get("reason", "Not specified")
            refund_amount = order_details.get("amount", 0.0)

            # Create refund confirmation
            confirmation = {
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "refund_time": refund_time,
                "status": "Processed",
                "amount": refund_amount,
                "reason": refund_reason,
                "message": "Your refund has been successfully processed."
            }

            return confirmation

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to process refund: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def get_faq_response(self, query: str) -> Dict[str, Any]:
        """Get response for a FAQ query using LLM."""
        if not self.is_initialized:
            await self.initialize()

        try:
            # Input validation
            if not query or not isinstance(query, str):
                raise ValueError("Invalid query format")

            # Verify FAQ access
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="read_faq",
                policy_code="policy:9e9834d8cbea",
                operation_name="FAQ Access"
            )

            # Get answer from LLM
            llm_response = await self._get_llm_response(query)

            # Create response using Pydantic model
            response_data = {
                "query": query,
                "found": llm_response["found"],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": llm_response.get("category"),
                "question": llm_response.get("question"),
                "answer": llm_response.get("answer"),
                "confidence_score": llm_response.get("confidence_score"),
                "suggested_questions": llm_response.get("suggested_questions", []),
                "helpful_links": [],
                "related_topics": []
            }

            # Validate response using Pydantic model
            validated_response = FAQResponse(**response_data)
            logger.info("FAQ response generated successfully")
            return validated_response.model_dump()

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return self._create_error_response(f"Invalid input: {str(e)}")
        except PolicyVerificationError as e:
            logger.error(f"Policy verification failed: {str(e)}")
            return self._create_error_response("Access denied")
        except Exception as e:
            logger.error(f"Error processing FAQ response: {str(e)}")
            return self._create_error_response("An unexpected error occurred")

    async def create_support_ticket(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new support ticket for escalation

        Args:
            issue_details: Dictionary containing issue information

        Returns:
            Ticket details with tracking information
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify ticket creation access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="ticket_creation",
                policy_code="policy:9e9834d8cbea",
                operation_name="Ticket Creation"
            )

            ticket_id = self._generate_ticket_id()
            creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract issue details
            customer_id = issue_details.get("customer_id", "Unknown")
            issue_type = issue_details.get("issue_type", "General")
            priority = issue_details.get("priority", "Medium")
            description = issue_details.get(
                "description", "No description provided")

            # Create ticket
            ticket = {
                "ticket_id": ticket_id,
                "creation_time": creation_time,
                "status": "Open",
                "customer_id": customer_id,
                "issue_type": issue_type,
                "priority": priority,
                "description": description,
                "assigned_to": "Pending Assignment",
                "estimated_response_time": "24 hours",
                "message": "Your support ticket has been created and will be addressed by our team."
            }

            return ticket

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to create support ticket: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    def _load_faq_database(self) -> None:
        """Load the FAQ database from JSON file."""
        try:
            faq_path = Path(__file__).parent.parent / \
                "data" / "faq_database.json"
            if not faq_path.exists():
                raise FileNotFoundError(
                    f"FAQ database not found at {faq_path}")

            with open(faq_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Validate FAQ database structure
            required_keys = ["version", "categories", "metadata"]
            if not all(key in data for key in required_keys):
                raise ValueError(
                    "Invalid FAQ database structure: missing required keys")

            self.faq_data = data
            self.categories = data["categories"]
            self.metadata = data["metadata"]

            # Create a knowledge base for the LLM
            self.knowledge_base = self._create_knowledge_base()
            logger.info("FAQ database loaded successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing FAQ database: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading FAQ database: {str(e)}")
            raise

    def _create_knowledge_base(self) -> str:
        """Create a formatted knowledge base from FAQ data for the LLM."""
        knowledge_base = []
        for category_id, category in self.categories.items():
            knowledge_base.append(f"\nCategory: {category['title']}")
            for faq in category["faqs"]:
                knowledge_base.append(f"\nQ: {faq['question']}")
                knowledge_base.append(f"A: {faq['answer']}")
        return "\n".join(knowledge_base)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _get_llm_response(self, query: str) -> Dict[str, Any]:
        """Get response from LLM using the FAQ knowledge base."""
        try:
            system_prompt = f"""You are a helpful customer support agent for our shopping application.
Use the following FAQ knowledge base to answer questions:

{self.knowledge_base}

If the exact answer isn't in the FAQs, use the knowledge to provide a helpful response.
Always maintain a professional and helpful tone.
If you really can't help, suggest contacting human support.

Format your response as JSON with the following structure:
{{
    "found": boolean,
    "category": string or null,
    "question": string or null,
    "answer": string,
    "confidence_score": float between 0 and 1,
    "suggested_questions": list of related questions
}}"""

            user_prompt = f"Question: {query}"

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return self._create_error_response("Failed to parse response")

        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            raise

    def _create_error_response(self, error_message: str) -> Dict:
        """Create a standardized error response"""
        return {
            "found": False,
            "message": f"I apologize, but there was an error: {error_message}. Would you like to try rephrasing your question or speak with a customer support representative?",
            "suggested_questions": self._get_popular_questions(3)
        }

    def _get_popular_questions(self, limit: int) -> List[str]:
        """Get most popular/common questions when no matches are found"""
        try:
            popular_questions = []
            for category in self.categories.values():
                for faq in category["faqs"]:
                    if len(popular_questions) < limit:
                        popular_questions.append(faq["question"])
                    else:
                        break
            return popular_questions[:limit]
        except Exception as e:
            logger.warning(f"Error getting popular questions: {str(e)}")
            return []

    def _calculate_match_score(self, question: str, faq: Dict[str, Any]) -> MatchScore:
        """Calculate match score between question and FAQ entry"""
        try:
            # Normalize inputs
            user_question = question.lower().strip()
            faq_question = faq["question"].lower().strip()
            user_keywords = set(self._get_question_keywords(user_question))
            faq_keywords = set(k.lower() for k in faq["keywords"])

            # Calculate keyword match score
            keyword_score = float(len(user_keywords.intersection(
                faq_keywords))) / float(len(faq_keywords)) if faq_keywords else 0.0

            # Calculate question similarity
            try:
                close_matches = get_close_matches(
                    user_question,
                    [faq_question],
                    n=1,
                    cutoff=0.1
                )
                similarity_score = float(
                    close_matches[0][1]) if close_matches else 0.0
            except (IndexError, AttributeError):
                similarity_score = 0.0

            # Calculate combined score
            combined_score = float(max(keyword_score, similarity_score))

            # Determine match type
            if combined_score >= 0.9:
                match_type = MatchType.EXACT
            elif combined_score >= 0.7:
                match_type = MatchType.PARTIAL
            elif combined_score >= 0.5:
                match_type = MatchType.KEYWORD
            else:
                match_type = MatchType.NONE

            return MatchScore(
                keyword_score=keyword_score,
                similarity_score=similarity_score,
                combined_score=combined_score,
                match_type=match_type
            )

        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return MatchScore(0.0, 0.0, 0.0, MatchType.NONE)

    def _find_best_matches(self, question: str, threshold: float = 0.6) -> List[Dict]:
        """Find the best matching FAQs for the given question."""
        if not question or not isinstance(question, str):
            logger.warning("Invalid question input")
            return []

        matches = []
        try:
            for category_id, category in self.categories.items():
                for faq in category["faqs"]:
                    try:
                        match_score = self._calculate_match_score(
                            question, faq)

                        if match_score.combined_score >= float(threshold):
                            matches.append({
                                "faq": faq,
                                "category": category_id,
                                "score": match_score.combined_score,
                                "match_type": match_score.match_type.value
                            })

                    except Exception as e:
                        logger.warning(f"Error processing FAQ entry: {str(e)}")
                        continue

            # Sort matches by score
            return sorted(matches, key=lambda x: float(x["score"]), reverse=True)

        except Exception as e:
            logger.error(f"Error finding matches: {str(e)}")
            return []

    def get_answer(self, question: str) -> Dict:
        """Get the best answer for a given question."""
        if not question or not isinstance(question, str):
            return self._create_error_response("Invalid question format")

        try:
            matches = self._find_best_matches(question)

            if not matches:
                return self._create_no_match_response()

            best_match = matches[0]
            match_type = best_match.get("match_type", MatchType.NONE.value)

            # Get suggested questions based on match type
            suggested_questions = self._get_suggested_questions(
                matches[1:],
                max_suggestions=self.metadata.get("max_related_questions", 3)
            )

            return {
                "found": True,
                "category": self.categories[best_match["category"]]["title"],
                "question": best_match["faq"]["question"],
                "answer": best_match["faq"]["answer"],
                "confidence_score": float(best_match["score"]),
                "match_type": match_type,
                "suggested_questions": suggested_questions
            }

        except Exception as e:
            logger.error(f"Error getting answer: {str(e)}")
            return self._create_error_response(str(e))

    def _create_no_match_response(self) -> Dict:
        """Create a response for when no matches are found"""
        return {
            "found": False,
            "message": "I apologize, but I couldn't find a specific answer to your question. Would you like me to connect you with a human customer support representative?",
            "suggested_questions": self._get_popular_questions(3)
        }

    def _get_suggested_questions(self, matches: List[Dict], max_suggestions: int) -> List[str]:
        """Get suggested questions based on matches"""
        try:
            return [
                m["faq"]["question"]
                for m in matches[:max_suggestions]
                if float(m["score"]) > 0.5
            ]
        except Exception as e:
            logger.warning(f"Error getting suggested questions: {str(e)}")
            return []

    def _extract_keywords(self) -> List[str]:
        """Extract all keywords from the FAQ database."""
        keywords = []
        for category in self.categories.values():
            for faq in category["faqs"]:
                keywords.extend(faq["keywords"])
        return list(set(keywords))

    def _get_question_keywords(self, question: str) -> List[str]:
        """Extract relevant keywords from the user's question."""
        return [word.lower() for word in question.split()]

    def get_category_faqs(self, category: str) -> List[Dict]:
        """Get all FAQs for a specific category."""
        if category in self.categories:
            return self.categories[category]["faqs"]
        return []

    def get_all_categories(self) -> List[Dict[str, str]]:
        """Get a list of all available FAQ categories.

        Returns:
            List of dictionaries containing category ID and title
        """
        return [
            {
                "id": cat_id,
                "title": data["title"]
            }
            for cat_id, data in self.categories.items()
        ]
