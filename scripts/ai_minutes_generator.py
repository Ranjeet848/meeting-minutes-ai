#!/usr/bin/env python3
"""
AI-Powered Meeting Minutes Generator with Confluence Integration
Uses OpenAI to intelligently extract and format meeting minutes from Teams transcripts
"""

import re
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import openai
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ConfluenceConfig:
    """Confluence configuration"""
    base_url: str
    username: str
    api_token: str
    space_key: str
    parent_page_id: Optional[str] = None


class ConfluencePublisher:
    """Handles publishing content to Confluence"""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        self.auth = (config.username, config.api_token)
        self.base_url = config.base_url.rstrip('/')
        
    def create_page(self, title: str, content: str, parent_id: Optional[str] = None) -> Dict:
        """Create a new Confluence page"""
        url = f"{self.base_url}/rest/api/content"
        
        # Convert to Confluence storage format
        confluence_content = self.format_for_confluence(content)
        
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": self.config.space_key},
            "body": {
                "storage": {
                    "value": confluence_content,
                    "representation": "storage"
                }
            },
            "metadata": {
                "labels": [
                    {"name": "meeting-minutes"},
                    {"name": "standup"},
                    {"name": "ai-generated"}
                ]
            }
        }
        
        if parent_id or self.config.parent_page_id:
            payload["ancestors"] = [{"id": parent_id or self.config.parent_page_id}]
        
        response = requests.post(url, json=payload, auth=self.auth)
        
        if response.status_code == 200:
            page_data = response.json()
            logger.info(f"Successfully created Confluence page: {page_data['_links']['webui']}")
            return page_data
        else:
            logger.error(f"Failed to create Confluence page: {response.status_code} - {response.text}")
            raise Exception(f"Confluence API error: {response.status_code}")
    
    def update_page(self, page_id: str, title: str, content: str, version: int) -> Dict:
        """Update an existing Confluence page"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        
        confluence_content = self.format_for_confluence(content)
        
        payload = {
            "version": {"number": version + 1},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": confluence_content,
                    "representation": "storage"
                }
            }
        }
        
        response = requests.put(url, json=payload, auth=self.auth)
        
        if response.status_code == 200:
            page_data = response.json()
            logger.info(f"Successfully updated Confluence page: {page_data['_links']['webui']}")
            return page_data
        else:
            logger.error(f"Failed to update Confluence page: {response.status_code} - {response.text}")
            raise Exception(f"Confluence API error: {response.status_code}")
    
    def find_page_by_title(self, title: str) -> Optional[Dict]:
        """Find a Confluence page by title"""
        url = f"{self.base_url}/rest/api/content"
        params = {
            "spaceKey": self.config.space_key,
            "title": title,
            "expand": "version"
        }
        
        response = requests.get(url, params=params, auth=self.auth)
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return data["results"][0]
        return None
    
    def format_for_confluence(self, html_content: str) -> str:
        """Format HTML content for Confluence storage format"""
        # Wrap in Confluence macro for better formatting
        confluence_content = f"""
        <ac:structured-macro ac:name="info" ac:schema-version="1">
            <ac:parameter ac:name="title">AI-Generated Meeting Minutes</ac:parameter>
            <ac:rich-text-body>
                <p>This page was automatically generated from a Teams meeting transcript using AI.</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        {html_content}
        """
        return confluence_content


class AIMinutesGenerator:
    """Generate meeting minutes using OpenAI"""
    
    def __init__(self, openai_api_key: str, confluence_config: Optional[ConfluenceConfig] = None):
        openai.api_key = openai_api_key
        self.confluence = ConfluencePublisher(confluence_config) if confluence_config else None
        
    def process_transcript_with_ai(self, transcript: str, meeting_date: str = None) -> Dict:
        """Process transcript using OpenAI to extract structured meeting minutes"""
        
        if not meeting_date:
            meeting_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create the prompt for OpenAI
        prompt = f"""
        Analyze this meeting transcript and create structured meeting minutes. 
        Extract the following information and format it as JSON:
        
        Analyze this engineering team standup transcript.
        Focus on:
        - Technical tasks and implementations
        - Blockers and dependencies
        - Testing and deployment status
        - Infrastructure decisions
        Team members: Ranjeet, Hieu, Varshith, Swati
        Projects: AI meeting pipeline, 5-FU clearance model, Kubernetes deployment
        Extract updates, action items, and technical decisions.
        
        Transcript: {transcript}
        
        Return ONLY valid JSON, no additional text.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing meeting transcripts and creating clear, concise meeting minutes. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the AI response
            ai_response = response.choices[0].message.content
            meeting_data = json.loads(ai_response)
            
            logger.info("Successfully processed transcript with AI")
            return meeting_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Fallback: Try to extract with a simpler prompt
            return self.simple_ai_extraction(transcript)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def simple_ai_extraction(self, transcript: str) -> Dict:
        """Simpler extraction if the complex one fails"""
        prompt = f"""
        Create a simple meeting summary from this transcript:
        {transcript[:3000]}  # Limit context for simpler processing
        
        Format as JSON with: attendees (list), summary (string), action_items (list), blockers (list)
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract meeting information and return as JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            # Ultimate fallback
            return {
                "attendees": ["Unable to extract attendees"],
                "summary": "Meeting transcript processed but extraction failed.",
                "action_items": [],
                "blockers": []
            }
    
    def format_minutes_as_html(self, meeting_data: Dict, meeting_date: str) -> str:
        """Format the extracted data as HTML for Confluence"""
        
        html = f"""
        <h1>Stand-up Meeting Minutes - {meeting_date}</h1>
        
        <table>
            <tr>
                <th>Date</th>
                <td>{meeting_date}</td>
            </tr>
            <tr>
                <th>Type</th>
                <td>Daily Stand-up</td>
            </tr>
            <tr>
                <th>Attendees</th>
                <td>{', '.join(meeting_data.get('attendees', ['No attendees extracted']))}</td>
            </tr>
        </table>
        
        <h2>Executive Summary</h2>
        <p>{meeting_data.get('summary', 'No summary available.')}</p>
        
        <h2>Individual Updates</h2>
        """
        
        # Add individual updates
        for update in meeting_data.get('individual_updates', []):
            html += f"""
            <h3>{update.get('name', 'Unknown')}</h3>
            <ul>
                <li><strong>Yesterday:</strong> {update.get('yesterday', 'Not mentioned')}</li>
                <li><strong>Today:</strong> {update.get('today', 'Not mentioned')}</li>
                <li><strong>Blockers:</strong> {update.get('blockers', 'None')}</li>
            </ul>
            """
        
        # Add blockers section
        blockers = meeting_data.get('blockers', [])
        if blockers:
            html += "<h2>Blockers/Impediments</h2><ul>"
            for blocker in blockers:
                html += f"<li>{blocker}</li>"
            html += "</ul>"
        
        # Add action items table
        action_items = meeting_data.get('action_items', [])
        if action_items:
            html += """
            <h2>Action Items</h2>
            <table>
                <tr>
                    <th>Action</th>
                    <th>Assignee</th>
                    <th>Due Date</th>
                    <th>Priority</th>
                </tr>
            """
            for item in action_items:
                html += f"""
                <tr>
                    <td>{item.get('action', '')}</td>
                    <td>{item.get('assignee', 'TBD')}</td>
                    <td>{item.get('due_date', 'TBD')}</td>
                    <td>{item.get('priority', 'Medium')}</td>
                </tr>
                """
            html += "</table>"
        
        # Add decisions section
        decisions = meeting_data.get('decisions', [])
        if decisions:
            html += "<h2>Decisions Made</h2><ul>"
            for decision in decisions:
                html += f"<li>{decision}</li>"
            html += "</ul>"
        
        # Add key discussions
        discussions = meeting_data.get('key_discussions', [])
        if discussions:
            html += "<h2>Key Discussion Points</h2><ul>"
            for discussion in discussions:
                html += f"<li>{discussion}</li>"
            html += "</ul>"
        
        # Add metadata
        html += f"""
        <hr/>
        <h2>Meeting Metrics</h2>
        <ul>
            <li><strong>Total Attendees:</strong> {len(meeting_data.get('attendees', []))}</li>
            <li><strong>Action Items:</strong> {len(action_items)}</li>
            <li><strong>Blockers:</strong> {len(blockers)}</li>
            <li><strong>Decisions:</strong> {len(decisions)}</li>
        </ul>
        
        <hr/>
        <p><em>Minutes generated automatically on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using AI</em></p>
        """
        
        return html
    
    def generate_improvement_suggestions(self, meeting_data: Dict) -> str:
        """Use AI to suggest meeting improvements"""
        
        prompt = f"""
        Based on these meeting minutes, suggest 2-3 specific improvements for future meetings:
        - Number of action items: {len(meeting_data.get('action_items', []))}
        - Number of blockers: {len(meeting_data.get('blockers', []))}
        - Attendees: {len(meeting_data.get('attendees', []))}
        
        Provide brief, actionable suggestions.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a meeting efficiency expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content
        except:
            return ""
    
    def process_and_publish(self, transcript: str, meeting_date: str = None) -> Dict:
        """Process transcript with AI and publish to Confluence"""
        
        if not meeting_date:
            meeting_date = datetime.now().strftime('%Y-%m-%d')
        
        # Process with AI
        logger.info("Processing transcript with AI...")
        meeting_data = self.process_transcript_with_ai(transcript, meeting_date)
        
        # Format as HTML
        html_content = self.format_minutes_as_html(meeting_data, meeting_date)
        
        # Add improvement suggestions
        suggestions = self.generate_improvement_suggestions(meeting_data)
        if suggestions:
            html_content += f"""
            <h2>AI Suggestions for Improvement</h2>
            <ac:structured-macro ac:name="note" ac:schema-version="1">
                <ac:rich-text-body>
                    <p>{suggestions}</p>
                </ac:rich-text-body>
            </ac:structured-macro>
            """
        
        # Publish to Confluence if configured
        if self.confluence:
            title = f"Stand-up Minutes - {meeting_date}"
            
            # Check if page exists
            existing_page = self.confluence.find_page_by_title(title)
            
            if existing_page:
                page_data = self.confluence.update_page(
                    existing_page['id'],
                    title,
                    html_content,
                    existing_page['version']['number']
                )
            else:
                page_data = self.confluence.create_page(title, html_content)
            
            return {
                'meeting_data': meeting_data,
                'html_content': html_content,
                'confluence_url': f"{self.confluence.base_url}{page_data['_links']['webui']}",
                'page_id': page_data['id']
            }
        
        return {
            'meeting_data': meeting_data,
            'html_content': html_content
        }
    
    def process_file(self, input_file: Path, output_dir: Path = None) -> Dict:
        """Process a transcript file"""
        
        # Read input file
        if input_file.suffix.lower() == '.docx':
            try:
                import docx
                doc = docx.Document(input_file)
                text = '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error("python-docx not installed. Install with: pip install python-docx")
                raise
        else:
            # Assume text file
            text = input_file.read_text(encoding='utf-8')
        
        # Process and publish
        result = self.process_and_publish(text)
        
        # Save local copy if output_dir specified
        if output_dir:
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
            
            # Save as HTML
            output_file = output_dir / f"minutes_{input_file.stem}_{datetime.now().strftime('%Y%m%d')}.html"
            output_file.write_text(result['html_content'], encoding='utf-8')
            logger.info(f"Local copy saved: {output_file}")
            
            # Save JSON data
            json_file = output_dir / f"minutes_{input_file.stem}_{datetime.now().strftime('%Y%m%d')}.json"
            json_file.write_text(json.dumps(result['meeting_data'], indent=2), encoding='utf-8')
            
            result['local_file'] = str(output_file)
            result['json_file'] = str(json_file)
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Generate meeting minutes using AI and publish to Confluence')
    parser.add_argument('input', type=str, help='Input transcript file (.txt or .docx)')
    parser.add_argument('--output-dir', type=str, help='Output directory for local copy')
    parser.add_argument('--date', type=str, help='Meeting date (YYYY-MM-DD format)')
    
    # OpenAI configuration
    parser.add_argument('--openai-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    # Confluence arguments
    parser.add_argument('--confluence-url', type=str, help='Confluence base URL')
    parser.add_argument('--confluence-username', type=str, help='Confluence username/email')
    parser.add_argument('--confluence-token', type=str, help='Confluence API token')
    parser.add_argument('--confluence-space', type=str, help='Confluence space key')
    parser.add_argument('--confluence-parent-id', type=str, help='Parent page ID (optional)')
    
    args = parser.parse_args()
    
    # Get OpenAI key from args or environment
    openai_api_key = args.openai_key or os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OpenAI API key is required. Set via --openai-key or OPENAI_API_KEY environment variable")
        return 1
    
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    # Setup Confluence if credentials provided
    confluence_config = None
    if all([args.confluence_url, args.confluence_username, args.confluence_token, args.confluence_space]):
        confluence_config = ConfluenceConfig(
            base_url=args.confluence_url,
            username=args.confluence_username,
            api_token=args.confluence_token,
            space_key=args.confluence_space,
            parent_page_id=args.confluence_parent_id
        )
        logger.info("Confluence configuration detected - will publish to Confluence")
    else:
        logger.info("No Confluence configuration - will generate local files only")
    
    # Initialize generator
    generator = AIMinutesGenerator(openai_api_key, confluence_config)
    
    try:
        logger.info(f"Processing transcript: {input_file}")
        result = generator.process_file(input_file, output_dir)
        
        print("\n" + "="*50)
        print("✅ SUCCESS! Meeting minutes generated using AI")
        print("="*50)
        
        if 'local_file' in result:
            print(f"📄 HTML Minutes: {result['local_file']}")
            print(f"📊 JSON Data: {result['json_file']}")
        
        if 'confluence_url' in result:
            print(f"🌐 Confluence Page: {result['confluence_url']}")
        
        # Print summary
        meeting_data = result['meeting_data']
        print(f"\n📋 Meeting Summary:")
        print(f"   • Attendees: {len(meeting_data.get('attendees', []))}")
        print(f"   • Action Items: {len(meeting_data.get('action_items', []))}")
        print(f"   • Blockers: {len(meeting_data.get('blockers', []))}")
        print(f"   • Decisions: {len(meeting_data.get('decisions', []))}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing transcript: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
