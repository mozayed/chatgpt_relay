import websockets, json, os, uuid, asyncio
from datetime import datetime
from models.tools import Tools
from models.jobs import Jobs
from models.servicenow import ServiceNow
from models.agent import NetworkAgent

class VoiceCall:
    def __init__(self, call_id):
        self.call_id = call_id

    async def monitor_call(self):
    #Monitor call and handle function calls
        try:
            async with websockets.connect(
                f"wss://api.openai.com/v1/realtime?call_id={self.call_id}",
                additional_headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
                }
            ) as ws:
                print(f"Monitoring call {self.call_id}", flush=True)
                
                async for message in ws:
                    event = json.loads(message)
                    event_type = event.get('type', '')
                    
                    if event_type == 'response.function_call_arguments.done':
                        call_data = event
                        function_name = call_data.get('name', '')
                        arguments = json.loads(call_data.get('arguments', '{}'))
                        
                        print(f"Function call: {function_name} with {arguments}", flush=True)
                        
                        # Handle get_device_vlans
                        if function_name == 'get_device_vlans':
                            device_name = arguments.get('device_name', '')
                            
                            # Queue request for on-prem
                            req_id = str(uuid.uuid4())
                            req_data = {
                                "id": req_id,
                                "tool": "get_device_vlans",
                                "params": {"device_name": device_name},
                                "timestamp": datetime.now().isoformat()
                            }
                            jobs = Jobs()
                            jobs.pending_requests.append(req_data)
                            print(f"Queued request {req_id}", flush=True)
                            
                            # Wait for response from on-prem
                            import time
                            timeout = 10
                            start = time.time()
                            while req_id not in jobs.responses:
                                if time.time() - start > timeout:
                                    result_text = "Sorry, request timed out"
                                    break
                                await asyncio.sleep(0.5)
                            else:
                                result = jobs.responses.pop(req_id)
                                result_text = f"VLANs: {json.dumps(result)}"
                            
                            print(f"Got result: {result_text}", flush=True)
                            
                            # Send result back to ChatGPT
                            await ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_data.get('call_id'),
                                    "output": result_text
                                }
                            }))
                        
                        # Handle ask_claude
                        elif function_name == 'ask_claude':
                            question = arguments.get('question', '')
                            
                            print(f"Asking Claude: {question}", flush=True)
                            
                            # Call network agent's Claude integration
                            servicenow_instance = ServiceNow(agent_instance=NetworkAgent())
                            answer = await servicenow_instance.ask_claude_with_context(question)
                            
                            print(f"Claude answered: {answer[:100]}...", flush=True)
                            
                            # Send result back to ChatGPT
                            await ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_data.get('call_id'),
                                    "output": answer
                                }
                            }))

        except websockets.exceptions.ConnectionClosedError:
            print(f"Call {self.call_id} ended (connection closed)", flush=True)

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}", flush=True)  

        except Exception as e:
            print(f"Monitor error: {e}", flush=True)
            import traceback
            traceback.print_exc()
