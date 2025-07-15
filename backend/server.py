import os
import json
import asyncio
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
IRYS_GATEWAY_URL = "https://gateway.irys.xyz"
IRYS_GRAPHQL_URL = "https://gateway.irys.xyz/graphql"

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
        self.gateway_url = IRYS_GATEWAY_URL
        self.graphql_url = IRYS_GRAPHQL_URL
        
    def is_valid_username(self, username: str) -> bool:
        """Validate username format: 3-20 characters, alphanumeric + underscore"""
        import re
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
    
    async def upload_username_to_irys(self, username: str, owner_address: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload username data to Irys using Node.js helper service"""
        try:
            normalized_username = username.lower()
            normalized_owner = owner_address.lower()
            
            # Prepare data for Irys helper service
            upload_data = {
                "username": normalized_username,
                "owner": normalized_owner,
                "metadata": metadata or {}
            }
            
            logger.info(f"Uploading username '{username}' to Irys via helper service")
            
            # Call the Node.js helper service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:3002/upload",
                    json=upload_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully uploaded username '{username}' with tx ID: {result['id']}")
                    return result
                else:
                    error_detail = response.text
                    logger.error(f"Irys helper service error: {error_detail}")
                    return {"success": False, "error": f"Upload failed: {error_detail}"}
            
        except Exception as error:
            logger.error(f"Upload error: {error}")
            return {"success": False, "error": str(error)}
    
    async def check_username_availability(self, username: str) -> bool:
        """Check if username is available using GraphQL query"""
        try:
            normalized_username = username.lower()
            
            # Use real GraphQL query to Irys
            query = """
            query($username: String!) {
                transactions(
                    tags: [
                        { name: "App-Name", values: ["IrysUsername"] },
                        { name: "Type", values: ["username-registration"] },
                        { name: "Username", values: [$username] }
                    ],
                    first: 1
                ) {
                    edges {
                        node { 
                            id 
                            tags {
                                name
                                value
                            }
                        }
                    }
                }
            }
            """
            
            # Check in-memory storage first (for demo)
            if hasattr(self, '_storage') and normalized_username in self._storage:
                return False
            
            # Make GraphQL request to Irys
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_url,
                    json={
                        "query": query,
                        "variables": {"username": normalized_username}
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    edges = result.get("data", {}).get("transactions", {}).get("edges", [])
                    available = len(edges) == 0
                    logger.info(f"Username '{username}' availability check: {available}")
                    return available
                else:
                    logger.error(f"GraphQL query failed with status {response.status_code}")
                    return True  # Default to available if query fails
            
        except Exception as error:
            logger.error(f"Availability check error: {error}")
            # For demo purposes, return True if there's an error
            return True
    
    async def resolve_username(self, username: str) -> Optional[UsernameRecord]:
        """Resolve username to owner record"""
        try:
            normalized_username = username.lower()
            
            # Use real GraphQL query to Irys
            query = """
            query($username: String!) {
                transactions(
                    tags: [
                        { name: "App-Name", values: ["IrysUsername"] },
                        { name: "Type", values: ["username-registration"] },
                        { name: "Username", values: [$username] }
                    ],
                    first: 1
                ) {
                    edges {
                        node {
                            id
                            tags {
                                name
                                value
                            }
                            block {
                                timestamp
                            }
                        }
                    }
                }
            }
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_url,
                    json={
                        "query": query,
                        "variables": {"username": normalized_username}
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    edges = result.get("data", {}).get("transactions", {}).get("edges", [])
                    
                    if edges:
                        node = edges[0]["node"]
                        tags = {tag["name"]: tag["value"] for tag in node["tags"]}
                        
                        return UsernameRecord(
                            id=node["id"],
                            username=tags.get("Username", normalized_username),
                            owner=tags.get("Owner", ""),
                            timestamp=int(tags.get("Timestamp", 0))
                        )
            
            return None
            
        except Exception as error:
            logger.error(f"Resolve username error: {error}")
            return None

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
    return {"message": "Irys Username API is running!", "version": "1.0.0"}

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
        result = await irys_service.upload_username_to_irys(
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