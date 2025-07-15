const express = require('express');
const cors = require('cors');
const Irys = require('@irys/sdk').default;
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Initialize Irys client
let irys = null;

const initializeIrys = async () => {
  try {
    const privateKey = process.env.PRIVATE_KEY;
    if (!privateKey) {
      throw new Error('PRIVATE_KEY environment variable not set');
    }

    irys = new Irys({
      network: 'devnet', // Use devnet for free uploads
      token: 'ethereum', // Use ethereum for devnet
      key: privateKey,
    });

    console.log('✅ Irys client initialized successfully');
    console.log('📍 Network:', irys.network);
    console.log('🔑 Address:', irys.address);
    
    // Check balance
    const balance = await irys.getBalance(irys.address);
    console.log('💰 Balance:', balance.toString());
    
  } catch (error) {
    console.error('❌ Failed to initialize Irys client:', error);
    throw error;
  }
};

// Upload username data to Irys
app.post('/upload', async (req, res) => {
  try {
    const { username, owner, metadata } = req.body;
    
    if (!username || !owner) {
      return res.status(400).json({ error: 'Username and owner are required' });
    }

    if (!irys) {
      await initializeIrys();
    }

    // Prepare username data
    const usernameData = {
      username: username.toLowerCase(),
      owner: owner.toLowerCase(),
      timestamp: Date.now(),
      metadata: metadata || {},
      version: '1.0.0'
    };

    // Create tags for querying
    const tags = [
      { name: 'Content-Type', value: 'application/json' },
      { name: 'App-Name', value: 'IrysUsername' },
      { name: 'Type', value: 'username-registration' },
      { name: 'Username', value: username.toLowerCase() },
      { name: 'Owner', value: owner.toLowerCase() },
      { name: 'Timestamp', value: Date.now().toString() },
      { name: 'Version', value: '1.0.0' }
    ];

    console.log('📤 Uploading username data to Irys:', {
      username: username.toLowerCase(),
      owner: owner.toLowerCase()
    });

    // Upload to Irys
    const receipt = await irys.upload(JSON.stringify(usernameData), {
      tags: tags
    });

    console.log('✅ Upload successful:', {
      id: receipt.id,
      timestamp: receipt.timestamp
    });

    res.json({
      success: true,
      id: receipt.id,
      timestamp: receipt.timestamp,
      username: username.toLowerCase(),
      owner: owner.toLowerCase(),
      explorer_url: `https://devnet.irys.xyz/${receipt.id}`
    });

  } catch (error) {
    console.error('❌ Upload error:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// Get balance
app.get('/balance', async (req, res) => {
  try {
    if (!irys) {
      await initializeIrys();
    }
    
    const balance = await irys.getBalance(irys.address);
    res.json({
      balance: balance.toString(),
      address: irys.address
    });
  } catch (error) {
    console.error('❌ Balance check error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    irys_initialized: irys !== null 
  });
});

const PORT = process.env.PORT || 3002;

app.listen(PORT, async () => {
  console.log(`🚀 Irys helper service running on port ${PORT}`);
  try {
    await initializeIrys();
  } catch (error) {
    console.error('❌ Failed to initialize Irys on startup:', error);
  }
});