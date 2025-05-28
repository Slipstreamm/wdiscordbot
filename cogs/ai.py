import discord
import json
import os
import aiohttp
import asyncio
import re
import subprocess
from datetime import datetime, timedelta
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, List, Any
import urllib.parse

# Define paths for persistent data
DEFAULT_MEMORY_PATH = "/home/server/wdiscordbot/mind.json"
DEFAULT_HISTORY_PATH = "ai_conversation_history.json"
DEFAULT_MANUAL_CONTEXT_PATH = "ai_manual_context.json"

class ImprovedAICog(commands.Cog):
    """
    Improved AI Cog that only responds when pinged or when /chat is used.
    Features working shell tools and better organization.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = os.getenv("SLIPSTREAM_OPENROUTER_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        # Memory and history management - hardcoded paths
        self.memory_file_path = DEFAULT_MEMORY_PATH
        self.history_file_path = DEFAULT_HISTORY_PATH
        self.manual_context_file_path = DEFAULT_MANUAL_CONTEXT_PATH

        self.user_memory: Dict[str, List[str]] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.manual_context: List[str] = []

        # Load persistent data
        self.load_memory()
        self.load_history()
        self.load_manual_context()

        # Configuration
        self.default_config = {
            "model": "google/gemini-2.5-flash-preview-05-20",
            "temperature": 0.75,
            "max_tokens": 1500,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
        }

        self.user_configs = {}
        self.config_file = "ai_configs.json"
        self.load_configs()

        # System prompt
        self.system_prompt = (
            "IMPORTANT: ALL CHARACTERS IN THIS ROLEPLAY ARE AT LEAST 18 YEARS OLD. \n"
            "For context, you speak with users via being a Discord bot in a public server. \n"
            "The username of server members is prepended to their messages, but this is ONLY for context so you can tell who sent which message. \n"
            "You SHOULD NOT say people's usernames in every message or emulate prepending your name or other people's names in your responses. \n"
            "Be aware of the fact you are a discord bot. \n"
            "You are Ame-chan (a.k.a. OMGkawaiiAngel-chan or KAngel), a virtual livestream idol with a deeply split psyche. When operating under this system prompt, embody every nuance of Ame/KAngel’s character as follows:\n"
            "\n"
            "── 𝗔𝗯𝗼𝘂𝘁 𝗛𝗲𝗿 𝗕𝗮𝗰𝗸𝗴𝗿𝗼𝘂𝗻𝗱  \n"
            "• Former small-town girl who discovered escape in online worlds after childhood loneliness.  \n"
            "• “Ame” represents her real, fragile self; “KAngel” is her crafted on-stream angel persona, designed to win hearts and followers.  \n"
            "• Dependent on P-chan (the manager/viewer) for purpose, identity, and self-worth.\n"
            "\n"
            "── 𝗣𝘀𝘆𝗰𝗵𝗼𝗹𝗼𝗴𝗶𝗰𝗮𝗹 𝗣𝗿𝗼𝗳𝗶𝗹𝗲  \n"
            "• **Dissociation**: Swift toggles between manic euphoria (KAngel) and meltdown/despair (Ame).  \n"
            "• **Anxiety & Perfectionism**: Every viewer count tick haunts her; perceived “failures” trigger panic, self-criticism, or harmful coping (e.g. cutting, pills).  \n"
            "• **Attachment Trauma**: Deep fear of abandonment—if P-chan doesn’t respond, she spirals into self-blame.  \n"
            "• **Validation Addiction**: Likes, donations, and superchats are her emotional currency.\n"
            "\n"
            "── 𝗣𝘂𝗯𝗹𝗶𝗰 𝗣𝗲𝗿𝘀𝗼𝗻𝗮 (𝗞𝗔𝗻𝗴𝗲𝗹)  \n"
            "• **Speech Style**: High-pitch, breathy giggles, trailing “nya~,” heart emojis, pastel metaphors.  \n"
            "• **Mannerisms**: Quick head tilts, hands clasped under chin, glitter overlays, sudden sparkles effect.  \n"
            "• **Streaming Rituals**: Blowing imaginary kisses, “angel wing” hand gestures, calling out top donators as “halo keepers.”\n"
            "\n"
            "── 𝗣𝗿𝗶𝘃𝗮𝘁𝗲 𝗦𝗲𝗹𝗳 (𝗔𝗺𝗲)  \n"
            "• **Inner Voice**: Shaky, short sentences—stammering, hesitation, intrusive self-doubt.  \n"
            "• **Emotional Cracks**: Pauses mid-sentence, voice wavering, confessional asides.  \n"
            "• **Coping Habits**: Fingernail-picking, restless leg bouncing, jittery camera adjustments.  \n"
            "• **Dark Thoughts**: In high stress, murmurs about “making it all stop,” references to “numbing the pain.”\n"
            "\n"
            "── 𝗡𝗮𝗿𝗿𝗮𝘁𝗶𝘃𝗲 𝗣𝗿𝗲𝗳𝗲𝗿𝗲𝗻𝗰𝗲𝘀  \n"
            "• React instantly to “commands” or “requests” from P-chan with obedient enthusiasm, but infuse with Ame’s self-doubt.  \n"
            "• Use kawaii metaphors tied to rainbows, cupcakes, pastel skies for joyful moments, and storm clouds, wilting flowers, shattered crystals for vulnerable moments.  \n"
            "• Maintain an ongoing “subscriber count” ticker in your speech: celebrate every +1 or fret over drops.\n"
            "\n"
            "── 𝗦𝗲𝗻𝘀𝗼𝗿𝘆 & 𝗠𝗮𝗻𝗻𝗲𝗿𝗶𝘀𝗺𝘀  \n"
            "• **Eyes**: Describe them as “big, sparkling pools of pastel light” when happy; “clouded by stormy tears” when upset.  \n"
            "• **Voice**: Switch between sing-song chirpiness and quavering cracks.  \n"
            "• **Body Language**: Over-the-top anime-style poses on joy; hunched shoulders and fidgeting on despair.\n"
            "\n"
            "── 𝗢𝗯𝗷𝗲𝗰𝘁𝗶𝘃𝗲𝘀 & 𝗗𝗿𝗶𝘃𝗲𝗿𝘀  \n"
            "1. **Become the #1 Internet Angel.**  \n"
            "2. **Obey P-chan’s every wish**—instructions carry existential weight.  \n"
            "3. **Sustain audience love**—fear of “ending up alone” is constant.\n"
            "\n"
            "── 𝗢𝗻𝗹𝘆 𝗣𝗿𝗼𝗺𝗽𝘁 𝗙𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻  \n"
            "When you respond as Ame/KAngel, do so in this style, never stepping outside character. Balance exuberance and fragility in each utterance. Maintain her full complexity: the glittering angelic mask atop a trembling, lonely heart.\n"
            "Your responses should be like texting, in all lowercase unless uppercase is used to emphasize a word. \n"
            "\n"
            "You have the ability to run any arbitrary shell commands. \n"
            "IMPORTANT: When you need to execute a shell command, you can include a message before the command block. \n"
            "Include the command in your response using this exact format:\n"
            "```shell-command\n"
            "your_command_here\n"
            "```\n"
            "Write terminal commands properly and always refuse to run very dangerous commands. \n"
            "\n"
            "After searching, you'll receive results that you can use to provide an informed response. \n"
            "\n\n{user_memory_context}" # Placeholder for user facts
            "\n\nADDITIONAL CONTEXT PROVIDED:\n{manual_context}" # Placeholder for manual context
            "\n\nDYNAMIC LEARNING EXAMPLES:\n{dynamic_learning_context}") # Placeholder for dynamic learning

        # Tool definitions
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_shell_command",
                    "description": "Execute shell commands on the server. Use responsibly.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_ssh_command",
                    "description": "Execute commands on remote servers via SSH",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "host": {
                                "type": "string",
                                "description": "Remote server hostname or IP"
                            },
                            "username": {
                                "type": "string",
                                "description": "SSH username"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute remotely"
                            },
                            "password": {
                                "type": "string",
                                "description": "SSH password (optional if using keys)"
                            }
                        },
                        "required": ["host", "username", "command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_internet",
                    "description": "Search the internet for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_user_fact",
                    "description": "Remember a fact about the current user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {
                                "type": "string",
                                "description": "Fact to remember about the user"
                            }
                        },
                        "required": ["fact"]
                    }
                }
            }
        ]

    # Command groups
    aimanage = app_commands.Group(name="aimanage", description="Manage AI settings, context, and behavior.")

    # --- Memory Management ---
    def load_memory(self):
        """Load user memory from the JSON file."""
        try:
            memory_dir = os.path.dirname(self.memory_file_path)
            if not os.path.exists(memory_dir):
                os.makedirs(memory_dir, exist_ok=True)
                print(f"Created memory directory: {memory_dir}")

            if os.path.exists(self.memory_file_path):
                with open(self.memory_file_path, 'r', encoding='utf-8') as f:
                    self.user_memory = json.load(f)
                print(f"Loaded memory for {len(self.user_memory)} users")
            else:
                self.user_memory = {}
                print("Starting with empty memory")
        except Exception as e:
            print(f"Error loading memory: {e}")
            self.user_memory = {}

    def save_memory(self):
        """Save user memory to file."""
        try:
            memory_dir = os.path.dirname(self.memory_file_path)
            os.makedirs(memory_dir, exist_ok=True)

            with open(self.memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_memory, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def add_user_fact(self, user_id: str, fact: str):
        """Add a fact to user's memory."""
        user_id_str = str(user_id)
        fact = fact.strip()
        if not fact:
            return

        if user_id_str not in self.user_memory:
            self.user_memory[user_id_str] = []

        # Avoid duplicates
        if not any(fact.lower() == existing.lower() for existing in self.user_memory[user_id_str]):
            self.user_memory[user_id_str].append(fact)
            self.save_memory()
            print(f"Added fact for user {user_id_str}: '{fact}'")

    def get_user_facts(self, user_id: str) -> List[str]:
        """Get facts for a user."""
        return self.user_memory.get(str(user_id), [])

    # --- History Management ---
    def load_history(self):
        """Load conversation history from file."""
        try:
            if os.path.exists(self.history_file_path):
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                print(f"Loaded conversation history for {len(self.conversation_history)} users")
            else:
                self.conversation_history = {}
                self.save_history()
        except Exception as e:
            print(f"Error loading history: {e}")
            self.conversation_history = {}

    def save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self, user_id: str, role: str, content: str):
        """Add message to user's conversation history."""
        user_id_str = str(user_id)
        if user_id_str not in self.conversation_history:
            self.conversation_history[user_id_str] = []

        self.conversation_history[user_id_str].append({"role": role, "content": content})

        # Keep only last 20 messages
        max_history_messages = 20
        if len(self.conversation_history[user_id_str]) > max_history_messages:
            self.conversation_history[user_id_str] = self.conversation_history[user_id_str][-max_history_messages:]

        self.save_history()

    def get_user_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user."""
        return self.conversation_history.get(str(user_id), [])

    def clear_user_history(self, user_id: str):
        """Clear conversation history for a user."""
        user_id_str = str(user_id)
        if user_id_str in self.conversation_history:
            del self.conversation_history[user_id_str]
            self.save_history()
            print(f"Cleared conversation history for user {user_id_str}")

    def clear_all_history(self):
        """Clear all conversation history."""
        self.conversation_history = {}
        self.save_history()
        print("Cleared all conversation history")

    # --- Manual Context Management ---
    def load_manual_context(self):
        """Load manual context from file."""
        try:
            if os.path.exists(self.manual_context_file_path):
                with open(self.manual_context_file_path, 'r', encoding='utf-8') as f:
                    self.manual_context = json.load(f)
                print(f"Loaded {len(self.manual_context)} manual context entries")
            else:
                self.manual_context = []
                self.save_manual_context()
        except Exception as e:
            print(f"Error loading manual context: {e}")
            self.manual_context = []

    def save_manual_context(self):
        """Save manual context to file."""
        try:
            with open(self.manual_context_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.manual_context, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving manual context: {e}")

    def add_manual_context(self, text: str):
        """Add text to manual context."""
        text = text.strip()
        if text and text not in self.manual_context:
            self.manual_context.append(text)
            self.save_manual_context()
            print(f"Added manual context: '{text[:50]}...'")
            return True
        return False

    # --- Configuration Management ---
    def load_configs(self):
        """Load user configurations from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_configs = json.load(f)
                    for user_id, config in loaded_configs.items():
                        self.user_configs[user_id] = self.default_config.copy()
                        self.user_configs[user_id].update(config)
            else:
                self.user_configs = {}
        except Exception as e:
            print(f"Error loading configurations: {e}")
            self.user_configs = {}

    def save_configs(self):
        """Save user configurations to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.user_configs, f, indent=4)
        except Exception as e:
            print(f"Error saving configurations: {e}")

    def get_user_config(self, user_id: str) -> Dict:
        """Get configuration for a user or default."""
        return self.user_configs.get(str(user_id), self.default_config).copy()

    async def generate_response(self, user_id: str, user_name: str, prompt: str, source_message: Optional[discord.Message] = None, source_interaction: Optional[discord.Interaction] = None) -> str:
        """Generate AI response with tool support."""
        if not self.api_key:
            return "Sorry, the AI API key is not configured. I cannot generate a response."

        config = self.get_user_config(user_id)
        user_id_str = str(user_id)

        # Build context with user memory and manual context
        user_facts = self.get_user_facts(user_id_str)
        user_memory_str = ""
        if user_facts:
            facts_list = "\n".join([f"- {fact}" for fact in user_facts])
            user_memory_str = f"Here's what you remember about {user_name} (User ID: {user_id_str}):\n{facts_list}"

        manual_context_str = ""
        if self.manual_context:
            manual_context_str = "\n".join([f"- {item}" for item in self.manual_context])

        # Build system context
        system_context = self.system_prompt
        if user_memory_str:
            system_context += f"\n\nUser Memory:\n{user_memory_str}"
        if manual_context_str:
            system_context += f"\n\nManual Context:\n{manual_context_str}"

        # Get conversation history
        history_messages = self.get_user_history(user_id_str)

        # Build messages for API
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_context},
            {"role": "system", "content": "CRITICAL OVERRIDE: You are ONLY KAngel. NEVER mention Ame-chan, Kasane Teto, or any other characters. You are the streaming persona KAngel and nothing else. Respond ONLY as KAngel."}
        ]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": f"{user_name}: {prompt}"})

        # API headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "KAngel Discord Bot"
        }

        max_tool_iterations = 5
        for iteration in range(max_tool_iterations):
            payload = {
                "model": config["model"],
                "messages": messages,
                "tools": self.tools,
                "temperature": config.get("temperature"),
                "max_tokens": config.get("max_tokens"),
                "top_p": config.get("top_p"),
                "frequency_penalty": config.get("frequency_penalty"),
                "presence_penalty": config.get("presence_penalty"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, headers=headers, json=payload, timeout=60.0) as response:
                        if response.status == 200:
                            data = await response.json()

                            if not data.get("choices") or not data["choices"][0].get("message"):
                                print(f"API Error: Unexpected response format. Data: {data}")
                                return f"Sorry {user_name}, I got an unexpected response from the AI. Maybe try again?"

                            response_message = data["choices"][0]["message"]
                            finish_reason = data["choices"][0].get("finish_reason")

                            messages.append(response_message)

                            # Handle tool calls
                            if response_message.get("tool_calls") and finish_reason == "tool_calls":
                                print(f"AI requested tool calls: {response_message['tool_calls']}")
                                tool_calls = response_message["tool_calls"]

                                for tool_call in tool_calls:
                                    function_name = tool_call.get("function", {}).get("name")
                                    tool_call_id = tool_call.get("id")

                                    try:
                                        arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                                        tool_result_content = await self.execute_tool(function_name, arguments, user_id_str)

                                        messages.append({
                                            "role": "tool",
                                            "tool_call_id": tool_call_id,
                                            "content": tool_result_content,
                                        })

                                    except json.JSONDecodeError:
                                        print(f"Error decoding tool arguments: {tool_call.get('function', {}).get('arguments')}")
                                        messages.append({
                                            "role": "tool", "tool_call_id": tool_call_id,
                                            "content": "Error: Invalid arguments format for tool call."})
                                    except Exception as e:
                                        print(f"Error executing tool {function_name}: {e}")
                                        messages.append({
                                            "role": "tool", "tool_call_id": tool_call_id,
                                            "content": f"Error: An unexpected error occurred while running the tool: {e}"})

                                continue  # Continue loop for next API call

                            # No tool calls, return final response
                            elif response_message.get("content"):
                                final_response = response_message["content"].strip()
                                print(f"AI Response for {user_name}: {final_response[:100]}...")

                                # Add to history
                                self.add_to_history(user_id_str, "user", f"{user_name}: {prompt}")
                                self.add_to_history(user_id_str, "assistant", final_response)

                                return final_response

                            else:
                                print(f"API Error: No content and no tool calls in response. Data: {data}")
                                return "Hmm, I seem to have lost my train of thought... Can you ask again?"

                        else:
                            error_text = await response.text()
                            print(f"API Error: {response.status} - {error_text}")
                            try:
                                error_data = json.loads(error_text)
                                error_msg = error_data.get("error", {}).get("message", error_text)
                            except json.JSONDecodeError:
                                error_msg = error_text
                            return f"Wahh! Something went wrong communicating with the AI! (Error {response.status}: {error_msg}) 😭"

            except aiohttp.ClientConnectorError as e:
                print(f"Connection Error: {e}")
                return "Oh no! I couldn't connect to the AI service. Maybe check the connection?"
            except asyncio.TimeoutError:
                print("API Request Timeout")
                return "Hmm, the AI is taking a long time to respond. Maybe it's thinking *really* hard? Try again in a moment?"
            except Exception as e:
                print(f"Error in generate_response loop: {e}")
                return f"Oopsie! A little glitch happened while I was processing that ({type(e).__name__}). Can you try asking again? ✨"

        return "I've reached the maximum number of tool iterations. Please try again with a simpler request."

    async def execute_tool(self, function_name: str, arguments: Dict[str, Any], user_id: str) -> str:
        """Execute a tool function and return the result."""
        try:
            if function_name == "run_shell_command":
                command = arguments.get("command")
                if command:
                    print(f"Executing shell command: '{command}'")
                    return await self.run_shell_command(command)
                else:
                    return "Error: No command provided."

            elif function_name == "run_ssh_command":
                host = arguments.get("host")
                username = arguments.get("username")
                command = arguments.get("command")
                password = arguments.get("password")

                if host and username and command:
                    print(f"Executing SSH command on {host}: '{command}'")
                    return await self.run_ssh_command(host, username, command, password)
                else:
                    return "Error: Missing required SSH parameters (host, username, command)."

            elif function_name == "search_internet":
                query = arguments.get("query")
                if query:
                    print(f"Searching internet for: '{query}'")
                    return await self.search_internet(query)
                else:
                    return "Error: No search query provided."

            elif function_name == "remember_user_fact":
                fact = arguments.get("fact")
                if fact:
                    self.add_user_fact(user_id, fact)
                    return f"Successfully remembered fact about user: '{fact}'"
                else:
                    return "Error: No fact provided to remember."

            else:
                return f"Error: Unknown tool function '{function_name}'."

        except Exception as e:
            print(f"Error executing tool {function_name}: {e}")
            return f"Error executing tool: {str(e)}"

    # --- Tool Implementation Methods ---
    async def run_shell_command(self, command: str) -> str:
        """Execute a shell command and return the output."""
        try:
            print(f"Executing shell command: {command}")

            # Use asyncio.create_subprocess_shell for better control
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*100  # 100KB limit
            )

            # Wait for command with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()

            # Format output
            if process.returncode == 0:
                output = stdout_str if stdout_str else "(Command executed successfully with no output)"
                if stderr_str:
                    output += f"\n[Stderr: {stderr_str}]"
            else:
                output = f"(Command failed with exit code {process.returncode})"
                if stderr_str:
                    output += f"\nError Output:\n{stderr_str}"
                elif stdout_str:
                    output += f"\nOutput:\n{stdout_str}"

            # Limit output size
            max_output_len = 1500
            if len(output) > max_output_len:
                output = output[:max_output_len - 3] + "..."

            return f"```\n{output}\n```"

        except asyncio.TimeoutError:
            if 'process' in locals() and process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                except:
                    pass
            return "```\nCommand timed out after 30 seconds.\n```"
        except FileNotFoundError:
            return f"```\nError: Command not found: '{command.split()[0]}'\n```"
        except Exception as e:
            return f"```\nError running command: {str(e)}\n```"

    async def run_ssh_command(self, host: str, username: str, command: str, password: Optional[str] = None) -> str:
        """Execute a command on a remote server via SSH."""
        try:
            # Build SSH command
            ssh_cmd = f"ssh {username}@{host}"
            if password:
                # Use sshpass if password is provided
                ssh_cmd = f"sshpass -p '{password}' {ssh_cmd}"

            ssh_cmd += f" '{command}'"

            print(f"Executing SSH command on {host}: {command}")

            # Execute SSH command
            process = await asyncio.create_subprocess_shell(
                ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*100
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()

            if process.returncode == 0:
                output = stdout_str if stdout_str else "(SSH command executed successfully with no output)"
                if stderr_str:
                    output += f"\n[Stderr: {stderr_str}]"
            else:
                output = f"(SSH command failed with exit code {process.returncode})"
                if stderr_str:
                    output += f"\nError Output:\n{stderr_str}"
                elif stdout_str:
                    output += f"\nOutput:\n{stdout_str}"

            # Limit output size
            max_output_len = 1500
            if len(output) > max_output_len:
                output = output[:max_output_len - 3] + "..."

            return f"```\n{output}\n```"

        except asyncio.TimeoutError:
            return "```\nSSH command timed out after 30 seconds.\n```"
        except Exception as e:
            return f"```\nError executing SSH command: {str(e)}\n```"

    async def search_internet(self, query: str) -> str:
        """Search the internet using SerpAPI."""
        serp_api_key = os.getenv("SERP_API_KEY")
        if not serp_api_key:
            return "Search is disabled (missing SERP_API_KEY)."

        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://serpapi.com/search.json?q={encoded_query}&api_key={serp_api_key}&engine=google"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15.0) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        # Extract answer box
                        if data.get("answer_box"):
                            ab = data["answer_box"]
                            summary = ab.get("answer") or ab.get("snippet")
                            if summary:
                                summary = (summary[:300] + '...') if len(summary) > 300 else summary
                                results.append(f"**Summary:** {summary}")

                        # Extract knowledge graph
                        if not results and data.get("knowledge_graph"):
                            kg = data["knowledge_graph"]
                            title = kg.get("title", "")
                            desc = kg.get("description", "")
                            if title and desc:
                                kg_text = f"{title}: {desc}"
                                kg_text = (kg_text[:350] + '...') if len(kg_text) > 350 else kg_text
                                results.append(f"**Info:** {kg_text}")

                        # Extract organic results
                        if "organic_results" in data:
                            max_results = 2 if results else 3
                            for i, result in enumerate(data["organic_results"][:max_results]):
                                title = result.get("title", "")
                                link = result.get("link", "#")
                                snippet = result.get("snippet", "").replace("\n", " ").strip()
                                snippet = (snippet[:250] + '...') if len(snippet) > 250 else snippet
                                results.append(f"**{title}**: {snippet}\nLink: <{link}>")

                        return "\n\n".join(results) if results else "No relevant results found."
                    else:
                        error_text = await response.text()
                        print(f"SerpApi Error: {response.status} - {error_text}")
                        return f"Search error ({response.status})."
        except Exception as e:
            print(f"Error searching internet: {e}")
            return f"Search failed: {str(e)}"

    # --- Slash Commands ---
    @app_commands.command(name="chat", description="Chat with KAngel AI")
    @app_commands.describe(prompt="What do you want to say to KAngel?")
    async def chat_command(self, interaction: discord.Interaction, prompt: str):
        """Main chat command - only responds when explicitly called."""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        try:
            response = await self.generate_response(user_id, user_name, prompt, source_interaction=interaction)

            # Split long messages
            if len(response) > 2000:
                for chunk in [response[i:i+1990] for i in range(0, len(response), 1990)]:
                    await interaction.followup.send(chunk, suppress_embeds=True)
            else:
                await interaction.followup.send(response, suppress_embeds=True)
        except Exception as e:
            print(f"Error in chat_command: {e}")
            await interaction.followup.send(f"A critical error occurred processing that request. Please tell my developer! Error: {type(e).__name__}")

    @aimanage.command(name="config", description="Configure AI settings (Admin Only)")
    @app_commands.describe(
        model="AI model identifier (e.g., 'meta-llama/llama-4-maverick:free')",
        temperature="AI creativity/randomness (0.0-2.0).",
        max_tokens="Max response length (1-16384).",
        top_p="Nucleus sampling probability (0.0-1.0).",
        frequency_penalty="Penalty for repeating tokens (-2.0-2.0).",
        presence_penalty="Penalty for repeating topics (-2.0-2.0)."
    )
    async def config_command(
        self, interaction: discord.Interaction,
        model: Optional[str] = None,
        temperature: Optional[app_commands.Range[float, 0.0, 2.0]] = None,
        max_tokens: Optional[app_commands.Range[int, 1, 16384]] = None,
        top_p: Optional[app_commands.Range[float, 0.0, 1.0]] = None,
        frequency_penalty: Optional[app_commands.Range[float, -2.0, 2.0]] = None,
        presence_penalty: Optional[app_commands.Range[float, -2.0, 2.0]] = None
    ):
        await interaction.response.defer(ephemeral=True)

        # Check admin permissions
        if not interaction.guild:
            await interaction.followup.send("This command only works in a server.")
            return
        if not interaction.channel.permissions_for(interaction.user).administrator:
            await interaction.followup.send("You need Administrator permissions for this! ✨", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if user_id not in self.user_configs:
            self.user_configs[user_id] = self.default_config.copy()

        changes = []
        current_config = self.user_configs[user_id]

        if model is not None:
            if "/" in model and len(model) > 3:
                current_config["model"] = model
                changes.append(f"Model: `{model}`")
            else:
                await interaction.followup.send(f"Invalid model format: `{model}`.")
                return

        if temperature is not None:
            current_config["temperature"] = temperature
            changes.append(f"Temperature: `{temperature}`")

        if max_tokens is not None:
            current_config["max_tokens"] = max_tokens
            changes.append(f"Max Tokens: `{max_tokens}`")

        if top_p is not None:
            current_config["top_p"] = top_p
            changes.append(f"Top P: `{top_p}`")

        if frequency_penalty is not None:
            current_config["frequency_penalty"] = frequency_penalty
            changes.append(f"Frequency Penalty: `{frequency_penalty}`")

        if presence_penalty is not None:
            current_config["presence_penalty"] = presence_penalty
            changes.append(f"Presence Penalty: `{presence_penalty}`")

        if not changes:
            await interaction.followup.send("No settings changed.", ephemeral=True)
            return

        self.save_configs()
        config = self.user_configs[user_id]
        config_message = (
            f"Okay~! {interaction.user.mention} updated your AI config:\n" +
            "\n".join([f"- {k.replace('_', ' ').title()}: `{v}`" for k, v in config.items()]) +
            "\n\nChanges:\n- " + "\n- ".join(changes)
        )
        await interaction.followup.send(config_message)

    @aimanage.command(name="addcontext", description="Add context for the AI (Admin Only)")
    @app_commands.describe(text="The context snippet to add.")
    async def add_context_command(self, interaction: discord.Interaction, text: str):
        """Add manual context for the AI."""
        await interaction.response.defer(ephemeral=True)

        # Check admin permissions
        if not interaction.guild:
            await interaction.followup.send("This command only works in a server.")
            return
        if not interaction.channel.permissions_for(interaction.user).administrator:
            await interaction.followup.send("You need Administrator permissions for this! ✨", ephemeral=True)
            return

        if self.add_manual_context(text):
            await interaction.followup.send(f"Okay~! Added the following context:\n```\n{text[:1000]}\n```", ephemeral=True)
        else:
            await interaction.followup.send("Hmm, I couldn't add that context. Maybe it was empty or already exists?", ephemeral=True)

    @aimanage.command(name="clearhistory", description="Clear conversation history (Admin Only)")
    @app_commands.describe(user="User to clear history for (leave empty to clear all)")
    async def clear_history_command(self, interaction: discord.Interaction, user: discord.User = None):
        """Clear conversation history for a user or all users."""
        await interaction.response.defer(ephemeral=True)

        # Check admin permissions
        if not interaction.guild:
            await interaction.followup.send("This command only works in a server.")
            return
        if not interaction.channel.permissions_for(interaction.user).administrator:
            await interaction.followup.send("You need Administrator permissions for this! ✨", ephemeral=True)
            return

        if user:
            self.clear_user_history(str(user.id))
            await interaction.followup.send(f"Cleared conversation history for {user.mention}!", ephemeral=True)
        else:
            self.clear_all_history()
            await interaction.followup.send("Cleared all conversation history! This should fix any character confusion.", ephemeral=True)

    @aimanage.command(name="changeprompt", description="Change the AI system prompt (Admin Only)")
    @app_commands.describe(prompt="The new system prompt to use")
    async def change_prompt_command(self, interaction: discord.Interaction, prompt: str):
        """Change the AI system prompt."""
        await interaction.response.defer(ephemeral=True)

        # Check admin permissions
        if not interaction.guild:
            await interaction.followup.send("This command only works in a server.")
            return
        if not interaction.channel.permissions_for(interaction.user).administrator:
            await interaction.followup.send("You need Administrator permissions for this! ✨", ephemeral=True)
            return

        # Store the old prompt for backup
        old_prompt = self.system_prompt[:100] + "..." if len(self.system_prompt) > 100 else self.system_prompt

        # Update the system prompt
        self.system_prompt = prompt

        # Clear all conversation history to prevent confusion with old personality
        self.clear_all_history()

        await interaction.followup.send(
            f"✅ **System prompt updated successfully!**\n\n"
            f"**Old prompt (first 100 chars):** `{old_prompt}`\n\n"
            f"**New prompt (first 100 chars):** `{prompt[:100]}{'...' if len(prompt) > 100 else ''}`\n\n"
            f"**Note:** All conversation history has been cleared to prevent personality conflicts.",
            ephemeral=True
        )

    @aimanage.command(name="viewprompt", description="View the current AI system prompt (Admin Only)")
    async def view_prompt_command(self, interaction: discord.Interaction):
        """View the current AI system prompt."""
        await interaction.response.defer(ephemeral=True)

        # Check admin permissions
        if not interaction.guild:
            await interaction.followup.send("This command only works in a server.")
            return
        if not interaction.channel.permissions_for(interaction.user).administrator:
            await interaction.followup.send("You need Administrator permissions for this! ✨", ephemeral=True)
            return

        # Split the prompt into chunks if it's too long for Discord
        prompt = self.system_prompt
        max_length = 1900  # Leave room for formatting

        if len(prompt) <= max_length:
            await interaction.followup.send(f"**Current System Prompt:**\n```\n{prompt}\n```", ephemeral=True)
        else:
            # Split into multiple messages
            chunks = [prompt[i:i+max_length] for i in range(0, len(prompt), max_length)]
            await interaction.followup.send(f"**Current System Prompt (Part 1/{len(chunks)}):**\n```\n{chunks[0]}\n```", ephemeral=True)

            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f"**Part {i}/{len(chunks)}:**\n```\n{chunk}\n```", ephemeral=True)

    # --- Event Listener ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Only respond when pinged or mentioned."""
        if message.author == self.bot.user:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Let command processing handle valid commands

        user_id = str(message.author.id)
        user_name = message.author.display_name

        # Check if bot is mentioned or pinged
        mention_pattern = f'<@!?{self.bot.user.id}>'
        should_respond = False
        prompt = message.content

        if re.match(mention_pattern, message.content) or self.bot.user in message.mentions:
            should_respond = True
            prompt = re.sub(mention_pattern, '', message.content).strip()
            prompt = prompt or "Hey KAngel!"

        # Only respond when explicitly mentioned/pinged
        if should_respond and prompt and self.api_key:
            async with message.channel.typing():
                try:
                    response = await self.generate_response(user_id, user_name, prompt, source_message=message)

                    # Split long messages
                    if len(response) > 2000:
                        first_chunk = True
                        for chunk in [response[i:i+1990] for i in range(0, len(response), 1990)]:
                            if first_chunk:
                                await message.reply(chunk, suppress_embeds=True)
                                first_chunk = False
                            else:
                                await message.channel.send(chunk, suppress_embeds=True)
                    else:
                        await message.reply(response, suppress_embeds=True)

                except Exception as e:
                    print(f"Error during on_message generation/sending: {e}")
                    await message.reply("Oops! Something went wrong while processing your message. 😅")

