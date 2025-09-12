# AI-Powered Meeting Minutes Automation Pipeline

## 📋 Overview

An automated pipeline that converts Microsoft Teams/Zoom meeting transcripts into structured meeting minutes using OpenAI GPT-4, with automatic publishing to Confluence and GitHub.

## ✨ Features

- **AI-Powered Extraction**: Uses OpenAI GPT-4 to intelligently extract meeting information
- **Automated Processing**: Runs daily at 8 AM IST (Monday-Friday)
- **Multi-Format Support**: Handles `.txt`, `.vtt`, and `.docx` transcript formats
- **Structured Output**: Generates JSON data and HTML formatted minutes
- **Confluence Integration**: Automatically publishes to Confluence space
- **Cost-Effective**: ~$0.10-0.30 per meeting
- **Version Control**: All minutes stored in GitHub with full history

## 🚀 Quick Start

### Prerequisites

- GitHub account
- OpenAI API key (with GPT-4 access)
- Confluence account (optional)
- Microsoft Teams or Zoom transcripts

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ranjeet848/meeting-minutes-ai.git
   cd meeting-minutes-ai
   ```

2. **Set up GitHub Secrets**
   
   Go to Settings → Secrets → Actions and add:
   
   | Secret Name | Description | Required |
   |------------|-------------|----------|
   | `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes |
   | `CONFLUENCE_URL` | Confluence URL (e.g., `https://company.atlassian.net/wiki`) | ⚪ No |
   | `CONFLUENCE_USERNAME` | Your Confluence email | ⚪ No |
   | `CONFLUENCE_API_TOKEN` | Confluence API token | ⚪ No |
   | `CONFLUENCE_SPACE_KEY` | Confluence space key | ⚪ No |

3. **Enable GitHub Actions permissions**
   - Go to Settings → Actions → General
   - Select "Read and write permissions"
   - Save changes

## 📁 Repository Structure

```
meeting-minutes-ai/
├── .github/
│   └── workflows/
│       └── ai-minutes.yml          # GitHub Actions workflow
├── scripts/
│   └── ai_minutes_generator.py     # Main AI processing script
├── transcripts/                    # Input folder for meeting transcripts
│   ├── test.txt                    # Sample transcript
│   └── standup_20250910.txt       # Real meeting transcript
├── minutes/                        # Output folder for generated minutes
│   ├── minutes_test_20250910.html
│   └── minutes_test_20250910.json
└── requirements.txt                # Python dependencies
```

## 🔄 How It Works

1. **Upload Transcript**: Add meeting transcript to `transcripts/` folder
2. **Trigger Processing**: 
   - Automatically on push
   - Daily at 8 AM IST
   - Manual trigger via Actions tab
3. **AI Analysis**: OpenAI GPT-4 extracts:
   - Attendees
   - Individual updates
   - Action items with assignees
   - Blockers/impediments
   - Decisions made
   - Meeting summary
4. **Generate Output**: Creates structured JSON and formatted HTML
5. **Publish**: 
   - Saves to `minutes/` folder in GitHub
   - Publishes to Confluence (if configured)

## 📝 Usage

### Manual Processing
```bash
# Add transcript
cp your-meeting.txt transcripts/meeting_$(date +%Y%m%d).txt
git add transcripts/
git commit -m "Add meeting transcript"
git push
```

### Trigger Workflow Manually
1. Go to Actions tab
2. Select "AI-Powered Meeting Minutes"
3. Click "Run workflow"
4. Enter transcript file path
5. Click "Run workflow"

### Automated Daily Processing
The workflow runs automatically at 8 AM IST Monday-Friday, processing the most recent transcript.

## 📊 Sample Output

The AI generates structured meeting minutes like:

```json
{
  "attendees": ["Ranjeet Prajapati", "Hieu Nguyen", "Varshith Meesala"],
  "individual_updates": [
    {
      "name": "Ranjeet Prajapati",
      "yesterday": "Set up AI meeting pipeline",
      "today": "Test with real transcript, switch to markdown",
      "blockers": "None"
    }
  ],
  "action_items": [
    {
      "action": "Create Helm charts for Kubernetes",
      "assignee": "Varshith Meesala",
      "due_date": "Today"
    }
  ],
  "decisions": [
    "Use markdown format instead of HTML",
    "Test on cloud infrastructure"
  ]
}
```

## 🔧 Configuration

### Customize AI Extraction

Edit `scripts/ai_minutes_generator.py` to customize extraction:

```python
# Add team-specific context
prompt = f"""
Analyze this engineering team standup.
Team members: {your_team_members}
Projects: {your_projects}
Extract updates, action items, and decisions.
"""
```

### Adjust Schedule

Edit `.github/workflows/ai-minutes.yml`:

```yaml
schedule:
  - cron: '30 2 * * 1-5'  # Modify for your timezone
```

## 🔌 Integrations

### Teams Transcript Upload Options

1. **Manual**: Upload transcripts to `transcripts/` folder
2. **Power Automate**: Automatic upload when meeting ends
3. **Email Integration**: Forward transcripts to process via email

### Confluence Setup

1. Generate API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Find your space key from Confluence URL
3. Add secrets to GitHub repository
4. Minutes automatically publish to Confluence

## 📈 Performance

- **Processing Time**: 30-60 seconds per meeting
- **Cost**: $0.10-0.30 per meeting (OpenAI API)
- **Accuracy**: Successfully extracts all key meeting components
- **Time Saved**: ~15-20 minutes per meeting

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No transcript found" | Ensure file exists in `transcripts/` folder |
| OpenAI API error | Check API key and credits |
| Confluence 404 | Verify space key and permissions |
| Permission denied (push) | Enable write permissions in Actions settings |

## 🛠️ Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python scripts/ai_minutes_generator.py transcripts/test.txt \
  --output-dir minutes \
  --openai-key YOUR_KEY
```

### Adding Features
- Webhook support for real-time processing
- Slack/Teams notifications
- Custom output formats
- Multi-language support

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For issues or questions:
- Open an issue in GitHub
- Check existing documentation
- Review workflow logs in Actions tab

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- GitHub Actions for automation
- Confluence for documentation platform
- Engineering team for testing and feedback

---

**Created by:** Ranjeet Prajapati  
**Date:** September 10, 2025  
**Status:** Production Ready 🚀
