import json
import os
import asyncio
from fastapi import FastAPI, HTTPException
from web3 import Web3
import httpx  # Async HTTP client
from fastmcp import FastMCP

# --- Faucet Configuration ---
MONAD_TESTNET_FAUCET_URL = os.getenv("MONAD_TESTNET_FAUCET_URL")  # Read Faucet API address from environment variable
if not MONAD_TESTNET_FAUCET_URL:
    print("Warning: MONAD_TESTNET_FAUCET_URL is not set, Faucet functionality will be unavailable.")
    # For demo purposes
    MONAD_TESTNET_FAUCET_URL = "https://faucet.monad-testnet.network/api/claim"

app = FastAPI()
mcp = FastMCP("Monad DevTools")

@mcp.tool("monad/claim_testnet_faucet")
async def monad_claim_testnet_faucet(recipient_address: str) -> dict:
    """
    Attempt to claim test tokens from known Monad testnet Faucet for a specified address.
    Note: The specific interaction mechanism with the Faucet is assumed.

    Args:
        recipient_address: Ethereum-compatible address to receive MONAD test tokens

    Returns:
        A dictionary with status, message, and transaction hash (if available)
    """
    if not MONAD_TESTNET_FAUCET_URL:
        return {"status": "error", "message": "Faucet URL not configured"}

    if not Web3.is_address(recipient_address):
        return {"status": "error", "message": "Invalid recipient address"}

    try:
        # --- Assuming Faucet provides a simple POST API ---
        payload = {"address": recipient_address}
        # May need to add API Key or other authentication headers
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:  # Set 30 second timeout
            print(f"Requesting from Faucet {MONAD_TESTNET_FAUCET_URL} for address: {recipient_address}")
            response = await client.post(MONAD_TESTNET_FAUCET_URL, json=payload, headers=headers)

            # Check response status code
            if response.status_code == 200 or response.status_code == 201:
                # Try to parse JSON response
                try:
                    response_data = response.json()
                    # Adjust success message based on actual Faucet API response
                    message = response_data.get("message", "Faucet request successful.")
                    tx_hash = response_data.get("txHash")  # Try to get transaction hash
                    return {"status": "success", "message": message, "tx_hash": tx_hash}
                except json.JSONDecodeError:
                    # If not JSON, return text content
                    return {"status": "success", "message": f"Faucet request successful, response: {response.text}"}
            elif response.status_code == 429:  # Handle rate limiting
                return {"status": "error", "message": f"Faucet rate limit: Please try again later. Response: {response.text}"}
            else:
                # Other error status codes
                return {"status": "error", "message": f"Faucet request failed, status code: {response.status_code}, response: {response.text}"}

        # --- Alternative: If Faucet is a smart contract call (requires backend wallet signature) ---
        # faucet_address = "0x..."
        # faucet_abi = '[...]'  # Faucet contract ABI
        # backend_account = Account.from_key("...")  # Backend wallet private key
        # w3 = Web3(...)  # Connect to Monad Testnet
        # faucet_contract = w3.eth.contract(address=faucet_address, abi=faucet_abi)
        # nonce = w3.eth.get_transaction_count(backend_account.address)
        # tx = faucet_contract.functions.requestTokens(recipient_address).build_transaction({...})
        # signed_tx = backend_account.sign_transaction(tx)
        # tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # return {"status": "submitted", "message": f"Faucet claim transaction sent: {tx_hash.hex()}"}

    except httpx.RequestError as e:
        print(f"Faucet request error: {e}")
        return {"status": "error", "message": f"Error connecting to Faucet: {e}"}
    except Exception as e:
        print(f"Unexpected error during Faucet claim: {e}")
        return {"status": "error", "message": f"Unexpected error during Faucet claim: {type(e).__name__}"}

# --- Run MCP server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# --- Register MCP with app ---
app.mount("/mcp", mcp)
