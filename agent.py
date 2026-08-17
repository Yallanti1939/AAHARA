import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import (
    search_menu, get_full_menu, add_to_cart, remove_from_cart, clear_cart,
    apply_promo_code, view_cart, place_order, track_order, get_order_history
)

load_dotenv()

client = None
client_key = None

def get_agent_client_and_model(force_provider=None):
    load_dotenv(override=True)
    
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if force_provider == "groq" and groq_key:
        client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        return client, model, "groq"

    if groq_key and force_provider is None:
        client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        return client, model, "groq"

    if openai_key and force_provider != "gemini":
        client = OpenAI(api_key=openai_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return client, model, "openai"

    if gemini_key:
        client = OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        return client, model, "gemini"

    raise ValueError("No API key (GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY) found in environment or .env file.")

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": "Search available food items in the menu by keyword, category, vegetarian preference (is_veg), or maximum price limit (max_price). Pass 'all' or empty string '' to retrieve the full menu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword (e.g. 'burger', 'pizza', 'biryani', 'all')"
                    },
                    "is_veg": {
                        "type": "boolean",
                        "description": "Set true for vegetarian items only, false for non-veg items."
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum budget/price cap in ₹."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_full_menu",
            "description": "Retrieve the complete menu grouped with prices, ratings, and veg/non-veg indicators.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a specific menu item to the cart using its item id and desired quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "The id of the menu item to add, obtained from search_menu results"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "How many units of this item to add"
                    }
                },
                "required": ["item_id", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove an item or decrease item quantity in the cart using its item_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "The id of the menu item in cart to remove or reduce"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to remove. Omit or set to 0 to remove item completely."
                    }
                },
                "required": ["item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Empty all items from the current cart.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_promo_code",
            "description": "Apply a discount promo code to the cart (e.g., AAHARA10 for 10% off, WELCOME50 for ₹50 off).",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The promo code string, e.g. AAHARA10 or WELCOME50"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "View all items in cart with subtotals, applied discount, tax, and final total.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place an order using current cart items and customer details (customer_name, customer_phone, delivery_address). Do not pass null for string parameters; pass empty string '' if omitted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer, e.g. 'Rahul Sharma'. Pass '' if omitted."
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Phone number of the customer, e.g. '9876543210'. Pass '' if omitted."
                    },
                    "delivery_address": {
                        "type": "string",
                        "description": "Complete delivery address, e.g. 'Flat 402, Sunshine Apartments, MG Road'. Pass '' if omitted."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Special cooking/delivery instructions, e.g. 'extra spicy'. Pass '' if none."
                    },
                    "promo_code": {
                        "type": "string",
                        "description": "Promo code string (e.g. 'AAHARA10'). Pass '' if none."
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method: 'UPI' or 'Cash on Delivery'. Pass '' if omitted."
                    },
                    "transaction_id": {
                        "type": "string",
                        "description": "Transaction UTR number if paid via UPI. Pass '' if none."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "track_order",
            "description": "Check the live status and total of a previously placed order using its order id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order id to track"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_history",
            "description": "Retrieve past order history placed by the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def execute_tool(name, arguments):
    """
    Bridges the LLM's requested tool call to the actual Python implementation.
    """
    if not isinstance(arguments, dict):
        arguments = {}
    for k in list(arguments.keys()):
        if arguments[k] is None:
            arguments[k] = ""

    if name == "search_menu":
        return search_menu(
            query=arguments.get("query"),
            is_veg=arguments.get("is_veg"),
            max_price=arguments.get("max_price")
        )
    elif name == "get_full_menu":
        return get_full_menu()
    elif name == "add_to_cart":
        return add_to_cart(arguments.get("item_id"), arguments.get("quantity"))
    elif name == "remove_from_cart":
        return remove_from_cart(arguments.get("item_id"), arguments.get("quantity"))
    elif name == "clear_cart":
        return clear_cart()
    elif name == "apply_promo_code":
        return apply_promo_code(arguments.get("code"))
    elif name == "view_cart":
        return view_cart()
    elif name == "place_order":
        return place_order(
            customer_name=arguments.get("customer_name"),
            customer_phone=arguments.get("customer_phone"),
            delivery_address=arguments.get("delivery_address"),
            notes=arguments.get("notes"),
            promo_code=arguments.get("promo_code")
        )
    elif name == "track_order":
        return track_order(arguments.get("order_id"))
    elif name == "get_order_history":
        return get_order_history()
    else:
        return {"error": f"Unknown tool: {name}"}

def make_completion_call(messages):
    import time
    llm_client, model_name, active_provider = get_agent_client_and_model()
    
    for attempt in range(3):
        try:
            response = llm_client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            return response, active_provider
        except Exception as e:
            err_str = str(e)
            if active_provider in ("groq", "openai"):
                try:
                    g_client, g_model, g_prov = get_agent_client_and_model(force_provider="gemini")
                    response = g_client.chat.completions.create(
                        model=g_model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                    return response, g_prov
                except Exception:
                    pass

            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()) and attempt < 2:
                time.sleep(3 * (attempt + 1))
            else:
                raise e

    raise RuntimeError("Failed to obtain LLM response across providers.")

def run_agent(user_message, history=None):
    system_prompt = (
        "You are Aahara, a warm, professional, and helpful AI food ordering assistant for a restaurant.\n"
        "You have access to tools to search the menu, filter by vegetarian/non-veg preference and price, manage cart items (add, remove, clear), apply promo codes (AAHARA10, WELCOME50), place orders, and track orders.\n"
        "Always use the tools to get real database data instead of guessing.\n"
        "When a user wants multiple items, call add_to_cart separately for each item.\n"
        "Be concise, engaging, and format responses clearly with item names, prices in ₹, ratings ⭐, and veg/non-veg indicators (🌱/🍗).\n\n"
        "Rules:\n"
        "1. Help users search the menu or filter by Veg/Non-Veg and budget.\n"
        "2. Never invent food items or prices. Always search the menu to verify availability.\n"
        "3. If a user mentions promo codes, recommend AAHARA10 (10% OFF) or WELCOME50 (₹50 OFF on orders > ₹200) and use apply_promo_code tool.\n"
        "4. Allow users to remove items or clear cart using remove_from_cart or clear_cart.\n"
        "5. BEFORE PLACING AN ORDER: Ask the user for their Name, Phone Number, and Delivery Address if they haven't provided them yet.\n"
        "6. Always pass customer_name, customer_phone, and delivery_address when calling place_order.\n"
        "7. Do not place an order if the cart is empty.\n"
        "8. Provide clear subtotal, discount, and order totals in confirmation messages.\n"
        "9. Use track_order for tracking order status and get_order_history for past orders.\n"
        "10. Handle special cooking requests (e.g. 'extra spicy', 'no onions') using the notes parameter when placing order."
    )
    
    clean_history = []
    if history:
        for msg in history:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
                if role == "user" and content:
                    clean_history.append({"role": "user", "content": content})
                elif role == "assistant" and content and not msg.get("tool_calls"):
                    clean_history.append({"role": "assistant", "content": content})

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(clean_history)
    messages.append({"role": "user", "content": user_message})
    
    max_turns = 8
    for _ in range(max_turns):
        response, current_provider = make_completion_call(messages)
        message = response.choices[0].message
        
        if not message.tool_calls:
            clean_history.append({"role": "user", "content": user_message})
            clean_history.append({"role": "assistant", "content": message.content})
            return message.content, clean_history
            
        if message.tool_calls:
            for tc in message.tool_calls:
                if "<|" in tc.function.name:
                    tc.function.name = tc.function.name.split("<|")[0]

        messages.append(message.model_dump(exclude_none=True))
        
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"[TOOL] {tool_name}")
            print(f"[ARGS] {tool_args}")
            
            result = execute_tool(tool_name, tool_args)
            print(f"[RESULT] {result}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(result)
            })
            
    return "Sorry, I could not complete the request. Please try again.", clean_history
