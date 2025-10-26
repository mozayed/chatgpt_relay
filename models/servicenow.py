import os, json, re, asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from models.llm_factory import AbstractLLMServiceFactory

class ServiceNow:

    processed_tickets = set()

    def __init__(self):
        self.assignment_group = os.getenv("SERVICENOW_ASSIGNMENT_GROUP_ID", "16eb774083b836101bf4ffd6feaad360")
        self.preferred_llm = None  # Stores LLM TYPE (string like "Claude"), not instance

    def set_preferred_llm(self, llm_type):
        """Set preferred LLM type"""
        self.preferred_llm = llm_type
        print(f"ServiceNow preferred LLM set to: {llm_type}", flush=True)

    async def create_ticket(self, short_description, description, priority="3"):
        """Create a new ServiceNow ticket"""
        print(f"Creating ticket: {short_description}", flush=True)
        
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
                        "create_incident",
                        {
                            "short_description": short_description,
                            "description": description,
                            "priority": priority,
                            "assignment_group": self.assignment_group
                        }
                    )
                    
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        print(f"Create ticket response: {data}", flush=True)
                        
                        if data.get('success'):
                            ticket_number = data.get('incident_number')
                            sys_id = data.get('incident_id')
                            print(f"✓ Created ticket: {ticket_number}", flush=True)

                            return {
                                "success": True,
                                "ticket_number": ticket_number,
                                "sys_id": sys_id,
                                "message": f"Ticket {ticket_number} created successfully"
                            }
                        else:
                            return {"success": False, "message": data.get('message')}
                    
                except Exception as e:
                    print(f"Error creating ticket: {e}", flush=True)
                    return {"success": False, "message": str(e)}
        
        return {"success": False, "message": "No response"}

    async def update_ticket(self, ticket_number, work_notes=None, state=None):
        """Update an existing ServiceNow ticket"""
        print(f"Updating ticket: {ticket_number}", flush=True)
        
        # First get the ticket to find sys_id
        ticket_query_result = await self.get_ticket_data(ticket_number)
        
        if not ticket_query_result.get('success'):
            print(f"✗ Failed to find ticket {ticket_number}", flush=True)
            return {"success": False, "message": "Ticket not found"}
        
        ticket = ticket_query_result.get('ticket', {})
        sys_id = ticket.get('sys_id')
        
        if not sys_id:
            print(f"✗ No sys_id found for {ticket_number}", flush=True)
            return {"success": False, "message": "Could not get ticket sys_id"}
        
        print(f"Found sys_id: {sys_id}", flush=True)
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "servicenow_mcp.cli"],
            env=dict(os.environ)
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                try:
                    update_data = {"incident_id": sys_id}
                    if work_notes:
                        update_data["work_notes"] = work_notes
                    if state:
                        update_data["state"] = state
                    
                    print(f"Calling update_incident with: {update_data}", flush=True)
                    
                    result = await session.call_tool("update_incident", update_data)
                    
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        print(f"Update result: {data}", flush=True)
                        
                        if data.get('success'):
                            print(f"✓ Updated ticket {ticket_number}", flush=True)
                            return {
                                "success": True,
                                "message": f"Ticket {ticket_number} updated successfully"
                            }
                        else:
                            print(f"✗ Update failed: {data.get('message')}", flush=True)
                            return {"success": False, "message": data.get('message')}
                    
                except Exception as e:
                    print(f"✗ Error updating ticket: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    return {"success": False, "message": str(e)}
        
        return {"success": False, "message": "No response"}

    async def close_ticket(self, ticket_number, resolution_notes, close_code="Solved"):
        """Close a ServiceNow ticket - two-step process"""
        print(f"Closing ticket: {ticket_number}", flush=True)
        
        # Step 1: Move to Resolved (state 6) with resolution notes
        print(f"Step 1: Resolving ticket...", flush=True)
        resolve_result = await self.update_ticket(
            ticket_number=ticket_number,
            work_notes=f"Resolution: {resolution_notes}\nClose Code: {close_code}",
            state="6"  # Resolved first
        )
        
        if not resolve_result.get('success'):
            return resolve_result
        
        # Step 2: Move to Closed (state 7)
        print(f"Step 2: Closing ticket...", flush=True)
        close_result = await self.update_ticket(
            ticket_number=ticket_number,
            state="7"  # Now close it
        )
        
        return close_result

    async def check_new_tickets(self, session):
        """Poll ServiceNow for new tickets assigned to Network_Agents group"""
        try:
            result = await session.call_tool(
                "list_incidents",
                {
                    "state": "1",
                    "limit": 10,
                    "assignment_group": self.assignment_group
                }
            )
            return result
        except Exception as e:
            print(f"Error fetching tickets: {e}", flush=True)
            return None
    
    async def list_open_tickets(self):
        """List all open tickets in the network queue"""
        try:
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "servicenow_mcp.cli"],
                env=dict(os.environ)
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "list_incidents",
                        {"assignment_group": self.assignment_group}
                    )
                    
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        
                        if data.get('success'):
                            tickets = data.get('incidents', [])
                            
                            # Return summary format
                            return {
                                "success": True,
                                "count": len(tickets),
                                "summary": f"There are {len(tickets)} open tickets in the network queue",
                                "tickets": [
                                    {
                                        "number": t.get("number"),
                                        "short_description": t.get("short_description"),
                                        "priority": t.get("priority"),
                                        "state": t.get("state")
                                    } for t in tickets
                                ]
                            }
                    
                    return {"success": False, "message": "Failed to list tickets"}
        
        except Exception as e:
            print(f"Error listing tickets: {e}", flush=True)
            return {"success": False, "error": str(e)}
        
    async def analyze_ticket(self, ticket, llm=None, rag_service=None):
        """Analyze ticket - with optional RAG context"""
        try:
            # Debug logging
            print(f"=== ANALYZE TICKET DEBUG ===", flush=True)
            print(f"RAG service provided: {rag_service is not None}", flush=True)
            print(f"Ticket: {ticket.get('number')}", flush=True)
            
            # Choose LLM type
            llm_type = llm if llm is not None else self.preferred_llm
            llm_service = AbstractLLMServiceFactory.get_llm_instance(llm_type)
            
            # Build ticket description
            ticket_text = f"""
    Number: {ticket.get('number', 'N/A')}
    Short Description: {ticket.get('short_description', 'N/A')}
    Description: {ticket.get('description', 'N/A')}
    """
            
            # Search RAG for relevant documentation
            context = ""
            if rag_service:
                print("✓ RAG service available, searching...", flush=True)
                try:
                    docs = rag_service.search(ticket_text, top_k=2)
                    print(f"✓ RAG returned {len(docs)} documents", flush=True)
                    if docs:
                        context = "\n\n=== RELEVANT DOCUMENTATION ===\n"
                        for i, doc in enumerate(docs):
                            context += f"\n[Document {i+1} from {doc['source']}]:\n{doc['text']}\n"
                            print(f"  - Doc {i+1}: {doc['source']} (score: {doc['score']:.3f})", flush=True)
                        context += "\n=== END DOCUMENTATION ===\n"
                except Exception as e:
                    print(f"❌ RAG search failed: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ No RAG service provided!", flush=True)
            
            # Build analysis prompt
            prompt = f"""{context}

    Analyze this ServiceNow ticket:
    {ticket_text}

    Based on the documentation above (if provided), what type of issue is this? 
    Can it be automated? Provide a brief analysis and troubleshooting steps."""
            
            # Analyze with LLM
            result = await llm_service.analyze(prompt)
            return result
            
        except Exception as e:
            print(f"Error analyzing ticket: {e}", flush=True)
            import traceback
            traceback.print_exc()
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
        
    async def process_ticket(self, session, ticket, llm=None, rag_service= None):
        """Process a single ticket - analyze and take ownership"""
        print(f"Processing: {ticket.get('number')} - {ticket.get('short_description')}", flush=True)
        
        # Analyze the ticket (pass llm if overriding, pass rag service)
        analysis = await self.analyze_ticket(ticket, llm=llm, rag_service= rag_service)
        
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
    
    async def get_ticket_data(self, ticket_number):
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
    
    async def ask_llm_with_context(self, question, llm=None):
        """Ask LLM a question with ServiceNow context - can override LLM per call"""
        print(f"LLM query: {question}", flush=True)
        
        # Choose LLM type (override or default)
        llm_type = llm if llm is not None else self.preferred_llm
        
        # Extract ticket number if mentioned
        ticket_match = re.search(r'INC\d+', question, re.IGNORECASE)
        
        context = question

        if ticket_match:
            ticket_number = ticket_match.group(0).upper()
            ticket_data = await self.get_ticket_data(ticket_number)
            
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

User Question: {question}

Provide helpful answer based on the ticket information above."""
        
        try:
            # Create LLM service via factory
            llm_service = AbstractLLMServiceFactory.get_llm_instance(llm_type)
            
            # Use it
            result = await llm_service.ask(context)
            return result

        except Exception as e:
            print(f"Error asking LLM: {e}", flush=True)
            return f"Sorry, I encountered an error: {str(e)}"
        
    async def start_servicenow_job(self, llm_type, rag_service= None):
        """Main autonomous loop - monitors and processes tickets"""
        
        # Set preferred LLM type
        self.set_preferred_llm(llm_type)
        
        print("Starting Autonomous Agent Loop...", flush=True)
        print(f"Using LLM: {self.preferred_llm}", flush=True)
        print(f"Monitoring tickets for group: {self.assignment_group}", flush=True)
        
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
                                            # Uses self.preferred_llm
                                            print(f"Processing ticket with RAG: {rag_service is not None}", flush=True)
                                            await self.process_ticket(session, ticket, rag_service= rag_service)
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
                    
                    await asyncio.sleep(300)  # Check every 300 seconds