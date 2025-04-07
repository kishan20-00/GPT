import React, { useState, useEffect } from "react";

function ApiKeys() {
  const [showModal, setShowModal] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [apiKeys, setApiKeys] = useState([]);
  const [newApiKey, setNewApiKey] = useState(null);
  const [isCopied, setIsCopied] = useState(false);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    const response = await fetch("http://localhost:8000/api/keys");
    const data = await response.json();
    setApiKeys(data.api_keys);
  };

  const handleCreateApiKey = async () => {
    const res = await fetch("http://localhost:8000/api/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_name: displayName })
    });

    const data = await res.json();
    setApiKeys(prev => [
      ...prev,
      { display_name: displayName, key: data.api_key }
    ]);
    setNewApiKey(data.api_key);
    setShowModal(false);
  };

  const handleDeleteApiKey = async (apiKey) => {
    await fetch(`http://localhost:8000/api/keys/${apiKey}`, {
      method: "DELETE",
    });
    setApiKeys(apiKeys.filter(key => key.key !== apiKey));
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(newApiKey);
    setIsCopied(true);
  };

  const handleDone = () => {
    setShowModal(false);
    setIsCopied(false);
    setNewApiKey(null);  // Reset the new API key to prevent it from being displayed after it's copied.
  };

  return (
    <div style={{ padding: "2rem", backgroundColor: "#f6f6f6", minHeight: "100vh" }}>
      <h2>API Key Management</h2>
      <button
        onClick={() => setShowModal(true)}
        style={{ margin: "1rem 0", padding: "0.5rem 1rem", backgroundColor: "#000", color: "#fff", border: "none", cursor: "pointer" }}
      >
        Create API Key
      </button>

      {/* Create API Key Modal */}
      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Create API Key</h3>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Enter display name"
              style={{ padding: "0.5rem", borderRadius: "8px", border: "1px solid #ccc" }}
            />
            <button
              onClick={handleCreateApiKey}
              style={{ marginTop: "1rem", padding: "0.5rem 1rem", backgroundColor: "#4caf50", color: "#fff", border: "none", cursor: "pointer" }}
            >
              Submit
            </button>
            <button
              onClick={() => setShowModal(false)}
              style={{ marginTop: "1rem", padding: "0.5rem 1rem", backgroundColor: "#f44336", color: "#fff", border: "none", cursor: "pointer" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* New API Key Modal (Shown after creating a key) */}
      {newApiKey && (
        <div className="modal">
          <div className="modal-content">
            <h3>Your new API key has been created.</h3>
            <input
              type="text"
              value={newApiKey}
              readOnly
              style={{ padding: "0.5rem", width: "100%", borderRadius: "8px", border: "1px solid #ccc" }}
            />
            {!isCopied && (
              <button
                onClick={handleCopyKey}
                style={{
                  marginTop: "1rem",
                  padding: "0.5rem 1rem",
                  backgroundColor: "#000",
                  color: "#fff",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Copy
              </button>
            )}
            {isCopied && <p>✅ Key Copied to Clipboard!</p>}
            <button
              onClick={handleDone}
              style={{
                marginTop: "1rem",
                padding: "0.5rem 1rem",
                backgroundColor: "#4caf50",
                color: "#fff",
                border: "none",
                cursor: "pointer",
              }}
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <table style={{ marginTop: "2rem", width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>Name</th>
            <th>API Key</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map((key, index) => (
            <tr key={index}>
              <td>{key.display_name}</td>
              <td>{key.key.slice(0, 3)}...</td> {/* Show only first 3 characters */}
              <td>
                <button
                  onClick={() => handleDeleteApiKey(key.key)}
                  style={{
                    padding: "0.5rem 1rem",
                    backgroundColor: "#f44336",
                    color: "#fff",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ApiKeys;
