import { ReactElement, useState, useEffect } from 'react';
import { Textfit } from 'react-textfit';
import { CircleStop, SendHorizonal, ChevronDown, ChevronRight, X, Plus, GripVertical } from 'lucide-react';
import axios from 'axios';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

// Define Source interface
interface Source {
  id: string;
  name: string;
  title: string;
  url: string;
  date: string;
  author: string;
  snippet: string;
  root: string;
}

// API base URL - replace with your actual API base URL when ready
const API_BASE_URL = 'https://api.example.com';

function Query() {
    const [searchValue, setSearchValue] = useState(''); // State to track the input value
    const [showOverlay, setOverlay] = useState(false); // State to track the expanding animation
    const [responseData, setResponseData] = useState('Please wait while we process your request.'); // State to store API response
    
    // Sources state
    const [sources, setSources] = useState<Source[]>([]);
    const [isSourcesOpen, setIsSourcesOpen] = useState(false);
    const [openSourceIds, setOpenSourceIds] = useState<Set<string>>(new Set());
    const [draggedItem, setDraggedItem] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Fetch sources on component mount
    useEffect(() => {
        fetchSources();
    }, []);
    
    // Fetch sources from API
    const fetchSources = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`${API_BASE_URL}/sources`);
            console.log('Fetched sources:', response.data);
            setSources(response.data);
        } catch (error) {
            console.error('Error fetching sources:', error);
            // setError('Failed to load sources. Please try again later.');
            
            // For development - create sample sources when API fails
            setSources([
                {
                    id: 'source-1',
                    name: 'Sample Source 1',
                    title: 'Introduction to AI',
                    url: 'https://example.com/ai-intro',
                    date: '2025-03-15',
                    author: 'John Doe',
                    snippet: 'This article provides an overview of modern AI technologies...',
                    root: 'example.com'
                },
                {
                    id: 'source-2',
                    name: 'Sample Source 2',
                    title: 'Machine Learning Fundamentals',
                    url: 'https://medium.com/ml-fundamentals',
                    date: '2025-02-28',
                    author: 'Jane Smith',
                    snippet: 'Understanding the core principles of machine learning...',
                    root: 'medium.com'
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };
    
    // Source handlers
    const toggleSourceOpen = (sourceId: string) => {
        const newOpenSourceIds = new Set(openSourceIds);
        if (newOpenSourceIds.has(sourceId)) {
            newOpenSourceIds.delete(sourceId);
        } else {
            newOpenSourceIds.add(sourceId);
        }
        setOpenSourceIds(newOpenSourceIds);
    };
    
    const addSource = async () => {
        const newSource: Source = {
            id: `source-${Date.now()}`,
            name: `Source ${sources.length + 1}`,
            title: '',
            url: '',
            date: '',
            author: '',
            snippet: '',
            root: '',
        };
        
        try {
            // Optimistically update UI
            setSources([...sources, newSource]);
            
            // Make API call to add source
            const response = await axios.post(`${API_BASE_URL}/sources`, newSource);
            console.log('Added source:', response.data);
            
            // Update with server response (it might include additional fields or normalized data)
            const updatedSources = sources.map(s => 
                s.id === newSource.id ? response.data : s
            );
            setSources([...updatedSources]);
        } catch (error) {
            console.error('Error adding source:', error);
            // Keep the optimistic update for better UX, but show an error notification if needed
        }
    };
    
    const removeSource = async (sourceId: string) => {
        try {
            // Optimistically update UI
            setSources(sources.filter(source => source.id !== sourceId));
            
            // Make API call to remove source
            await axios.delete(`${API_BASE_URL}/sources/${sourceId}`);
            console.log('Removed source:', sourceId);
        } catch (error) {
            console.error('Error removing source:', error);
            // Revert the optimistic update if needed
            fetchSources();
        }
    };
    
    const updateSource = async (index: number, field: keyof Source, value: string) => {
        const sourceToUpdate = sources[index];
        const updatedSource = { ...sourceToUpdate, [field]: value };
        
        try {
            // Optimistically update UI
            const newSources = [...sources];
            newSources[index] = updatedSource;
            setSources(newSources);
            
            // Make API call to update source
            await axios.put(`${API_BASE_URL}/sources/${sourceToUpdate.id}`, updatedSource);
            console.log('Updated source:', updatedSource);
        } catch (error) {
            console.error('Error updating source:', error);
            // Revert the optimistic update if needed
            fetchSources();
        }
    };
    
    const handleDragStart = (index: number) => {
        setDraggedItem(index);
    };
    
    const handleDragOver = (e: React.DragEvent, index: number) => {
        e.preventDefault();
        
        if (draggedItem === null) return;
        
        const items = [...sources];
        const draggedItemContent = items[draggedItem];
        items.splice(draggedItem, 1);
        items.splice(index, 0, draggedItemContent);
        
        setDraggedItem(index);
        setSources(items);
    };
    
    const handleDragEnd = async () => {
        setDraggedItem(null);
        
        try {
            // Make API call to update source order
            await axios.put(`${API_BASE_URL}/sources/order`, {
                sourceIds: sources.map(source => source.id)
            });
            console.log('Updated source order:', sources.map(source => source.id));
        } catch (error) {
            console.error('Error updating source order:', error);
            // Fetch the sources again to ensure we have the correct order from the server
            fetchSources();
        }
    };

    const handleSend = async () => {
        if (searchValue.trim() === '') {
            return; // Empty input, do nothing
        }
        
        console.log('Send button pressed with input:', searchValue);
        setOverlay(true); // Trigger the expanding animation

        // set overlay-title as query text
        const overlayTitle = document.querySelector('.overlay-title') as HTMLElement;
        if (overlayTitle) {
            overlayTitle.textContent = searchValue;
        }
        
        try {
            // Make POST request with searchValue
            const response = await axios.post(`${API_BASE_URL}/query`, {
                query: searchValue
            });
            
            console.log('POST response:', response.data);
            
            // After successful POST, fetch the results
            fetchResults(response.data.id || 'default-id');
        } catch (error) {
            console.error('Error sending query:', error);
            setResponseData('Error processing your request. Please try again.');
        }
        
        setSearchValue(''); // Clear input field
    };
    
    const fetchResults = async (queryId: string) => {
        try {
            // Simulate delay for showing loading state
            setResponseData('Fetching results...');
            
            // Make GET request to fetch results
            const response = await axios.get(`${API_BASE_URL}/results/${queryId}`);
            
            console.log('GET response:', response.data);
            
            // Update the overlay text with the response
            setResponseData(response.data.result || 'No results found.');
        } catch (error) {
            console.error('Error fetching results:', error);
            setResponseData('Error retrieving results. Please try again.');
        }
    };

    const handleStop = () => {
        // Add this line to ensure the animation has time to complete
        const fadeContainer = document.querySelector('.fade-container') as HTMLElement;
        if (fadeContainer) {
            fadeContainer.style.transition = 'all 0.5s ease-in-out';
        }
        setOverlay(false); // Reset the overlay state when Stop is clicked
        setResponseData('Please wait while we process your request.'); // Reset response text
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchValue(event.target.value); // Update the state with the input value
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend(); // Trigger the send action on Enter press
        }
    };

    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown}/>],
        ['Stop', <CircleStop size={40} className="stop-btn" onClick={handleStop}/>],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend}/>],
    ];

    return (
        <div>
            {/* Overlay container */}
            <div className={`fade-container ${showOverlay ? 'overlay' : ''}`}>
                <div className={`overlay-content ${showOverlay ? 'visible' : ''}`}>
                    <Textfit 
                        mode="multi"
                        min={12}
                        max={48}
                        style={{
                            height: '100%',
                            width: '80%',
                        }}
                    >
                        <p className="overlay-title"></p>
                    </Textfit>
                    <div className="sources">
                        <div className="sources-card">
                            <div 
                                className="sources-header" 
                                onClick={() => setIsSourcesOpen(!isSourcesOpen)}
                            >
                                {isSourcesOpen ? 
                                    <ChevronDown size={16} className="chevron-icon" /> : 
                                    <ChevronRight size={16} className="chevron-icon" />
                                }
                                <span>Sources</span>
                            </div>
                            
                            {isSourcesOpen && (
                                <div className="sources-content">
                                    {isLoading ? (
                                        <div className="loading-indicator">Loading sources...</div>
                                    ) : error ? (
                                        <div className="error-message">{error}</div>
                                    ) : (
                                        <>
                                            <div className="sources-list">
                                                {sources.map((source, index) => (
                                                    <div 
                                                        key={source.id}
                                                        className="source-item"
                                                        draggable={true}
                                                        onDragStart={() => handleDragStart(index)}
                                                        onDragOver={(e) => handleDragOver(e, index)}
                                                        onDragEnd={handleDragEnd}
                                                    >
                                                        <div className="source-card">
                                                            <div className="source-header">
                                                                <div className="drag-handle">
                                                                    <GripVertical size={14} />
                                                                </div>
                                                                <div 
                                                                    className="source-title"
                                                                    onClick={() => toggleSourceOpen(source.id)}
                                                                >
                                                                    {openSourceIds.has(source.id) ? 
                                                                        <ChevronDown size={14} /> : 
                                                                        <ChevronRight size={14} />
                                                                    }
                                                                    <span>{source.name}</span>
                                                                </div>
                                                                <X 
                                                                    size={14} 
                                                                    className="delete-icon" 
                                                                    onClick={() => removeSource(source.id)} 
                                                                />
                                                            </div>
                                                            
                                                            {openSourceIds.has(source.id) && (
                                                                <div className="source-details">
                                                                    <div className="source-field">
                                                                        <label>Title:</label>
                                                                        <input 
                                                                            type="text"
                                                                            value={source.title}
                                                                            onChange={(e) => updateSource(index, 'title', e.target.value)}
                                                                        />
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>URL:</label>
                                                                        <input 
                                                                            type="text"
                                                                            value={source.url}
                                                                            onChange={(e) => updateSource(index, 'url', e.target.value)}
                                                                        />
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>Date:</label>
                                                                        <input 
                                                                            type="text"
                                                                            value={source.date}
                                                                            onChange={(e) => updateSource(index, 'date', e.target.value)}
                                                                        />
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>Author:</label>
                                                                        <input 
                                                                            type="text"
                                                                            value={source.author}
                                                                            onChange={(e) => updateSource(index, 'author', e.target.value)}
                                                                        />
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>Root:</label>
                                                                        <input 
                                                                            type="text"
                                                                            value={source.root}
                                                                            onChange={(e) => updateSource(index, 'root', e.target.value)}
                                                                        />
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>Snippet:</label>
                                                                        <textarea 
                                                                            value={source.snippet}
                                                                            onChange={(e) => updateSource(index, 'snippet', e.target.value)}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            <button className="add-source-btn" onClick={addSource}>
                                                <Plus size={14} /> Add Source
                                            </button>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                    <p className="overlay-text">{responseData}</p>
                </div>
            </div>

            {/* QueryBar container */}
            <div className={`query-bar-container ${showOverlay ? 'moved' : ''}`}>
                <QueryBar li={queryItems} />
            </div>
        </div>
    );
}

export default Query;