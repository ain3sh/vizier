import { ReactElement, useState, useEffect, useRef } from 'react';
import { 
  SendHorizonal, ChevronDown, ChevronRight, 
  X, Plus, GripVertical, Check, XCircle, Link 
} from 'lucide-react';
import axios from 'axios';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

// Define Source interface
interface Source {
  id: string;
  title: string;
  url: string;
  date: string;
  author: string;
  snippet: string;
  root: string;
}

// Define Phase type
type Phase = 'query_refinement' | 'source_refinement' | 'draft_review';

// API base URL
const API_BASE_URL = 'https://api.example.com';

function Query() {
    const [searchValue, setSearchValue] = useState(''); // State to track the input value
    const [showOverlay, setOverlay] = useState(false); // State to track the expanding animation
    const [responseData, setResponseData] = useState('Please wait while we process your request.'); // State to store API response
    const [currentPhase, setCurrentPhase] = useState<Phase>('query_refinement'); // Track the current phase
    
    // Add new state variables for query refinement
    const [isQuerySatisfactory, setIsQuerySatisfactory] = useState(false);
    const [queryFeedback, setQueryFeedback] = useState<string | null>(null);
    const [refinedQuery, setRefinedQuery] = useState<string | null>(null);
    const [isRefining, setIsRefining] = useState(false);
    
    // Sources state
    const [sources, setSources] = useState<Source[]>([]);
    const [openSourceIds, setOpenSourceIds] = useState<Set<string>>(new Set());
    const [draggedItem, setDraggedItem] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Draft content
    const [draftContent, setDraftContent] = useState('');

    // Add new state for URL input
    const [showUrlInput, setShowUrlInput] = useState(false);
    const [sourceUrl, setSourceUrl] = useState('');
    const [isAddingSource, setIsAddingSource] = useState(false);
    const urlInputRef = useRef<HTMLInputElement>(null);
    
    // Effect to focus the URL input field when it appears
    useEffect(() => {
        if (showUrlInput && urlInputRef.current) {
            urlInputRef.current.focus();
        }
    }, [showUrlInput]);
    
    // Fetch sources on component mount or phase change
    useEffect(() => {
        if (currentPhase === 'source_refinement') {
            fetchSources();
        } else if (currentPhase === 'draft_review') {
            fetchDraft();
        }
    }, [currentPhase]);
    
    // Phase transition handlers
    const handleConfirm = () => {
        if (currentPhase === 'query_refinement') {
            if (isQuerySatisfactory) {
                setCurrentPhase('source_refinement');
            } else {
                // If query is not satisfactory, show refinement interface
                setIsRefining(true);
                if (refinedQuery) {
                    setSearchValue(refinedQuery);
                }
            }
        } else if (currentPhase === 'source_refinement') {
            setCurrentPhase('draft_review');
        } else if (currentPhase === 'draft_review') {
            // Here you would typically submit the final draft
            console.log('Final draft approved');
            // Reset the app
            setOverlay(false);
            setResponseData('Please wait while we process your request.');
            setCurrentPhase('query_refinement');
            setIsQuerySatisfactory(false);
            setRefinedQuery(null);
            setQueryFeedback(null);
        }
    };
    
    const handleDeny = () => {
        if (currentPhase === 'query_refinement') {
            // Reset query refinement
            setResponseData('Please wait while we process your request.');
            setOverlay(false);
        } else if (currentPhase === 'source_refinement') {
            // Go back to query refinement
            setCurrentPhase('query_refinement');
        } else if (currentPhase === 'draft_review') {
            // Go back to source refinement
            setCurrentPhase('source_refinement');
        }
    };
    
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
                    id: 'id1',
                    title: 'Introduction to AI',
                    url: 'https://example.com/ai-intro',
                    date: '2025-03-15',
                    author: 'John Doe',
                    snippet: 'This article provides an overview of modern AI technologies...',
                    root: 'example.com'
                },
                {
                    id: 'id2',
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
    
    // Fetch draft content
    const fetchDraft = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/draft`);
            setDraftContent(response.data.content);
        } catch (error) {
            console.error('Error fetching draft:', error);
            setDraftContent('Based on the sources you provided, here is a draft that synthesizes the information...\n\nArtificial Intelligence (AI) has rapidly evolved in recent years, becoming increasingly integrated into various aspects of our daily lives and industries. From fundamental concepts in machine learning to advanced applications, AI represents a transformative technology with far-reaching implications.\n\nMachine learning, a core component of AI, relies on algorithms that enable systems to learn from data and improve over time without explicit programming. These principles form the foundation for more complex AI systems that can analyze information, recognize patterns, and make predictions with increasing accuracy.');
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
    
    const addSource = () => {
        // Simply show the URL input field
        setShowUrlInput(true);
    };
    
    const handleUrlSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!sourceUrl.trim()) {
            return; // Don't submit empty URLs
        }
        
        setIsAddingSource(true);
        
        try {
            // Send only the URL to the backend
            const response = await axios.post(`${API_BASE_URL}/process-url`, {
                url: sourceUrl
            });
            
            console.log('Processed URL:', response.data);
            
            // Add the processed source to our sources list
            setSources([...sources, response.data]);
            
            // Reset the URL input
            setSourceUrl('');
            setShowUrlInput(false);
        } catch (error) {
            console.error('Error processing URL:', error);
            // You might want to show an error message to the user
        } finally {
            setIsAddingSource(false);
        }
    };
    
    const cancelUrlInput = () => {
        setSourceUrl('');
        setShowUrlInput(false);
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
            fetchSources();
        }
    };
    
    // Drag and drop handlers
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
            fetchSources();
        }
    };

    const handleSend = async () => {
        if (searchValue.trim() === '') {
            return; // Empty input, do nothing
        }
        
        console.log('Send button pressed with input:', searchValue);
        setOverlay(true); // Trigger the expanding animation
        setCurrentPhase('query_refinement');
        setIsRefining(false);

        const currentQuery = searchValue; // Store the current query value

        try {
            // Make POST request with searchValue
            setResponseData('Processing your query...');
            const response = await axios.post(`${API_BASE_URL}/refine-query`, {
                query: searchValue
            });
            
            console.log('POST response:', response.data);
            
            // Check if the query is satisfactory based on the response
            if (response.data.isSatisfactory) {
                setIsQuerySatisfactory(true);
                setRefinedQuery(response.data.refinedQuery || searchValue);
                setQueryFeedback(null);
                setResponseData(`Your query is ready to proceed: "${response.data.refinedQuery || searchValue}"`);
            } else {
                setIsQuerySatisfactory(false);
                setRefinedQuery(response.data.refinedQuery || null);
                setQueryFeedback(response.data.feedback || 'Your query needs refinement.');
                setResponseData(`Your query needs refinement: ${response.data.feedback || 'Please provide more specific details.'}`);
                if (response.data.refinedQuery) {
                    setResponseData(prev => `${prev}\n\nSuggested query: "${response.data.refinedQuery}"`);
                }
            }
            
            // For development/demo purposes
            if (!response.data) {
                // Mock response for testing
                const isMockSatisfactory = Math.random() > 0.5;
                setIsQuerySatisfactory(isMockSatisfactory);
                if (isMockSatisfactory) {
                    setResponseData(`Your query is ready to proceed: "${searchValue}"`);
                    setRefinedQuery(searchValue);
                    setQueryFeedback(null);
                } else {
                    setResponseData(`Your query needs refinement: Please be more specific about what you're looking for.
                    
Suggested query: "${searchValue} with recent developments and practical applications"`);
                    setRefinedQuery(`${searchValue} with recent developments and practical applications`);
                    setQueryFeedback("Please be more specific about what you're looking for.");
                }
            }
        } catch (error) {
            console.error('Error sending query:', error);
            setResponseData('Error processing your request. Please try again.');

            /** TEMPORARILY SET TO TRUE */
            // setIsQuerySatisfactory(false);
            setIsQuerySatisfactory(true);
        }
        
        setRefinedQuery(currentQuery); // Save the query for display
        setSearchValue(''); // Clear input field
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchValue(event.target.value); // Update the state with the input value
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend(); // Trigger the send action on Enter press
        }
    };
    
    // Render confirmation buttons based on current phase
    const renderConfirmationButtons = () => {
        let confirmText = 'Confirm';
        let denyText = 'Deny';
        
        if (currentPhase === 'query_refinement') {
            if (isQuerySatisfactory) {
                confirmText = 'Use This Query';
            } else {
                confirmText = 'Refine Query';
            }
            denyText = 'Cancel';
        } else if (currentPhase === 'source_refinement') {
            confirmText = 'Generate Draft';
            denyText = 'Back to Query';
        } else if (currentPhase === 'draft_review') {
            confirmText = 'Approve Draft';
            denyText = 'Back to Sources';
        }
        
        return (
            <div className="confirmation-buttons">
                <button className="deny-button" onClick={handleDeny}>
                    <XCircle size={16} />
                    <span>{denyText}</span>
                </button>
                <button className="confirm-button" onClick={handleConfirm}>
                    <Check size={16} />
                    <span>{confirmText}</span>
                </button>
            </div>
        );
    };

    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown}/>],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend}/>],
    ];

    // Render progress bar
    const renderProgressBar = () => {
        const phases = ['Query', 'Sources', 'Draft'];
        const currentIndex = 
            currentPhase === 'query_refinement' ? 0 : 
            currentPhase === 'source_refinement' ? 1 : 2;
            
        return (
            <div className="phase-progress">
                <div className="progress-steps">
                    {phases.map((phase, index) => (
                        <div 
                            key={phase}
                            className={`phase-step ${currentIndex >= index ? 'active' : ''} 
                                       ${currentIndex === index ? 'current' : ''}`}
                        >
                            {phase}
                        </div>
                    ))}
                </div>
                <div className="progress-line">
                    <div 
                        className="progress-completed" 
                        style={{ width: `${currentIndex * 50}%` }}
                    ></div>
                </div>
            </div>
        );
    };

    // Modify renderPhase function
    const renderPhase = () => {
        switch (currentPhase) {
            case 'query_refinement':
                return (
                    <div>
                        <h3 className="query-title">{refinedQuery || ''}</h3>
                        <div className="phase-card">
                            <div className="phase-header">
                                <span>Query Refinement</span>
                            </div>
                            <div className="phase-content">
                                <div className="query-refinement-content">
                                    <p className="query-text">{responseData}</p>
                                    
                                    {isRefining && !isQuerySatisfactory && (
                                        <div className="query-refinement-input">
                                            <input
                                                type="text"
                                                value={searchValue}
                                                onChange={handleSearchChange}
                                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                                placeholder="Refine your query..."
                                                className="refine-input"
                                            />
                                            <button 
                                                className="refine-send-btn"
                                                onClick={handleSend}
                                            >
                                                <SendHorizonal size={16} />
                                                <span>Submit Refined Query</span>
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                );
                
            case 'source_refinement':
                return (
                    <div>
                        <div className="phase-card">
                            <div className="phase-header">
                                <span>Sources</span>
                            </div>
                            <div className="phase-content">
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
                                                                    
                                                                    <span>{source.title || 'Untitled Source'}</span>
                                                                    <span style={{display: 'inline-block', fontSize: '14px'}}>
                                                                        {source.root ?
                                                                            `| ${source.root}` : null}
                                                                    </span>
                                                                    <span style={{display: 'inline-block', fontSize: '14px'}}>
                                                                        {source.date ?
                                                                            `| ${source.date}` : null}
                                                                    </span>
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
                                                                        <span style={{color: 'gray', fontSize: '12px'}}>
                                                                            {source.url ? `${source.url} | ` : null}
                                                                        </span>
                                                                        <span style={{color: 'gray', fontSize: '12px'}}>
                                                                            {source.author ? `by ${source.author}` : null}
                                                                        </span>
                                                                    </div>
                                                                    <div className="source-field">
                                                                        <label>{source.snippet}</label>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            
                                            {/* URL Input Field (conditionally rendered) */}
                                            {showUrlInput ? (
                                                <div className="url-input-container">
                                                    <form onSubmit={handleUrlSubmit}>
                                                        <div className="url-input-field">
                                                            <Link size={16} className="url-icon" />
                                                            <input 
                                                                type="url"
                                                                ref={urlInputRef}
                                                                placeholder="Enter URL to source..."
                                                                value={sourceUrl}
                                                                onChange={(e) => setSourceUrl(e.target.value)}
                                                                className="url-input"
                                                            />
                                                            <div className="url-input-actions">
                                                                <button 
                                                                    type="button"
                                                                    className="url-cancel-btn"
                                                                    onClick={cancelUrlInput}
                                                                    disabled={isAddingSource}
                                                                >
                                                                    <X size={16} />
                                                                </button>
                                                                <button 
                                                                    type="submit"
                                                                    className="url-add-btn"
                                                                    disabled={isAddingSource}
                                                                >
                                                                    {isAddingSource ? 'Processing...' : 'Add'}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </form>
                                                </div>
                                            ) : (
                                                <button className="add-source-btn" onClick={addSource}>
                                                    <Plus size={14} /> Add Source
                                                </button>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                );
                
            case 'draft_review':
                return (
                    <div>
                        <div className="phase-card">
                            <div className="phase-header">
                                <span>Draft</span>
                            </div>
                            <div className="phase-content">
                                <div className="draft-content">
                                    <p className="draft-text">{draftContent}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                );
                
            default:
                return null;
        }
    };

    // The main render method
    return (
        <div>
            {/* Overlay container */}
            <div className={`fade-container ${showOverlay ? 'overlay' : ''}`}>
                <div className={`overlay-content ${showOverlay ? 'visible' : ''}`}>               
                    {/* Add progress bar */}
                    {showOverlay && renderProgressBar()}
                    
                    {/* Phase containers */}
                    <div className="phase-containers">
                        {renderPhase()}
                    </div>
                    
                </div>
                {/* Confirmation buttons */}
                {renderConfirmationButtons()}
            </div>

            {/* QueryBar container */}
            <div className={`query-bar-container ${showOverlay ? 'moved' : ''}`}>
                <QueryBar li={queryItems} />
            </div>
        </div>
    );
}

export default Query;