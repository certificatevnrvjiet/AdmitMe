// React Frontend (src/App.js)
import React, { useState, useEffect } from 'react';

function ImageFromDrive({ fileId }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchImage = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/drive/image/${fileId}`); // Adjust the backend URL if needed
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`HTTP error! status: ${response.status}, details: ${errorData?.detail || response.statusText}`);
        }
        const blob = await response.blob();
        setImageUrl(URL.createObjectURL(blob));
      } catch (err) {
        console.error('Error fetching image:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (fileId) {
      fetchImage();
    }

    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl); // Clean up the object URL
      }
    };
  }, [fileId]);

  if (loading) {
    return <div>Loading image...</div>;
  }

  if (error) {
    return <div>Error loading image: {error}</div>;
  }

  return (
    <div>
      {imageUrl && <img src={imageUrl} alt="Image from Google Drive" />}
      <h1>{imageUrl}</h1>
      {!imageUrl && !loading && !error && <p>No image to display.</p>}
    </div>
  );
}

function App() {
  const [googleDriveFileId, setGoogleDriveFileId] = useState('');

  const handleInputChange = (event) => {
    setGoogleDriveFileId(event.target.value);
  };

  return (
    <div>
      <h1>Display Image from Google Drive</h1>
      <div>
        <label htmlFor="fileId">Google Drive File ID:</label>
        <input
          type="text"
          id="fileId"
          value={googleDriveFileId}
          onChange={handleInputChange}
          placeholder="Enter Google Drive File ID"
        />
      </div>
      <ImageFromDrive fileId={googleDriveFileId} />
    </div>
  );
}

export default App;