# MCP Demo App (Python)

This repository contains a comprehensive demonstration solution for **Model Context Protocol (MCP)** showcasing all three core MCP capabilities: **Tools**, **Prompts**, and **Resources**. Built with Python and designed for Azure deployment.

> Workshop: Step-by-step labs for deploying APIs, MCP servers, and the chat client (Option 1) are in `docs/index.md`. When published with GitHub Pages, the workshop is available at `https://prwani.github.io/mcp_demo_app_python/`.

## 🎯 MCP Capabilities Demonstrated

### ⚡ Tools (Actions)
- **Leave Management**: Apply for leave, check balances
- **Timesheet Management**: Log hours, list entries
- Interactive tool discovery and execution

### 🎯 Prompts (Templates)
- **Leave Prompts**: Email templates, policy summaries, calendar planning
- **Timesheet Prompts**: Submission reminders, project summaries, overtime analysis
- Dynamic prompt generation with user arguments

### 📚 Resources (Data/Content)
- **Leave Resources**: Policies, forms, holiday calendars, team status
- **Timesheet Resources**: Submission guidelines, project codes, templates, utilization reports
- Rich content delivery in multiple formats (text, JSON)

## 🏗️ Architecture

### 1. Leave Application
- **REST API**: FastAPI with SQLAlchemy ORM
- **Database**: Azure SQL DB (serverless) with leave balances and requests
- **MCP Server**: Full MCP implementation with tools, prompts, and resources
- **Web UI**: Interactive leave management interface

### 2. Timesheet Application  
- **REST API**: FastAPI with timesheet entry management
- **Database**: Azure SQL DB (serverless) with employee time tracking
- **MCP Server**: Complete MCP server with timesheet-specific capabilities
- **Web UI**: Simple timesheet logging interface

### 3. Chat Client (MCP Client)
- **Smart Chat**: Azure OpenAI integration with intent detection
- **MCP Discovery**: Automatic discovery of server capabilities
- **Multi-Protocol**: Supports tools, prompts, and resources from both servers
- **Web UI**: Enhanced interface showcasing all MCP features

## 📁 Project Structure
```
leave_app/
  api/         # FastAPI REST API for leave management
  mcp_server/  # Complete MCP server (tools, prompts, resources)
  web/         # Interactive web UI for leave operations
  sql/         # Database schema and seed data
timesheet_app/
  api/         # FastAPI REST API for timesheet management  
  mcp_server/  # Full MCP server implementation
  web/         # Timesheet logging web interface
  sql/         # Database schema and seed data
chat_client/
  api/         # Enhanced chat client with MCP discovery
  web/         # Rich web UI showcasing all MCP capabilities
requirements.txt # Python dependencies
.dockerignore    # Docker build optimization
*/Dockerfile.*  # Containerization for each service
```

## 🚀 Quick Start

### Local Development
```bash
# 1. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 2. Run services locally (separate terminals)
uvicorn leave_app.api.main:app --port 8001 --reload
uvicorn leave_app.mcp_server.server:app --port 8011 --reload
uvicorn timesheet_app.api.main:app --port 8002 --reload  
uvicorn timesheet_app.mcp_server.server:app --port 8012 --reload
uvicorn chat_client.api.main:app --port 8000 --reload

# 3. Open http://localhost:8000 for the enhanced chat interface
```

### Try MCP Features
- **Tools**: "Apply leave 2025-08-20 to 2025-08-22" or "Log 8 hours on 2025-08-20"
- **Prompts**: "Generate leave request email" or "Create timesheet reminder" 
- **Resources**: "Show leave policy" or "Get project codes list"
- **Discovery**: Click "Discover MCP Capabilities" to see all available features

## 🔧 MCP Endpoints

### Tools (Actions)
- `POST /mcp/tools/apply_leave` - Submit leave requests
- `GET /mcp/tools/get_balance` - Check leave balances
- `POST /mcp/tools/add_timesheet_entry` - Log work hours
- `GET /mcp/tools/list_timesheet_entries` - Retrieve timesheet data

### Prompts (Templates)  
- `GET /mcp/prompts/list` - Discover available prompts
- `POST /mcp/prompts/get` - Generate customized content
- Examples: leave_request_email, timesheet_reminder, policy_summary

### Resources (Content)
- `GET /mcp/resources/list` - Browse available resources
- `POST /mcp/resources/read` - Access specific content
- Examples: leave policies, project codes, best practices, reports

## 🌐 Azure Deployment
- **Containers**: Docker images built with Azure Container Registry
- **Hosting**: Azure Web Apps for Containers with Linux
- **Databases**: Azure SQL DB (serverless) with automatic scaling
- **AI**: Azure OpenAI for intelligent chat interactions
- **Security**: Managed Identity with role-based access control

## 🎛️ Configuration
Set these environment variables for full functionality:
```bash
# Database connections
LEAVE_DATABASE_URL="azure-sql-connection-string"
TIMESHEET_DATABASE_URL="azure-sql-connection-string"

# MCP server URLs  
LEAVE_MCP_URL="https://leave-mcp.azurewebsites.net"
TIMESHEET_MCP_URL="https://timesheet-mcp.azurewebsites.net"

# Azure OpenAI (optional for enhanced chat)
AZURE_OPENAI_ENDPOINT="https://your-aoai.openai.azure.com/"
AZURE_OPENAI_KEY="your-api-key"
AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
```

## 💡 What Makes This Special
- **Complete MCP Implementation**: First demo showcasing tools, prompts, AND resources
- **Real-World Use Cases**: Practical workplace scenarios with actual business logic
- **Intelligent Chat**: Azure OpenAI integration with intent detection and fallback heuristics
- **Auto-Discovery**: Dynamic MCP capability discovery and presentation
- **Production Ready**: Containerized with Azure deployment, security, and monitoring

## License
MIT

For detailed Azure deployment steps, see [Azure_setup.md](./Azure_setup.md).

## 📘 Workshop
- The full MCP Workshop (Labs 1–4, concepts-first then commands) is available at `docs/index.md` and on GitHub Pages when enabled.
  - Quick link in this repo: [docs/index.md](./docs/index.md)
  - GitHub Pages URL (after enabling Pages for /docs): https://<your-username>.github.io/<repo-name>/
