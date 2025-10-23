import os, json, re, asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class ServiceNow:

    processed_tickets = set()

    def __init__(self):
        self.aassignment_group = os.getenv("SERVICENOW_ASSIGNMENT_GROUP_ID", "16eb774083b836101bf4ffd6feaad360")
        self.preferred_llm = None

    def set_prederred_llm(self, llm):
        self.preferred_llm = llm

    async def check_new_tickets(self, session):
        """Poll ServiceNow for new tickets assigned to Network_Agents group"""
        try:
            result = await session.call_tool(
                "list_incidents",
                {
                    "state": "1",
                    "limit": 10,
                    "assignment_group": self.aassignment_group
                }
            )
            return result
        except Exception as e:
            print(f"Error fetching tickets: {e}", flush=True)
            return None
    
    async def analyze_ticket(self, ticket):
        """Analyze ticket - Using default llm or overrided"""
        try:
            # llm chosen for the task

            result = await self.preferred_llm.analyze(f'Analyze: {ticket}')
            return result
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
                    "assigned_to": os.getenv("SERVICENOW_USERNAME", "ai_user"),
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
        
        # Analyze the ticket
        analysis = await self.analyze_ticket(ticket)
        
        if analysis:
            sys_id = ticket.get('sys_id')
            if sys_id:
                work_notes = f"""AI Agent Analysis: {analysis}

                ---
                Status: Ticket taken by AI Agent
                State changed: New → In Progress
                Assigned to: ai_user"""
                
                update_result = await self.take_ticket_ownership(session, sys_id, work_notes)
                
                if update_result:
                    print(f"✓ Took ownership of {ticket.get('number')}", flush=True)
                    ServiceNow.processed_tickets.add(sys_id)
                    return True
                else:
                    print(f"✗ Failed to take ownership of {ticket.get('number')}", flush=True)
        
        return False
    
    async def query_ticket_by_number(self, ticket_number):
        """Query a specific ticket by number - for voice queries"""
        print(f"Querying ticket: {ticket_number}", flush=True)
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "servicenow_mcp.cli"],
            env=dict(os.environ)
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
                        
                        if data.get('success'):
                            ticket = data.get('incident', {})
                            return {
                                "success": True,
                                "ticket": ticket
                            }
                        else:
                            return {
                                "success": False,
                                "message": data.get('message', 'Ticket not found')
                            }
                    
                except Exception as e:
                    print(f"Error querying ticket: {e}", flush=True)
                    return {"success": False, "message": str(e)}
        
        return {"success": False, "message": "No response"}
    
    async def ask_llm_with_context(self, question):

        """Ask LLM a question with ServiceNow context"""
        print(f"LLM query: {question}", flush=True)
        
        # Extract ticket number if mentioned
        ticket_match = re.search(r'INC\d+', question, re.IGNORECASE)
        
        context = question

        if ticket_match:
            ticket_number = ticket_match.group(0).upper()
            ticket_data = await self.query_ticket_by_number(ticket_number)
            
            if ticket_data.get('success'):
                ticket = ticket_data.get('ticket', {})
                context = f"""
                    Ticket Information:
                    - Number: {ticket.get('number')}
                    - Short Description: {ticket.get('short_description')}
                    - Description: {ticket.get('description')}
                    - State: {ticket.get('state')}
                    - Priority: {ticket.get('priority')}
                    - Assigned To: {ticket.get('assigned_to')}
                    - Created: {ticket.get('created_on')}
                    - Updated: {ticket.get('updated_on')}
                    - Work Notes: {ticket.get('work_notes', 'No work notes')}
                    - Comments: {ticket.get('comments', 'No comments')}
                    - User Question {question}
                    provide helpful answer based on the ticket information above
                    """
        
        try:
            
            reuslt = await self.preferred_llm.ask(context)
            return reuslt

        except Exception as e:
            print(f"Error asking LLM: {e}", flush=True)
            return f"Sorry, I encountered an error: {str(e)}"
        
    async def start_servicenow_job(self, llm):
        
        self.set_prederred_llm(llm)

        """Main autonomous loop - monitors and processes tickets"""
        print("Starting Autonomous Agent Loop...", flush=True)
        print(f"Monitoring tickets for group: {os.getenv('SERVICENOW_ASSIGNMENT_GROUP_ID')}", flush=True)
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "servicenow_mcp.cli"],
            env=dict(os.environ)
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