import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Wallet connection utilities
const connectWallet = async () => {
  if (!window.ethereum) {
    throw new Error("MetaMask is not installed");
  }
  
  await window.ethereum.request({ method: 'eth_requestAccounts' });
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const address = await signer.getAddress();
  
  return { provider, signer, address };
};

const signMessage = async (signer, message) => {
  return await signer.signMessage(message);
};

// Username Registration Component
const UsernameRegistration = () => {
  const [walletAddress, setWalletAddress] = useState('');
  const [connected, setConnected] = useState(false);
  const [username, setUsername] = useState('');
  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const handleConnectWallet = async () => {
    try {
      const { address } = await connectWallet();
      setWalletAddress(address);
      setConnected(true);
      setStatusMessage(`Connected: ${address.slice(0, 6)}...${address.slice(-4)}`);
    } catch (err) {
      setStatusMessage(`Connection failed: ${err.message}`);
    }
  };

  const checkAvailability = async () => {
    if (!username || username.length < 3) {
      setStatusMessage('Username must be at least 3 characters');
      return;
    }

    setLoading(true);
    setStatusMessage('Checking availability...');
    setAvailability(null);

    try {
      const response = await axios.get(`${API_URL}/api/username/check/${username}`);
      const { available } = response.data;
      setAvailability(available);
      setStatusMessage(
        available 
          ? `✅ "${username}.irys" is available!` 
          : `❌ "${username}.irys" is already taken.`
      );
    } catch (err) {
      console.error(err);
      setStatusMessage('Error checking availability.');
    } finally {
      setLoading(false);
    }
  };

  const registerUsername = async () => {
    if (!connected) {
      setStatusMessage('Please connect your wallet first.');
      return;
    }
    
    if (!username) {
      setStatusMessage('Please enter a username.');
      return;
    }
    
    if (availability === false) {
      setStatusMessage('Username is already taken. Choose another.');
      return;
    }

    try {
      setLoading(true);
      setStatusMessage('Sign the message in your wallet...');
      
      // Get signer
      const { signer } = await connectWallet();
      
      // Sign registration message
      const message = `Register username: ${username}`;
      const signature = await signMessage(signer, message);

      setStatusMessage('Registering username on Irys...');
      
      // Call backend API
      const response = await axios.post(`${API_URL}/api/username/register`, {
        username,
        address: walletAddress,
        signature,
        metadata: {
          registeredAt: new Date().toISOString(),
          network: 'Irys Testnet'
        }
      });

      if (response.data.success) {
        setStatusMessage(`✅ Successfully registered "${username}.irys"!`);
        setUsername('');
        setAvailability(null);
      }
    } catch (err) {
      console.error(err);
      const errorMessage = err.response?.data?.detail || err.message;
      setStatusMessage(`Registration failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="registration-container">
      <div className="header">
        <h1>🔐 Irys Username System</h1>
        <p>Register your unique username on the Irys datachain</p>
      </div>

      <div className="wallet-section">
        {!connected ? (
          <button onClick={handleConnectWallet} className="connect-btn">
            Connect Wallet
          </button>
        ) : (
          <div className="wallet-info">
            <div className="wallet-address">
              {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
            </div>
            <div className="wallet-status">✅ Connected</div>
          </div>
        )}
      </div>

      <div className="username-section">
        <div className="input-group">
          <input
            type="text"
            placeholder="Enter username"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value.toLowerCase());
              setAvailability(null);
            }}
            disabled={loading}
            className="username-input"
          />
          <span className="domain-suffix">.irys</span>
        </div>

        <div className="actions">
          <button 
            onClick={checkAvailability}
            disabled={loading || !username}
            className="check-btn"
          >
            {loading ? 'Checking...' : 'Check Availability'}
          </button>
          
          <button 
            onClick={registerUsername}
            disabled={!connected || loading || availability === false || !username}
            className="register-btn"
          >
            {loading ? 'Processing...' : 'Register Name'}
          </button>
        </div>

        {statusMessage && (
          <div className={`status-message ${availability === true ? 'success' : availability === false ? 'error' : ''}`}>
            {statusMessage}
          </div>
        )}
      </div>
    </div>
  );
};

// Username Resolver Component
const UsernameResolver = () => {
  const [queryName, setQueryName] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const resolveName = async () => {
    if (!queryName) {
      setMessage('Please enter a username');
      return;
    }
    
    setLoading(true);
    setMessage('');
    setResult(null);
    
    try {
      console.log('Resolving username:', queryName);
      const response = await axios.get(`${API_URL}/api/resolve/${queryName}`);
      console.log('Resolve response:', response.data);
      setResult(response.data);
      setMessage(''); // Clear any previous error messages
    } catch (err) {
      console.error('Resolve error:', err);
      if (err.response?.status === 404) {
        setMessage(`Username "${queryName}.irys" not found.`);
      } else {
        setMessage(`Error resolving username: ${err.response?.data?.detail || err.message}`);
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      resolveName();
    }
  };

  return (
    <div className="resolver-container">
      <h2>🔍 Resolve Username</h2>
      
      <div className="input-group">
        <input
          type="text"
          placeholder="Enter username (without .irys)"
          value={queryName}
          onChange={(e) => setQueryName(e.target.value.toLowerCase())}
          onKeyPress={handleKeyPress}
          className="resolver-input"
        />
        <button onClick={resolveName} disabled={loading} className="resolve-btn">
          {loading ? 'Resolving...' : 'Resolve'}
        </button>
      </div>

      {message && <div className="error-message">{message}</div>}
      
      {result && (
        <div className="result-container">
          <h3>{result.username}.irys</h3>
          <div className="result-details">
            <div className="detail-item">
              <strong>Owner:</strong> 
              <span className="address">{result.owner}</span>
            </div>
            <div className="detail-item">
              <strong>Registered:</strong> 
              <span>{new Date(result.timestamp).toLocaleString()}</span>
            </div>
            <div className="detail-item">
              <strong>Irys Tx ID:</strong> 
              <span className="tx-id">{result.id}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Leaderboard Component
const Leaderboard = () => {
  const [usernames, setUsernames] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchUsernames = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/usernames?limit=100`);
      setUsernames(response.data.usernames || []);
    } catch (err) {
      console.error("Error fetching usernames:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsernames();
    // Refresh every 30 seconds
    const interval = setInterval(fetchUsernames, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatAddress = (addr) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString();
  };

  if (loading && usernames.length === 0) {
    return <div className="loading">Loading leaderboard...</div>;
  }

  return (
    <div className="leaderboard-container">
      <h2>🏆 Registered Usernames</h2>
      <div className="stats">
        <span className="count">Total: {usernames.length}</span>
        <button onClick={fetchUsernames} className="refresh-btn">
          Refresh
        </button>
      </div>
      
      {usernames.length > 0 ? (
        <div className="table-container">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Username</th>
                <th>Owner</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {usernames.map((entry, index) => (
                <tr key={entry.id} className="table-row">
                  <td>#{index + 1}</td>
                  <td className="username-cell">{entry.username}.irys</td>
                  <td className="address-cell" title={entry.owner}>
                    {formatAddress(entry.owner)}
                  </td>
                  <td>{formatDate(entry.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <p>No usernames registered yet.</p>
          <p>Be the first to register a username!</p>
        </div>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [activeTab, setActiveTab] = useState('register');

  return (
    <div className="app">
      <nav className="nav-tabs">
        <button 
          onClick={() => setActiveTab('register')}
          className={activeTab === 'register' ? 'tab active' : 'tab'}
        >
          Register
        </button>
        <button 
          onClick={() => setActiveTab('resolve')}
          className={activeTab === 'resolve' ? 'tab active' : 'tab'}
        >
          Resolve
        </button>
        <button 
          onClick={() => setActiveTab('leaderboard')}
          className={activeTab === 'leaderboard' ? 'tab active' : 'tab'}
        >
          Leaderboard
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'register' && <UsernameRegistration />}
        {activeTab === 'resolve' && <UsernameResolver />}
        {activeTab === 'leaderboard' && <Leaderboard />}
      </main>

      <footer className="footer">
        <p>Built on Irys Testnet • Permanent Usernames • No Renewal Fees</p>
      </footer>
    </div>
  );
};

export default App;