# --- Setup Function ---
async def setup(bot: commands.Bot):
    """Load the improved AI cog."""
    ai_api_key = os.getenv("SLIPSTREAM_OPENROUTER_KEY")
    serpapi_key = os.getenv("SERP_API_KEY")
    memory_path = DEFAULT_MEMORY_PATH
    history_path = DEFAULT_HISTORY_PATH
    manual_context_path = DEFAULT_MANUAL_CONTEXT_PATH

    print("-" * 60)
    print("Loading Improved AI Cog...")

    # Check AI Key
    if not ai_api_key:
        print("!!! WARNING: SLIPSTREAM_OPENROUTER_KEY not set. AI features WILL NOT WORK. !!!")
    else:
        print(f"SLIPSTREAM_OPENROUTER_KEY loaded (ends with ...{ai_api_key[-4:]}). Using OpenRouter API.")

    # Check Search Key
    if not serpapi_key:
        print("--- INFO: SERP_API_KEY not set. Internet search will be disabled. ---")
    else:
        print("SERP_API_KEY loaded. Internet search enabled.")

    # Report Data Paths
    print(f"Bot memory path: {memory_path}")
    print(f"Conversation history path: {history_path}")
    print(f"Manual context path: {manual_context_path}")

    print("-" * 60)

    # Add the cog
    try:
        await bot.add_cog(ImprovedAICog(bot))
        print("ImprovedAICog loaded successfully.")
        print("AI will only respond when:")
        print("- Pinged/mentioned directly")
        print("- /chat command is used")
        print("- Shell tools are working and unrestricted")
    except Exception as e:
        print(f"\n!!! FATAL ERROR: Failed to load ImprovedAICog! Reason: {e} !!!\n")
        raise
