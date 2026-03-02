# OpenAI Integration Branch

This branch contains the OpenAI integration for Project2412, replacing the local Ollama LLM with OpenAI's API.

## Changes Made

### Configuration Updates
- **`backend/core/config.py`**: Replaced Ollama settings with OpenAI configuration
  - `OPENAI_API_KEY`: Your OpenAI API key
  - `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
  - `OPENAI_BASE_URL`: OpenAI API base URL

### New Services
- **`backend/services/openai_lesson_generator.py`**: New OpenAI-based lesson generator
  - Uses OpenAI Chat Completions API
  - Maintains the same state-wise generation approach
  - Compatible with existing lesson structure

### Updated Services
- **`backend/services/job_service.py`**: Updated to use OpenAI lesson generator
- **`backend/requirements.txt`**: Added `openai==1.3.7` dependency

### Environment Configuration
- **`backend/.env`**: Updated with OpenAI configuration
  - Set your OpenAI API key: `OPENAI_API_KEY=your_actual_api_key_here`
  - Local LLM disabled: `USE_LOCAL_LLM=false`

## Setup Instructions

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure OpenAI API key**:
   Edit `backend/.env` and replace `your-openai-api-key-here` with your actual OpenAI API key.

3. **Run the application**:
   ```bash
   cd backend
   python main.py
   ```

## Security Notes

- The `.env` file is already in `.gitignore` to protect your API key
- Never commit your actual OpenAI API key to version control
- Use environment variables in production

## Usage

The application now uses OpenAI for lesson generation instead of local Ollama. All existing functionality remains the same, but lesson generation will be faster and more reliable using OpenAI's infrastructure.

## Switching Back to Ollama

If you want to switch back to the local Ollama setup:
1. Checkout the main branch: `git checkout main`
2. Ensure Ollama is running locally
3. Update your `.env` file accordingly

## API Key Requirements

You need an OpenAI API key with access to the Chat Completions API. Get one from: https://platform.openai.com/api-keys
