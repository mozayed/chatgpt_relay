import anthropic
import os
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class NetworkAgent:
    def __init__(self):
        self.claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.processed_tickets = set()
        
    async def check_new_tickets(self, session):
        """Poll ServiceNow for new tickets assigned to Network_Agents group"""
        try:
            result = await session.call_tool(
                "list_incidents",
                {
                    "state": "1",
                    "limit": 10,
                    "assignment_group": os.getenv("SERVICENOW_ASSIGNMENT_GROUP_ID", "16eb774083b836101bf4ffd6feaad360")
                }
            )
            return result
        except Exception as e:
            print(f"Error fetching tickets: {e}", flush=True)
            return None
    
    async def analyze_ticket_with_claude(self, ticket):
        """Use Claude to analyze the ticket"""
        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this ServiceNow ticket:
                    
                    Number: {ticket.get('number', 'N/A')}
                    Short Description: {ticket.get('short_description', 'N/A')}
                    Description: {ticket.get('description', 'N/A')}
                    
                    What type of issue is this? Can it be automated? Provide a brief analysis."""
                }]
            )
            
            return message.content[0].text
        except Exception as e:
            print(f"Error analyzing ticket: {e}", flush=True)
            return None
    
    async def take_ticket_ownership(self, session, sys_id, work_notes):
        """Take ownership of ticket and update with AI analysis"""
        try:
            result = await session.call_tool(
                "update_incident",
                {
                    "incident_id": sys_id,
                    "state": "2",
                    "assigned_to": os.getenv("SERVICENOW_USERNAME", "ai_agent"),
                    "work_notes": work_notes
                }
            )
            return result
        except Exception as e:
            print(f"Error updating ticket: {e}", flush=True)
            return None
    
    async def process_ticket(self, session, ticket):
        """Process a single ticket - analyze and take ownership"""
        print(f"Processing: {ticket.get('number')} - {ticket.get('short_description')}", flush=True)
        
        # Analyze with Claude
        analysis = await self.analyze_ticket_with_claude(ticket)
        
        if analysis:
            sys_id = ticket.get('sys_id')
            if sys_id:
                work_notes = f"""AI Agent Analysis:
{analysis}

---
Status: Ticket taken by AI Agent
State changed: New → In Progress
Assigned to: ai_agent"""
                
                update_result = await self.take_ticket_ownership(session, sys_id, work_notes)
                
                if update_result:
                    print(f"✓ Took ownership of {ticket.get('number')}", flush=True)
                    self.processed_tickets.add(sys_id)
                    return True
                else:
                    print(f"✗ Failed to take ownership of {ticket.get('number')}", flush=True)
        
        return False
    
    async def autonomous_loop(self):
        """Main autonomous loop - monitors and processes tickets"""
        print("Starting Autonomous Agent Loop...", flush=True)
        print(f"Monitoring tickets for group: {os.getenv('SERVICENOW_ASSIGNMENT_GROUP_ID')}", flush=True)
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "servicenow_mcp.cli"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("ServiceNow MCP connected", flush=True)
                
                iteration = 0
                while True:
                    iteration += 1
                    print(f"\n[Agent Iteration {iteration}] Checking for new tickets...", flush=True)
                    
                    try:
                        result = await self.check_new_tickets(session)
                        
                        if result and result.content:
                            tickets_data = result.content[0].text
                            
                            try:
                                response_json = json.loads(tickets_data)
                                
                                if response_json.get('success') and 'incidents' in response_json:
                                    tickets = response_json['incidents']
                                    new_tickets = [t for t in tickets if t['sys_id'] not in self.processed_tickets]
                                    
                                    if new_tickets:
                                        print(f"Found {len(new_tickets)} NEW unprocessed ticket(s)", flush=True)
                                        
                                        for ticket in new_tickets:
                                            await self.process_ticket(session, ticket)
                                    else:
                                        if tickets:
                                            print(f"All {len(tickets)} tickets already processed", flush=True)
                                else:
                                    print("No new tickets", flush=True)
                                    
                            except json.JSONDecodeError as e:
                                print(f"JSON error: {e}", flush=True)
                        
                    except Exception as e:
                        print(f"Agent loop error: {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                    
                    await asyncio.sleep(60)  # Check every 60 seconds
    
    async def query_ticket(self, ticket_number):
        """Query a specific ticket - for on-demand voice queries"""
        print(f"Querying ticket: {ticket_number}", flush=True)
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "servicenow_mcp.cli"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                try:
                    result = await session.call_tool(
                        "get_incident_by_number",
                        {"incident_number": ticket_number}
                    )
                    
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        return data
                    
                except Exception as e:
                    print(f"Error querying ticket: {e}", flush=True)
                    return {"success": False, "message": str(e)}
