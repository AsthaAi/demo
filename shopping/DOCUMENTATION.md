# ShopperAI Documentation

## Project Overview

ShopperAI is an intelligent shopping assistant that helps users find and analyze products based on their criteria. The system uses AI agents to perform product research, analysis, and recommendations.

## Architecture

### Core Components

1. **ResearchAgent**

   - Main agent responsible for product search and analysis
   - Inherits from CrewAI's Agent class
   - Uses specialized tools for product search and analysis
   - Located in `agents/research_agent.py`

2. **Search Tools**

   - `ProductSearchTool`: Interfaces with Google Serper API for product search
   - `ProductAnalyzerTool`: Analyzes and filters products based on criteria
   - Located in `tools/search_tools.py`

3. **Task Management**
   - Uses CrewAI's Task system for orchestrating agent actions
   - Tasks are defined in `agents/tasks.py` for search and analysis operations

### File Structure

```
shopping/
├── agents/
│   ├── research_agent.py    # Research agent implementation
│   ├── tasks.py            # Task definitions
│   └── tasks/              # Additional task implementations
├── tools/
│   └── search_tools.py     # Search and analysis tools
├── main.py                 # Main orchestration and CLI
├── requirements.txt        # Project dependencies
└── .env                    # Environment variables
```

## Implementation Details

### ResearchAgent

The ResearchAgent class is the core component that handles product search and analysis:

```python
class ResearchAgent(Agent):
    def __init__(self):
        super().__init__(
            role='Research Agent',
            goal='Find and analyze products based on user criteria',
            backstory="""You are an expert product researcher...""",
            verbose=True
        )
        self._search_tool = ProductSearchTool()
        self._analyzer_tool = ProductAnalyzerTool()
```

Key methods:

- `search_and_analyze(query, criteria)`: Searches and analyzes products
- `get_best_match(query, criteria)`: Returns the best matching product
- `analyze_products(products, criteria)`: Performs detailed product analysis
- `get_product_details(product)`: Extracts formatted product details

### Search Tools

#### ProductSearchTool

```python
class ProductSearchTool:
    def run(self, query: str) -> List[Dict[str, Any]]:
        # Searches products using Google Serper API
        # Returns list of product dictionaries
```

#### ProductAnalyzerTool

```python
class ProductAnalyzerTool:
    def run(self, products: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Analyzes products based on criteria
        # Returns filtered and analyzed products
```

### Task System

Tasks are defined in `agents/tasks.py`:

```python
class ResearchTasks:
    def create_search_task(self, agent, query, criteria):
        return Task(
            description=f"Search for products matching: {query}",
            agent=agent,
            expected_output="A list of products matching the search criteria"
        )
```

## Setup and Configuration

### Environment Variables

Create a `.env` file with:

```
SERPAPI_API_KEY=your_api_key_here
```

### Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Current dependencies:

- crewai>=0.11.0
- python-dotenv>=0.19.0
- requests>=2.26.0
- google-search-results>=2.4.2
- langchain>=0.1.0
- aztp>=0.1.0
- termcolor>=1.1.0

## Usage

### Running the Application

```bash
python main.py
```

The application will:

1. Prompt for search query
2. Ask for maximum budget
3. Request minimum rating requirement
4. Search for products
5. Analyze results
6. Display recommendations

### Example Interaction

```
## Welcome to ShopperAI
------------------------

What would you like to search for?
laptop

What is your maximum budget?
800

What is your minimum required rating (0-5)?
4.0
```

## Future Enhancements

1. Add more specialized agents for:
   - Price comparison
   - Review analysis
   - Deal hunting
2. Implement product tracking
3. Add support for multiple retailers
4. Enhance product recommendations with ML

## Troubleshooting

### Common Issues

1. **API Key Issues**

   - Ensure SERPAPI_API_KEY is set in .env
   - Verify API key is valid and has sufficient credits

2. **Search Results**
   - No results found: Try broadening search criteria
   - Too many results: Add more specific criteria

### Error Messages

- "Unable to generate pydantic-core schema": Check agent implementation
- "API request failed": Verify API key and internet connection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
