import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from eth_utils import to_checksum_address
from eth_account import Account
from eth_account.messages import encode_defunct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Irys Username API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "725bbe9ad10ef6b48397d37501ff0c908119fdc0513a85a046884fc9157c80f5")
IRYS_RPC_URL = "https://rpc.devnet.irys.xyz/v1"
IRYS_GATEWAY_URL = "https://gateway.irys.xyz"

# Pydantic models
class UsernameRegistrationRequest(BaseModel):
    username: str
    address: str
    signature: str
    metadata: Optional[Dict[str, Any]] = {}

class UsernameAvailabilityResponse(BaseModel):
    username: str
    available: bool

class UsernameRegistrationResponse(BaseModel):
    success: bool
    username: str
    owner: str
    tx_id: str
    explorer_url: str
    message: str

class UsernameRecord(BaseModel):
    id: str
    username: str
    owner: str
    timestamp: int

class IrysService:
    def __init__(self):
        self.private_key = PRIVATE_KEY
        self.rpc_url = IRYS_RPC_URL
        self.gateway_url = IRYS_GATEWAY_URL
        self.initialized = False
        
    def is_valid_username(self, username: str) -> bool:
        """Validate username format: 3-20 characters, alphanumeric + underscore"""
        import re
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
    
    async def upload_username(self, username: str, owner_address: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload username data to Irys using HTTP API"""
        try:
            normalized_username = username.lower()
            normalized_owner = owner_address.lower()
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # Prepare data payload
            data = {
                "username": normalized_username,
                "owner": normalized_owner,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "version": "1.0.0"
            }
            
            # Prepare tags for the transaction
            tags = [
                {"name": "App-Name", "value": "IrysUsername"},
                {"name": "Type", "value": "username-registration"},
                {"name": "Username", "value": normalized_username},
                {"name": "Owner", "value": normalized_owner},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Version", "value": "1.0.0"},
                {"name": "Timestamp", "value": str(timestamp)}
            ]
            
            # For devnet, we'll simulate the upload and return a mock transaction ID
            # In real implementation, this would use the Irys SDK
            mock_tx_id = f"irys_tx_{normalized_username}_{timestamp}"
            
            logger.info(f"Simulated upload for username '{username}' with tx ID: {mock_tx_id}")
            
            return {
                "success": True,
                "id": mock_tx_id,
                "username": normalized_username,
                "owner": normalized_owner,
                "timestamp": timestamp
            }
            
        except Exception as error:
            logger.error(f"Upload error: {error}")
            return {"success": False, "error": str(error)}
    
    async def check_username_availability(self, username: str) -> bool:
        """Check if username is available using GraphQL query simulation"""
        try:
            normalized_username = username.lower()
            
            # Simulate GraphQL query to Irys
            # In real implementation, this would query the actual Irys GraphQL endpoint
            query = """
            query {
                transactions(
                    tags: [
                        { name: "App-Name", values: ["IrysUsername"] },
                        { name: "Type", values: ["username-registration"] },
                        { name: "Username", values: ["%s"] }
                    ],
                    first: 1
                ) {
                    edges {
                        node { id }
                    }
                }
            }
            """ % normalized_username
            
            # For demo purposes, simulate some taken usernames
            taken_usernames = ["admin", "test", "demo", "alice", "bob", "charlie"]
            available = normalized_username not in taken_usernames
            
            logger.info(f"Username '{username}' availability check: {available}")
            return available
            
        except Exception as error:
            logger.error(f"Availability check error: {error}")
            raise HTTPException(status_code=500, detail="Error checking availability")
    
    async def get_usernames(self, limit: int = 100) -> List[UsernameRecord]:
        """Get list of registered usernames"""
        try:
            # Simulate fetching from Irys GraphQL
            # In real implementation, this would query the actual Irys endpoint
            mock_usernames = [
                {
                    "id": "irys_tx_demo_1699564800000",
                    "username": "demo",
                    "owner": "0x742d35cc6634c0532925a3b844bc9e7595f2bd7e",
                    "timestamp": 1699564800000
                },
                {
                    "id": "irys_tx_alice_1699564900000", 
                    "username": "alice",
                    "owner": "0x8ba1f109551bd432803012645hac136c4975ac8",
                    "timestamp": 1699564900000
                },
                {
                    "id": "irys_tx_bob_1699565000000",
                    "username": "bob", 
                    "owner": "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5",
                    "timestamp": 1699565000000
                }
            ]
            
            return [UsernameRecord(**record) for record in mock_usernames[:limit]]
            
        except Exception as error:
            logger.error(f"Get usernames error: {error}")
            raise HTTPException(status_code=500, detail="Error fetching usernames")
    
    async def resolve_username(self, username: str) -> Optional[UsernameRecord]:
        """Resolve username to owner record"""
        try:
            normalized_username = username.lower()
            
            # Simulate resolution using mock data
            mock_records = {
                "demo": {
                    "id": "irys_tx_demo_1699564800000",
                    "username": "demo",
                    "owner": "0x742d35cc6634c0532925a3b844bc9e7595f2bd7e",
                    "timestamp": 1699564800000
                },
                "alice": {
                    "id": "irys_tx_alice_1699564900000",
                    "username": "alice", 
                    "owner": "0x8ba1f109551bd432803012645hac136c4975ac8",
                    "timestamp": 1699564900000
                },
                "bob": {
                    "id": "irys_tx_bob_1699565000000",
                    "username": "bob",
                    "owner": "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5", 
                    "timestamp": 1699565000000
                }
            }
            
            if normalized_username in mock_records:
                return UsernameRecord(**mock_records[normalized_username])
            
            return None
            
        except Exception as error:
            logger.error(f"Resolve username error: {error}")
            raise HTTPException(status_code=500, detail="Error resolving username")

# Initialize Irys service
irys_service = IrysService()

def verify_signature(message: str, signature: str, expected_address: str) -> bool:
    """Verify Ethereum signature"""
    try:
        # Create message hash
        message_hash = encode_defunct(text=message)
        
        # Recover address from signature
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == expected_address.lower()
        
    except Exception as error:
        logger.error(f"Signature verification error: {error}")
        return False

@app.get("/")
async def root():
    return {"message": "Irys Username API is running!"}

@app.get("/api/username/check/{username}", response_model=UsernameAvailabilityResponse)
async def check_username_availability(username: str):
    """Check if a username is available"""
    try:
        # Validate username format
        if not irys_service.is_valid_username(username):
            raise HTTPException(
                status_code=400,
                detail="Invalid username format. Must be 3-20 characters (letters, numbers, underscores)"
            )
        
        available = await irys_service.check_username_availability(username)
        
        return UsernameAvailabilityResponse(
            username=username,
            available=available
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Check availability error: {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/username/register", response_model=UsernameRegistrationResponse)
async def register_username(request: UsernameRegistrationRequest):
    """Register a new username"""
    try:
        # Validate username format
        if not irys_service.is_valid_username(request.username):
            raise HTTPException(
                status_code=400,
                detail="Invalid username format"
            )
        
        # Check availability
        available = await irys_service.check_username_availability(request.username)
        if not available:
            raise HTTPException(
                status_code=409,
                detail="Username is already taken"
            )
        
        # Verify signature
        message = f"Register username: {request.username}"
        if not verify_signature(message, request.signature, request.address):
            raise HTTPException(
                status_code=401,
                detail="Signature verification failed"
            )
        
        # Upload to Irys
        result = await irys_service.upload_username(
            request.username,
            request.address,
            request.metadata
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Upload failed")
            )
        
        return UsernameRegistrationResponse(
            success=True,
            username=request.username,
            owner=request.address,
            tx_id=result["id"],
            explorer_url=f"{IRYS_GATEWAY_URL}/{result['id']}",
            message=f"{request.username}.irys registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Registration error: {error}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/usernames")
async def get_usernames(limit: int = 100):
    """Get list of registered usernames (leaderboard)"""
    try:
        usernames = await irys_service.get_usernames(limit)
        return {
            "count": len(usernames),
            "usernames": [username.dict() for username in usernames]
        }
        
    except Exception as error:
        logger.error(f"Get usernames error: {error}")
        raise HTTPException(status_code=500, detail="Failed to fetch usernames")

@app.get("/api/resolve/{username}")
async def resolve_username(username: str):
    """Resolve username to owner address"""
    try:
        record = await irys_service.resolve_username(username)
        
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Username not found"
            )
        
        return record.dict()
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Resolve username error: {error}")
        raise HTTPException(status_code=500, detail="Failed to resolve username")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)